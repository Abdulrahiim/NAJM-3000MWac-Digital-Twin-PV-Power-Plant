# DATA_GAP_REGISTER.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> This register records all missing, incomplete, or conflicting engineering data
> that must be resolved before the Digital Twin can progress to each phase.

---

## Gap Priority Levels

| Priority | Meaning |
|---|---|
| P1 — Critical | Blocks Sprint 1 or current phase from proceeding |
| P2 — High | Required before Sprint 2/3; model will use assumption |
| P3 — Medium | Required for full validation; acceptable placeholder for POC |
| P4 — Low | Enhancement; does not block any sprint |

---

## Gap Status

| Status | Meaning |
|---|---|
| Open | Gap not resolved |
| Partially Resolved | Some data available; gap remains |
| Resolved | Confirmed data available; source ID assigned |

---

## Register

| Gap ID | Parameter Category | Asset Class | Description | Source IDs Consulted | Priority | Status | Blocking Phase | Notes |
|---|---|---|---|---|---|---|---|---|
| GAP-001 | Final block assignment matrix | Plant | Design basis now gives plant totals (365 MVPS, 2 PSS, DC/AC 1.096 inverter-level / 1.180 POI, ~3,540 MWp) but no per-block vendor assignment or tracker layout | SRC-026, SRC-025 | P2 | Partially Resolved | Plant scaling | Per-block vendor mix still missing; see also GAP-019 (count conflict) |
| GAP-002 | Measured weather time series | Site | No on-site pyranometer or meteorological station data available. 19-station met system fully specified (SRC-025) but not yet installed or operational | SRC-025, SRC-027 | P1 | Open | All phases | **Unchanged by the 2026-08-02 PVGIS authorization.** Public satellite data (SRC-027, PROVISIONAL_PUBLIC) now exercises the chain with real weather, but it is not site-measured and cannot calibrate or validate the model. See GAP-020 for TMY |
| GAP-003 | SCADA tag dictionary | SCADA | No operational SCADA tag dictionary or register has been provided | SRC-001 | P1 | Open | Commissioning phase | Architecture documented; tags not available |
| GAP-004 | PV module STC parameters (CEC/SAPM-compatible) | PV Module (all) | Full STC tables per power bin (Pmax/Vmp/Imp/Voc/Isc) and temperature coefficients available for both vendors. **Feasibility tested 2026-08-02** (see note) — single-diode fit still unavailable | SRC-006, SRC-007 | P3 | Partially Resolved | DC model upgrade (post-POC) | `cells_in_series` is **no longer a blocker** (derived = 66, ASMP-022). `pvlib.ivtools.sdm.fit_desoto` fails to converge from datasheet STC values across four initial guesses (overflow in `expm1`). Remaining routes: NREL-PySAM `fit_cec_sam` (new dependency), vendor PAN files (DR-004), or flash-test IV curves. PVWatts remains fully parameterized |
| GAP-005 | Inverter efficiency curve (Vendor B) | Inverter (Vendor B) | Re-audit: Vendor B datasheet includes efficiency curves (max 99.0%, Euro 98.7%) as graphs; digitized curve points not yet extracted | SRC-009 | P3 | Partially Resolved | Sprint 2 (inverter model) | PVWatts uses nominal efficiency; curve digitization optional |
| GAP-006 | IDT no-load loss (4.466 MVA variant) | IDT (Vendor A) | Resolved: vendor GTP states no-load 0.1% (4.466 kW) and load 0.7% (31.262 kW) at 75 °C, principal tap | SRC-011 | — | Resolved | — | Values Provisional until routine test reports |
| GAP-007 | Bifaciality factor (module-specific) | PV Module (all) | Resolved: both vendors state 80% ±5% bifaciality | SRC-006, SRC-007 | — | Resolved | — | ASMP-003 updated to 0.80 (Provisional) |
| GAP-008 | Ground albedo (site-specific) | Site | No on-site albedo measurements or confirmed albedo specification | — | P2 | Open | Sprint 3 (bifacial model) | Using ASMP-005 provisional range |
| GAP-009 | GCR and inter-row spacing (all block types) | Block / Tracker | Final layout with confirmed GCR values per block area not available | SRC-012 | P2 | Open | Sprint 1 (tracker), Sprint 3 (bifacial) | ASMP-013 used; high risk |
| GAP-010 | Tracker specification (Vendor B and Vendor C) | Tracker | Text extraction performed 2026-07-24: all three vendors confirm ±60° tracking range, single-axis 1P; GCR capability range 25–60% (Vendor A doc). Axis height and site GCR/pitch still not stated per block area | SRC-012, SRC-021, SRC-022 | P3 | Partially Resolved | Sprint 3 (bifacial geometry) | ASMP-001 resolved; ASMP-002 (axis height) and ASMP-013 (GCR) remain Assumed |
| GAP-011 | Module rear-side IAM (incidence angle modifier) | PV Module (all) | Rear IAM data not present in available datasheets | SRC-006, SRC-007 | P3 | Open | Sprint 3 (bifacial model) | pvlib default rear IAM used |
| GAP-012 | Inverter temperature derating curve | Inverter (all) | Discrete rating points now available — Vendor A: 5280 kVA@27 °C / 4463 kVA@50 °C / 4400 kVA@52 °C; Vendor B: 1320 kVA@23 °C / 1100 kVA@52 °C. Continuous curve not provided | SRC-008, SRC-009 | P3 | Partially Resolved | Sprint 2 (inverter model) | POC clips at the design-ambient (50–52 °C) rating — conservative |
| GAP-013 | Soiling model parameters | Site | No cleaning schedule, soiling rate measurement, or regional dust data available | — | P3 | Open | Sprint 3 (soiling model) | ASMP-006 used; model flagged as assumed |
| GAP-014 | DC and AC cable specifications | Block (all) | Cable lengths, cross-sections, and material specifications not available from audited documents | — | P3 | Open | Sprint 3 (electrical losses) | Design allowance from ASMP-007/ASMP-008 |
| GAP-015 | String arrangement per block (modules per string, strings per SMB) | Block (all) | Strings per SMB confirmed as 16 (all three SMB vendors + electrical design basis: 16-in-1-out at 1,500 V). Modules per string still not documented — string-sizing methodology given but final calculation not provided | SRC-013, SRC-014, SRC-015, SRC-026 | P2 | Partially Resolved | Sprint 1 (block config) | strings_per_smb = 16 (Provisional); modules_per_string via ASMP-017 (28, Assumed) |
| GAP-016 | Inverter MPPT window (Vendor B) | Inverter (Vendor B) | Resolved: MPP range 938–1500 V; min PV voltage 938 V, startup 950 V | SRC-009 | — | Resolved | — | ASMP-014 updated |
| GAP-017 | Operational alarm and fault history | Plant | Does not exist — SCADA not commissioned | — | P4 | Open | Operational phase | Not needed for POC |
| GAP-018 | Performance ratio baseline | Plant | Does not exist — requires measured production data | — | P4 | Open | Commissioning phase | Not needed for POC |
| GAP-019 | MVPS count conflict | Plant | Design basis states 365 MVPS; IDT GTP BOQ lists 286+2 units | SRC-010, SRC-011, SRC-026, SRC-028 | P2 | **Resolved 2026-08-04** | Plant scaling | **365 is authoritative for plant totals**: 365 x 8.845 MVA = 3228.5 MVA and 365 x 9.699 MWp = 3540.1 MWp, both matching the stated plant figures exactly. The 286+2 BOQ figure cannot reconcile with either total and is presumed a partial or phased scope. Configuration corrected from 286 to 365; a conformance test now asserts plant totals against the design basis |
| GAP-020 | Official TMY dataset | Site | The electrical/I&C design bases state an owner-provided TMY is the required basis for performance estimation, but the TMY file has not been supplied to this repository and is not approved for Digital Twin use | SRC-025, SRC-026 | P2 | Open | Design benchmarking (validation phase 3) | Request logged as DR-001; POC continues on SYNTHETIC_SOFTWARE_TEST |
| GAP-021 | Transmission line count discrepancy | Plant | Electrical design basis rev C states 8 transmission lines; the later I&C design basis rev B states 15 | SRC-025, SRC-026 | P4 | Open — Conflicting | None (outside POC physics scope) | Recorded for completeness; does not affect block modeling |

---

## Data Requests Log

| Request ID | Gap ID | Requested From | Date Raised | Date Required | Status |
|---|---|---|---|---|---|
| DR-001 | GAP-020 | Project stakeholders (owner OTS annex) | 2026-07-24 | Before design-benchmark validation | Drafted — awaiting formal issue |
| DR-002 | GAP-001, GAP-015, GAP-019 | EPC engineering (final configuration / block matrix / string sizing calc) | 2026-07-24 | Before plant-level scaling is quoted | Drafted — awaiting formal issue |
| DR-003 | GAP-009, GAP-010 | EPC engineering (tracker layout: GCR, pitch, axis height per block area) | 2026-07-24 | Before Sprint 3 bifacial runs | Drafted — awaiting formal issue |
| DR-004 | GAP-004, GAP-005 | Module and inverter vendors (PAN/OND files, or digitized efficiency curve points and flash-test IV data) | 2026-08-02 | Before any CEC/PVsyst DC model or curve-based inverter model | Drafted — awaiting formal issue |

---

*NAJM-3000 Digital Twin | DATA_GAP_REGISTER.md | Revision 1.0*
