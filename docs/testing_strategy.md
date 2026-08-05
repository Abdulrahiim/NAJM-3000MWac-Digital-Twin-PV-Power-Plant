# testing_strategy.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> This document is authoritative for all verification and test requirements.
> All agents must consult this document before implementing test functions.

---

## Principles

1. **Every physics component must have tests.** No component ships without coverage.
2. **Tests verify physics, not values.** Do not write tests that merely reproduce
   hard-coded expected outputs. Tests must enforce physical laws and invariants.
3. **Synthetic data must be labeled.** Tests using synthetic inputs must verify that
   the label propagates correctly to outputs.
4. **Reproducibility is mandatory.** A fixed synthetic clear-sky test day must
   produce identical results across runs.
5. **Tests must fail clearly.** Missing critical parameters must raise errors, not
   return silent zero values.

---

## Test Categories

### Category 1: Schema Validation

| Test | Description |
|---|---|
| `test_valid_project_config` | Valid project YAML passes Pydantic schema |
| `test_invalid_latitude` | Latitude outside −90…+90 raises `ValidationError` |
| `test_invalid_timezone` | Non-IANA timezone string raises `ValidationError` |
| `test_missing_source_id` | Parameter without provenance raises `ValidationError` |
| `test_naive_timestamp` | Naive datetime in weather input raises `ValidationError` |
| `test_invalid_data_classification` | Unknown source classification raises `ValidationError` |
| `test_placeholder_value_rejected` | String "PLACEHOLDER" in numeric field raises `ValidationError` |

### Category 2: SI-Unit Consistency

| Test | Description |
|---|---|
| `test_power_units_watts` | All power outputs are in W, not kW or MW |
| `test_irradiance_units_wm2` | All irradiance values are in W/m², not kWh/m² |
| `test_temperature_units_degc` | All temperatures are in °C |
| `test_angle_units_degrees` | All tracker angles are in degrees |
| `test_voltage_units_volts` | All voltage values are in V |

### Category 3: Timezone-Aware Timestamps

| Test | Description |
|---|---|
| `test_output_timestamps_have_tz` | All output DataFrames have timezone-aware index |
| `test_naive_input_rejected` | Weather input with naive index raises error |
| `test_timezone_preserved` | Output timezone matches configured project timezone |
| `test_dst_handling` | Simulation over a DST transition does not produce duplicate timestamps |

### Category 4: Physical Limits

| Test | Description |
|---|---|
| `test_no_negative_dc_power` | DC power is non-negative at all timesteps |
| `test_no_negative_ac_power` | AC power is non-negative at all timesteps |
| `test_zero_nighttime_generation` | AC power = 0 when solar elevation < 0° (excluding auxiliary) |
| `test_dc_greater_than_ac` | DC power ≥ AC power at every timestep (energy conservation) |
| `test_poa_non_negative` | POA irradiance is non-negative |
| `test_bifacial_poa_exceeds_front` | Bifacial effective irradiance ≥ front-side POA |
| `test_cell_temperature_bounds` | Cell temperature within [−30°C, +100°C] for all inputs |
| `test_non_negative_transformer_losses` | IDT losses are non-negative at all timesteps |

### Category 5: Tracker Limits

| Test | Description |
|---|---|
| `test_tracker_angle_within_max` | All tracker angles are within ±`max_angle` |
| `test_tracker_backtracking_active` | With backtrack=True, no row-on-row shading at low sun angles |
| `test_tracker_flat_at_night` | Tracker returns to configured stow position at night (if modeled) |

### Category 6: MPPT Window and Clipping

| Test | Description |
|---|---|
| `test_inverter_clipping_enforced` | AC output never exceeds `paco` |
| `test_mppt_window_low` | DC voltage below `mppt_low` produces zero or derated output |
| `test_mppt_window_high` | DC voltage above `mppt_high` produces clipped output |

### Category 7: Energy Balance

| Test | Description |
|---|---|
| `test_smb_equals_string_sum` | SMB energy = sum of constituent string energies |
| `test_inverter_equals_smb_sum` | Inverter DC input = sum of connected SMB outputs (before inverter losses) |
| `test_idt_equals_inverter_minus_losses` | IDT output = inverter AC − transformer losses |
| `test_block_equals_idt_sum` | Block total = sum of IDT outputs |
| `test_loss_waterfall_closes` | Sum of all loss categories + net output = gross input (POA × area) |

### Category 8: Provenance

| Test | Description |
|---|---|
| `test_all_key_params_have_provenance` | All key parameters in configuration carry `source_id` or `assumption_id` |
| `test_assumption_ids_in_register` | All assumption IDs in configuration exist in `ASSUMPTIONS_REGISTER.md` |
| `test_provenance_preserved_in_output` | Output Parquet files contain provenance metadata tags |

### Category 9: Weather Source Classification

| Test | Description |
|---|---|
| `test_synthetic_label_in_output` | Outputs from `SYNTHETIC_SOFTWARE_TEST` inputs carry the disclaimer label |
| `test_measured_label_not_synthetic` | Inputs labeled `SYNTHETIC_SOFTWARE_TEST` cannot be reclassified as `MEASURED_SITE` |
| `test_source_classification_required` | Weather inputs without a classification field raise an error |

### Category 10: Multi-Vendor Isolation

| Test | Description |
|---|---|
| `test_vendor_a_different_from_vendor_b` | Simulation with Vendor A equipment produces different results from Vendor B |
| `test_overrides_are_isolated` | Block-level overrides do not affect other block configurations |
| `test_no_cross_vendor_averaging` | No test fixture averages unlike equipment configurations |

### Category 11: Failure Modes

| Test | Description |
|---|---|
| `test_missing_critical_param_raises` | Missing required parameter raises a hard error, not silent default |
| `test_large_time_gap_not_interpolated` | Time gaps exceeding configured threshold are flagged, not silently interpolated |
| `test_placeholder_value_rejected` | String "PLACEHOLDER" in numeric field raises error at load time |
| `test_conflicting_params_not_averaged` | Conflicting parameter values raise a warning, not silent resolution |

### Category 12: Reproducibility

| Test | Description |
|---|---|
| `test_synthetic_clearsky_deterministic` | Identical synthetic clear-sky inputs → identical output (all decimal places) |
| `test_independent_of_run_order` | Running blocks in different orders produces identical individual-block results |

---

## Test Infrastructure

### File Structure (Planned — Sprint 1)

```
tests/
├── conftest.py               # Shared fixtures
├── fixtures/
│   ├── project.yaml          # Minimal valid project config
│   ├── equipment.yaml        # Multi-vendor equipment fixtures
│   └── blocks.yaml           # Block configuration fixtures
├── unit/
│   ├── test_config.py            # Schema validation and loader tests
│   ├── test_weather.py           # Weather interface and classification
│   ├── test_physics_chain.py     # Solar position → tracker → POA → bifacial
│   │                             #   → temperature → DC
│   ├── test_inverter_components.py  # Clipping, MPPT window, night draw
│   ├── test_guards.py            # Every hard-fail guard, across all modules
│   ├── test_provenance_report.py
│   ├── test_assumption_report.py
│   ├── test_scenarios.py         # Overrides and sensitivity comparison
│   ├── test_plots.py             # Figures and the loss waterfall
│   └── test_viewer.py            # Dashboard data layer
├── integration/
│   ├── test_clearsky_chain.py    # End-to-end config → block result
│   ├── test_reporting_cli.py     # python -m najm3000.reporting artifacts
│   └── test_streamlit_viewer.py  # UI shell executes (AppTest)
└── smoke/
    └── test_smoke.py             # Runs once on fixed synthetic day; must not regress
```

Physics stages are tested per-stage inside `test_physics_chain.py` and
`test_guards.py` rather than in one file per module. The requirement is that
each stage is *separately* testable, which it is — the grouping is a file-layout
choice, not a coverage gap.

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src/najm3000 --cov-report=term-missing

# Run unit tests only
pytest tests/unit/ -v

# Run smoke test (reproducibility check)
pytest tests/smoke/ -v
```

### Coverage Target

- Sprint 1 minimum: 60% line coverage
- Sprint 4 target: ≥90% line coverage

### Achieved Coverage (Sprint 4, 2026-08-01)

| Metric | Value |
|---|---|
| Tests passing | 157 |
| Line coverage | 96.3% (1,413 statements, 52 uncovered) |
| Enforced gate | `fail_under = 90` in `pyproject.toml` — the suite fails below it |
| Lint | `ruff check src/ tests/ notebooks/` — clean |
| Type check | `mypy src/ notebooks/` (strict) — clean |

Modules at 100% line coverage: config loader, loss ledger, sanity checks,
weather interface, cell temperature, DC model, DC/AC cable, soiling,
single-axis tracker, asset hierarchy, and the reporting plot/viewer layers.

The ~52 uncovered statements are defensive guards that cannot be reached
without corrupting a third-party return value (for example, the
"pvlib returned a frame missing required columns" `RuntimeError` branches) plus
`if __name__ == "__main__"` lines. These are deliberately left uncovered rather
than reached by mocking pvlib internals, which would test the mock and not the
model.

### Test Suite Composition

| Area | Tests | What they hold to account |
|---|---|---|
| Configuration and schemas | 8 | Hard-fail on invalid, placeholder, or unreferenced config |
| Weather | 8 | Classification labeling, timezone-awareness, synthetic disclaimer |
| Physics chain | 15 | Tracker limits, POA, bifacial gain, temperature, DC/AC conversion |
| Inverter components | 6 | Clipping, MPPT window, night draw |
| Guards and physical limits | 38 | Every hard-fail branch fires instead of degrading silently |
| Provenance report | 10 | Every parameter traceable to a source or assumption ID |
| Assumption report | 15 | Register parsing, risk attribution, unregistered-ID detection |
| Scenario comparison | 16 | Override validation, physical monotonicity, ledger closure |
| Plots and loss waterfall | 14 | Mandatory labeling, SI units, waterfall closure |
| Viewer data layer | 8 | Context assembly and error handling |
| Reporting CLI | 9 | Artifact generation, disclaimer presence, exit codes |
| Streamlit viewer | 6 | UI shell executes; status labels present |
| Clear-sky integration + smoke | 4 | End-to-end chain, reproducibility on a fixed test day |

---

## Anti-Patterns to Avoid

- ❌ Tests that hard-code expected energy values and merely check for equality.
- ❌ Tests that pass with zero input (division-by-zero bypassed by fixture).
- ❌ Tests that skip timezone-awareness checks.
- ❌ Tests that accept a `PLACEHOLDER` string as a valid parameter value.
- ❌ Tests that allow negative power or irradiance silently.
- ❌ Tests that assume a single vendor configuration for a multi-vendor plant.

---

*NAJM-3000 Digital Twin | docs/testing_strategy.md | Revision 1.0*
