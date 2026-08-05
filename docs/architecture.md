# architecture.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**

---

## System Overview

The NAJM-3000 Digital Twin is a Python/pvlib pre-operational engineering model.
It is designed to:

1. Compute expected energy generation for one or more configurable MV blocks.
2. Support multi-vendor equipment configurations with full parameter provenance.
3. Define integration interfaces for future SCADA-connected operational monitoring.
4. Serve as the engineering foundation for commissioning validation and AI analytics.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      CONFIGURATION LAYER                         │
│  config/*.yaml → Pydantic schemas → validated parameter objects  │
└──────────────────────┬───────────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────────┐
│                       WEATHER INTERFACE                          │
│  source_classification → canonical weather schema                │
│  [SYNTHETIC_SOFTWARE_TEST for POC]                               │
└──────────────────────┬───────────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────────┐
│                      PHYSICS ENGINE                              │
│                                                                  │
│   Solar Position  →  Tracker  →  POA Irradiance  →  Bifacial    │
│        ↓                                               ↓         │
│   Cell Temperature ────────────────────────────────────┘         │
│        ↓                                                         │
│   DC Power (PVWatts → CEC/SAPM when params available)           │
│        ↓                                                         │
│   Inverter (PVWatts → Sandia/ADR when params available)          │
│        ↓                                                         │
│   IDT Transformer Losses                                         │
│        ↓                                                         │
│   Aggregation: String → SMB → Inverter → IDT → Block → Plant    │
│        ↓                                                         │
│   Loss Ledger + Provenance Report + Assumption Report            │
└──────────────────────┬───────────────────────────────────────────┘
                       │                        │
                       ▼                        ▼
┌──────────────────────────────┐  ┌─────────────────────────────────┐
│         OUTPUT LAYER         │  │       SCADA ADAPTER LAYER       │
│  Parquet time series         │  │  (INACTIVE — interface defined)  │
│  Engineering plots           │  │  Mock adapter for testing only   │
│  Loss waterfall              │  │  Historian adapter (future)      │
│  Provenance report           │  └─────────────────────────────────┘
│  Assumption report           │
└──────────────────────────────┘
```

---

## Package Structure

```
src/najm3000/
├── __init__.py              Package initialization and version
├── assets/
│   ├── __init__.py
│   ├── hierarchy.py         Asset hierarchy definitions (electrical + physical)
│   └── provenance.py        Provenance data model (Pydantic)
├── config/
│   ├── __init__.py
│   ├── loader.py            YAML configuration loader
│   ├── schemas.py           Pydantic v2 schemas for all config objects
│   └── validate.py          CLI entry point for config validation
├── ingestion/
│   ├── __init__.py
│   ├── qc_engine.py         Data quality control engine
│   └── data_checks.py       Individual QC check functions
├── weather/
│   ├── __init__.py
│   ├── interface.py         Weather schema (canonical) + classification enforcement
│   └── synthetic.py         Clear-sky and synthetic profile generator
├── tracking/
│   ├── __init__.py
│   ├── solar_position.py    Solar position calculation wrapper
│   ├── single_axis.py       Single-axis tracker model wrapper
│   └── poa_irradiance.py    Front-side POA irradiance calculation
├── bifacial/
│   ├── __init__.py
│   └── infinite_sheds.py    Bifacial irradiance (pvlib.bifacial.infinite_sheds)
├── temperature/
│   ├── __init__.py
│   └── cell_temperature.py  Cell temperature model selection and wrapper
├── dc_model/
│   ├── __init__.py
│   └── pvwatts_dc.py        PVWatts DC model wrapper
├── inverter/
│   ├── __init__.py
│   ├── pvwatts_inverter.py  PVWatts inverter model wrapper
│   └── idt_losses.py        IDT transformer loss model
├── electrical_losses/
│   ├── __init__.py
│   ├── dc_cable.py          DC cable loss model
│   └── ac_cable.py          AC cable loss model
├── soiling/
│   ├── __init__.py
│   └── soiling_factor.py    Soiling loss placeholder
├── aggregation/
│   ├── __init__.py
│   ├── aggregator.py        Multi-level aggregation engine
│   └── loss_ledger.py       Loss classification and tracking
├── validation/
│   ├── __init__.py
│   └── sanity_checks.py     Physical sanity check functions
├── analytics/
│   ├── __init__.py
│   └── scenario.py          Scenario comparison engine
├── scada/
│   ├── __init__.py
│   ├── adapter_interface.py Abstract SCADA adapter base class
│   └── mock_adapter.py      Mock adapter for testing (synthetic data only)
└── reporting/
    ├── __init__.py
    ├── provenance_report.py  Parameter provenance report generator
    ├── assumption_report.py  Assumption and gap report generator
    └── plots.py              Engineering visualizations
```

---

## Dependency Graph (Planned)

```
config/schemas.py
    ↑ loaded by
config/loader.py
    ↑ used by
assets/hierarchy.py ← assets/provenance.py
    ↑ used by
weather/interface.py ← weather/synthetic.py
    ↑ feeds
tracking/ ← ingestion/qc_engine.py
    ↑ feeds
bifacial/ ← temperature/
    ↑ feeds
dc_model/
    ↑ feeds
inverter/ ← inverter/idt_losses.py
    ↑ feeds
electrical_losses/ ← soiling/
    ↑ feeds
aggregation/aggregator.py → aggregation/loss_ledger.py
    ↑ feeds
validation/sanity_checks.py
    ↑ feeds
reporting/ ← analytics/
    ↑ writes
outputs/ (Parquet, plots, reports)
```

---

## Key Design Constraints

| Constraint | Enforcement |
|---|---|
| No hard-coded equipment parameters | Pydantic schema rejects missing provenance |
| Timezone-aware timestamps everywhere | `pd.Timestamp` with tz; naive timestamps rejected |
| SI units throughout | ruff/mypy enforce type annotations; unit tests check output columns |
| Multi-vendor isolation | Block config selects vendor alias; no averaging |
| Weather source independence | Physics engine accepts any canonical schema input |
| SCADA independence | Physics engine has zero imports from `scada/` module |
| No network access | No `requests`, `urllib`, or download calls in any module |

---

*NAJM-3000 Digital Twin | docs/architecture.md | Revision 1.0*
