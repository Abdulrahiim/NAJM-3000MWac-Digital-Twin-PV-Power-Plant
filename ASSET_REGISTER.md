# ASSET_REGISTER.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> Asset identifiers and quantities in this register are provisional, based on audited
> engineering documents. They are subject to change as final as-built data becomes
> available.

---

## Important Caveats

- **Equipment not confirmed as installed.** Entries are based on datasheets and design
  documents, not as-built records.
- **Block count and assignment matrix are not finalized.** See GAP-001.
- **Multiple vendor configurations are possible for the same asset class.**
- **Do not average across vendor variants** unless explicitly running a sensitivity
  scenario.

---

## Plant Level

| Parameter | Value | Unit | Status | Source ID | Notes |
|---|---|---|---|---|---|
| Plant rated capacity (AC, POI) | 3,000 | MWac | Provisional | SRC-026 | @50 °C; maximum export cap at POI |
| Plant DC capacity (minimum design) | ~3,540 | MWp | Provisional | SRC-026 | Minor discrepancy between sources (3,540.003 vs 3,540.055) |
| DC/AC ratio (inverter level / POI) | 1.096 / 1.180 | — | Provisional | SRC-026 | POI figure is a stated minimum |
| Grid frequency | 60 | Hz | Provisional | SRC-019, SRC-026 | Consistent across design basis, IDT, RMU, main transformer |
| System voltage (MV) | 33 | kV | Provisional | SRC-002 | 36 kV equipment class |
| DC bus voltage | 1,500 | V | Provisional | SRC-013 | SMB and string system voltage |
| MV power stations (MVPS) | 365 | count | Conflicting | SRC-025, SRC-026 | Conflicts with IDT BOQ of 288 units — see GAP-019 |
| Pooling substations (PSS) | 2 | count | Provisional | SRC-026 | Evacuation at HV via multiple transmission lines (count conflicting — GAP-021) |
| Site altitude | ~1,100 | m a.s.l. | Provisional | SRC-026 | Design maximum elevation |
| Design ambient temperature | 50 | °C | Provisional | SRC-026 | Outdoor equipment design basis; site extremes −3.5 to 46.2 °C (shade) |
| Weather stations (planned) | 19 | count | Provisional | SRC-025 | Full sensor fit-out specified; not yet installed |
| SCADA architecture | 4-level | — | Provisional | SRC-025 | Levels 0–3; ~24 fiber rings, ≤16 MVPS per ring |
| Historian retention | 3 | years | Provisional | SRC-025 | Design concept |

---

## PV Modules

| Alias | Vendor | Technology | Configuration | STC Power | Bifacial | Status | Source ID |
|---|---|---|---|---|---|---|---|
| module_vendor_a_model_1 | Vendor A | n-type TOPCon bifacial dual-glass | 132 half-cells, 2382×1134×30 mm | 620–645 Wp bins; γ_Pmax −0.29%/°C; bifaciality 80±5% | Yes | Provisional | SRC-006 |
| module_vendor_b_model_1 | Vendor B | n-type TOPCon bifacial dual-glass | 132 half-cells, 2382×1134×30 mm | 620–645 Wp bins; γ_Pmax −0.274%/°C; bifaciality 80±5% | Yes | Provisional | SRC-007 |

> Parameter detail available in `config/equipment.example.yaml` (placeholder values).

---

## Inverters

| Alias | Vendor | Rating | Type | Detailed Data | Status | Source ID |
|---|---|---|---|---|---|---|
| inverter_vendor_a_model_1 | Vendor A | 4,400 kW @52 °C (5,280 kVA @27 °C); 660 V; MPP 950–1300 V; ηmax 99.02% / Euro 98.8%; night <250 W | Central | Yes (GTP) | Provisional | SRC-008 |
| inverter_vendor_b_model_1 | Vendor B | 1,100 kVA @52 °C (1,320 kVA @23 °C); 660 V; MPP 938–1500 V; ηmax 99.0% / Euro 98.7%; night <200 W | Central (modular) | Yes (re-audited) | Provisional | SRC-009 |

---

## Inverter Duty Transformers (IDT)

| Alias | Vendor | Rated Power | HV Voltage | LV Voltage | Status | Source ID |
|---|---|---|---|---|---|---|
| idt_vendor_a_8_932_mva | Vendor A | 8.932 MVA @50 °C; no-load 8.932 kW; load 62.524 kW @75 °C; Dy11y11 (2 LV windings); Uk 9.5%; ONAN | 33 kV | 2 × 660 V | Provisional | SRC-010 |
| idt_vendor_a_4_466_mva | Vendor A | 4.466 MVA @50 °C; no-load 4.466 kW; load 31.262 kW @75 °C; Dy11 (1 LV winding); Uk 8%; ONAN | 33 kV | 660 V | Provisional (GAP-006 resolved) | SRC-011 |

---

## Main Step-Up Transformers (PSS)

| Asset | Rating | Voltages | Vector Group | Cooling | Status | Source ID |
|---|---|---|---|---|---|---|
| Main step-up transformer | 230 MVA (ONAN/ONAF1/ONAF2: 138/181/230) | HV with OLTC ±15% in 1.25% steps / 2 × 33 kV LV (115 MVA each) | YN,d11-d11 | ONAN/ONAF | Provisional | SRC-019 |

---

## Trackers

| Alias | Vendor | Type | Axis Orientation | Max Rotation | Axis Height | Status | Source ID |
|---|---|---|---|---|---|---|---|
| tracker_vendor_a_model_1 | Vendor A | Single-axis, 1-in-portrait | N–S (configurable) | 60° | ~1.5 m | Provisional | SRC-012 |
| tracker_vendor_b_model_1 | Vendor B | Single-axis, 1-in-portrait | TBD | TBD | TBD | Datasheet received — extraction pending (GAP-010) | SRC-021 |
| tracker_vendor_c_model_1 | Vendor C | Single-axis, 1-in-portrait | TBD | TBD | TBD | Datasheet received — extraction pending (GAP-010) | SRC-022 |

---

## String Monitoring Boxes (SMB)

| Alias | Vendor | System Voltage | String Inputs | Status | Source ID |
|---|---|---|---|---|---|
| smb_vendor_a_model_1 | Vendor A | 1,500 V DC | 16 in / 1 out; ≤18.1 A per string; 400 A output LBS | Provisional | SRC-013 |
| smb_vendor_b_model_1 | Vendor B | 1,500 V DC | 16 in / 1 out; ≤17.28 A per string; 400 A DC switch | Provisional | SRC-014 |
| smb_vendor_c_model_1 | Vendor C | 1,500 V DC | 16 in / 1 out; 30 A gPV string fuses; 400 A main switch | Provisional | SRC-015 |

---

## MV Switchgear and RMU

| Asset | Voltage Class | Status | Source ID |
|---|---|---|---|
| MV Switchgear | 36 kV | Provisional | SRC-016 |
| RMU | 36 kV | Provisional | SRC-017 |

---

## Block Register

> ⚠️ **Final block assignment matrix not available (GAP-001).**
> This section will be populated when the block assignment document is received.

| Block ID | Area | Module Vendor | Inverter Vendor | IDT Variant | Tracker Vendor | SMB Vendor | Status |
|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | Not finalized |

---

## Weather Stations

> ⚠️ **19 stations planned but not yet installed or operational.**
> Geographic zone assignments to be defined when station layouts are confirmed.

| Station ID | Zone | Instruments | Status |
|---|---|---|---|
| WS-001 to WS-019 | TBD | Per SRC-025: 1× Class A GHI pyranometer, 2× Class A POA, 3× Class C rear-side, Class A albedometer, DHI sensor, ambient T, RH, wind speed/direction, rain gauge, 3× module temperature, conventional + front/rear optical soiling systems, datalogger (6-month storage) | Planned — not installed |

---

*NAJM-3000 Digital Twin | ASSET_REGISTER.md | Revision 1.0*
*All values provisional — not confirmed as installed equipment*
