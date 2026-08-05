# scada_integration_plan.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**
> SCADA integration is architecturally defined but **fully inactive**.
> No live addresses, credentials, register maps, or network diagrams
> with restricted details appear in this document.

---

## Status

> ⚠️ **SCADA is not active.** No connection to any live system exists or is
> permitted. This document defines the architecture and interface contracts.

NAJM-3000 SCADA system:
- **Not commissioned.**
- **Not delivering data.**
- **Not connected to this repository.**

### Implementation status (updated 2026-08-02)

| Component | Status |
|---|---|
| Canonical time-series schema | ✅ Implemented — `src/najm3000/scada/canonical.py` |
| `HistorianAdapter` interface | ✅ Implemented — `src/najm3000/scada/adapter_interface.py` |
| `InactiveHistorianAdapter` | ✅ Implemented — raises on every data request |
| Tag mapping + confidentiality guard | ✅ Implemented — `src/najm3000/scada/tag_mapping.py` |
| `SimulatedHistorianAdapter` | ⏳ Sprint 5 — physics engine dressed as telemetry |
| **Real historian adapter** | ❌ Sprint 7 — requires commissioning |

**The swap point.** The pre-commissioning dashboard (Sprints 5–6) reads from a
`HistorianAdapter`, never from the physics engine. At commissioning, the real
adapter is registered in place of `SimulatedHistorianAdapter`; because both
return the canonical schema, the API and dashboard require no change. That
substitution is the deliverable this document exists to protect.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NAJM-3000 SCADA / Historian                  │
│                       (INACTIVE — future)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ Historian adapter (mock during POC)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SCADA Adapter Layer                           │
│  src/najm3000/scada/                                            │
│  • adapter_interface.py  (abstract base class)                  │
│  • mock_adapter.py       (synthetic data for testing)           │
│  • historian_adapter.py  (future — INACTIVE)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Immutable raw records
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Quality-Control Layer                          │
│  src/najm3000/ingestion/                                        │
│  • qc_engine.py                                                 │
│  • data_checks.py                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ Quality-flagged time series
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│             Canonical Time-Series Schema                        │
│  (defined in docs/data_dictionary.md)                           │
│  Fields: timestamp, tag_id, value_raw, value_qc,                │
│          quality_flag, source_classification, unit              │
└───────────────────┬─────────────────────────────────────────────┘
                    │                        │
                    ▼                        ▼
        ┌───────────────────┐    ┌────────────────────────┐
        │  Asset/Tag Map    │    │  Physics Engine        │
        │  tag_mapping.yaml │    │  (independent of SCADA)│
        └───────────────────┘    └────────────────────────┘
                    │                        │
                    └──────────┬─────────────┘
                               ▼
               ┌───────────────────────────────┐
               │  Expected-vs-Actual Module    │
               │  (future — Phase 4+)          │
               └───────────────────────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │  Diagnostics and Reporting    │
               └───────────────────────────────┘
```

---

## Design Principles

1. **Physics independence.** The physics engine has no dependency on the SCADA adapter.
   The physics engine can run without any SCADA connection.
2. **Adapter independence.** The SCADA adapter has no dependency on the physics engine.
3. **Immutable raw records.** All raw SCADA/historian records are stored immutably
   before QC processing.
4. **Canonical schema.** The adapter transforms all SCADA data into the canonical
   time-series schema before any downstream use.
5. **Tag mapping isolation.** SCADA tag-to-asset mapping is defined in YAML
   (`config/tag_mapping.yaml` — not yet created; gitignored if it contains live tags).

---

## SCADA Architecture Reference (Design Concept)

Based on engineering document audit (SRC-001):

- **4-level SCADA architecture** — field devices, RTU/PLC, SCADA server, historian.
- **3-year historian retention** — design concept.
- **19 weather instrumentation stations** — planned, not yet installed.
- Detailed SCADA tag structure — not yet available (GAP-003).

---

## Tag-Mapping Schema (Planned)

```yaml
# config/tag_mapping.example.yaml
# EXAMPLE ONLY — real tags are gitignored
# Tag names are sanitized identifiers only (no live register addresses)

tag_mappings:
  - tag_id: "BLOCK_01_INV_01_PAC"
    description: "Inverter 01, Block 01, AC active power"
    asset_id: "representative_block_01.inverter_01"
    asset_class: "Inverter"
    physical_quantity: "ac_power"
    unit: "kW"
    expected_range: [0, 5000]  # kW — placeholder
    quality_checks:
      - "non_negative"
      - "range_check"
      - "flatline_check"
```

---

## Canonical Time-Series Schema

All data entering the physics comparison layer must conform to this schema:

| Field | Type | Required | Description |
|---|---|---|---|
| `timestamp` | datetime (tz-aware) | ✅ | Timestamp of measurement |
| `tag_id` | string | ✅ | Sanitized SCADA tag identifier |
| `asset_id` | string | ✅ | Asset hierarchy identifier |
| `value_raw` | float | ✅ | Original uncorrected value |
| `value_qc` | float | ✅ | Quality-corrected value (null if no correction) |
| `quality_flag` | string | ✅ | QC result code |
| `source_classification` | string | ✅ | DataSourceClassification enum |
| `unit` | string | ✅ | Physical unit (SI) |
| `sensor_status` | string | ❌ | Sensor health indicator |
| `exclusion_reason` | string | ❌ | Reason excluded from analysis |
| `correction_reason` | string | ❌ | Reason correction applied |
| `processing_version` | string | ✅ | Version of QC pipeline |

---

## Historian Adapter Interface (Planned)

```python
# src/najm3000/scada/adapter_interface.py (planned — not yet implemented)

from abc import ABC, abstractmethod
import pandas as pd

class HistorianAdapter(ABC):
    """Abstract interface for SCADA/historian data adapters."""

    @abstractmethod
    def fetch(
        self,
        tag_ids: list[str],
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        """
        Fetch raw time-series data for the specified tags.
        Returns a DataFrame conforming to the canonical time-series schema.
        No credentials, hostnames, or network addresses in this interface.
        """
        ...

    @abstractmethod
    def list_available_tags(self) -> list[str]:
        """Return sanitized list of available tag IDs."""
        ...
```

---

## Simulated Adapter (Sprint 5)

`SimulatedHistorianAdapter` drives the pre-commissioning dashboard. It runs the
physics chain and expands the result into per-asset canonical rows, so the
dashboard is exercised against the same contract the real historian will honour.

It must:
- Return `source_classification` matching the weather source actually used —
  `SYNTHETIC_SOFTWARE_TEST` or `PROVISIONAL_PUBLIC`. **Never `MEASURED_SITE`.**
- Report `is_active = False`.
- Include quality flags and the disclaimer for the classification in use.
- Never be described, in code, API responses, or the UI, as live, measured, or
  actual plant data.

---

## Security Requirements

The following must **never** appear in any committed file:

- Live SCADA server hostnames or IP addresses.
- SCADA tag register addresses or OPC-UA node IDs.
- Authentication credentials (usernames, passwords, certificates).
- Network topology diagrams showing live infrastructure.

These are stored only in gitignored configuration files managed outside this repository.

---

*NAJM-3000 Digital Twin | docs/scada_integration_plan.md | Revision 1.0*
*SCADA Status: INACTIVE*
