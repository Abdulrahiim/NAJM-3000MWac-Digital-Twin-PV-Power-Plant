# security_and_data_handling.md — NAJM-3000 Digital Twin

> **Classification: RESTRICTED — Internal Use Only**

---

## Overview

This document defines the security and data-handling requirements for the
NAJM-3000 Digital Twin repository and all associated workflows.

---

## Repository Security

### Access Control

- This repository contains proprietary engineering intellectual property.
- Access must be restricted to authorized personnel only.
- Repository must not be made public or shared externally without written approval.
- All collaborators must have read and agreed to `CONFIDENTIALITY.md`.

### Git History

- If confidential content is accidentally committed, it must be removed from
  Git history using `git filter-repo` (not `git rm`) before the repository
  is shared externally.
- Do not use `git push --force` to overwrite history on shared branches without
  notifying all collaborators.

---

## Credential Management

### Prohibited

- **Never** commit credentials, passwords, API keys, or tokens.
- **Never** commit SCADA server hostnames, IP addresses, or network details.
- **Never** commit database connection strings.

### Required Practice

- Use environment variables for all runtime credentials.
- Use a secrets manager (e.g., Azure Key Vault, AWS Secrets Manager, or
  equivalent) for production deployments.
- Rotate credentials immediately if any credential is accidentally committed.
- Use `.env` files locally (excluded by `.gitignore`).

---

## Confidential Data Handling

### Engineering Documents

- Raw engineering documents (PDFs, DWGs, DOCXs) are **never committed**.
- They are excluded by `.gitignore`.
- They must be stored securely outside this repository.
- Source IDs (`SRC-001`, `SRC-002`, …) are used instead of original filenames.

### Site Coordinates

- Site coordinates (latitude, longitude) are **confidential**.
- They must only appear in gitignored `config/project.yaml`.
- They must never appear in committed files, logs, or artifacts.

### SCADA Data

- No live SCADA data, historian exports, or operational data may be committed.
- All SCADA data is stored in `data/raw/` (gitignored).

---

## Data Classification and Labeling

All data must carry a `source_classification` label:

| Label | Storage | Commitment |
|---|---|---|
| `MEASURED_SITE` | `data/raw/` | Never committed |
| `OFFICIAL_TMY` | `data/raw/` | Never committed |
| `PROVISIONAL_PUBLIC` | `data/public/` | Committed with label |
| `SYNTHETIC_SOFTWARE_TEST` | `data/public/synthetic/` | Committed with label |

---

## Output Security

- Model outputs may contain derived information about site parameters.
- Outputs committed to the repository must not contain site coordinates,
  confidential equipment serial numbers, or SCADA tag addresses.
- Reports intended for external sharing must be reviewed for confidentiality
  before distribution.

---

## Incident Response

If a confidentiality violation is detected:

1. Immediately notify the project lead.
2. Do not push the affected commits to any remote.
3. Remove the confidential content from Git history using `git filter-repo`.
4. Review all recent commits for similar violations.
5. Document the incident (without reproducing the violated content).

---

*NAJM-3000 Digital Twin | docs/security_and_data_handling.md | Revision 1.0*
