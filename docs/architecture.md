# Architecture

## System Name

```text
Data Hermetica Private Document Intelligence Pipeline v0.2
```

## Purpose

This project is a local-first private document intelligence pipeline for logistics, customs, commercial, and proforma invoice automation.

The system converts invoice PDFs into validated canonical invoice-line outputs using local OCR, deterministic parsers, invoice-family-specific extraction, validation, and weight-total reconciliation.

The system is designed as the local/private core of a future Power Platform automation layer.

---

## Current End-to-End Workflow

```text
PDF invoices
→ Poppler page rendering
→ Tesseract OCR
→ OCR text output
→ invoice-family recognition
→ item segmentation
→ header metadata extraction
→ deterministic canonical row building
→ special-family parsing
→ field normalization
→ validation
→ weight-total reconciliation
→ individual JSON output
→ individual CSV output
→ master JSON output
→ master CSV output
→ master validation flags CSV
→ master pipeline summary
```

Short version:

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

## Current Script Flow

```text
src/ocr-pdf-with-tesseract.js
→ src/segment-ocr-invoice-items.js
→ src/build-canonical-rows-from-segments.js
→ src/build-canonical-rows-for-special-families.js
→ src/reconcile-invoice-weight-totals.js
→ src/build-master-canonical-output.js
→ src/run-private-document-pipeline.js
```

---

## Main Runner

Main command:

```powershell
cd H:\DataHermetica\local-ai-document-core
node src\run-private-document-pipeline.js
```

Current intended runner steps:

```text
STEP 1: OCR PDF invoices with Tesseract
STEP 2: Segment OCR invoice items
STEP 3: Build deterministic canonical rows from segmented Honeywell invoices
STEP 4: Build canonical rows for special invoice families
STEP 5: Reconcile invoice weight totals
STEP 6: Build master canonical JSON and CSV output
```

---

## Current Input Layer

Current source documents are local PDF invoices stored in:

```text
pdfs\
```

Current sample PDF names:

```text
sample-commercial-invoice-001.pdf
sample-commercial-invoice-002.pdf
sample-commercial-invoice-003.pdf
sample-commercial-invoice-004.pdf
sample-commercial-invoice-005.pdf
```

The `pdfs` folder is ignored by Git because it may contain private source documents.

---

## PDF Rendering Layer

Script:

```text
src/ocr-pdf-with-tesseract.js
```

Rendering tool:

```text
Poppler pdftoppm
```

Local Poppler path:

```text
H:\Poppler\poppler-25.12.0\Library\bin\pdftoppm.exe
```

Purpose:

```text
Convert each PDF page into page images that Tesseract can OCR.
```

Generated output folder:

```text
images\
```

Example generated image path pattern:

```text
images\sample-commercial-invoice-001\page-01.png
```

The `images` folder is ignored by Git except for `.gitkeep`.

---

## OCR Layer

Script:

```text
src/ocr-pdf-with-tesseract.js
```

OCR tool:

```text
Tesseract OCR
```

Installed version observed:

```text
tesseract v5.5.0.20241111
```

Tessdata path:

```text
H:\Tesseract-OCR\tessdata
```

Generated output folder:

```text
ocr\
```

Example generated OCR output:

```text
ocr\sample-commercial-invoice-001-tesseract-ocr.txt
ocr\sample-commercial-invoice-002-tesseract-ocr.txt
ocr\sample-commercial-invoice-003-tesseract-ocr.txt
ocr\sample-commercial-invoice-004-tesseract-ocr.txt
ocr\sample-commercial-invoice-005-tesseract-ocr.txt
ocr\tesseract-ocr-run-summary.json
```

The `ocr` folder is ignored by Git except for `.gitkeep`.

---

## Segmentation Layer

Script:

```text
src/segment-ocr-invoice-items.js
```

Purpose:

```text
Split OCR text into invoice item blocks for Honeywell-style multiline proforma invoices.
```

Works strongly for:

```text
sample-commercial-invoice-001
sample-commercial-invoice-002
sample-commercial-invoice-003
```

Expected behavior for special-family invoices:

```text
sample-commercial-invoice-004 itemStartCount = 0
sample-commercial-invoice-005 itemStartCount = 0
```

That is expected because invoices 004 and 005 do not follow the Honeywell multiline item format. They are handled by the special-family parser.

Generated outputs:

```text
ocr\sample-commercial-invoice-001-segmented-items.json
ocr\sample-commercial-invoice-002-segmented-items.json
ocr\sample-commercial-invoice-003-segmented-items.json
ocr\sample-commercial-invoice-004-segmented-items.json
ocr\sample-commercial-invoice-005-segmented-items.json
ocr\segmented-items-summary.json
```

---

## Deterministic Canonical Row Builder

Script:

```text
src/build-canonical-rows-from-segments.js
```

Purpose:

```text
Build canonical invoice line rows from segmented Honeywell-style invoice item blocks.
```

Handles:

```text
sample-commercial-invoice-001
sample-commercial-invoice-002
sample-commercial-invoice-003
```

Generated outputs:

```text
outputs\sample-commercial-invoice-001-deterministic-canonical-lines.json
outputs\sample-commercial-invoice-001-deterministic-canonical-lines.csv
outputs\sample-commercial-invoice-002-deterministic-canonical-lines.json
outputs\sample-commercial-invoice-002-deterministic-canonical-lines.csv
outputs\sample-commercial-invoice-003-deterministic-canonical-lines.json
outputs\sample-commercial-invoice-003-deterministic-canonical-lines.csv
outputs\deterministic-canonical-lines-summary.json
```

---

## Special-Family Parser Layer

Script:

```text
src/build-canonical-rows-for-special-families.js
```

Purpose:

```text
Build canonical rows for invoice families that do not follow the Honeywell multiline item pattern.
```

Currently handles:

```text
sample-commercial-invoice-004 = solstice_customs_invoice_iso_tank
sample-commercial-invoice-005 = navin_india_commercial_invoice_kg_rate
```

Generated outputs:

```text
outputs\sample-commercial-invoice-004-special-family-canonical-lines.json
outputs\sample-commercial-invoice-004-special-family-canonical-lines.csv
outputs\sample-commercial-invoice-005-special-family-canonical-lines.json
outputs\sample-commercial-invoice-005-special-family-canonical-lines.csv
outputs\special-family-canonical-lines-summary.json
```

---

## Weight Reconciliation Layer

Script:

```text
src/reconcile-invoice-weight-totals.js
```

Purpose:

```text
Compare line-item net/gross weights against invoice bottom total net/gross weights.
```

Currently handles Honeywell-style invoices:

```text
sample-commercial-invoice-001
sample-commercial-invoice-002
sample-commercial-invoice-003
```

Core behavior:

```text
1. Read OCR text.
2. Read deterministic canonical invoice JSON.
3. Extract invoice bottom total net and gross weights.
4. Extract raw line-level net/gross weight strings.
5. Generate numeric candidates for European/US number formats.
6. Patch ambiguous European-dot weights only when invoice totals prove the correction.
7. Emit validation flags when line-level totals do not reconcile to invoice bottom totals.
8. Write diagnostics.
```

Generated outputs:

```text
outputs\sample-commercial-invoice-001-weight-reconciliation.json
outputs\sample-commercial-invoice-002-weight-reconciliation.json
outputs\sample-commercial-invoice-003-weight-reconciliation.json
outputs\weight-reconciliation-summary.json
```

---

## Master Output Builder

Script:

```text
src/build-master-canonical-output.js
```

Purpose:

```text
Combine all individual canonical invoice outputs into master JSON and CSV files.
Carry forward source validation flags from individual invoice JSON files.
Generate an Excel-readable master validation flags CSV.
```

Generated outputs:

```text
outputs\master-canonical-invoice-lines.json
outputs\master-canonical-invoice-lines.csv
outputs\master-validation-flags.csv
```

---

## Master Pipeline Summary

Generated by:

```text
src/run-private-document-pipeline.js
```

Output:

```text
outputs\master-pipeline-run-summary.json
```

Purpose:

```text
Summarize the entire run, including steps, runtime, row counts, validation flags, reconciliation summary existence, and master output existence.
```

---

## Current Verified Runtime Metrics

Latest verified run showed:

```text
Pipeline status: completed
Version: v0.2
Runtime: about 53 seconds
Canonical jobs: 5
Weight reconciliation jobs: 3
Expected rows: 58
Extracted rows: 58
Line amount grand total USD: 343420.71
Net weight grand total KG: 9099.896
Gross weight grand total KG: 9204.178
Source validation flags: 5
Master validation flags: 0
Total validation flags: 5
Has validation errors: true
All row counts matched: true
All validation clear: false
Weight reconciliation summary created: true
Master validation flags CSV created: true
```

Interpretation:

```text
Extraction succeeded.
Row counts matched.
The system correctly carried forward source validation flags.
Validation is not fully clear because invoice weight reconciliation found source-level mismatches.
```

---

## Current Canonical Schema

Master columns:

```text
SourceInvoiceFile
SourceParser
InvoiceNumber
InvoiceDate
ShipmentNumber
InvoiceFamily
LineNo
ProductNumber
Description
Unit
Quantity
UnitPriceUSD
LineAmountUSD
CommodityCode
CountryOfOrigin
DeliveryNote
OrderNumber
NetWeightKG
GrossWeightKG
```

---

## Current Output Set

Important generated outputs:

```text
outputs\master-canonical-invoice-lines.json
outputs\master-canonical-invoice-lines.csv
outputs\master-validation-flags.csv
outputs\master-pipeline-run-summary.json
outputs\weight-reconciliation-summary.json
```

Generated files are not committed to Git.

---

## Git/GitHub Architecture

Local project path:

```text
H:\DataHermetica\local-ai-document-core
```

Private GitHub repo:

```text
https://github.com/Data-Hermetica-Systems/private-document-intelligence-pipeline
```

Branch:

```text
main
```

Tracked safe files include:

```text
README.md
PROJECT_CONTEXT.md
CHANGELOG.md
TODO.md
docs\
src\
expected\
samples\
prompts\
package.json
.gitignore
images\.gitkeep
ocr\.gitkeep
outputs\.gitkeep
```

Ignored/private/generated files include:

```text
pdfs/*.pdf
images/*
ocr/*
outputs/*
*.before-weight-reconciliation
node_modules/
.env
```

---

## Future Target Architecture

```text
PDF / Image / Email
→ Poppler page rendering
→ Tesseract OCR baseline
→ PaddleOCR PP-StructureV3 layout/table extraction
→ invoice-family detection
→ deterministic segmentation
→ canonical row building
→ validation
→ weight-total reconciliation
→ BGE-M3 embeddings retrieve vendor rules from Qdrant
→ BitNet b1.58 2B4T handles rule reasoning and exception triage
→ Qwen2.5:7B handles text fallback repair
→ Qwen2.5-VL handles visual/layout ambiguity
→ Qwen3-32B-Instruct handles hard fallback correction
→ final schema enforcement
→ JSON output
→ CSV output
→ Dataverse
→ Power Automate approval flow
→ Power Apps exception review
→ ERP/customs/finance integration
```