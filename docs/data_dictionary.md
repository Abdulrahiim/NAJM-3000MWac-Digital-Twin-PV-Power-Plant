# data_dictionary.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> This document defines all field names, units, and conventions used in the
> NAJM-3000 Digital Twin data model.

---

## Units Convention

All internal values are in **SI units**:

| Quantity | SI Unit | Symbol |
|---|---|---|
| Power | Watt | W |
| Energy | Watt-hour | Wh |
| Irradiance | Watt per square metre | W/m² |
| Voltage | Volt | V |
| Current | Ampere | A |
| Resistance | Ohm | Ω |
| Temperature | Degree Celsius | °C |
| Temperature coefficient | Per degree Celsius | /°C |
| Length | Metre | m |
| Area | Square metre | m² |
| Angle | Degree | ° |
| Fraction / ratio | Dimensionless | — |
| Pressure | Pascal | Pa |
| Wind speed | Metre per second | m/s |
| Time | Second (intervals as minutes) | s or min |

---

## Provenance Object Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `parameter_name` | str | ✅ | Name of the parameter |
| `value` | float | ✅ | Parameter value in SI units |
| `unit` | str | ✅ | SI unit string |
| `asset_id` | str | ❌ | Asset hierarchy identifier |
| `asset_class` | str | ❌ | Asset class (e.g., "Inverter", "Tracker") |
| `vendor_alias` | str | ❌ | Vendor alias (e.g., "Vendor A") |
| `model_alias` | str | ❌ | Model alias (e.g., "inverter_vendor_a_model_1") |
| `source_id` | str | ✅* | Source document ID (e.g., "SRC-001") |
| `assumption_id` | str | ✅* | Assumption ID (e.g., "ASMP-001") |
| `gap_id` | str | ❌ | Data gap ID (e.g., "GAP-001") |
| `source_section` | str | ❌ | Section of source document |
| `source_page` | str | ❌ | Page of source document |
| `revision` | str | ❌ | Document revision |
| `issue_status` | str | ❌ | Document issue status |
| `data_quality_status` | str | ✅ | See quality status table below |
| `confidence` | str | ✅ | High / Medium / Low |
| `date_extracted` | date | ❌ | Date parameter was extracted |
| `extractor_version` | str | ❌ | Version of extraction tool/process |
| `notes` | str | ❌ | Free-text notes |

*Either `source_id` or `assumption_id` must be present.

### Data Quality Status Values

| Status | Meaning |
|---|---|
| `Confirmed` | Value confirmed from a formally issued document |
| `Provisional` | Value from a document in draft or review status |
| `Conflicting` | Value conflicts with another source; not resolved |
| `Missing` | Parameter not found in any source |
| `Assumed` | Value assumed in absence of source data; recorded in ASSUMPTIONS_REGISTER |
| `Not applicable` | Parameter does not apply to this configuration |

### Confidence Values

| Value | Meaning |
|---|---|
| `High` | Low uncertainty; confirmed from authoritative source |
| `Medium` | Moderate uncertainty; provisional or inferred |
| `Low` | High uncertainty; assumed or extrapolated |

---

## Weather Schema Fields

| Field | Type | Unit | Required | Description |
|---|---|---|---|---|
| `timestamp` | datetime (tz-aware) | — | ✅ | Measurement timestamp |
| `ghi` | float | W/m² | ✅ | Global horizontal irradiance |
| `dni` | float | W/m² | ✅ | Direct normal irradiance |
| `dhi` | float | W/m² | ✅ | Diffuse horizontal irradiance |
| `poa_front` | float | W/m² | ❌ | Front-side POA (measured) |
| `poa_rear` | float | W/m² | ❌ | Rear-side POA (measured) |
| `temp_ambient` | float | °C | ✅ | Ambient temperature |
| `temp_module` | float | °C | ❌ | Module temperature (measured) |
| `wind_speed` | float | m/s | ✅ | Wind speed |
| `wind_direction` | float | ° | ❌ | Wind direction (0° = North) |
| `relative_humidity` | float | % | ❌ | Relative humidity |
| `pressure` | float | Pa | ❌ | Atmospheric pressure |
| `rainfall` | float | mm | ❌ | Rainfall per timestep |
| `albedo` | float | — | ❌ | Ground albedo (0–1) |
| `soiling_ratio` | float | — | ❌ | Soiling loss ratio (0–1) |
| `sensor_status` | str | — | ❌ | Sensor health code |
| `quality_flag` | str | — | ✅ | QC result code |
| `source_classification` | str | — | ✅ | DataSourceClassification |

---

## Output Time-Series Fields (Per Simulation Stage)

### Solar Position

| Field | Unit | Description |
|---|---|---|
| `apparent_zenith` | ° | Apparent solar zenith angle |
| `apparent_azimuth` | ° | Apparent solar azimuth angle |
| `elevation` | ° | Solar elevation angle |
| `airmass` | — | Relative airmass |

### Tracker

| Field | Unit | Description |
|---|---|---|
| `tracker_theta` | ° | Tracker rotation angle |
| `surface_tilt` | ° | Module surface tilt |
| `surface_azimuth` | ° | Module surface azimuth |
| `aoi` | ° | Angle of incidence |
| `backtracking_active` | bool | Whether backtracking is active |

### Irradiance

| Field | Unit | Description |
|---|---|---|
| `poa_global` | W/m² | Total front-side POA irradiance |
| `poa_direct` | W/m² | Direct POA component |
| `poa_diffuse` | W/m² | Diffuse POA component |
| `poa_sky_diffuse` | W/m² | Sky diffuse component |
| `poa_ground_diffuse` | W/m² | Ground-reflected component |
| `poa_rear` | W/m² | Rear-side POA (bifacial model) |
| `poa_bifacial_effective` | W/m² | Bifacial effective irradiance |
| `iam_front` | — | Incidence angle modifier (front) |

### Temperature

| Field | Unit | Description |
|---|---|---|
| `temp_cell` | °C | Cell temperature |
| `temp_module_model` | °C | Modeled module temperature |

### DC Power

| Field | Unit | Description |
|---|---|---|
| `pdc_module` | W | DC power per module (at STC) |
| `pdc_string` | W | DC power per string |
| `pdc_smb` | W | DC power at SMB |
| `pdc_inverter` | W | DC power at inverter input |

### Inverter

| Field | Unit | Description |
|---|---|---|
| `pac_inverter` | W | AC power output |
| `p_clipping` | W | Clipped power |
| `p_auxiliary` | W | Auxiliary consumption |
| `inverter_efficiency` | — | AC/DC efficiency |
| `mppt_active` | bool | MPPT window enforcement active |

### Transformer

| Field | Unit | Description |
|---|---|---|
| `p_idt_input` | W | Power into IDT |
| `p_no_load_loss` | W | IDT no-load loss |
| `p_load_loss` | W | IDT load-dependent loss |
| `p_idt_output` | W | Power out of IDT |
| `load_fraction` | — | IDT load fraction (0–1) |

### Loss Ledger Fields

| Field | Unit | Classification |
|---|---|---|
| `loss_tracker_shading` | W | Physics-derived |
| `loss_soiling` | W | Assumed |
| `loss_iam` | W | Equipment-derived |
| `loss_temperature` | W | Physics-derived |
| `loss_dc_mismatch` | W | Design allowance |
| `loss_dc_cable` | W | Design allowance |
| `loss_inverter_conversion` | W | Physics-derived |
| `loss_inverter_clipping` | W | Physics-derived |
| `loss_idt_no_load` | W | Equipment-derived |
| `loss_idt_load` | W | Equipment-derived |
| `loss_ac_cable` | W | Design allowance |
| `loss_auxiliary` | W | Equipment-derived / Assumed |

---

## QC Flag Codes

| Code | Meaning |
|---|---|
| `OK` | Passed all checks |
| `QC_FAIL_NEGATIVE` | Value negative (physical impossibility) |
| `QC_FAIL_RANGE` | Value outside expected physical range |
| `QC_FAIL_FLATLINE` | Repeated identical value — sensor freeze suspected |
| `QC_FAIL_SPIKE` | Value spike exceeding physical maximum |
| `QC_FAIL_NIGHTTIME` | Irradiance > threshold at night |
| `QC_FAIL_GAP` | Missing data interval |
| `QC_FAIL_UNIT` | Unit inconsistency detected |
| `QC_WARN_CLIPPING` | Value at sensor maximum for multiple intervals |
| `QC_WARN_CALIBRATION` | Within calibration period |
| `QC_WARN_DROPOUT` | Extended NaN block — communication dropout suspected |

---

*NAJM-3000 Digital Twin | docs/data_dictionary.md | Revision 1.0*
