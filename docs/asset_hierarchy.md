# asset_hierarchy.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**

---

## Overview

This document defines both the electrical and physical asset hierarchies for NAJM-3000.
These hierarchies are the basis for:

- Aggregation logic in `src/najm3000/aggregation/`
- Tag-to-asset mapping in SCADA integration
- Loss attribution at each level
- Performance ratio calculation at each level

> ⚠️ **Block count and final block assignments are not confirmed (GAP-001).**
> Hierarchy is defined structurally; asset counts are placeholders.

---

## Electrical Hierarchy

```
NAJM-3000 Plant
│
└── Grid Interface
    │
    └── Main Transformer(s)
        │
        └── MV Bus (33 kV)
            │
            ├── Feeder 1
            │   ├── MV Block 01
            │   │   ├── RMU / MV Switchgear (36 kV class)
            │   │   │   └── IDT — Vendor A, 8.932 MVA (33 kV / 660 V)
            │   │   │       └── Inverter(s) — Vendor A (e.g., ~4.4 MW each)
            │   │   │           └── SMB(s) — Vendor A/B/C (1,500 V DC)
            │   │   │               └── Strings (1,500 V DC)
            │   │   │                   └── PV Module Groups
            │   │   └── IDT — (additional IDTs per block)
            │   │       └── ...
            │   └── MV Block 02
            │       └── ...
            ├── Feeder 2
            │   └── ...
            └── Feeder N
                └── ...
```

### Electrical Hierarchy Level Definitions

| Level | Identifier Pattern | Description |
|---|---|---|
| Plant | `NAJM-3000` | Entire NAJM-3000 site |
| Grid interface | `GRID_INTERFACE` | Point of connection to transmission grid |
| Main transformer | `XFMR_MAIN_{n}` | Plant-level step-up transformer |
| MV bus | `MV_BUS_{n}` | 33 kV collection bus |
| Feeder | `FEEDER_{nn}` | MV feeder circuit |
| MV block | `BLOCK_{nnn}` | One MV collection block |
| RMU / switchgear | `BLOCK_{nnn}_RMU` | Ring main unit or MV switchgear panel |
| IDT | `BLOCK_{nnn}_IDT_{n}` | Inverter duty transformer |
| Inverter | `BLOCK_{nnn}_IDT_{n}_INV_{n}` | Central inverter |
| SMB | `BLOCK_{nnn}_IDT_{n}_INV_{n}_SMB_{n}` | String monitoring box |
| String | `BLOCK_{nnn}_IDT_{n}_INV_{n}_SMB_{n}_STR_{n}` | PV string |
| Module group | `...STR_{n}_MOD_GRP_{n}` | Group of series-connected modules |

---

## Physical Hierarchy

```
NAJM-3000 Site
│
└── Geographic Zone {n}
    │
    └── Weather-Station Zone {n} (coverage area of one met station)
        │
        └── MV Block Area {nnn}
            │
            └── Tracker Row {nnnn}
                │
                └── Tracker Table {nnnnnn}
                    │
                    └── Module Group {n}
                        │
                        └── Sensor Location (for pyranometers, temp sensors)
```

### Physical Hierarchy Level Definitions

| Level | Identifier Pattern | Description |
|---|---|---|
| Site | `NAJM-3000` | Entire site area |
| Geographic zone | `GEO_ZONE_{n}` | Defined geographic sub-area |
| Weather-station zone | `WS_ZONE_{n}` | Coverage zone of one weather station |
| MV block area | `BLOCK_AREA_{nnn}` | Physical land area of one MV block |
| Tracker row | `ROW_{nnnn}` | One single-axis tracker row |
| Tracker table | `TABLE_{nnnnnn}` | One tracker motor/drive table unit |
| Module group | `TABLE_{nnnnnn}_GRP_{n}` | Series-connected module group on one table |
| Sensor location | `SENSOR_{nnnnnn}` | Physical location of a measurement sensor |

---

## Cross-Reference Mappings

### String → Physical

| Electrical | Physical |
|---|---|
| String (`STR_{n}`) | One tracker row or partial row |
| Module group | Modules on one tracker table |

### SMB → String

| SMB | Connected Strings |
|---|---|
| `SMB_{n}` | Multiple strings (count TBD — see GAP-015) |

### Inverter → SMB

| Inverter | Connected SMBs |
|---|---|
| `INV_{n}` | Multiple SMBs (count TBD — see GAP-015) |

### IDT → Inverter

| IDT | Connected Inverters |
|---|---|
| `IDT_{n}` (8.932 MVA) | 1 or 2 inverters (TBD) |
| `IDT_{n}` (4.466 MVA) | 1 inverter (TBD) |

### MV Block → IDT

| MV Block | Connected IDTs |
|---|---|
| `BLOCK_{nnn}` | Multiple IDTs (count TBD — see GAP-001) |

### Block Area → Weather Station Zone

| Block | Weather Station Zone | Station ID |
|---|---|---|
| TBD | TBD | WS-001 to WS-019 (planned — not installed) |

---

## Aggregation Rules

1. **Parent = sum of children** — energy balance must close at every level.
2. **Losses are attributed at the level where they occur** — not distributed upward.
3. **Multi-vendor blocks are not averaged** — each block aggregation uses its
   own equipment configuration.
4. **Plant-level totals** during the POC are illustrative scaling only (labeled
   `PROVISIONAL SCALING — NOT PRODUCTION VALIDATION`).

---

## Known Gaps

| Gap | Description | Gap ID |
|---|---|---|
| Block count | Total number of MV blocks not confirmed | GAP-001 |
| String arrangement | Modules per string, strings per SMB not confirmed | GAP-015 |
| Block vendor assignments | Which vendor goes in which block not confirmed | GAP-001 |
| Weather station zones | Zone-to-block mapping not available | GAP-002 |

---

*NAJM-3000 Digital Twin | docs/asset_hierarchy.md | Revision 1.0*
