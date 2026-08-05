# CHANGELOG.md — NAJM-3000 Digital Twin

All notable changes to this repository are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added — Sprint 6: pre-commissioning SCADA-style dashboard (2026-08-02)

**Local only.** The dashboard is not hosted, by decision of the project lead:
serving plant configuration on a public URL would place site data outside the
controls in `CONFIDENTIALITY.md`. Run it with
`python -m najm3000.dashboard --config-dir config --date 2025-06-21`.

- `dashboard/static/` — hand-built HTML, CSS and SVG charts. No framework, no
  build step, and **no external requests**: no CDN, font, or analytics call, so
  the page works fully offline. Enforced by test.
- Screens: plant overview (block grid with drill-down), block detail, trends,
  weather panel, and an accelerated replay of the simulated day.
- The data-source chip renders from `/api/status` and is not dismissible, so the
  page cannot show live-looking values while claiming something the backend did
  not say. Tests assert the chip has no dismiss control and that the script
  never hides it.

**Visualisation decisions:**
- Trends are **three separate charts**, not one dual-axis chart — irradiance,
  temperature and power carry different units. Dual-axis was rejected outright.
- Series palette (blue `#2a78d6` / orange `#eb6834`, and their dark-mode steps)
  was **validated with the palette checker in both modes**, not chosen by eye:
  lightness band, chroma floor, CVD separation, normal-vision floor and contrast
  all pass.
- Zero baseline is applied to magnitudes (irradiance, power) but not to
  temperature, which is not a magnitude from zero.
- Plant blocks are assigned to **contiguous zones** rather than alternating. The
  earlier alternating assignment rendered as a checkerboard and misrepresented
  the layout. Per-block vendor mix is unknown (GAP-001), so the arrangement is
  labeled illustrative in the UI.
- Crosshair and tooltip on every chart; per-cell tooltip on the plant grid.

**Quality:** 277 → 292 tests; coverage 94.89% against the 90% gate; ruff and
mypy strict clean. Verified visually in light and dark mode at full plant scale
(286 blocks) with no console or page errors.

### Added — Public weather ingestion and post-POC cleanup (2026-08-02)

**Authorization.** The project lead approved use of an external public weather
source on 2026-08-02. The weather policy's six-step approval process was
followed and recorded in `DATA_REGISTER.md` (DAT-004) and
`DOCUMENT_REGISTER.md` (SRC-027).

**Pluggable weather sources:**
- `weather/provider.py` — `WeatherProvider` protocol plus
  `SyntheticClearskyProvider`. `run_block_simulation` now takes a provider
  instead of calling the synthetic generator directly, so the README claim that
  "weather source can be replaced without changing the physics engine" is
  structurally true rather than nominal.
- `weather/pvgis.py` — PVGIS ingestion via `pvlib.iotools.get_pvgis_hourly`
  (PVGIS-SARAH3 satellite + ERA5). PVGIS returns plane-of-array components, so
  the horizontal plane is asserted in the response and GHI/DHI derived from it;
  DNI uses `pvlib.irradiance.dni` rather than dividing by `sin(elevation)`,
  which diverges at sunrise and sunset.
- `weather/selection.py` — source selection, timestep override, and
  classification-appropriate run labeling.
- `--weather {synthetic_clearsky,public_pvgis}` and `--timestep-minutes` on both
  CLIs.

**Guardrails:**
- Classification locked to `PROVISIONAL_PUBLIC` by `Literal`; the disclaimer
  field must contain "NOT SITE-MEASURED" or schema validation fails.
- `WeatherTimeSeries.relabel` now refuses promotion to `MEASURED_SITE` from
  *any* non-measured source, not just synthetic. A test caught that public data
  could previously have been relabeled, which the weather policy forbids.
- Coverage guard (2005–2023), hourly-timestep guard, horizontal-plane guard,
  and missing-column guard — all hard failures.
- Retrieval failure raises `WeatherSourceError`; the model never falls back to
  another source, which would emit unlabeled data.
- Run output is labeled by the data actually used: a PVGIS run no longer prints
  "SYNTHETIC DEMONSTRATION" over real satellite data.
- Response cache goes to `data/interim/` (gitignored), not the committed
  `data/public/`, because a cache keyed to exact site coordinates is
  site-identifying. The committed test fixture uses a neutral coordinate.

**Registers:** SRC-027, DAT-004 (with the full approval record and the
exact-coordinate decision), FIX-003, ASMP-020 (10 m wind height), ASMP-021
(grid resolution). GAP-002 annotated as **unchanged** — public data does not
close it.

**Documentation drift correction.** Six locations still described shipped work
as unstarted or unauthorized. Most consequential: `CLAUDE.md` told every future
agent session that only documentation work was authorized. Also corrected
`requirements.txt`, the Sprint 1/2/3 headers in `PLANS.md`,
`docs/IMPLEMENTATION_PLAN.md`, and the stale test-file tree in
`docs/testing_strategy.md`.

**SCADA adapter interface — defined, deliberately inactive:**
- `scada/canonical.py` — canonical time-series schema. `value_raw` and
  `value_qc` are both required so a QC correction can never overwrite the
  original measurement, and `processing_version` is required so untraceable QC
  output cannot enter the comparison layer.
- `scada/adapter_interface.py` — `HistorianAdapter` ABC and
  `InactiveHistorianAdapter`, which raises `ScadaInactiveError` on every data
  request. Returning empty rows would let downstream code read "no data" as
  "zero production".
- `scada/tag_mapping.py` — tag mapping schema that **rejects IP addresses,
  hostnames, register addresses, and credentials** at parse time, per
  `CONFIDENTIALITY.md`. `config/tag_mapping.example.yaml` added; the real
  mapping is gitignored.

**Physics deepening (GAP-004) — assessed, still blocked, now diagnosed:**
- `cells_in_series` is no longer a blocker. It is **derived** as 66 from the
  datasheet "132 half-cells" (SRC-006/007) in standard half-cut topology, and
  confirmed against datasheet Voc (0.759 / 0.752 V per cell — the expected
  n-type TOPCon range; 72, 132 and 144 are all implausible). Logged as ASMP-022.
- `pvlib.ivtools.sdm.fit_desoto` nonetheless fails to converge from datasheet
  STC values across four initial guesses. GAP-004 updated with that diagnosis;
  remaining routes are NREL-PySAM `fit_cec_sam`, vendor PAN files, or flash-test
  IV curves. DR-004 raised for GAP-004 and GAP-005.
- No CEC/PVsyst DC model was implemented: the parameters to drive it do not
  exist, and PVWatts remains fully parameterized.

**Quality:** 157 → 215 tests; coverage 95.5% against the 90% gate; ruff and
mypy strict clean.

> PVGIS data is real weather but is **not site-measured**. It does not close
> GAP-002 or GAP-020, and the Digital Twin remains **not calibrated** and
> **not validated**.

### Added — Sprint 4: reporting, quality, and full test suite (2026-08-01)

**Reporting layer (`src/najm3000/reporting/`):**
- `provenance_report.py` — recursively walks the validated configuration tree
  and emits one row per engineering parameter with its source ID or assumption
  ID, unit, data-quality status, and confidence. Rejects any parameter that
  reaches the report with neither ID. Vendor variants are reported under their
  own alias and are never merged.
- `assumption_report.py` — parses the `## Register` table of
  `ASSUMPTIONS_REGISTER.md` and `DATA_GAP_REGISTER.md` and attaches the
  **registered** risk level to every `Assumed`, `Conflicting`, or `Missing`
  parameter. Risk is never derived or inferred; an assumption ID absent from
  the register is reported as `UNREGISTERED`.
- `scenarios.py` — scenario comparison and albedo/GCR sensitivity. Overrides
  are restricted to non-structural parameters, re-validated by Pydantic, and
  re-stamped as `Assumed` provenance carrying the assumption ID under study.
- `plots.py` — irradiance, temperature, power-chain, and automated loss
  waterfall figures (built on `matplotlib.figure.Figure`, no pyplot global
  state). The waterfall annotates each loss with its share of gross energy and
  refuses to render if the ledger does not close.
- `viewer.py` — data layer bundling configuration, simulation, and both
  reports for the dashboard.
- `__main__.py` — `python -m najm3000.reporting` CLI writing Markdown/CSV
  reports, the loss-waterfall table, and PNG figures. Re-runs the simulation
  from configuration so artifacts are always self-consistent.

**Optional viewer:**
- `notebooks/streamlit_viewer.py` — read-only dashboard; a thin UI shell with
  no engineering logic. Configuration paths are overridable by environment
  variable. Declared as the optional `viewer` extra in `pyproject.toml`.

**Quality:**
- Test suite raised from 41 to 157 tests; line coverage from 88% to 96%.
- `tests/unit/test_guards.py` — 38 tests asserting that every hard-fail guard
  fires (timezone rejection, weather relabeling refusal, tracker rotation
  limit, cell-temperature bounds, IDT loading bound, loss-fraction ranges,
  negative-loss rejection, placeholder and schema rejection, sanity checks).
  Config loader, sanity checks, and weather interface reached 100% coverage.
- Coverage gate raised from `fail_under = 70` to `fail_under = 90`.
- `docs/testing_strategy.md` updated with achieved coverage and suite
  composition, including which statements are deliberately left uncovered.

**Status statements (unchanged and re-asserted):**
- Every generated report, plot, and dashboard panel carries
  `SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION`.
- POC definition of done in `README.md` marked complete, with an explicit note
  that a complete POC is a *software* milestone and does not make the Digital
  Twin calibrated, validated, or operational.

### Added — Phase 0.5 audit + Sprints 1–3 implementation (2026-07-24)

**Datasheet audit (source-of-truth update):**
- Audited the locally supplied (uncommitted, gitignored) datasheet folder
  against all registers; `DOCUMENT_REGISTER.md` gained SRC-019…SRC-026 and
  re-audited SRC-009/010/011.
- Resolved assumptions ASMP-001 (tracker ±60°, all three vendors), ASMP-003
  (bifaciality 0.80), ASMP-009 (night draw 250/200 W), ASMP-010 (IDT 4.466 MVA
  losses), ASMP-011 (γ_Pmax per vendor), ASMP-014 (MPPT windows); added
  ASMP-016…ASMP-019 for block build-up assumptions.
- Data gaps: GAP-006, GAP-007, GAP-016 resolved; GAP-001/004/005/010/012/015
  narrowed; new GAP-019 (MVPS-count conflict), GAP-020 (TMY not supplied),
  GAP-021 (transmission-line count conflict); data requests DR-001…DR-003.
- `ASSET_REGISTER.md` populated with audited ratings incl. new main step-up
  transformer section; `CONFIDENTIALITY.md` sanitized-title list extended;
  `docs/weather_data_policy.md` updated (TMY status, 19-station sensor list).
- `.gitignore`: explicit `Data Sheets/` exclusion (PDFs were already ignored).

**Live configuration (gitignored, confidential):**
- `config/project.yaml`, `equipment.yaml`, `blocks.yaml`, `data_sources.yaml`
  populated with datasheet-grade values and full provenance blocks; two
  representative block variants (Vendor A and Vendor B chains).

**Physics engine (Sprints 1–3, approved by project lead 2026-07-24):**
- Config: Pydantic v2 schemas + hard-fail loader + `najm3000.config.validate` CLI.
- Weather: canonical `WeatherTimeSeries` with enforced classification and
  disclaimer; deterministic synthetic clear-sky generator (fixed turbidity).
- Chain: solar position, single-axis tracker (limit-enforced), Perez POA,
  infinite-sheds bifacial, PVsyst cell temperature, PVWatts DC, PVWatts
  inverter (clipping, MPPT window, night draw), IDT two-component losses,
  DC/AC cable + mismatch allowances, soiling placeholder with warning.
- Aggregation: block orchestrator, loss ledger with energy-balance closure,
  labeled plant-scaling scenario; `python -m najm3000` CLI writing Parquet +
  metadata sidecar with mandatory synthetic disclaimer.
- Fixed `pyproject.toml` build backend (`setuptools.build_meta`); added
  `py.typed`.

**Verification (all passing 2026-07-24):**
- `pytest`: 41 tests, coverage 88% (threshold 70%).
- `ruff check src/ tests/`: clean. `mypy src/` (strict): clean.
- End-to-end runs of both live block variants complete with closed energy
  balance; outputs carry `SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION`.

### Added — Phase 0: Governance and Foundation (2026-07-21)

**Repository structure and governance:**
- `CONFIDENTIALITY.md` — Confidentiality policy and NDA controls
- `AGENTS.md` — Repository-level AI agent instructions
- `CLAUDE.md` — Claude Code–specific guidance
- `README.md` — Comprehensive project documentation (25 required sections)
- `PLANS.md` — Phased implementation roadmap (Phase 0 through future operational phases)
- `CHANGELOG.md` — This file
- `.gitignore` — Raw-document and credential exclusions

**Registers:**
- `DOCUMENT_REGISTER.md` — Sanitized engineering document registry (18 source IDs assigned)
- `DATA_REGISTER.md` — Data inventory, classification, and QC requirements
- `ASSET_REGISTER.md` — Provisional asset register (all equipment classes)
- `ASSUMPTIONS_REGISTER.md` — Engineering assumptions register (15 open assumptions)
- `DATA_GAP_REGISTER.md` — Data gap register (18 identified gaps)

**Configuration examples:**
- `config/README.md` — Configuration structure and conventions
- `config/project.example.yaml` — Project and location configuration (placeholder)
- `config/equipment.example.yaml` — Multi-vendor equipment configuration (placeholder)
- `config/blocks.example.yaml` — MV block configuration (placeholder)
- `config/data_sources.example.yaml` — Weather and data source configuration (placeholder)

**Data directory:**
- `data/README.md` — Data handling policy and directory structure

**Documentation suite:**
- `docs/POC_PLAN.md` — POC objectives and scope
- `docs/IMPLEMENTATION_PLAN.md` — Technical implementation plan
- `docs/architecture.md` — System architecture overview
- `docs/modeling_methodology.md` — pvlib modeling chain and decisions
- `docs/asset_hierarchy.md` — Electrical and physical hierarchy definitions
- `docs/data_dictionary.md` — Field definitions and units
- `docs/validation_plan.md` — Validation phases and criteria
- `docs/testing_strategy.md` — Test categories and requirements
- `docs/weather_data_policy.md` — Weather source classification and policy
- `docs/scada_integration_plan.md` — SCADA integration architecture (inactive)
- `docs/ai_analytics_roadmap.md` — AI/analytics scope and roadmap
- `docs/security_and_data_handling.md` — Security and data governance
- `docs/decisions/ADR-001-initial-poc-architecture.md` — Architecture decision record

**Python package skeleton:**
- `src/najm3000/__init__.py` — Package initialization
- Module subdirectory stubs (README placeholders): `assets/`, `config/`, `ingestion/`,
  `weather/`, `tracking/`, `bifacial/`, `temperature/`, `dc_model/`, `inverter/`,
  `electrical_losses/`, `soiling/`, `aggregation/`, `validation/`, `analytics/`,
  `scada/`, `reporting/`

**Project configuration:**
- `pyproject.toml` — Project metadata and planned dependencies
- `requirements.txt` — Development requirements (planning stage; not installed)

**Directories created:**
- `notebooks/` — Jupyter notebook workspace
- `tests/` — Test suite (skeleton)
- `outputs/` — Simulation output directory

---

## Notes

- No raw engineering documents have been committed.
- No dependencies have been installed.
- No network requests have been made.
- No physics code has been written.
- All confidentiality checks passed.

---

*NAJM-3000 Digital Twin | CHANGELOG.md | Phase 0 — Governance and Foundation*
