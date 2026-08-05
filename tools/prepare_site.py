"""Build site.json for the dashboard map from the project KML.

Every line segment in the CAD-derived KML is assigned to its nearest MVPS, so
each block carries its own real linework and a hull polygon of its actual
shape. The dashboard colours those shapes by live state and glows them on
faults — the layout on screen is the drawn layout, not a generated grid.

Run:  .venv/Scripts/python tools/prepare_site.py
Out:  src/najm3000/dashboard/static/models/site.json
"""

from __future__ import annotations

import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
KML = ROOT / "Google Earth kml" / "NAJM-3000 PROJECT.kml"
OUT = ROOT / "src" / "najm3000" / "dashboard" / "static" / "models" / "site.json"

#: A segment further than this from every MVPS is site infrastructure
#: (perimeter, main roads) rather than part of a block.
ASSIGN_RADIUS_M = 220.0

#: Segments longer than this are roads or trunk cabling that merely pass
#: through a block; assigning them would stretch the block hull kilometres.
MAX_BLOCK_SEGMENT_M = 320.0


def hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Convex hull (Andrew monotone chain) over (lon, lat) points."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def main() -> None:
    raw = KML.read_text(encoding="utf-8", errors="ignore")

    mvps = []
    for m in re.finditer(
        r"<name>(G(\d+))</name>.*?<coordinates>([-\d.,\s]+)</coordinates>", raw, re.S
    ):
        lon, lat = map(float, m.group(3).strip().split(",")[:2])
        mvps.append({"n": int(m.group(2)), "lat": round(lat, 6), "lon": round(lon, 6)})
    mvps.sort(key=lambda p: p["n"])

    lat0 = sum(p["lat"] for p in mvps) / len(mvps)
    mlat = 111_320.0
    mlon = mlat * math.cos(math.radians(lat0))

    def nearest(lon: float, lat: float) -> tuple[int | None, float]:
        best, best_d = None, float("inf")
        for p in mvps:
            d = math.hypot((p["lat"] - lat) * mlat, (p["lon"] - lon) * mlon)
            if d < best_d:
                best, best_d = p["n"], d
        return best, best_d

    lines = []
    block_points: dict[int, list[tuple[float, float]]] = {}
    for m in re.finditer(
        r"<LineString>.*?<coordinates>(.*?)</coordinates>.*?</LineString>", raw, re.S
    ):
        pts = []
        for triple in m.group(1).split():
            parts = triple.split(",")
            if len(parts) >= 2:
                try:
                    pts.append((round(float(parts[0]), 6), round(float(parts[1]), 6)))
                except ValueError:
                    continue
        if len(pts) < 2:
            continue
        mid_lon = sum(p[0] for p in pts) / len(pts)
        mid_lat = sum(p[1] for p in pts) / len(pts)
        length_m = math.hypot(
            (pts[-1][0] - pts[0][0]) * mlon, (pts[-1][1] - pts[0][1]) * mlat
        )
        owner, distance = nearest(mid_lon, mid_lat)
        block = (
            owner
            if distance <= ASSIGN_RADIUS_M and length_m <= MAX_BLOCK_SEGMENT_M
            else None
        )
        lines.append({"b": block, "pts": [[p[1], p[0]] for p in pts]})
        if block is not None:
            block_points.setdefault(block, []).extend(pts)

    blocks = []
    for point in mvps:
        pts = block_points.get(point["n"], [])
        ring = hull(pts) if len(pts) >= 3 else []
        width_m = height_m = 0.0
        if ring:
            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            width_m = (max(lons) - min(lons)) * mlon
            height_m = (max(lats) - min(lats)) * mlat
        blocks.append(
            {
                "n": point["n"],
                "lat": point["lat"],
                "lon": point["lon"],
                "w": round(width_m, 1),
                "h": round(height_m, 1),
            }
        )

    zones = []
    for m in re.finditer(r"<name>(Z-\w+)</name>(.*?)</Placemark>", raw, re.S):
        c = re.search(r"<coordinates>([-\d.,\s]+)</coordinates>", m.group(2))
        if c:
            first = c.group(1).split()[0].split(",")
            zones.append(
                {
                    "name": m.group(1),
                    "lat": round(float(first[1]), 6),
                    "lon": round(float(first[0]), 6),
                }
            )

    lats = [p["lat"] for p in mvps]
    lons = [p["lon"] for p in mvps]
    payload = {
        "note": (
            "Derived from the project CAD/KML. Block shapes and MVPS positions "
            "are as-designed, not surveyed as-built."
        ),
        "bounds": {
            "south": min(lats),
            "north": max(lats),
            "west": min(lons),
            "east": max(lons),
        },
        "mvps": [{"n": b["n"], "lat": b["lat"], "lon": b["lon"]} for b in blocks],
        "blocks": blocks,
        "zones": zones,
        "lines": lines,
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    with_hull = sum(1 for b in blocks if b["w"] > 0)
    unassigned = sum(1 for l in lines if l["b"] is None)
    sizes = sorted((b["w"], b["h"]) for b in blocks if b["w"] > 0)
    print(f"mvps: {len(mvps)}  blocks with hull: {with_hull}")
    print(f"lines: {len(lines)}  unassigned (infrastructure): {unassigned}")
    print(f"hull sizes: median {sizes[len(sizes)//2]}, max {sizes[-1]}")
    print(f"site.json: {OUT.stat().st_size/1e6:.2f} MB")


if __name__ == "__main__":
    main()
