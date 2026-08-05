# modeling_methodology.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> This document is authoritative for all physics modeling decisions.
> All agents and contributors must consult this document before implementing
> or modifying model functions.

---

## Status

> ⚠️ The NAJM-3000 Digital Twin model is **not calibrated** and **not validated**.
> Results are engineering estimates based on datasheet parameters and assumptions.
> See `docs/validation_plan.md` for the path to calibration and validation.

---

## Design Principles

1. **No hard-coded equipment parameters.** All parameters come from YAML configuration
   loaded through Pydantic schemas.
2. **Full parameter provenance.** Every important parameter carries a source ID,
   quality status, and confidence level.
3. **Explicit assumption labeling.** All assumed values are recorded in
   `ASSUMPTIONS_REGISTER.md` and flagged in model outputs.
4. **Multi-vendor isolation.** Each block uses its configured vendor variant.
   Unlike equipment is never averaged.
5. **Modular and testable.** Each modeling stage is independently testable.
6. **Weather source independence.** The physics engine accepts any weather input
   that satisfies the canonical weather schema, regardless of source classification.

---

## Modeling Chain Summary

```
Location + Time
     ↓
Solar Position (pvlib.solarposition)
     ↓
Single-Axis Tracker (pvlib.tracking.singleaxis)
     ↓
Front-Side POA Irradiance (pvlib.irradiance.get_total_irradiance)
     ↓
Bifacial Irradiance (pvlib.bifacial.infinite_sheds)
     ↓
Cell Temperature (pvlib.temperature.pvsyst_cell / sapm_cell)
     ↓
DC Power (pvlib.pvsystem.pvwatts_dc → CEC/SAPM when params confirmed)
     ↓
Inverter Conversion (pvlib.inverter.pvwatts → Sandia/ADR when params confirmed)
     ↓ [clipping, MPPT, auxiliary, night losses]
IDT Transformer Losses (P_no_load + P_load_rated × load_fraction²)
     ↓
Aggregation (String → SMB → Inverter → IDT → MV Block → Feeder → Plant Scenario)
     ↓
Loss Ledger + Provenance Report + Assumption Report
```

---

## 1. Location and Time

**Library:** `pvlib.location.Location`

**Requirements:**
- Latitude, longitude, timezone (IANA string), altitude.
- All timestamps must be timezone-aware `pandas.DatetimeIndex`.
- Naive datetimes are rejected at the configuration validation stage.
- Site coordinates are confidential — stored only in gitignored `config/project.yaml`.

**Timestep:** Match SCADA design timestep (10 minutes) when data is available.
For software testing, 10-minute or 1-hour intervals are acceptable.

---

## 2. Solar Position

**Library:** `pvlib.solarposition` or `Location.get_solarposition()`

**Method:** `nrel_numpy` (configurable in `config/project.yaml`)

**Outputs used:**
- `apparent_zenith` — for tracker and irradiance calculations
- `apparent_azimuth` — for tracker and irradiance calculations
- `elevation` — for nighttime masking

---

## 3. Single-Axis Tracker

**Library:** `pvlib.tracking.singleaxis()`

**Parameters (all from configuration — no hard-coded values):**

| Parameter | Description | Status |
|---|---|---|
| `axis_tilt` | Tilt of tracker rotation axis | Provisional (SRC-012) |
| `axis_azimuth` | Azimuth of tracker rotation axis | Provisional (SRC-012) |
| `max_angle` | Maximum rotation from horizontal | Provisional 60° (ASMP-001) |
| `backtrack` | Enable backtracking | Configurable |
| `gcr` | Ground coverage ratio | Assumed (ASMP-013) |
| `cross_axis_tilt` | Cross-axis slope | Assumed 0° for POC |

**Physical enforcement:** Tracker angle output must be clamped to `±max_angle`.
Any simulation producing tracker angles outside this range raises an error.

**Backtracking:** Must be enabled by default for all SAT configurations.
Disabling backtracking is a named scenario, not the default.

---

## 4. Front-Side POA Irradiance

**Library:** `pvlib.irradiance.get_total_irradiance()`

**Transposition model:** Perez (configurable; Hay-Davies as alternative)

**Inputs:** GHI, DNI, DHI from weather source (or pvlib clear-sky for software testing)

**Output:** `poa_global`, `poa_direct`, `poa_diffuse`, `poa_sky_diffuse`, `poa_ground_diffuse`

---

## 5. Bifacial Irradiance

**Library:** `pvlib.bifacial.infinite_sheds`

**Rationale:** Physically rigorous for row-based SAT configurations with a uniform
ground surface. See ADR-001.

**Parameters (all from configuration):**

| Parameter | Description | Status |
|---|---|---|
| `gcr` | Ground coverage ratio | Assumed (ASMP-013) |
| `height` | Tracker axis height | Assumed (ASMP-002) |
| `albedo` | Ground albedo | Assumed (ASMP-005) |
| `bifaciality` | Module bifaciality factor | Assumed (ASMP-003) |
| `rear_mismatch` | Rear-side mismatch allowance | Assumed (ASMP-004) |

**Effective bifacial irradiance:**
```
G_eff = G_poa_front + bifaciality × G_poa_rear × (1 - rear_mismatch)
```

---

## 6. Cell Temperature

**Primary model:** `pvlib.temperature.pvsyst_cell()`
**Fallback model:** `pvlib.temperature.sapm_cell()`

**Selection:** Determined by available datasheet parameters:
- Use `pvsyst_cell` when `u_c` and `u_v` are available.
- Use `sapm_cell` when SAPM thermal coefficients are available.
- For POC software testing with synthetic inputs, use `pvsyst_cell` with
  provisional default coefficients (clearly labeled as assumed).

---

## 7. DC Power

**Sprint 1–2 model:** `pvlib.pvsystem.pvwatts_dc()`

**Required parameters:** `pdc_stc`, `gamma_pdc`

**Rationale:** Minimal parameter requirement; PVWatts is sufficient for POC
demonstration while full CEC/SAPM parameter sets are confirmed.

**Upgrade path:** When complete CEC parameter sets are confirmed from datasheets
or flash test certificates, upgrade to `pvlib.pvsystem.calcparams_cec()` and
`pvlib.pvsystem.singlediode()`.

**Constraint:** PVWatts DC must never be used for bankable yield assessments.

---

## 8. Inverter Conversion

**Sprint 1–2 model:** `pvlib.inverter.pvwatts()`

**Explicit handling required:**

| Effect | Treatment |
|---|---|
| AC output clipping | Hard limit at `paco` |
| MPPT window | DC input below `mppt_low` or above `mppt_high` → zero or derated output |
| Night auxiliary consumption | Configurable constant loss when DC input = 0 |
| Temperature derating | Placeholder — not modeled until thermal curve confirmed |

**Upgrade path:** `pvlib.inverter.sandia()` or `pvlib.inverter.adr()` when
complete coefficient sets are confirmed.

---

## 9. IDT Transformer Losses

**Model:** Two-component transformer loss formula

```
P_loss(t) = P_no_load + P_load_rated × [P_ac(t) / P_rated]²
```

Where:
- `P_no_load` = no-load (core / iron) losses [W] — from IDT datasheet
- `P_load_rated` = load (copper / winding) losses at rated power [W] — from IDT datasheet
- `P_ac(t)` = instantaneous AC power from inverter(s) [W]
- `P_rated` = IDT rated power [W]

**Constraint:** Ambiguous IDT loss data rows (GAP-006) must not be silently assumed.
The 4.466 MVA variant requires explicit engineering review before use.

---

## 10. Loss Ledger

All losses are classified and tracked:

| Loss Term | Classification | Sprint |
|---|---|---|
| Tracker / shading geometry | Physics-derived | Sprint 1 |
| Soiling | Assumed (ASMP-006) | Sprint 3 |
| IAM (incidence angle modifier) | Equipment-derived | Sprint 3 |
| Spectral effects | Not modeled (POC) | Future |
| Module temperature | Physics-derived | Sprint 2 |
| DC mismatch | Design allowance | Sprint 2 |
| DC cable losses | Design allowance | Sprint 3 |
| Inverter conversion | Physics-derived | Sprint 2 |
| Inverter clipping | Physics-derived | Sprint 2 |
| IDT no-load losses | Equipment-derived | Sprint 3 |
| IDT load-dependent losses | Equipment-derived | Sprint 3 |
| AC cable losses | Design allowance | Sprint 3 |
| Auxiliary consumption | Equipment-derived / Assumed | Sprint 2 |
| Availability | Not modeled (physics baseline = 100%) | Labeled explicitly |
| Curtailment | Not modeled (physics baseline = 0%) | Labeled explicitly |
| Degradation | Not modeled (POC) | Future |
| Tracker availability | Not modeled (POC) | Future |

---

## Model Limitations

1. PVWatts DC is a simplified model — not suitable for bankable yield assessment.
2. Bifacial model parameters are provisional — significant uncertainty in rear-side gain.
3. No temperature derating curve for inverters.
4. No spectral correction model.
5. Soiling is a constant assumption — no dynamic soiling model.
6. Degradation not modeled.
7. Tracker availability not modeled.
8. Shading losses from cross-row inter-row shading handled by tracker backtracking only;
   near-field shading not modeled.

---

*NAJM-3000 Digital Twin | docs/modeling_methodology.md | Revision 1.0*
*Model: Not Calibrated | Model: Not Validated*
