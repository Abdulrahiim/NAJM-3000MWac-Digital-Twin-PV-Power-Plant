# CONFIDENTIALITY POLICY — NAJM-3000 Digital Twin

**Classification: RESTRICTED — Internal Project Use Only**

---

## 1. Scope

This policy governs all agents, contributors, and automated tools operating within the
NAJM-3000 Digital Twin repository.

---

## 2. Approved Project Identity

The only approved project identifier for all files, comments, logs, outputs, and
artifacts is:

> **NAJM-3000**

---

## 3. Prohibited Disclosures

> **Revised 2026-08-04 by the project lead.** The previous policy sanitized site
> name, coordinates, vendor names, and document codes throughout. That made
> engineering work harder to follow without materially protecting a repository
> that is local-only. **The project name is now the sole substituted identifier.**

Only the following must **never** appear in any committed file, log, output,
artifact, agent response, or intermediate document:

| Category | Examples |
|---|---|
| Real project names | Any name other than NAJM-3000 |
| Network credentials | Passwords, API keys, private keys, tokens |
| Live network addresses | Production IPs, SCADA hostnames, live register maps |

Everything else may be recorded with its real value, including:

- Real site name, location, and coordinates
- Equipment vendor and model names
- Source document codes and reference numbers
- Plant capacity, layout, and configuration figures
- Owner, EPC, and off-taker names

Real values are preferred over placeholders: an engineering register that says
"Vendor A" where the vendor is known is harder to audit, not safer.

### Condition attached to this revision

This relaxation assumes the repository stays **local, with no git remote**. Before
adding a remote, publishing, or sharing the repository outside this machine,
re-read §8 — the content now inside it is genuinely confidential.

Verify with `git remote -v` (currently empty).

---

## 4. Source-Document Handling

Raw engineering documents must **never** be committed to Git.

The raw-document exclusion is unchanged: PDFs, DWGs, spreadsheets and similar
stay out of Git (enforced by `.gitignore`). Their *contents* may be recorded.

When referencing source content:

1. Substitute the project name with **NAJM-3000**. Nothing else needs substituting.
2. Keep assigning source IDs (`SRC-001`, `SRC-002`, …) — not for secrecy, but
   because a stable short ID is easier to cite in registers than a long filename.
   Record the real document code alongside the ID in `DOCUMENT_REGISTER.md`.
3. Real vendor and model names may be used directly. The `Vendor A` / `Vendor B`
   aliases remain valid as *configuration keys* where they are already embedded
   in `config/` and code, so renaming them is a cosmetic change, not a
   confidentiality requirement.
4. Never commit credentials, private keys, or live network addresses.

---

## 5. Vendor Anonymization

Use **Vendor A**, **Vendor B**, **Vendor C** unless a manufacturer model must be
retained to distinguish equipment behavior and is approved for **internal engineering
use only**.

---

## 6. Data Classification

| Label | Meaning |
|---|---|
| `MEASURED_SITE` | Measured data from the project site |
| `OFFICIAL_TMY` | Approved satellite or climate TMY dataset |
| `PROVISIONAL_PUBLIC` | Publicly available data not formally approved for NAJM-3000 |
| `SYNTHETIC_SOFTWARE_TEST` | Synthetic data for software verification only |

Data labeled `SYNTHETIC_SOFTWARE_TEST` must carry this warning wherever results are
presented:

> **SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION**

---

## 7. Agent and Contributor Obligations

All agents and contributors must:

- Read CONFIDENTIALITY.md before operating on this repository.
- Report suspected confidentiality violations immediately.
- Refuse to generate content that would violate this policy.
- Apply this policy retroactively to any intermediate artifacts before committing.

---

## 8. Enforcement

Files violating this policy must be removed from Git history using `git filter-repo`
or equivalent before the repository is shared externally.

---

*This document is part of the NAJM-3000 Digital Twin governance foundation.*
*Revision: 1.0 | Status: ACTIVE*
