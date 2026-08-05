# DATA_REGISTER.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> This register tracks all data inputs, outputs, and processed datasets.
> Raw engineering documents are excluded from this register — see DOCUMENT_REGISTER.md.

---

## Data Category Definitions

| Category | Description | Committed to Git |
|---|---|---|
| Raw | Immutable source data; never modified | No — excluded by .gitignore |
| Interim | Reproducible intermediate products from raw data | Yes — when sanitized |
| Processed | Provenance-tagged model outputs | Yes — when sanitized |
| Public | Separately classified public or synthetic data | Yes — with classification label |
| Fixtures | Small sanitized CSV/YAML files used in testing | Yes |

---

## Data Source Classification

| Label | Description | Permitted Use |
|---|---|---|
| `MEASURED_SITE` | On-site measured data | Operational phases only |
| `OFFICIAL_TMY` | Approved satellite/reanalysis TMY | Approved analysis only |
| `PROVISIONAL_PUBLIC` | Publicly available, not formally approved | Sensitivity studies only, clearly labeled |
| `SYNTHETIC_SOFTWARE_TEST` | Synthetic data for software verification | Software testing only — not production estimates |

---

## Current Data Inventory

### Raw Data

| Data ID | Type | Classification | Description | Status | Path |
|---|---|---|---|---|---|
| — | Measured weather | MEASURED_SITE | On-site pyranometer/met station data | **Does not exist** | — |
| — | Operational SCADA | MEASURED_SITE | Plant production and alarm history | **Does not exist** | — |

### Synthetic / Test Data

| Data ID | Type | Classification | Description | Status | Path |
|---|---|---|---|---|---|
| DAT-001 | Clear-sky irradiance | SYNTHETIC_SOFTWARE_TEST | pvlib Ineichen clear-sky for software testing | Planned — Sprint 1 | data/public/synthetic/ |
| DAT-002 | Synthetic temperature profile | SYNTHETIC_SOFTWARE_TEST | Diurnal temperature profile for software testing | Planned — Sprint 1 | data/public/synthetic/ |
| DAT-003 | Synthetic wind-speed profile | SYNTHETIC_SOFTWARE_TEST | Constant or diurnal wind for software testing | Planned — Sprint 1 | data/public/synthetic/ |

> ⚠️ **All synthetic data must carry the label:**
> `SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION`

### Provisional Public Data

| Data ID | Type | Classification | Description | Status | Path |
|---|---|---|---|---|---|
| DAT-004 | Satellite/reanalysis weather | PROVISIONAL_PUBLIC | PVGIS hourly GHI/DHI/DNI, air temperature, wind (SRC-027) | **Authorized 2026-08-02** | data/interim/ (cache, gitignored) |

> ⚠️ **All public data must carry the label:**
> `PROVISIONAL PUBLIC DATA — NOT SITE-MEASURED, NOT VALIDATED`

#### DAT-004 — approval record (weather data policy, six-step process)

| Step | Record |
|---|---|
| 1. Source registered | SRC-027, `DOCUMENT_REGISTER.md` |
| 2. Written approval | Project lead, **2026-08-02**, authorizing use of a free public satellite/reanalysis weather API |
| 3. `authorized: true` | Set in `config/data_sources.yaml` under `public_pvgis` |
| 4. Classification assigned | `PROVISIONAL_PUBLIC` — locked by `Literal` in `PublicWeatherConfig` |
| 5. Download method | `pvlib.iotools.get_pvgis_hourly`, endpoint `https://re.jrc.ec.europa.eu/api/v5_3/seriescalc`, radiation database `PVGIS-SARAH3`, meteorological database ERA5, horizontal plane (`slope=0`), hourly, coverage 2005–2023 |
| 6. No silent substitution | Retrieval failure raises `WeatherSourceError`; the model never falls back to another source |

**Coordinate policy.** The project lead was advised that querying an external
API with the exact site coordinates transmits the confidential site location to
a third party, and that the ~5–11 km reanalysis/satellite grid makes the
accuracy gain over a rounded coordinate negligible. **The project lead elected
to query at exact site coordinates on 2026-08-02.** Recorded here so the
decision is auditable rather than implicit.

**Limits of this data.** PVGIS data is real weather. It is **not** site-measured
data and **not** the owner's official TMY. It does not close GAP-002 or GAP-020,
and it **cannot calibrate or validate** the Digital Twin.

### Test Fixtures

| Data ID | Type | Description | Path |
|---|---|---|---|
| FIX-001 | YAML configuration | Representative block config fixture (placeholder values) | tests/fixtures/ |
| FIX-002 | YAML configuration | Multi-vendor equipment fixture (placeholder values) | tests/fixtures/ |
| FIX-003 | PVGIS response | Recorded hourly response at a **neutral coordinate (40.0N, 0.0E), deliberately not the site**, for offline tests | tests/fixtures/pvgis_neutral_2023.csv |

---

## Data Quality Requirements

All data ingested into the pipeline must pass these checks before use:

| Check | Description |
|---|---|
| Timestamp parsing | Valid ISO-8601 timestamps with explicit timezone |
| Duplicate timestamps | No duplicate timestamp entries |
| Missing intervals | Gaps identified and flagged |
| Negative irradiance | Values < 0 flagged as `QC_FAIL_NEGATIVE` |
| Nighttime irradiance | Irradiance > threshold at solar elevation < 0° flagged |
| Physical temperature limits | Values outside −30°C to +85°C flagged |
| Sensor freeze / flatline | Repeated identical values over multiple intervals flagged |
| Spikes | Values exceeding physical maximum for sensor type flagged |
| Clipping | Values at exact sensor maximum over multiple intervals flagged |
| Unit inconsistency | Checks against expected unit from metadata |
| Counter resets | Cumulative counters with unexpected decrements flagged |
| Communication dropouts | Extended NaN blocks flagged |
| Sampling frequency | Changes in timestep flagged |
| Quality flags | Source quality flags preserved and propagated |
| Calibration periods | Calibration windows excluded from analysis |

---

## Data Preservation Rules

Data correction is non-destructive. The following fields are always preserved:

| Field | Description |
|---|---|
| `value_raw` | Original uncorrected value |
| `value_corrected` | Corrected value (if applicable) |
| `quality_flag` | QC result code |
| `exclusion_reason` | Reason for excluding from analysis |
| `correction_reason` | Reason for correction |
| `correction_method` | Method used to correct value |
| `processing_version` | Version of the processing pipeline applied |

**Never silently delete or overwrite raw values.**

---

## Output Data Format

| Format | Use |
|---|---|
| Parquet | Primary time-series output (processed results) |
| CSV | Interoperability; small reports |
| YAML | Configuration and provenance records |

All output files include:
- `najm3000_version` tag
- `data_source_classification` tag
- `simulation_date` tag
- `block_id` tag
- `weather_source_id` tag
- `model_stage` tag

---

*NAJM-3000 Digital Twin | DATA_REGISTER.md | Revision 1.0*
