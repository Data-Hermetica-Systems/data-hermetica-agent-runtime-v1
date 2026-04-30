# Codex Instructions for Data Hermetica Private Document Intelligence Pipeline

## Always Read First

Before modifying code, read:

1. `README.md`
2. `PROJECT_CONTEXT.md`
3. `docs/architecture.md`
4. `docs/validation-rules.md`
5. `docs/weight-reconciliation.md`
6. `package.json`
7. `src/run-private-document-pipeline.js`
8. `src/reconcile-invoice-weight-totals.js`
9. `src/build-master-canonical-output.js`

---

## Project Purpose

This project is a local-first private document intelligence pipeline for logistics, customs, commercial, and proforma invoice PDFs.

The pipeline converts PDFs into validated canonical invoice line rows using:

```text
Poppler PDF page rendering
Tesseract OCR
Node.js orchestration
invoice-family-specific parsers
deterministic validation
weight-total reconciliation
master JSON/CSV output generation
master validation flags CSV generation
```

---

## Local Project Path

```text
H:\DataHermetica\local-ai-document-core
```

---

## Private GitHub Repository

```text
https://github.com/Data-Hermetica-Systems/private-document-intelligence-pipeline
```

---

## Main Command

```powershell
cd H:\DataHermetica\local-ai-document-core
node src\run-private-document-pipeline.js
```

---

## Current Intended Pipeline Order

```text
PDFs
→ OCR
→ segmentation
→ Honeywell canonical rows
→ special-family canonical rows
→ weight-total reconciliation
→ master JSON/CSV output
→ master validation flags CSV
→ master pipeline summary
```

---

## Current Intended Runner Steps

```text
STEP 1: OCR PDF invoices with Tesseract
STEP 2: Segment OCR invoice items
STEP 3: Build deterministic canonical rows from segmented Honeywell invoices
STEP 4: Build canonical rows for special invoice families
STEP 5: Reconcile invoice weight totals
STEP 6: Build master canonical JSON and CSV output
```

---

## Critical Design Rules

1. Do not rely on one giant LLM prompt for extraction.
2. Use deterministic parsing for known invoice-family fields.
3. Use AI only for ambiguity, fallback repair, or future RAG-assisted reasoning.
4. Always validate row counts, line amounts, required fields, and weights.
5. Missing fields must be represented as `N/A`.
6. Do not use invoice tare to repair line items.
7. Do not invent fake weights to force totals.
8. If line-item weights do not reconcile to invoice bottom totals, emit validation flags.
9. Do not silently hide source validation flags in master output.
10. Preserve existing outputs unless explicitly changing the schema.
11. Always provide full updated code files, not partial snippets.
12. Keep extraction success separate from reconciliation truth.
13. Never use `git add .` unless `.gitignore` has been verified and the staged file list is reviewed.
14. Do not commit private PDFs, generated OCR, generated images, generated outputs, or local backups.

---

## Supported Invoice Families

1. Honeywell multiline proforma invoice
2. Solstice customs ISO tank invoice
3. Navin India commercial invoice KG-rate layout

---

## Current Benchmark

Extraction layer:

```text
5 invoice PDFs
3 invoice families
58 canonical line rows
master CSV and JSON output
343420.71 USD line amount grand total
```

Reconciliation layer:

```text
source validation flags may exist after weight reconciliation
source validation flags must be carried forward into master output
master-validation-flags.csv must be generated
```

Verified current full-run behavior:

```text
Pipeline status: completed
Version: v0.2
Canonical jobs: 5
Weight reconciliation jobs: 3
Expected rows: 58
Rows extracted: 58
Source validation flags: 5
Master validation flags: 0
Total validation flags: 5
Has validation errors: true
All row counts matched: true
All validation clear: false
```

---

## Important Source Files

```text
src/ocr-pdf-with-tesseract.js
src/segment-ocr-invoice-items.js
src/build-canonical-rows-from-segments.js
src/build-canonical-rows-for-special-families.js
src/reconcile-invoice-weight-totals.js
src/build-master-canonical-output.js
src/run-private-document-pipeline.js
```

---

## Important Documentation Files

```text
README.md
PROJECT_CONTEXT.md
CHANGELOG.md
TODO.md
docs/architecture.md
docs/validation-rules.md
docs/weight-reconciliation.md
docs/codex-instructions.md
```

---

## Important Output Files

Generated locally, ignored by Git:

```text
outputs/weight-reconciliation-summary.json
outputs/master-canonical-invoice-lines.json
outputs/master-canonical-invoice-lines.csv
outputs/master-validation-flags.csv
outputs/master-pipeline-run-summary.json
```

---

## Do Not Commit

Do not commit private PDFs, OCR text, generated images, generated outputs, or backups unless they are sanitized samples.

Do not commit:

```text
pdfs/*.pdf
images/*
ocr/*
outputs/*
*.before-weight-reconciliation
node_modules/
.env
```

Only keep safe placeholders:

```text
images/.gitkeep
ocr/.gitkeep
outputs/.gitkeep
```

---

## Safe Commit Pattern

Before committing, run:

```powershell
git status
git ls-files
git status --ignored
```

Safe staging pattern:

```powershell
git add README.md PROJECT_CONTEXT.md CHANGELOG.md TODO.md docs src package.json .gitignore
```

Then inspect:

```powershell
git status
```

Only commit after confirming no private PDFs, OCR files, output files, or rendered images are staged.

---

## Current Next Engineering Task

The full runner has been updated to include weight reconciliation.

Next likely engineering tasks:

```text
1. Update README with v0.2 verified pipeline results.
2. Add screenshots for portfolio.
3. Add Dataverse schema documentation.
4. Add expected-value fixtures for weight reconciliation.
5. Investigate unresolved gross/net reconciliation flags for invoices 001, 002, and 003.
```

---

## Power Platform Direction

The next major project layer is a Dataverse and Power Platform review system.

The local pipeline produces:

```text
outputs\master-canonical-invoice-lines.csv
outputs\master-validation-flags.csv
```

These should feed:

```text
Invoice Batch
Invoice Line
Validation Issue
Processing Run
Vendor Rule
Review Action
```

Then Power Automate should route flagged batches to human review.

---

## Response Requirements for Codex/LLM

When asked for code changes:

```text
Provide the full updated file.
Do not provide fragments unless explicitly requested.
Do not remove existing working behavior unless necessary.
Preserve path compatibility for Windows 11 PowerShell.
Use CommonJS style unless the project is intentionally migrated.
Keep generated outputs ignored.
Update docs if behavior changes.
```