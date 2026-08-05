# ASSUMPTIONS_REGISTER.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> This register records every engineering assumption made in the absence of confirmed
> source data. All assumptions must be revisited when missing data is supplied.

---

## How to Use This Register

1. Never hard-code an assumed value in model functions.
2. Assign an assumption ID (`ASMP-001`, `ASMP-002`, …).
3. Record the assumed value, unit, reason, and risk level.
4. Attach the assumption ID to the Pydantic provenance object for the parameter.
5. When confirmed data is available, update the parameter to `Confirmed` status and
   mark the assumption as resolved.

---

## Assumption Risk Levels

| Level | Meaning |
|---|---|
| High | Could significantly alter energy yield, loss attribution, or design decisions |
| Medium | Could affect results but unlikely to change major conclusions |
| Low | Minor sensitivity; results robust to reasonable variation |

---

## Register

| ID | Parameter | Asset Class | Assumed Value | Unit | Reason | Risk | Invalidation Condition | Status |
|---|---|---|---|---|---|---|---|---|
| ASMP-001 | Tracker maximum rotation | Tracker (all) | 60 | degrees | **Resolved 2026-07-24:** all three vendor datasheets state ±60° tracking range (SRC-012, SRC-021, SRC-022); one vendor offers a 75° hail-stow option (not modeled) | Low | As-built controller configuration | Resolved (Provisional) |
| ASMP-002 | Tracker axis height | Tracker (all) | 1.5 | m | Preliminary design reference; not confirmed for all block areas | Medium | As-built survey or confirmed datasheet | Open |
| ASMP-003 | Bifaciality factor | PV Module (all) | 0.80 | — | **Resolved 2026-07-24:** both vendor datasheets state 80% ±5% (SRC-006, SRC-007); value updated from 0.70 | Medium | Flash-test / as-installed confirmation (±5% tolerance) | Resolved (Provisional) |
| ASMP-004 | Rear-side mismatch factor | PV Module (all) | 0.02 | fraction | Industry guideline; no site-specific measurement | Medium | Commissioning measurement or vendor confirmation | Open |
| ASMP-005 | Ground albedo (provisional) | Site | 0.20 | — | Typical desert/gravel range; no measured value | High | On-site albedo measurement | Open |
| ASMP-006 | Soiling loss factor | Site | 0.02 | fraction | Placeholder; no cleaning schedule or soiling measurement available | High | Operational soiling monitoring data | Open |
| ASMP-007 | DC cable loss | Block (all) | 0.005 | fraction | Design allowance; specific cable lengths not confirmed | Medium | Final electrical design confirmation | Open |
| ASMP-008 | AC cable loss | Block (all) | 0.003 | fraction | Design allowance; specific cable lengths not confirmed | Medium | Final electrical design confirmation | Open |
| ASMP-009 | Inverter auxiliary consumption (night) | Inverter (all) | 250 (Vendor A) / 200 (Vendor B) | W | **Resolved 2026-07-24:** datasheet night-consumption upper bounds (SRC-008: <250 W; SRC-009: <200 W) used as conservative constants | Low | Commissioning measurement | Resolved (Provisional) |
| ASMP-010 | IDT no-load loss (4.466 MVA variant) | IDT (Vendor A) | 4.466 | kW | **Resolved 2026-07-24:** vendor GTP states no-load 0.1% and load 0.7% at 75 °C, principal tap (SRC-011) | Medium | Confirmed IDT routine test report | Resolved (Provisional) |
| ASMP-011 | Module temperature coefficient (Pmax) | PV Module (all) | -0.0029 (Vendor A) / -0.00274 (Vendor B) | per °C | **Resolved 2026-07-24:** datasheet values (SRC-006: −0.29%/°C; SRC-007: −0.274%/°C); per-vendor, never averaged | Low | Flash test data | Resolved (Provisional) |
| ASMP-012 | Plant block count (for scaling scenario) | Plant | 365 MVPS (design basis) | count | Design basis states 365 MVPS / 2 PSS (SRC-026), but IDT GTP BOQ lists 286+2 units (SRC-010/011) — see GAP-019; scaling scenarios must label which figure is used | High | Final block assignment matrix | Partially Resolved (Conflicting) |
| ASMP-013 | GCR (ground coverage ratio) | Block (all) | 0.35 | — | Typical single-axis tracker range; site-specific GCR not confirmed | High | Final layout design confirmation | Open |
| ASMP-014 | Inverter MPPT window (lower bound) | Inverter (all) | 950 (Vendor A) / 938 (Vendor B) | V DC | **Resolved 2026-07-24:** SRC-008 MPP 950–1300 V for nominal power (operating to 1500 V); SRC-009 MPP 938–1500 V | Low | Final inverter GTP confirmation | Resolved (Provisional) |
| ASMP-015 | Availability (physics baseline only) | Plant | 1.00 | fraction | Physics baseline — 100% availability is clearly labeled; does not represent operations | Low | Operational availability data | N/A — Labeled |
| ASMP-016 | Module power bin (representative) | PV Module (all) | 645 | Wp | Datasheets cover 620-645 Wp bins (Jinko JKM620-645N-66HL4M-BDV, SRC-006; Jollywood, SRC-007); delivered bin mix not confirmed - top bin used for the representative station. **Corrected 2026-08-04:** an earlier note claimed this implied a ~637 Wp average because plant DC ran +1.3% high. That was wrong - SRC-026/SRC-028 state a **minimum** design capacity ("Facility Minimum Design Capacity", "for rated (min)"), so top-bin modules exceeding it is expected, not a discrepancy | Low | Module BOQ / flash test distribution | Open |
| ASMP-017 | Modules per string | Block (all) | 28 | count | Derived from 1500 V limit with cold-Voc check at site minimum ambient (−3.5 °C, SRC-026 method); formal string-sizing calculation not provided | Medium | Approved string sizing calculation | Open |
| ASMP-018 | SMBs per inverter (Vendor A block) | Block (Vendor A) | 17 | count | Back-calculated from design DC/AC ratio ≈1.096–1.12 at inverter level (SRC-026) with 16 strings/SMB and 28×645 Wp strings | Medium | Final block assignment matrix | Open |
| ASMP-019 | Inverters per IDT (Vendor B block) | Block (Vendor B) | 8 | count | **Corrected 2026-08-04.** Previously 4, on the reasoning that 4 x 1.1 MVA matched a "4.466 MVA IDT". That mistook the **LV winding rating** of the 8.932 MVA dual-winding transformer for a whole transformer, producing a half-size 4.4 MVA station. SRC-026/SRC-028 give 365 MVPS totalling 3228.471 MVA = 8.845 MVA each, so a Vendor B station is 8 x 1.1 MVA (four per LV winding) | Medium | Final block assignment matrix / SLD (DR-002) | Partially Resolved (derived from plant totals) |
| ASMP-020 | Public weather wind-speed height | Site (public data runs) | 10 | m | PVGIS supplies `WS10m` at 10 m; the PVsyst cell-temperature model expects wind at module height. No height correction is applied, which biases cell temperature slightly high at low wind | Medium | On-site anemometer data at module height, or an agreed wind-shear correction | Open |
| ASMP-021 | Public weather grid resolution vs site | Site (public data runs) | ~5–11 | km | PVGIS-SARAH3 satellite and ERA5 grids are coarse relative to a 3,000 MWac footprint; a single grid cell represents the whole modeled block. Queried at exact site coordinates per project-lead decision 2026-08-02 (DAT-004) | Medium | On-site measured weather (GAP-002) or approved TMY (GAP-020) | Open |
| ASMP-023 | Illustrative per-block output spread | Plant (dashboard only) | ±2 | % | Blocks of identical configuration produce identical model output. The pre-commissioning dashboard applies a deterministic spread seeded from the block index, representing module power-bin distribution, layout and orientation differences, so the plant view does not misrepresent a real plant as perfectly uniform. **Illustrative only — not observed or expected variation.** Affects presentation only; never used in energy accounting or reports | Low | Measured per-block production data (Sprint 7) | Open |
| ASMP-022 | Cells in series (electrical) | PV Module (all) | 66 | count | Derived, not invented: datasheets state 132 half-cells (SRC-006, SRC-007) in the standard half-cut topology of two parallel strings of 66 series cells. Confirmed against datasheet Voc — 50.08/66 = 0.759 V and 49.63/66 = 0.752 V per cell, in the expected n-type TOPCon range; 72, 132 and 144 all give physically implausible per-cell voltages. Not currently used by PVWatts; required by any single-diode model (GAP-004) | Low | Vendor confirmation of cell topology, or a PAN file (DR-004) | Open **Corroborated 2026-08-04:** the module part number JKM620-645N-**66**HL4M-BDV encodes 66 cells in series, independently confirming the value derived from Voc |

---

## Resolved Assumptions

| ID | Resolved On | Previous Value | Resolved Value | Source | Notes |
|---|---|---|---|---|---|
| ASMP-003 | 2026-07-24 | 0.70 | 0.80 (±5%) | SRC-006, SRC-007 | Both module vendors state 80% bifaciality; classified Provisional (datasheet, not flash test) |
| ASMP-009 | 2026-07-24 | 0.0 kW | 250 W (A) / 200 W (B) | SRC-008, SRC-009 | Datasheet night-consumption upper bounds |
| ASMP-010 | 2026-07-24 | To be extracted | 4.466 kW no-load; 31.262 kW load @75 °C | SRC-011 | GAP-006 ambiguity resolved by vendor GTP response |
| ASMP-011 | 2026-07-24 | −0.0035 /°C | −0.0029 (A) / −0.00274 (B) /°C | SRC-006, SRC-007 | Per-vendor values; never averaged |
| ASMP-014 | 2026-07-24 | 900 V | 950 V (A) / 938 V (B) | SRC-008, SRC-009 | Vendor A full-power MPP window 950–1300 V |

> Resolved values are **Provisional** (datasheet/GTP grade) — not Confirmed until
> factory/routine test reports or as-built records are received.

---

## Conflict Resolution Rules

When a confirmed value differs from an assumed value by more than 5%:

1. Update the parameter value and provenance record.
2. Re-run the simulation and check for changes in energy yield > 0.5%.
3. Document the change in `CHANGELOG.md`.
4. Update any affected test expected values.

---

*NAJM-3000 Digital Twin | ASSUMPTIONS_REGISTER.md | Revision 1.0*
