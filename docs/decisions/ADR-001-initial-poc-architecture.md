# ADR-001 — Initial POC Architecture Decision

**Date:** 2026-07-21
**Status:** Accepted
**Deciders:** Lead Architect (NAJM-3000 Digital Twin)

---

## Context

NAJM-3000 is a 3,000 MWac utility-scale solar PV project under construction and pre-operational.
No measured weather data, SCADA telemetry, or operational production data exists.

The Digital Twin must be designed to:
1. Support engineering analysis before commissioning.
2. Scale to full plant simulation when block assignments are finalized.
3. Accommodate multiple equipment vendors and model variants.
4. Connect to SCADA when commissioned, without changing the physics engine.
5. Support future AI/analytics when operational data exists.

---

## Decision

### 1. Python / pvlib as the physics engine

**Decision:** Use Python ≥3.11 and pvlib as the primary modeling library.

**Rationale:**
- pvlib is the industry standard for open, auditable, reproducible PV simulation.
- All model functions are transparent and documented.
- Compatible with pandas time-series workflows.
- Supports single-axis tracking, bifacial modeling, and all required irradiance models.

**Alternatives considered:**
- Commercial software (e.g., PVsyst): Not open-source; poor version control integration.
- Custom MATLAB/Python model: Higher maintenance burden; pvlib is better tested.

### 2. Single representative MV block as POC scope

**Decision:** Design the POC around one configurable MV block. Architecture must support
all blocks without treating the plant as one generic system.

**Rationale:**
- Block assignment matrix is not finalized (GAP-001).
- Prevents over-engineering before vendor mix is confirmed.
- Block-level modeling correctly captures multi-vendor differences.

### 3. PVWatts DC and inverter models for Sprint 1–2

**Decision:** Use `pvlib.pvsystem.pvwatts_dc()` and `pvlib.inverter.pvwatts()` as the
initial POC models.

**Rationale:**
- PVWatts requires only `pdc_stc` and `gamma_pdc` — parameters available from partial
  datasheets (SRC-006, SRC-007).
- CEC, SAPM, and PVsyst models require full parameter sets not yet confirmed.
- PVWatts is clearly documented as a simplified model.
- Architecture permits upgrading to CEC/SAPM/ADR when parameters are confirmed.

**Constraint:** Never use PVWatts for bankable energy assessments.

### 4. Infinite sheds bifacial model

**Decision:** Use `pvlib.bifacial.infinite_sheds` for bifacial irradiance.

**Rationale:**
- Physically rigorous for row-based SAT configurations.
- Accepts GCR, axis height, albedo, and bifaciality parameters from configuration.
- Consistent with industry practice for utility-scale bifacial SAT plants.

**Risk:** GCR and axis height are provisional assumptions (ASMP-001, ASMP-013).

### 5. YAML configuration with Pydantic validation

**Decision:** All equipment and block parameters are stored in YAML files.
Schema validation is performed by Pydantic v2 at load time.

**Rationale:**
- YAML is human-readable and version-controllable.
- Pydantic enforces types, units, and required provenance fields.
- Hard errors on invalid configuration prevent silent incorrect runs.
- Easy to extend for multi-vendor overrides.

### 6. Provenance object on every important parameter

**Decision:** Every parameter must carry a provenance record with source ID, quality
status, and confidence. Parameters without provenance must carry an assumption ID.

**Rationale:**
- Required for engineering auditability.
- Enables automated provenance and assumption reports.
- Prevents silent use of invented values.

### 7. SCADA interface isolated from physics engine

**Decision:** The SCADA/historian adapter is defined as a separate module with a
documented interface contract. The physics engine has no dependency on SCADA.

**Rationale:**
- Physics engine must run without SCADA (pre-commissioning).
- Decoupling prevents SCADA changes from breaking the model.
- Clean separation enables mock-adapter testing.

### 8. Parquet as primary output format

**Decision:** Processed time-series outputs are stored in Parquet format.

**Rationale:**
- Columnar format with efficient compression.
- Preserves all metadata tags.
- Compatible with pandas, xarray, and Spark.

---

## Consequences

### Positive
- Physics engine can run on day 1 with synthetic inputs.
- Architecture is auditable and reproducible.
- Multi-vendor support is built in from the start.
- SCADA connection does not require refactoring the physics engine.

### Negative / Risks
- PVWatts DC is a simplified model; final accuracy limited until CEC/SAPM parameters
  are confirmed.
- GCR, bifaciality, and albedo assumptions carry high risk (ASMP-003, ASMP-005, ASMP-013).
- Plant-level scaling is illustrative until block assignment matrix is confirmed (GAP-001).

---

## Review Trigger

This ADR should be reviewed when:
- Block assignment matrix is available (GAP-001 resolved).
- Complete CEC or SAPM parameters are confirmed from datasheets.
- First measured weather data is available (GAP-002 resolved).
- SCADA commissioning begins.

---

*NAJM-3000 Digital Twin | ADR-001 | Status: Accepted | 2026-07-21*
