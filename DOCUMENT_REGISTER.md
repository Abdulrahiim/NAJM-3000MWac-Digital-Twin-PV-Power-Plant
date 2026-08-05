# DOCUMENT_REGISTER.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> Source document filenames are confidential and must not appear in this register.
> Use sanitized source IDs and approved document titles only.

---

## Purpose

This register records all engineering documents reviewed during development of the
NAJM-3000 Digital Twin. It provides a full audit trail of information sources without
exposing confidential identifiers or original filenames.

---

## Register

| Source ID | Sanitized Title | Document Class | Format | Revision | Issue Status | Unique | Audit Date | Notes |
|---|---|---|---|---|---|---|---|---|
| SRC-001 | Design Basis – Instrumentation and Control | Engineering Basis | PDF | B | Issued for Review | Yes | 2026-07-21 | 4-level SCADA architecture; 19-station met system; 3-year historian |
| SRC-002 | Design Basis – Electrical | Engineering Basis | PDF | C | Issued for Review | Yes | 2026-07-21 | 33 kV / 660 V transformer interface; MV bus topology |
| SRC-003 | Design Basis – Civil and Structural | Engineering Basis | PDF | B | Issued for Construction | Yes | 2026-07-21 | Site civil/structural basis |
| SRC-004 | Design Basis – Electrical (Supplement) | Engineering Basis | PDF | C | Issued for Review | Yes | 2026-07-21 | Supplementary electrical scope |
| SRC-005 | Earthing Layout | Engineering Drawing | PDF | — | Issued | Yes | 2026-07-21 | Overall earthing layout |
| SRC-006 | PV Module Datasheet – Vendor A | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | Bifacial module; partial dataset; parameters provisional |
| SRC-007 | PV Module Datasheet – Vendor B | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | Bifacial module; partial dataset; parameters provisional |
| SRC-008 | Inverter Datasheet – Vendor A | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | 4.4 MW-class central inverter; detailed dataset |
| SRC-009 | Inverter Datasheet – Vendor B | Equipment Datasheet | PDF | — | — | Yes | 2026-07-24 | Re-audited: detailed datasheet incl. efficiency curve; 1.1 MVA class @52 °C central unit; MPPT 938–1500 V; night draw <200 W |
| SRC-010 | IDT Datasheet – Vendor A (8.932 MVA) | Equipment Datasheet | PDF | C | Issued for Approval | Yes | 2026-07-24 | Re-audited: no-load 0.1% (8.932 kW), load 0.7% (62.524 kW) at 75 °C principal tap; Dy11y11; Uk 9.5%; 60 Hz |
| SRC-011 | IDT Datasheet – Vendor A (4.466 MVA) | Equipment Datasheet | PDF | C | Issued for Approval | Yes | 2026-07-24 | Re-audited: no-load 4.466 kW, load 31.262 kW at 75 °C; Dy11; Uk 8%; ambiguity of GAP-006 resolved (Provisional) |
| SRC-012 | Tracker Datasheet – Vendor A | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | Single-axis 1P; 60° rotation limit; ~1.5 m axis height; full re-audit pending (large file) |
| SRC-013 | SMB Specification – Vendor A | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | 1,500 V DC; specifications available |
| SRC-014 | SMB Specification – Vendor B | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | 1,500 V DC; specifications available |
| SRC-015 | SMB Specification – Vendor C | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | 1,500 V DC; specifications available |
| SRC-016 | MV Switchgear Specification | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | 36 kV class |
| SRC-017 | RMU Specification | Equipment Datasheet | PDF | — | — | Yes | 2026-07-21 | Ring main unit; 36 kV class |
| SRC-018 | SCADA Specification | System Specification | PDF | D | Issued for Review | Yes | 2026-07-21 | 4-level architecture; historian design concept |
| SRC-019 | Main Step-Up Transformer Datasheet | Equipment Datasheet | PDF | 08 | Issued for Approval | Yes | 2026-07-24 | 230 MVA (ONAN/ONAF1/ONAF2 138/181/230); dual 33 kV LV windings; OLTC ±15% in 1.25% steps; 60 Hz; nameplate drawing |
| SRC-020 | STATCOM Specification | System Specification | PDF | A | Issued for Review | Yes | 2026-07-24 | Reactive power compensation at PSS; detailed audit pending (large file) |
| SRC-021 | Tracker Datasheet – Vendor B | Equipment Datasheet | PDF | — | — | Yes | 2026-07-24 | Text-audited: single-axis 1P, tracking range ±60° (±45° option exists); full mechanical extraction pending |
| SRC-022 | Tracker Datasheet – Vendor C | Equipment Datasheet | PDF | — | — | Yes | 2026-07-24 | Text-audited: single-axis 1P, rotational range ±60° (75° hail-stow option); full mechanical extraction pending |
| SRC-023 | Plant Communication Architecture | System Specification | PDF | E | Issued for Review | Yes | 2026-07-24 | Two PSS-variant documents rev E (an earlier rev B copy is superseded); detailed audit pending |
| SRC-024 | Overall Plant Layout Drawing | Engineering Drawing | PDF | B | Issued for Review | Yes | 2026-07-24 | Plant/control layout; detailed audit pending (large file) |
| SRC-025 | Design Basis – I&C (General, PV Plant) | Engineering Basis | PDF | B | Issued for Approval | Yes | 2026-07-24 | Later revision of SRC-001 scope: 19 met stations with full sensor fit-out; 4-level SCADA; 3-yr historian; ~24 fiber rings × ≤16 MVPS |
| SRC-026 | Design Basis – Electrical (General) | Engineering Basis | PDF | C | Issued for Approval | Yes | 2026-07-24 | Later revision of SRC-002 scope: plant summary (365 MVPS, 2 PSS), string sizing method, SMB 16-in-1-out, loss criteria DC ≤1.7% / AC ≤0.5% |
| SRC-027 | PVGIS public weather dataset (EU JRC) | External Dataset | API (JSON) | v5_3 | Public | No — external | 2026-08-02 | **Not a project document.** Radiation database PVGIS-SARAH3 (Meteosat satellite), meteorological database ERA5. Coverage 2005–2023, hourly. Classified PROVISIONAL_PUBLIC; use authorized by the project lead 2026-08-02 (see DAT-004). Attribution to EU JRC required. Not site-measured; does not close GAP-002 or GAP-020 |

> **Note:** 22 additional files inspected during the 2026-07-21 audit were identified
> as exact PDF duplicates of the above sources. Duplicate files are not listed
> separately.
>
> **2026-07-24 re-audit:** A local (uncommitted, gitignored) datasheet folder was
> supplied and audited against this register. Rows SRC-009 through SRC-011 were
> re-audited; SRC-019 through SRC-026 were added. Documents marked "pending" exceed
> current tooling limits and await text extraction.

---

## Document Status Definitions

| Status | Meaning |
|---|---|
| Issued for Review | Under review; parameters provisional |
| Issued for Construction | Approved for construction; parameters may still change |
| Issued for Information | Reference only; not contractually binding |
| Superseded | Replaced by later revision; do not use |
| Draft | Not formally issued |

---

## Parameter Extraction Rules

- Parameters extracted from documents in `Issued for Review` status are classified as
  **Provisional** in the provenance record.
- Parameters extracted from `Issued for Construction` documents may be classified as
  **Confirmed** only if no conflict exists with other sources.
- Conflicting parameters across sources must be recorded in `DATA_GAP_REGISTER.md`
  and classified as **Conflicting** — never silently resolved.
- No parameters may be extracted without assigning the originating Source ID.

---

*NAJM-3000 Digital Twin | DOCUMENT_REGISTER.md | Revision 1.0*


---

## Real Document Codes

> Recorded per the 2026-08-04 confidentiality revision: the project name is the
> only substituted identifier, so real source codes belong here rather than
> being withheld.

| Source ID | Real document code | Title |
|---|---|---|
| SRC-026 | SAU1006-G000-___-&EEC-00003-C | General Design Basis for Electrical |
| SRC-028 | SAU1006-K000-___-&BEC-00001-B | General Design Basis (I&C / plant summary) |

### Confirmed Equipment Vendors (2026-08-04)

Read directly from the datasheet folder and cross-checked against configuration
values, so the `vendor_a` / `vendor_b` configuration keys now have a recorded
real-world identity.

| Config alias | Real vendor and model | Basis for the mapping |
|---|---|---|
| `inverter_vendor_a_model_1` | Sineng EP-4400-HB-UD, 4,400 kW | Datasheet rating matches `paco` 4.4 MW |
| `inverter_vendor_b_model_1` | Sungrow SG1100UD-20, 1,100 kVA | Datasheet rating matches `paco` 1.1 MVA |
| `module_vendor_a_model_1` | Jinko JKM620-645N-66HL4M-BDV | γ_Pmax −0.29 %/°C matches config |
| `module_vendor_b_model_1` | Jollywood (620–645 Wp bifacial) | γ_Pmax −0.274 %/°C matches config |
| `tracker_vendor_a/b/c` | ARCTECH, J Solar, PVH | Three tracker datasheets on file; per-alias mapping not yet confirmed |
| `smb_vendor_a/b/c` | Canbang, LONGMAX, Trinity Touch | Three SMB datasheets on file; per-alias mapping not yet confirmed |

The two MVPS variants are referred to in SRC-026 as the Sineng and Sungrow
stations (MVPS lighting calculations are issued per variant).

Other source IDs retain their sanitized titles in the register above; real codes
may be filled in here as each is re-checked against the source folder.
