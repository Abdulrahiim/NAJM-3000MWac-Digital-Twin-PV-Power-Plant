# weather_data_policy.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**

---

## Status

> ⚠️ No measured weather time series is currently available for NAJM-3000.
> 19 on-site weather stations are planned but not yet installed.
> The current POC uses `SYNTHETIC_SOFTWARE_TEST` data only.
>
> **TMY update (2026-07-24):** the project design basis (SRC-025/SRC-026) states that
> an owner-provided TMY dataset exists and is the required basis for performance
> estimation. That TMY file has **not** been supplied to this repository and is
> **not** approved for Digital Twin use. A formal data request is logged (DR-001,
> GAP-020). Until it is supplied and approved, no `OFFICIAL_TMY` source may be
> configured, and nothing may be downloaded as a substitute.

---

## Data Source Classifications

| Classification Label | Description | Permitted Use |
|---|---|---|
| `MEASURED_SITE` | On-site pyranometer and met station data | Operational and calibration phases only |
| `OFFICIAL_TMY` | Approved satellite/reanalysis TMY | Approved analysis; requires written approval |
| `PROVISIONAL_PUBLIC` | Publicly available; not approved for NAJM-3000 | Sensitivity studies only; must be labeled |
| `SYNTHETIC_SOFTWARE_TEST` | Synthetic data; software verification only | POC software testing; must be labeled |

**The classification `MEASURED_SITE` must only be applied to data actually measured
on the NAJM-3000 site.** Misclassifying any other data source as `MEASURED_SITE`
is a confidentiality and engineering integrity violation.

---

## Current POC Weather (Software Test Only)

For Phase 0 and Sprint 1 software testing, the model uses:

1. **pvlib clear-sky irradiance** — Ineichen model (or Simplified Solis as alternative).
   - No download required.
   - Computed from site location and time.
   - Represents a cloudless "best case" day — not representative of actual conditions.

2. **Synthetic ambient temperature profile** — Diurnal sinusoidal profile.
   - Configurable minimum and maximum (placeholder values only).
   - Not representative of site temperatures.

3. **Synthetic wind-speed profile** — Constant or diurnal profile.
   - Configurable constant value (placeholder only).
   - Not representative of site wind conditions.

4. **Provisional configurable albedo** — Fixed constant (ASMP-005).
   - No site-specific albedo measurement exists.

> ⚠️ **Clear-sky and synthetic data verify software behavior only.**
> They do not predict actual NAJM-3000 production.
> Every output produced with synthetic data must carry:
> `SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION`

---

## Approved External Source — PVGIS (2026-08-02)

The project lead granted written approval on **2026-08-02** to retrieve public
satellite/reanalysis weather. The approved source is PVGIS (EU JRC), radiation
database `PVGIS-SARAH3`, meteorological database ERA5 — registered as SRC-027
and DAT-004.

| Property | Value |
|---|---|
| Classification | `PROVISIONAL_PUBLIC` (locked in schema) |
| Coverage | 2005–2023, hourly |
| Retrieval | `pvlib.iotools.get_pvgis_hourly`, PVGIS API v5_3 |
| Coordinates | Exact site coordinates, by project-lead decision (see DAT-004) |
| Permitted use | Sensitivity studies and exercising the model with real weather |
| **Not permitted** | Calibration, validation, yield reporting, or any use implying site measurement |

This approval does **not** close GAP-002 (measured site weather) or GAP-020
(owner TMY). Data request DR-001 remains open.

---

## Prohibited Actions (Current Phase)

- ❌ Downloading NSRDB, MERRA-2, or any reanalysis/satellite source **other than
  the approved PVGIS source above** without further explicit written approval.
- ❌ Using any external data source and labeling it `MEASURED_SITE`.
  **This has no approval clause and is never permitted.**
- ❌ Labeling the approved PVGIS data as `OFFICIAL_TMY`; the owner TMY is a
  different dataset and has not been supplied.
- ❌ Using synthetic or provisional public data for energy yield reports or
  investor presentations.
- ❌ Connecting to any external API other than the approved PVGIS endpoint.
- ❌ Falling back to a different weather source when retrieval fails — failures
  must surface as errors, never as an unlabeled substitution.

---

## Weather Interface Requirements (for All Future Sources)

The canonical weather schema must support all of the following fields:

| Field | Unit | Required | Description |
|---|---|---|---|
| `timestamp` | — | ✅ | Timezone-aware ISO-8601 timestamp |
| `timezone` | IANA string | ✅ | Explicit timezone |
| `ghi` | W/m² | ✅ | Global horizontal irradiance |
| `dni` | W/m² | ✅ | Direct normal irradiance |
| `dhi` | W/m² | ✅ | Diffuse horizontal irradiance |
| `poa_front` | W/m² | ❌ | Front-side plane-of-array irradiance (measured) |
| `poa_rear` | W/m² | ❌ | Rear-side plane-of-array irradiance (measured) |
| `temp_ambient` | °C | ✅ | Ambient temperature |
| `temp_module` | °C | ❌ | Module temperature (measured) |
| `wind_speed` | m/s | ✅ | Wind speed at met station height |
| `wind_direction` | degrees | ❌ | Wind direction (0° = North) |
| `relative_humidity` | % | ❌ | Relative humidity |
| `pressure` | Pa | ❌ | Atmospheric pressure |
| `rainfall` | mm | ❌ | Rainfall accumulation per interval |
| `albedo` | fraction | ❌ | Ground albedo (measured or assumed) |
| `soiling_ratio` | fraction | ❌ | Soiling loss ratio from soiling sensors |
| `sensor_status` | string | ❌ | Sensor health indicator |
| `quality_flag` | string | ✅ | Data quality flag |
| `source_classification` | enum | ✅ | Data source classification label |

---

## On-Site Weather Station Plan (Reference)

Based on SRC-025 (Design Basis — I&C, General, PV Plant; supersedes the provisional
instrument list from SRC-001):

- **19 weather stations planned** across the NAJM-3000 site.
- Specified instruments per station (Provisional — design basis, not as-built):
  - 1 × Class A pyranometer (GHI)
  - 2 × Class A pyranometers (POA, plane of array)
  - 3 × Class C pyranometers (rear-side irradiance)
  - 1 × Class A albedometer (two horizontally mounted pyranometers)
  - 1 × Diffuse horizontal radiation sensor (DHI)
  - 1 × Ambient temperature sensor; 1 × humidity sensor
  - 1 × Wind speed and direction sensor
  - 1 × Rain gauge
  - 3 × Module temperature sensors
  - Soiling measurement: 1 × conventional system, 1 × front-side optical,
    1 × rear-side optical
  - 1 × Datalogger (minimum six-month local storage; Modbus TCP to SCADA)

**Status: Not yet installed or operational.** See GAP-002.

---

## Approval Process for New Weather Sources

Before using any new weather data source:

1. Record the proposed source in `DATA_REGISTER.md`.
2. Obtain written approval from the project lead.
3. Set `authorized: true` in `config/data_sources.yaml`.
4. Assign the correct `source_classification` label.
5. Document the download method and version in `DATA_REGISTER.md`.
6. Never substitute an unapproved source for an approved one silently.

---

*NAJM-3000 Digital Twin | docs/weather_data_policy.md | Revision 1.0*
