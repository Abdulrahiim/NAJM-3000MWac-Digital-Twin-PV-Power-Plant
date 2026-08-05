# ai_analytics_roadmap.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**

---

## Status

> ⚠️ **NAJM-3000 is pre-operational. No operational data exists.**
> AI and analytics are currently limited to software architecture, synthetic
> demonstrations, and pre-operational planning.

---

## Guiding Principle

**Synthetic demonstrations do not prove operational detection accuracy.**

Every result generated from `SYNTHETIC_SOFTWARE_TEST` data must be clearly labeled:

> **SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION**

No AI or analytics claim may be made about NAJM-3000 plant performance before
representative measured operational data exists.

---

## Phase A — Pre-Operational (Current)

### Authorized Activities

| Activity | Description |
|---|---|
| Software architecture testing | Test ML pipeline components with synthetic data |
| Synthetic fault demonstrations | Demonstrate fault signatures on synthetic time series |
| Scenario analysis | Sensitivity of energy yield to parameter variations |
| Data-quality algorithm development | Test QC algorithms on synthetic and public data |
| Weather-pattern analysis | Analyze publicly available regional climate data |
| Sensitivity studies | Parameter uncertainty quantification |

### Synthetic Fault Demonstrations

The following synthetic faults may be simulated for software demonstration:

| Fault Type | Description | Label Required |
|---|---|---|
| Stuck tracker | Tracker angle constant; POA reduced | ✅ SYNTHETIC |
| Reduced string current | One string at 60% of expected current | ✅ SYNTHETIC |
| Open string | One string producing zero current | ✅ SYNTHETIC |
| Fuse failure | SMB input fuse open; string disconnected | ✅ SYNTHETIC |
| Inverter clipping | AC output flat at maximum; DC input rising | ✅ SYNTHETIC |
| Inverter thermal derating | AC output reduced by temperature | ✅ SYNTHETIC |
| Communication dropout | SCADA signal loss; data gap | ✅ SYNTHETIC |

Every synthetic fault demonstration must:
- Use `source_classification = "SYNTHETIC_SOFTWARE_TEST"`.
- Carry the label `SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION` in all outputs.
- Not be cited as evidence of real plant fault detection capability.

---

## Phase B — Post-Commissioning (Requires Measured Data)

### Prerequisites

- ≥6 months of quality-controlled operational data at block level.
- Validated weather data from on-site stations.
- SCADA tag dictionary confirmed (GAP-003 resolved).
- Digital Twin commissioned (Phases 4–5 of validation plan complete).

### Planned Analytics Capabilities

| Capability | Description |
|---|---|
| Expected-vs-actual residual modeling | Compare physics expected output to measured production |
| String-level anomaly detection | Identify underperforming strings from current imbalance |
| Inverter anomaly detection | Identify inverter efficiency degradation or faults |
| Fault classification | Classify anomalies by fault type using decision rules or ML |
| Soiling estimation | Estimate soiling rate from irradiance-normalized performance |
| Cleaning optimization | Recommend cleaning schedule based on soiling rate and cost |
| Degradation analysis | Estimate long-term power degradation rate |
| Availability forecasting | Predict equipment availability for operations planning |
| Predictive maintenance | Recommend maintenance actions before failure |

### ML Model Requirements (when applicable)

- All training data must be quality-controlled and labeled.
- Training data must be representative of full operational range.
- Models must be versioned, documented, and reproducible.
- Model predictions must include uncertainty estimates.
- Models must be re-validated after any major plant configuration change.
- No model trained on synthetic data may be deployed for operational decisions.

---

## Prohibited Claims

Until Phase B prerequisites are met:

- ❌ Do not claim that any anomaly detection algorithm is proven for NAJM-3000.
- ❌ Do not claim specific detection accuracy or precision/recall metrics.
- ❌ Do not present synthetic fault results as evidence of operational capability.
- ❌ Do not use AI model outputs for contractual, financial, or safety-critical decisions.

---

*NAJM-3000 Digital Twin | docs/ai_analytics_roadmap.md | Revision 1.0*
*Status: Pre-Operational — Phase A Only*
