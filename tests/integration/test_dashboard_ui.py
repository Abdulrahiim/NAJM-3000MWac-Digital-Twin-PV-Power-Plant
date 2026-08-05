"""Tests for the dashboard front end (Sprint 6).

The dashboard exists to be presented while the plant is under construction, so
its labeling is load-bearing. These tests hold it to that: the data-source
indicator is always present, no value is baked into the page, and the page
talks only to the API.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from najm3000.dashboard.api import build_app

FIXTURES = Path(__file__).parent.parent / "fixtures"
STATIC = (
    Path(__file__).parent.parent.parent
    / "src"
    / "najm3000"
    / "dashboard"
    / "static"
)
DAY = "2025-06-21"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(build_app(config_dir=FIXTURES, day=DAY))


# --- serving ----------------------------------------------------------------


def test_root_serves_the_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_static_assets_are_served(client):
    for asset in ("styles.css", "app.js"):
        assert client.get(f"/static/{asset}").status_code == 200


# --- mandatory labeling -----------------------------------------------------


def test_page_contains_the_data_source_indicator(client):
    assert 'id="data-source-chip"' in client.get("/").text


def test_page_shows_a_simulated_source_before_any_data_loads(client):
    """If the API never responds, the page must not look like a live system."""
    body = client.get("/").text
    chip = body[body.index('id="data-source-chip"') :][:400]
    assert "SIM" in chip
    assert "LIVE" not in chip


def test_page_carries_elements_for_calibration_and_provenance(client):
    """Labelling is API-driven, so the page must expose slots for it."""
    body = client.get("/").text
    assert 'id="status-calibration"' in body
    assert 'id="provenance-note"' in body
    assert 'id="data-source-chip"' in body


def test_the_api_supplies_the_uncalibrated_and_unvalidated_wording(client):
    """The disclaimer cannot be edited out of the HTML: it comes from here."""
    status = client.get("/api/status").json()
    assert status["calibration_status"] == "not-calibrated"
    assert status["validation_status"] == "not-validated"
    disclaimer = status["disclaimer"].upper()
    assert "NOT MEASURED DATA" in disclaimer
    assert "NOT CALIBRATED" in disclaimer
    assert "NOT VALIDATED" in disclaimer


def test_the_script_renders_the_api_disclaimer_into_the_page(client):
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "provenance-note" in js
    assert "status.disclaimer" in js


def test_data_source_indicator_has_no_dismiss_control():
    """The indicator must not be closable — it is not a notification."""
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    start = html.index('id="data-source-chip"')
    chip = html[start : html.index("</div>", start)]
    # A dismiss affordance would be a button, or the element starting hidden.
    assert "<button" not in chip.lower()
    assert "dismiss" not in chip.lower()
    assert not re.search(r"\bhidden\b(?!=)", chip.lower())
    assert "display:none" not in chip.lower().replace(" ", "")


def test_the_script_never_hides_the_data_source_indicator():
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    chip_lines = [line for line in js.splitlines() if "data-source-chip" in line]
    assert chip_lines
    for line in chip_lines:
        assert ".remove()" not in line
        assert "display" not in line


# --- honesty of the markup --------------------------------------------------


def test_page_does_not_bake_in_any_power_value():
    """Every number must come from the API, never from the page source."""
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    body = html[html.index("<body") :] if "<body" in html else html
    # Any run of digits with a unit suffix would be a hardcoded reading.
    assert not re.search(r"\d[\d,.]*\s*(MW|kW|W/m|°C)\b", body)


def test_page_never_claims_the_data_is_live_or_measured():
    html = (STATIC / "index.html").read_text(encoding="utf-8").lower()
    for phrase in ("live data", "measured data", "actual production", "real-time data"):
        assert phrase not in html


def test_script_reads_the_status_endpoint_for_its_labeling():
    """The chip must be driven by the API, not hardcoded optimism."""
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "/api/status" in js
    assert "data-source-chip" in js


def test_script_requests_only_api_paths():
    """No third-party or file access from the page."""
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    requested = re.findall(r"""getJSON\(\s*[`'"]([^`'"$]*)""", js)
    assert requested, "expected the dashboard to call the API"
    assert all(path.startswith("/api/") for path in requested), requested


#: The SVG namespace is an XML identifier, never fetched over the network.
SVG_NAMESPACE = "http://www.w3.org/2000/svg"

#: The single permitted external host: satellite imagery tiles for the site
#: map, approved by the project lead 2026-08-05. Everything else stays local.
#: Viewing the map necessarily reveals which tiles (and hence the site
#: location) to the imagery provider.
PERMITTED_EXTERNAL = ("server.arcgisonline.com",)


def test_page_makes_no_external_requests_beyond_the_tile_exemption():
    """Offline by construction, except the documented imagery host."""
    for name in ("index.html", "app.js", "styles.css", "sitemap.js"):
        text = (STATIC / name).read_text(encoding="utf-8").replace(SVG_NAMESPACE, "")
        for host in PERMITTED_EXTERNAL:
            text = text.replace(f"https://{host}", "")
        assert "http://" not in text, name
        assert "https://" not in text, name


def test_the_tile_exemption_is_only_the_approved_host():
    js = (STATIC / "sitemap.js").read_text(encoding="utf-8")
    import re
    hosts = set(re.findall(r"https://([^/'\"]+)", js))
    assert hosts <= set(PERMITTED_EXTERNAL), hosts


def test_the_map_attribution_credits_esri_and_flags_simulated_markers():
    js = (STATIC / "sitemap.js").read_text(encoding="utf-8")
    assert "Esri" in js
    assert "simulated" in js.lower()


# --- visualisation rules ----------------------------------------------------


def test_charts_use_the_validated_series_colours():
    """Palette was validated with scripts/validate_palette.js in both modes."""
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    for token in ("--series-1", "--series-2"):
        assert token in css


def test_stylesheet_defines_a_dark_mode(client):
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    assert "prefers-color-scheme: dark" in css
    assert 'data-theme="dark"' in css


def test_trends_are_separate_charts_not_one_dual_axis_chart():
    """Irradiance, temperature and power have different units."""
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    for chart_id in ("chart-irradiance", "chart-temperature", "chart-power"):
        assert f'id="{chart_id}"' in html


# --- 3D viewer must never take down the dashboard ---------------------------


def test_viewer_init_is_not_on_the_critical_path():
    """3D is one panel. It must not be able to break the whole page."""
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    init = js.index("initModelViewer(")
    status = js.index("await loadStatus()")
    guarded = js[max(0, init - 400):init]
    assert "try {" in guarded, "viewer init must be inside a try block"
    assert init < status, "viewer init should run before loadStatus but guarded"


def test_viewer_probes_webgl_before_constructing_a_renderer():
    js = (STATIC / "model.js").read_text(encoding="utf-8")
    probe = js.index("getContext('webgl")
    renderer = js.index("new THREE.WebGLRenderer")
    assert probe < renderer, "WebGL support must be probed first"
    assert "WebGL unavailable" in js


def test_model_load_failures_are_reported_not_swallowed():
    js = (STATIC / "model.js").read_text(encoding="utf-8")
    assert "catch (error)" in js
    assert "Model failed to load" in js


def test_page_has_a_status_line_for_the_3d_panel():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="model-status"' in html


# --- expected vs actual presentation (Sprint 8) -----------------------------


def test_measured_series_is_distinguishable_without_colour():
    """Acceptance criterion: not colour-alone."""
    css = (STATIC / "styles.css").read_text(encoding="utf-8")
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "series-measured" in css
    assert "stroke-dasharray" in css
    assert "dashed: true" in js


def test_the_measured_series_is_labelled_as_simulated_in_the_legend():
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "Measured AC (simulated)" in js


def test_page_has_deviation_and_performance_ratio_tiles():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'id="kpi-deviation"' in html
    assert 'id="kpi-pr"' in html
    assert "simulated measurement" in html.lower()


def test_plant_grid_can_shade_by_deviation():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert 'data-mode="deviation"' in html
    assert "deviationColour" in js


def test_deviation_shading_uses_the_reserved_status_palette():
    """Status colours are reserved and must not double as series colours."""
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    block = js[js.index("function deviationColour") :][:420]
    for token in ("--critical", "--serious", "--warning", "--good"):
        assert token in block
