# validation_plan.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> This document defines the six-phase validation strategy.
> The Digital Twin is currently **not calibrated** and **not validated**.

---

## Overview

Validation is the process of confirming that the Digital Twin produces physically
correct results and, eventually, results that match measured NAJM-3000 production.

Validation has six distinct phases. Phases 1–3 can be completed before commissioning.
Phases 4–6 require measured operational data.

---

## Phase 1 — Software Verification

**Goal:** Confirm that the software correctly implements the intended physics.

**Method:**
- All unit and integration tests pass (`pytest tests/`).
- Physical invariants hold for synthetic inputs (see `docs/testing_strategy.md`).
- Energy balance closes at every aggregation level.
- Reproducibility test passes on a fixed synthetic clear-sky day.

**Possible now:** ✅ Yes

**Does not require:** Measured data, SCADA, or site parameters.

**Output:** Test coverage report, CI pass/fail record.

---

## Phase 2 — Physical Sanity Checking

**Goal:** Confirm that model outputs are within physically plausible ranges
for the project's climate and configuration.

**Checks:**
- Annual POA irradiance within expected range for the site's climate zone.
- DC/AC ratio consistent with configuration.
- Peak DC power consistent with module STC and configuration.
- Temperature coefficients produce plausible derating at high ambient temperatures.
- Loss waterfall percentages consistent with industry benchmarks.
- Tracker backtracking effective at low solar angles.
- Bifacial gain within plausible range (typically 3–12% for SAT configurations).

**Possible now:** ✅ Partially (with synthetic clear-sky and provisional parameters)

**Limitation:** Sanity thresholds are based on provisional assumptions and
public climate data — not confirmed site measurements.

**Output:** Sanity check report with flagged outliers and assumption warnings.

---

## Phase 3 — Design-Model Benchmarking

**Goal:** Compare Digital Twin output against any available design-basis energy
estimate or independent third-party assessment for NAJM-3000.

**Approach:**
- Obtain (or request) the design-basis P50/P90 energy yield estimate for the
  representative block.
- Run the Digital Twin with the closest available configuration.
- Compare at the annual and monthly level.
- Document all differences and their engineering cause.

**Possible now:** Partial — depends on availability of a design-basis reference.

**Constraint:** Discrepancies must be explained, not ignored. The Digital Twin
is not expected to match exactly at this stage (parameters are provisional).

**Output:** Benchmarking report with quantified discrepancies and explanations.

---

## Phase 4 — Commissioning Validation

**Goal:** Validate the Digital Twin against first measured production data
during plant commissioning.

**Requirements:**
- SCADA system commissioned and delivering data.
- At least 30 days of measured production data with on-site weather.
- Quality-controlled and timestamped weather and production data.
- Block-level performance data (not only plant-level totals).

**Activities:**
- Compare modeled vs. measured POA irradiance.
- Compare modeled vs. measured string currents.
- Compare modeled vs. measured inverter output.
- Compare modeled vs. measured block-level AC output.
- Calculate performance ratio (PR) and compare to design basis.
- Identify systematic deviations and attribute to causes.

**Possible now:** ❌ No — SCADA not active; measured data does not exist.

**Output:** Commissioning validation report; model calibration proposal.

---

## Phase 5 — Operational Calibration

**Goal:** Calibrate the Digital Twin model parameters to match long-term
measured production data.

**Requirements:**
- Minimum 6–12 months of quality-controlled operational data.
- Confirmed block-level equipment inventory.
- Validated weather data from on-site stations.

**Activities:**
- Parameter estimation for degradation, soiling, and availability.
- Inverter efficiency curve fitting (if Sandia/ADR model used).
- Cell temperature model coefficient refinement.
- Bifaciality and albedo calibration.
- Soiling rate estimation from clean-vs-soiled performance comparison.

**Possible now:** ❌ No.

**Output:** Calibrated model configuration; calibration report; updated
parameter confidence levels.

---

## Phase 6 — Long-Term Performance Validation

**Goal:** Confirm that the calibrated model continues to accurately track
plant performance across multi-year timescales.

**Requirements:**
- ≥3 years of quality-controlled operational data.
- Regular model recalibration schedule.

**Activities:**
- Annual model-vs-actual PR comparison.
- Degradation rate estimation and model update.
- Long-term soiling and availability trend analysis.

**Possible now:** ❌ No.

**Output:** Annual validation report; model update log.

---

## Summary Table

| Phase | Description | Possible Now | Key Requirement |
|---|---|---|---|
| 1. Software Verification | Tests pass; physics rules hold | ✅ Yes | Test suite |
| 2. Physical Sanity | Outputs within plausible ranges | ✅ Partial | Provisional config |
| 3. Design Benchmarking | Compare to design-basis estimate | ⚠️ Partial | Design-basis reference |
| 4. Commissioning | Compare to first measured data | ❌ No | SCADA + measured data |
| 5. Operational Calibration | Tune model to long-term measured | ❌ No | 6–12 months data |
| 6. Long-Term Validation | Multi-year performance tracking | ❌ No | 3+ years data |

---

## Prohibited Claims

Until Phase 4 is completed, the Digital Twin must not claim:

- ❌ Calibrated model coefficients.
- ❌ Validated against NAJM-3000 production.
- ❌ Accurate energy yield prediction.
- ❌ Performance ratio calculation from actual data.
- ❌ That synthetic results represent actual plant behavior.

---

*NAJM-3000 Digital Twin | docs/validation_plan.md | Revision 1.0*
*Digital Twin Status: Not Calibrated | Not Validated*
