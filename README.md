# NAJM-3000 Digital Twin

> ⚠️ **CONFIDENTIAL — RESTRICTED INTERNAL USE ONLY**
> This repository contains engineering intellectual property.
> See `CONFIDENTIALITY.md` for the full data-handling policy before proceeding.

---

## Project Status

**NAJM-3000 is a 3,000 MWac utility-scale solar PV project currently under construction
and pre-operational.**

### Plant Identity (SRC-026 §2, SRC-028 — design basis)

| Item | Value |
|---|---|
| Location | Al Hinakiyah, Kingdom of Saudi Arabia |
| Coordinates | 25.058417° N, 41.106583° E |
| Altitude | 1,100 m a.s.l. |
| Site boundary area | 13,822.26 acre |
| Mounting | Single-axis tracker, 1-in-portrait |
| DC peak capacity | 3,540.055 MWp |
| AC at inverter level | 3,228.471 MVA @ 50 °C, PF 1 |
| DC/AC at inverter level | 1.096 : 1 |
| Nominal rating at POI | 3,000 MWac @ 50 °C |
| DC/AC at POI | 1.180 : 1 (min) |
| Export cap | 3,000 MW at POI |
| MV power stations (MVPS) | 365 |
| Pooling substations (PSS) | 2 |
| Transmission lines | 8 (7 double-circuit, 1 single-circuit) |
| Evacuation voltage | 110 kV |

> Recorded per the 2026-08-04 confidentiality revision, under which the project
> name is the only substituted identifier.

### Status

| Status Item | Current State |
|---|---|
| SCADA telemetry | **INACTIVE** — not connected |
| Operational production data | **DOES NOT EXIST** |
| Alarm / fault / event history | **DOES NOT EXIST** |
| Digital Twin calibration | **NOT PERFORMED** |
| Digital Twin validation | **NOT PERFORMED** |
| Equipment installation confirmation | **NOT CONFIRMED** — datasheets only |
| Measured weather time series | **NOT AVAILABLE** |
| Final as-built block assignments | **NOT FINALIZED** |

No output of this Digital Twin represents actual or predicted NAJM-3000 production
until commissioning validation is completed with measured data.

---

## Purpose

This repository implements a Python/pvlib Digital Twin proof of concept (POC) for
NAJM-3000. Its engineering purposes are:

1. Establish a rigorous, auditable physics model architecture.
2. Support multi-vendor equipment modeling with full parameter provenance.
3. Enable pre-commissioning design verification and sensitivity analysis.
4. Define the integration interfaces for future SCADA-connected operational
   monitoring, performance ratio calculation, and anomaly detection.
5. Serve as the engineering foundation for later commissioning validation,
   operational calibration, and AI-assisted analytics.

---

## What Kind of Digital Twin This Is

NAJM-3000 is under construction and SCADA is not commissioned, so there is no
operational data. The project is explicit about which stage it is in:

| Stage | Definition | Status |
|---|---|---|
| **As-designed twin** | Physics model built from design and datasheet data | ✅ Complete |
| **Pre-commissioning twin** | SCADA-style dashboard driven by the simulation engine, proving the integration path | ⏳ Sprints 5–6 |
| **Operational twin** | Same system driven by the historian, calibrated against measured production | ❌ Requires commissioning |

The architectural commitment linking them: the dashboard reads from a
`HistorianAdapter`, never from the physics engine. At commissioning the
simulated adapter is replaced by the real one and nothing above it changes.

**Supportable statement:**

> The physics engine, asset hierarchy, loss accounting and dashboard are
> complete and running. They are currently driven by the simulation engine
> because the plant is under construction and SCADA is not commissioned. On
> commissioning, the same dashboard is pointed at the historian — no rework.

**Not supportable, and must not appear in any presentation or export:** that the
dashboard shows live, measured, or actual plant data; that the model is
calibrated or validated; that any figure is a predicted NAJM-3000 energy yield.

---

## POC Scope (Honest Statement)

The current POC targets **one configurable representative MV block**.

The POC demonstrates the capability to:

- Run a complete pvlib modeling chain for a single representative block.
- Use synthetic (clear-sky + synthetic temperature/wind) inputs clearly labeled as
  software-test data only.
- Load all equipment parameters from validated YAML configuration with Pydantic
  schema enforcement.
- Attach provenance metadata to every important parameter.
- Support multi-vendor equipment overrides.
- Calculate provisional plant-level totals by block count scaling (clearly labeled
  as illustrative).
- Produce a loss waterfall, provenance report, and assumption report.

### Explicit Non-Goals of the POC

- Does **not** predict actual NAJM-3000 energy yield.
- Does **not** constitute a bankable energy assessment.
- Does **not** use or download measured weather.
- Does **not** connect to SCADA or any live data source.
- Does **not** validate or calibrate any model against measured production.
- Does **not** prove that any datasheet equipment is installed at NAJM-3000.
- Does **not** replace a professional independent engineer assessment.

---

## Current Engineering Data Available

The following data categories have been audited from engineering documents
(source IDs assigned; raw documents not committed to this repository):

| Category | Status | Notes |
|---|---|---|
| PV module datasheets | Good — 2 bifacial variants (re-audited 2026-07-24) | Full STC tables per bin, temp coefficients, bifaciality 80±5%; CEC/PVsyst fit parameters still pending (GAP-004) |
| Inverter datasheets | Good — 2 variants, both detailed | 4.4 MW-class (Vendor A) and 1.1 MVA-class (Vendor B) central units; MPPT windows and night draw documented |
| IDT datasheets | Good — 2 rating variants | 8.932 / 4.466 MVA; 33 kV / 660 V; no-load and load losses documented (GAP-006 resolved) |
| Main step-up transformer | Nameplate available | 230 MVA, dual 33 kV LV windings, OLTC (SRC-019) |
| Tracker datasheets | Partial — 3 vendors on file | Vendor A audited (60° limit, ~1.5 m axis height); Vendor B/C extraction pending (GAP-010) |
| SMB datasheets | Good — 3 vendor variants | 1,500 V DC, 16-in-1-out confirmed for all vendors |
| SCADA specification | Concept — 4-level architecture | Not operational; 3-year historian; ~24 fiber rings design |
| MV switchgear/RMU | Partial — 36 kV class | RMU GTP audited (25 kA/1s, 630 A, GIS) |
| Weather instrumentation | Planned — 19 stations, fully specified | Sensor fit-out documented; not yet installed or operational |
| Official TMY | Exists per design basis — **not supplied** | Request logged (DR-001, GAP-020); not approved for Digital Twin use |
| Public satellite weather | Available — `PROVISIONAL_PUBLIC` | PVGIS/SARAH-3 + ERA5 (SRC-027), authorized 2026-08-02. Real weather, **not site-measured**; cannot calibrate or validate |
| Measured weather | **None** | No on-site time series available (GAP-002) |
| Operational SCADA data | **None** | System not active |
| Final block assignment | **Partial** | Plant totals known (365 MVPS / 2 PSS, conflicting with 288-unit IDT BOQ — GAP-019); per-block vendor mix unknown |

---

## Multi-Vendor Modeling Approach

NAJM-3000 contains multiple equipment vendors. This Digital Twin treats each
equipment type as a distinct model variant. Unlike equipment is **never averaged**.

Supported vendor aliases (equipment details kept in configuration):

- `module_vendor_a_model_1`, `module_vendor_b_model_1`
- `inverter_vendor_a_model_1`, `inverter_vendor_b_model_1`
- `idt_vendor_a_8_932_mva`, `idt_vendor_a_4_466_mva`
- `tracker_vendor_a_model_1`, `tracker_vendor_b_model_1`, `tracker_vendor_c_model_1`
- `smb_vendor_a_model_1`, `smb_vendor_b_model_1`, `smb_vendor_c_model_1`

Each block configuration file specifies which vendor variant applies to that block.
Multi-vendor sensitivity scenarios are explicitly labeled.

---

## Asset Hierarchy

### Electrical Hierarchy

```
NAJM-3000 Plant
└── Grid Interface
    └── Main Transformer(s)
        └── MV Bus
            └── Feeder
                └── MV Block
                    └── RMU / MV Switchgear
                        └── IDT (Inverter Duty Transformer)
                            └── Inverter
                                └── SMB (String Monitoring Box)
                                    └── String
                                        └── PV Module Group
```

### Physical Hierarchy

```
NAJM-3000 Site
└── Geographic Zone
    └── Weather-Station Zone
        └── MV Block Area
            └── Tracker Row
                └── Tracker Table
                    └── Module Group
                        └── Sensor Location
```

### Cross-Reference Mappings

| Physical | → | Electrical |
|---|---|---|
| Tracker row | → | Strings |
| Module group | → | String / SMB input |
| Tracker table | → | SMB input group |
| Block area | → | MV Block |
| Weather-station zone | → | Block weather input |

---

## pvlib Modeling Chain

> Implemented as described below (Sprints 1–3). Implementing a chain is not the
> same as validating it — see *Current Limitations*.

### 1. Location and Time

```python
pvlib.location.Location(latitude, longitude, tz, altitude)
# Timezone-aware pandas DatetimeIndex
```

### 2. Solar Position

```python
pvlib.solarposition  # or Location.get_solarposition()
```

### 3. Single-Axis Tracker

```python
pvlib.tracking.singleaxis(
    apparent_zenith, apparent_azimuth,
    axis_tilt,        # configurable
    axis_azimuth,     # configurable
    max_angle,        # configurable; ≤60° per design basis
    backtrack,        # configurable
    gcr,              # configurable
    cross_axis_tilt,  # configurable
)
```

### 4. Front-Side POA Irradiance

```python
pvlib.irradiance.get_total_irradiance(
    surface_tilt, surface_azimuth,
    dni, ghi, dhi,
    # Perez or Hay-Davies — configurable
)
```

### 5. Bifacial Irradiance

```python
pvlib.bifacial.infinite_sheds(
    # albedo, gcr, axis_height, row geometry,
    # module bifaciality, rear mismatch allowance
    # all from configuration
)
```

### 6. Cell Temperature

```python
pvlib.temperature.pvsyst_cell()   # preferred when coefficients available
pvlib.temperature.sapm_cell()     # alternative
# Selection driven by available datasheet parameters
```

### 7. DC Power

```python
# POC Phase 1: PVWatts DC (minimal parameter requirement)
pvlib.pvsystem.pvwatts_dc(g_poa_effective, temp_cell, pdc0, gamma_pdc)
# Later: CEC, PVsyst, SAPM — only when required parameters confirmed
```

### 8. Inverter Conversion

```python
# POC Phase 1: PVWatts inverter or provisional efficiency model
pvlib.inverter.pvwatts()
# Later: Sandia or ADR — only when complete coefficients are confirmed
# Explicit: clipping, MPPT window, temperature derating,
#           night losses, auxiliary consumption
```

### 9. Transformer Losses

```
P_loss = P_no_load + P_load_rated × load_fraction²
# Parameters from IDT datasheet (source ID required)
# Ambiguous rows must not be silently assumed
```

### 10. Aggregation Levels

| Level | Calculation |
|---|---|
| Module group | Sum of module outputs |
| String | Sum of module groups |
| SMB | Sum of strings |
| Inverter | SMB aggregation + inverter losses |
| IDT | Inverter output − transformer losses |
| MV Block | Sum of IDTs |
| Feeder | Sum of blocks |
| Plant scenario | Block totals × scaling factor (clearly labeled) |

---

## Weather-Data Policy

### Data Source Classifications

| Label | Description |
|---|---|
| `MEASURED_SITE` | On-site pyranometer / meteorological station data |
| `OFFICIAL_TMY` | Approved satellite or reanalysis TMY dataset |
| `PROVISIONAL_PUBLIC` | Publicly available data not formally approved for NAJM-3000 |
| `SYNTHETIC_SOFTWARE_TEST` | Synthetic data for software verification only |

### POC Weather (Software Test Only)

For the initial software test, the model will use:

- **pvlib clear-sky irradiance** (Ineichen or Simplified Solis)
- **Synthetic ambient temperature profile** — clearly labeled
- **Synthetic wind-speed profile** — clearly labeled
- **Provisional configurable albedo** — clearly labeled

> ⚠️ **Clear-sky and synthetic data verify software behavior only.**
> They do not predict actual NAJM-3000 production.

### Future Weather Interface Requirements

The weather interface must accept these fields:

`timestamp`, `timezone`, `ghi`, `dni`, `dhi`, `poa_front`, `poa_rear`,
`temp_ambient`, `temp_module`, `wind_speed`, `wind_direction`,
`relative_humidity`, `pressure`, `rainfall`, `albedo`, `soiling_ratio`,
`sensor_status`, `quality_flag`, `source_classification`

---

## Parameter Provenance

Every important parameter must carry a provenance record:

```yaml
parameter_name: string
value: number
unit: string (SI)
asset_id: string
asset_class: string
vendor_alias: string       # Vendor A, Vendor B, etc.
model_alias: string
source_id: string          # SRC-001, SRC-002, etc.
source_section: string
source_page: string
revision: string
issue_status: string
data_quality_status: string  # Confirmed | Provisional | Conflicting | Missing | Assumed | Not applicable
confidence: string           # High | Medium | Low
date_extracted: date
extractor_version: string
notes: string
```

**No model function may contain hard-coded equipment parameters.**

---

## Assumption and Conflict Management

All engineering assumptions are recorded in `ASSUMPTIONS_REGISTER.md` with:
- Assumption ID
- Parameter affected
- Assumed value and unit
- Reason for assumption
- Risk level (High / Medium / Low)
- Invalidation condition

Conflicting datasheet parameters are recorded in the Data Gap Register
(`DATA_GAP_REGISTER.md`) and must not be silently resolved.

---

## Repository Structure

```
NAJM-3000/
├── README.md
├── CONFIDENTIALITY.md
├── AGENTS.md
├── CLAUDE.md
├── DOCUMENT_REGISTER.md
├── DATA_REGISTER.md
├── ASSET_REGISTER.md
├── ASSUMPTIONS_REGISTER.md
├── DATA_GAP_REGISTER.md
├── CHANGELOG.md
├── PLANS.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── config/
│   ├── README.md
│   ├── project.example.yaml
│   ├── equipment.example.yaml
│   ├── blocks.example.yaml
│   └── data_sources.example.yaml
├── data/
│   ├── README.md
│   ├── raw/          # NEVER committed — gitignored
│   ├── interim/      # Reproducible intermediate products
│   ├── processed/    # Provenance-tagged outputs
│   └── public/       # Separately classified public data
├── docs/
│   ├── POC_PLAN.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── architecture.md
│   ├── modeling_methodology.md
│   ├── asset_hierarchy.md
│   ├── data_dictionary.md
│   ├── validation_plan.md
│   ├── testing_strategy.md
│   ├── weather_data_policy.md
│   ├── scada_integration_plan.md
│   ├── ai_analytics_roadmap.md
│   ├── security_and_data_handling.md
│   └── decisions/
│       └── ADR-001-initial-poc-architecture.md
├── src/
│   └── najm3000/
│       ├── __init__.py
│       ├── assets/         # Asset hierarchy models
│       ├── config/         # YAML loading and Pydantic schemas
│       ├── ingestion/      # Data ingestion and QC
│       ├── weather/        # Weather interface and source classification
│       ├── tracking/       # Single-axis tracker model
│       ├── bifacial/       # Bifacial irradiance model
│       ├── temperature/    # Cell temperature model
│       ├── dc_model/       # DC power model
│       ├── inverter/       # Inverter conversion model
│       ├── electrical_losses/ # DC/AC cable and SMB losses
│       ├── soiling/        # Soiling model (placeholder)
│       ├── aggregation/    # Multi-level aggregation
│       ├── validation/     # Physical sanity checks
│       ├── analytics/      # Diagnostics and reporting
│       ├── scada/          # SCADA adapter interface (inactive)
│       └── reporting/      # Reports, plots, scenarios, viewer data layer
│           ├── __main__.py            # Reporting CLI
│           ├── provenance_report.py
│           ├── assumption_report.py
│           ├── scenarios.py
│           ├── plots.py
│           └── viewer.py
├── notebooks/
│   └── streamlit_viewer.py  # Optional read-only dashboard (UI shell only)
├── tests/
└── outputs/                 # Generated — gitignored
```

---

## Installation

**Requirements:**
- Python 3.11 or later
- See `pyproject.toml` for the full dependency list

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate        # Linux/macOS
.\.venv\Scripts\Activate.ps1     # Windows PowerShell
.venv\Scripts\activate.bat       # Windows cmd.exe

# Install with development extras
pip install -e ".[dev]"

# Optional extras
pip install -e ".[viewer]"       # Streamlit results viewer
pip install -e ".[dashboard]"    # Pre-commissioning dashboard backend
```

The physics engine and the reporting CLI never require the optional extras.

### Every command below needs the virtual environment

`najm3000` is installed **into `.venv`**, not system-wide. Running a bare
`python -m najm3000...` against the system interpreter fails with
`ModuleNotFoundError: No module named 'najm3000'`.

Either activate the environment first, or call its interpreter directly:

```powershell
# Windows PowerShell — works without activating
.\.venv\Scripts\python.exe -m najm3000.dashboard --config-dir config --date 2025-06-21
```

```bash
# Linux/macOS — works without activating
./.venv/bin/python -m najm3000.dashboard --config-dir config --date 2025-06-21
```

If PowerShell blocks `Activate.ps1`, allow it for the current session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

---

## Configuration Approach

All equipment and block parameters are stored in YAML files under `config/`.
Example files (marked as provisional/placeholder) are provided.
Live configuration files are **not committed** if they contain confidential values.

Schema validation is performed by Pydantic at load time. Any configuration that
fails schema validation raises a hard error — the model does not run with invalid
parameters.

See `config/README.md` for structure and conventions.

---

## Execution Workflow

> Run these with the virtual environment **activated**. Without activation,
> prefix each command with `.\.venv\Scripts\python.exe` (Windows) or
> `./.venv/bin/python` (Linux/macOS) in place of `python`.

```bash
# 1. Validate configuration (hard-fails on any schema or provenance violation)
python -m najm3000.config.validate --config-dir config/

# 2a. Run single-block simulation (clear-sky software test)
python -m najm3000 \
  --block representative_block_a \
  --weather synthetic_clearsky \
  --date 2025-06-21 \
  --output outputs/

# 2b. Run with real public satellite weather (PROVISIONAL_PUBLIC, hourly)
#     Coverage is 2005-2023; the source is NOT site-measured.
python -m najm3000 \
  --block representative_block_a \
  --weather public_pvgis \
  --date 2023-06-21 \
  --timestep-minutes 60 \
  --output outputs/public/

# 3. Generate the provenance, assumption, waterfall, and plot artifacts
python -m najm3000.reporting \
  --block representative_block_a \
  --date 2025-06-21 \
  --output outputs/reports/ \
  --sensitivity both        # none | albedo | gcr | both

# 4. (Optional) Browse the results — requires the `viewer` extra
streamlit run notebooks/streamlit_viewer.py

# 5. Pre-commissioning dashboard — requires the `dashboard` extra
#    Runs locally only. Not hosted: serving plant configuration on a public
#    URL would place site data outside the CONFIDENTIALITY.md controls.
python -m najm3000.dashboard --config-dir config --date 2025-06-21
#    then open http://127.0.0.1:8000
```

The reporting command re-runs the simulation from configuration rather than
reading a stored result file, so the reports, plots, and loss waterfall are
always internally consistent with the numbers they describe.

### Report Artifacts

| Artifact | Contents |
|---|---|
| `provenance_report.md` / `.csv` | Every configured parameter with its source ID or assumption ID, unit, data-quality status, and confidence |
| `assumption_report.md` / `.csv` | Every `Assumed`, `Conflicting`, or `Missing` parameter with the risk level **read from `ASSUMPTIONS_REGISTER.md`** and any linked gap priority |
| `loss_waterfall.csv` | Gross DC energy → each named loss → net block energy, with each loss as a share of gross |
| `scenario_comparison.md` / `.csv` | Albedo (ASMP-005) and GCR (ASMP-013) sensitivity against a baseline |
| `plots/*.png` | Irradiance, temperature, power chain, annotated loss waterfall, scenario comparison |

A parameter citing an assumption ID that is absent from the register is
reported as `UNREGISTERED` rather than assigned a guessed risk level.

---

## Testing Strategy

See `docs/testing_strategy.md` for complete details.

Summary of required test categories:

| Category | Examples |
|---|---|
| Schema validation | Valid/invalid YAML passes/fails Pydantic |
| Unit consistency | SI units enforced throughout |
| Timestamp | Timezone-aware; naive datetimes rejected |
| Physical limits | No negative production; zero night generation |
| Tracker | Angle limits respected |
| MPPT | Window enforced |
| Clipping | Inverter AC limit respected |
| Transformer | Non-negative losses |
| Energy balance | Parent = sum of children at every level |
| Provenance | All key parameters have source IDs |
| Weather labeling | Source classification enforced |
| Reproducibility | Fixed synthetic test day → identical output |

---

## Validation Strategy

See `docs/validation_plan.md` for complete details.

| Phase | Description | Possible Now |
|---|---|---|
| 1. Software verification | Tests pass; physics rules hold | ✅ |
| 2. Physical sanity | Results within physically plausible ranges | ✅ |
| 3. Design benchmarking | Compare against design-basis energy estimate | Partial |
| 4. Commissioning | Compare against first measured data | ❌ Requires measured data |
| 5. Operational calibration | Tune model to match long-term measured data | ❌ Requires operational data |
| 6. Long-term validation | Multi-year performance tracking | ❌ Far future |

---

## SCADA Integration (Planned — Not Active)

SCADA integration is architecturally defined but **fully inactive**.

Planned data flow:
```
SCADA / historian adapter
  → Immutable raw records
  → Quality-control layer
  → Canonical time-series schema
  → Asset/tag mapping
  → Physics expected signal
  → Expected-vs-actual comparison
  → Diagnostics and reporting
```

The physics engine has no dependency on the SCADA adapter.
The SCADA adapter has no dependency on the physics engine.
They interact only through the canonical time-series schema.

---

## AI and Analytics Boundaries

### Before Commissioning (Current Period)

AI and analytics may support only:
- Software architecture testing.
- Synthetic fault demonstrations (clearly labeled).
- Scenario sensitivity analysis.
- Data-quality algorithm development.

### After Representative Operational Data Exists

The roadmap may include:
- Expected-vs-actual residual modeling.
- String/inverter anomaly detection.
- Soiling estimation and cleaning optimization.
- Degradation analysis.
- Predictive maintenance.

> Synthetic demonstrations do **not** prove operational detection accuracy.
> See `docs/ai_analytics_roadmap.md`.

---

## Current Limitations

1. **No measured weather** — clear-sky/synthetic inputs only.
2. **No operational data** — SCADA not active.
3. **Incomplete parameter sets** — PVsyst/CEC/SAPM fits not yet possible for most equipment.
4. **No final block assignment** — block count and configuration subject to change.
5. **Model not calibrated or validated** — results are engineering estimates only.
6. **Datasheets ≠ installed equipment** — vendor and model confirmation required.
7. **Single-block POC** — plant-level scaling is illustrative.
8. **Bifacial model parameters provisional** — albedo, GCR, and rear-mismatch values unconfirmed.

---

## POC Definition of Done

**Status: all criteria satisfied as of 2026-08-01 (Sprint 4 complete).**

- [x] One command runs a representative-block simulation end-to-end.
- [x] All equipment parameters come from validated YAML configuration.
- [x] Every important parameter has provenance or an assumption ID.
- [x] Synthetic weather is unmistakably labeled in all outputs.
- [x] Multi-vendor overrides work and are isolated per block.
- [x] Tracker, irradiance, temperature, DC, inverter, transformer, and aggregation
      stages are separately testable.
- [x] Results pass physical sanity checks.
- [x] Energy balance closes at every aggregation level.
- [x] Weather source can be replaced without changing the physics engine.
- [x] SCADA adapter interfaces are defined but inactive.
- [x] All tests pass with `pytest` — 157 tests, 96% line coverage.
- [x] Linting passes with `ruff`.
- [x] Type checking passes with `mypy` (strict).
- [x] No output claims calibration, validation, or operational accuracy.

> ⚠️ **A complete POC is not a validated model.** Every criterion above is a
> *software* criterion. NAJM-3000 remains pre-operational, the Digital Twin
> remains **not calibrated** and **not validated**, and every result to date
> was produced from `SYNTHETIC_SOFTWARE_TEST` weather. Nothing in this
> repository predicts NAJM-3000 production.

---

## Data Handling and Contribution Rules

1. **Do not commit raw engineering documents** — they are excluded by `.gitignore`.
2. **Do not commit confidential configuration** — use `.example.yaml` files only.
3. **Do not commit credentials** — use environment variables or a secrets manager.
4. **Do not silently delete or correct data** — preserve raw values, flags, and reasons.
5. **Do not download public weather** without explicit written approval.
6. **Do not access external systems** (SCADA, databases) without explicit approval.
7. Assign a source ID to every engineering value extracted from source documents.
8. Record every assumption in `ASSUMPTIONS_REGISTER.md`.
9. Record every data gap in `DATA_GAP_REGISTER.md`.
10. Record every engineering document reviewed in `DOCUMENT_REGISTER.md`.

---

## Project Roadmap

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Governance and foundation | ✅ Complete |
| Phase 0.5 | Datasheet audit and register sync | ✅ Complete (2026-07-24) |
| Sprint 1 | Minimum executable block (solar position, tracker, POA) | ✅ Implemented |
| Sprint 2 | Electrical conversion (temperature, DC, inverter) | ✅ Implemented |
| Sprint 3 | Bifacial, losses, aggregation | ✅ Complete |
| Sprint 4 | Reporting, quality, full test suite | ✅ Complete (2026-08-01) |
| Sprint 4.5 | Public weather (PVGIS), SCADA interface | ✅ Complete (2026-08-02) |
| Sprint 5 | Pre-commissioning twin: simulated telemetry backend | ✅ Complete (2026-08-02) |
| Sprint 6 | Pre-commissioning twin: SCADA-style dashboard | ✅ Complete (2026-08-02) |
| Future | Commissioning: SCADA activation, measured data | ❌ Requires operational data |
| Future | Analytics: anomaly detection, soiling, degradation | ❌ Requires operational data |

See `PLANS.md` for full sprint-level detail.

---

*NAJM-3000 Digital Twin | README.md | Phase 0 — Governance and Foundation*
*Status: Pre-Operational | Model: Not Calibrated | Model: Not Validated*
