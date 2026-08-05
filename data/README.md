# data/ — NAJM-3000 Digital Twin Data Handling Policy

> **Classification: RESTRICTED — Internal Use Only**
> See `CONFIDENTIALITY.md` and `DATA_REGISTER.md` for the complete data governance framework.

---

## ⚠️ Critical Data Handling Rules

1. **Raw data is immutable.** Never modify, rename, or delete raw data files.
2. **Raw engineering documents are never committed to Git.** They are excluded by `.gitignore`.
3. **No data source may be silently replaced.** Changes must be documented in `DATA_REGISTER.md`.
4. **Do not silently delete or correct values.** Preserve raw, corrected, flag, reason, and method.
5. **Synthetic data must be labeled** with `SYNTHETIC_SOFTWARE_TEST` and the disclaimer
   `SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION` in all outputs.
6. **No measured weather currently exists.** Do not substitute any other data as measured.
7. **Do not download public weather** (PVGIS, NSRDB, ERA5, etc.) without explicit written approval.

---

## Directory Structure

```
data/
├── README.md           ← This file
├── raw/                ← Immutable source data (gitignored)
├── interim/            ← Reproducible intermediate products (selectively committed)
├── processed/          ← Provenance-tagged model outputs (selectively committed)
└── public/             ← Separately classified public or synthetic data
    └── synthetic/      ← Synthetic software-test data (committed with labels)
```

---

## Directory Definitions

### `raw/`

Immutable source data. **Never modify.** Entirely gitignored.

Intended for (when available):
- Measured site weather time series from on-site stations.
- SCADA historian exports.
- Official approved TMY datasets.

**Current status: No measured data exists.** The `raw/` directory is empty.

### `interim/`

Reproducible intermediate data products derived from `raw/`. Committed only when
sanitized (no confidential identifiers). Every interim file must be reproducible
from the raw input using a versioned script.

Naming convention: `{data_id}_{processing_version}_{YYYY-MM-DD}.parquet`

### `processed/`

Final provenance-tagged model outputs in Parquet format. Each file contains:
- `najm3000_version` metadata tag
- `data_source_classification` tag
- `simulation_date` tag
- `block_id` tag
- `weather_source_id` tag
- `model_stage` tag

Committed only when sanitized and appropriately labeled.

### `public/`

Separately classified public or synthetic data. All files in this directory must
carry explicit source classification labels.

- `public/synthetic/` — Synthetic software-test data. All files carry the label
  `SYNTHETIC_SOFTWARE_TEST` and the disclaimer `SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION`.

---

## Data Quality Preservation

All QC processing preserves original values. The following fields are mandatory:

| Field | Description |
|---|---|
| `value_raw` | Original uncorrected measurement |
| `value_corrected` | Corrected value (null if uncorrected) |
| `quality_flag` | QC result code |
| `exclusion_reason` | Reason for excluding from analysis (null if included) |
| `correction_reason` | Reason a correction was applied (null if uncorrected) |
| `correction_method` | Method used (null if uncorrected) |
| `processing_version` | Version of the processing pipeline |

---

## Data Registration

All data inputs must be registered in `DATA_REGISTER.md` before use in the model.
Unregistered data inputs will be rejected by the ingestion pipeline.

---

*NAJM-3000 Digital Twin | data/README.md | Revision 1.0*
