# LLM CONTINUATION CONTEXT
# Data Hermetica Private Document Intelligence Pipeline v0.1

## Instruction to the next LLM

You are continuing an active engineering build. Treat this document as the source-of-truth project context. Do not restart from generic advice. Continue from the current implemented state.

Primary objective: help continue building a production-grade private AI document automation system for logistics, customs, commercial, and proforma invoice processing.

Communication style requested by the user:

- Give exact step-by-step build instructions.
- Give full updated code when code changes are requested.
- Avoid vague summaries when implementation detail is needed.
- Use Windows 11 / PowerShell / VS Code instructions.
- Prefer complete file paths and commands.
- Keep continuity with the current project state.
- The user is building this for a portfolio, job transition, and private AI automation business under Data Hermetica.

---

# 1. Project Name

```text
Data Hermetica Private Document Intelligence Pipeline v0.1
```

Alternate descriptive title:

```text
Private AI Document Intelligence Pipeline for Logistics and Customs Invoice Automation
```

Repository/project folder name:

```text
local-ai-document-core
```

Suggested GitHub repo name:

```text
private-document-intelligence-pipeline
```

---

# 2. Project Purpose

This is a local-first/private document automation system for processing logistics, customs, commercial, and proforma invoice PDFs into validated structured data.

The current system converts invoice PDFs into canonical JSON and CSV line-item outputs using:

- Node.js
- Poppler `pdftoppm`
- Tesseract OCR
- Deterministic invoice-family parsers
- OCR item segmentation
- Canonical field normalization
- Validation logic
- Weight-total reconciliation
- Master JSON/CSV output generation
- Master validation flags CSV generation
- Local AI/Qwen experiments through Ollama for fallback extraction

The long-term goal is to evolve this into a production-grade private AI document automation platform that can integrate with:

- Dataverse
- Power Apps
- Power Automate
- UiPath
- RAG/vendor rules
- BGE-M3 embeddings
- Qdrant
- BitNet b1.58 2B4T for lightweight CPU-side rule reasoning
- Qwen2.5-VL for layout/visual ambiguity
- Qwen3-32B-Instruct or another stronger local model for hard fallback correction

---

# 3. Local Project Path

Windows 11 local project path:

```text
H:\DataHermetica\local-ai-document-core
```

Main command to run the complete current pipeline:

```powershell
cd H:\DataHermetica\local-ai-document-core
node src\run-private-document-pipeline.js
```

This command is intended to run the entire working pipeline.

---

# 4. Current Working Pipeline

Current end-to-end workflow:

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

Short form:

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

# 5. Current Benchmark Result

Latest successful extraction + master output state:

```text
Canonical jobs: 5
Invoices processed: 5
Expected canonical rows: 58
Extracted canonical rows: 58
Line amount grand total USD: 343420.71
Master JSON output: created
Master CSV output: created
Master validation flags CSV: created
```

Important update:

```text
The original extraction pipeline can produce 58/58 rows, but the newer weight reconciliation layer found source-level weight validation flags in the Honeywell invoices.

The master output must now carry source validation flags forward. It should not claim total validation flags = 0 if source invoice JSON files contain validation flags.
```

Current known reconciliation status:

```text
sample-commercial-invoice-001:
Net weight reconciled after candidate repair.
Gross weight still does not reconcile to invoice bottom total.

sample-commercial-invoice-002:
Net and gross invoice totals do not reconcile to extracted line-item totals.

sample-commercial-invoice-003:
Net and gross invoice totals do not reconcile to extracted line-item totals.
```

Current expected rigorous behavior:

```text
Extraction success and reconciliation truth are separate.

Extraction success:
PDFs → rows → canonical JSON/CSV

Reconciliation truth:
line-item weights → invoice bottom totals → validation flags if inconsistent
```

---

# 6. Supported Invoice Families

## 6.1 Family 1: Honeywell Multiline Proforma Invoices

Files:

```text
sample-commercial-invoice-001.pdf
sample-commercial-invoice-002.pdf
sample-commercial-invoice-003.pdf
```

Parser method:

```text
Tesseract OCR
→ line-item segmentation
→ deterministic canonical row builder
→ weight-total reconciliation
```

Current extraction results before weight reconciliation:

```text
Invoice 001: 47 expected rows, 47 actual rows
Invoice 002: 2 expected rows, 2 actual rows
Invoice 003: 6 expected rows, 6 actual rows
```

Current reconciliation truth:

```text
Invoice 001: net weight repaired and reconciled; gross still does not reconcile.
Invoice 002: net and gross do not reconcile.
Invoice 003: net and gross do not reconcile.
```

Typical OCR row pattern:

```text
1(R) 10193348 EA 12.000 11.8308 /EA 141.97
R34965 2-Propanol LC-MS CRS = 2,50LFL
34965 2,500 LT GLASS BOTTLE
2-PROPANOL LC-MS CHROMASOLV
Commodity Code: 29051200
Country of Origin: Germany
Delivery Note: 88671853
Shipment:7000383484
Net weight 23,580 KG
Gross weight 40,056 KG
```

Canonical mapping:

```text
LineNo = 1
ProductNumber = 10193348
Unit = EA
Quantity = 12
UnitPriceUSD = 11.8308
LineAmountUSD = 141.97
Description = product description lines
CommodityCode = 29051200
CountryOfOrigin = Germany
DeliveryNote = 88671853
ShipmentNumber = 7000383484
NetWeightKG = 23.580
GrossWeightKG = 40.056
```

---

## 6.2 Family 2: Solstice Customs Invoice ISO Tank Layout

File:

```text
sample-commercial-invoice-004.pdf
```

Parser method:

```text
Special-family deterministic parser
```

Result:

```text
Expected rows: 2
Actual rows: 2
Validation flags: 0
```

Invoice metadata extracted:

```json
{
  "invoiceNumber": "84293441A",
  "invoiceDate": "10.29.2025",
  "customerPo": "H125-509",
  "orderNumber": "2810152",
  "orderDate": "06/25/25",
  "countryOfOrigin": "USA",
  "shippedFrom": "CANTAS KIMYA SANAYI VE TICARET AS",
  "containerNumber": "EURU5354732",
  "totalAmount": 41891
}
```

Correct canonical rows:

```text
Row 1:
ProductNumber = 10305599
Description = T50 ISO TANK
Unit = EA
Quantity = 1
UnitPriceUSD = 40000
LineAmountUSD = 40000
CountryOfOrigin = USA
ShipmentNumber = EURU5354732
OrderNumber = 2810152
NetWeightKG = N/A
GrossWeightKG = N/A

Row 2:
ProductNumber = 10641585
Description = GENETRON 125 ISO TANK BLEND
Unit = KG
Quantity = 305
UnitPriceUSD = 6.20
LineAmountUSD = 1891
CountryOfOrigin = USA
ShipmentNumber = EURU5354732
OrderNumber = 2810152
NetWeightKG = 305
GrossWeightKG = N/A
```

Important interpretation:

```text
The 305 KG in invoice 004 is the residual quantity/mass. It is mapped as both Quantity and NetWeightKG.
```

---

## 6.3 Family 3: Navin India Commercial Invoice KG-Rate Layout

File:

```text
sample-commercial-invoice-005.pdf
```

Parser method:

```text
Special-family deterministic parser
```

Result:

```text
Expected rows: 1
Actual rows: 1
Validation flags: 0
```

Invoice metadata extracted:

```json
{
  "invoiceNumber": "DH2656000189",
  "invoiceDate": "12.09.2025",
  "salesOrderNumber": "10005595",
  "buyerOrderNumber": "4503665993",
  "countryOfOrigin": "INDIA",
  "containerNumber": "EURU5359251",
  "hsnCode": "29037990",
  "vessel": "MAERSK BOSTON / 543W",
  "totalAmount": 95627
}
```

Correct canonical row:

```text
LineNo = 1
ProductNumber = EURU5359251
Description = SOLSTICE LBA ISO 1233ZD FILLED IN ISO TANK HSN.CODE: 29037990 MAERSK BOSTON / 543W
Unit = KG
Quantity = 14380
UnitPriceUSD = 6.65
LineAmountUSD = 95627
CommodityCode = 29037990
CountryOfOrigin = INDIA
DeliveryNote = N/A
ShipmentNumber = EURU5359251
OrderNumber = 4503665993
NetWeightKG = 21820
GrossWeightKG = N/A
```

Important interpretation:

```text
The invoice has both Quantity KG and Nett Wt.
Quantity = 14380
NetWeightKG = 21820
GrossWeightKG = N/A
Do not force gross weight from net weight.
```

---

# 7. Canonical Master Output Schema

The master output columns are:

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

Each invoice line is normalized into this canonical row structure.

---

# 8. Project Folder Structure

Current project structure:

```text
local-ai-document-core
├── README.md
├── PROJECT_CONTEXT.md
├── CHANGELOG.md
├── TODO.md
├── package.json
├── .gitignore
├── pdfs
│   ├── sample-commercial-invoice-001.pdf
│   ├── sample-commercial-invoice-002.pdf
│   ├── sample-commercial-invoice-003.pdf
│   ├── sample-commercial-invoice-004.pdf
│   └── sample-commercial-invoice-005.pdf
├── images
│   └── .gitkeep
├── ocr
│   └── .gitkeep
├── outputs
│   └── .gitkeep
├── prompts
│   └── canonical-invoice-line-extraction-prompt.md
├── docs
│   ├── architecture.md
│   ├── validation-rules.md
│   ├── weight-reconciliation.md
│   └── codex-instructions.md
├── src
│   ├── ocr-pdf-with-tesseract.js
│   ├── segment-ocr-invoice-items.js
│   ├── build-canonical-rows-from-segments.js
│   ├── build-canonical-rows-for-special-families.js
│   ├── reconcile-invoice-weight-totals.js
│   ├── build-master-canonical-output.js
│   ├── extract-canonical-invoice-lines.js
│   ├── extract-canonical-invoice-lines-from-ocr.js
│   └── run-private-document-pipeline.js
├── tests
├── expected
└── samples
```

Generated local runtime files are ignored by Git:

```text
images/*
ocr/*
outputs/*
pdfs/*.pdf
```

except safe placeholders:

```text
images/.gitkeep
ocr/.gitkeep
outputs/.gitkeep
```

---

# 9. Scripts and Their Roles

## 9.1 `src\ocr-pdf-with-tesseract.js`

Purpose:

```text
Converts PDF invoices into PNG page images using Poppler, then runs Tesseract OCR on each page image.
```

Inputs:

```text
pdfs\sample-commercial-invoice-001.pdf
pdfs\sample-commercial-invoice-002.pdf
pdfs\sample-commercial-invoice-003.pdf
pdfs\sample-commercial-invoice-004.pdf
pdfs\sample-commercial-invoice-005.pdf
```

Outputs:

```text
images\sample-commercial-invoice-###\page-#.png
ocr\sample-commercial-invoice-###-tesseract-ocr.txt
ocr\tesseract-ocr-run-summary.json
```

---

## 9.2 `src\segment-ocr-invoice-items.js`

Purpose:

```text
Segments OCR text into invoice item blocks for Honeywell-style multiline proforma invoices.
```

Works strongly for invoices 001, 002, 003.

Outputs:

```text
ocr\sample-commercial-invoice-001-segmented-items.json
ocr\sample-commercial-invoice-002-segmented-items.json
ocr\sample-commercial-invoice-003-segmented-items.json
ocr\sample-commercial-invoice-004-segmented-items.json
ocr\sample-commercial-invoice-005-segmented-items.json
ocr\segmented-items-summary.json
```

Note:

```text
Invoice 004 and 005 intentionally produce itemStartCount = 0 in this segmentation script because they use different layouts and are handled by special-family parsers.
```

---

## 9.3 `src\build-canonical-rows-from-segments.js`

Purpose:

```text
Builds deterministic canonical rows from segmented Honeywell invoice item blocks.
```

Handles:

```text
sample-commercial-invoice-001
sample-commercial-invoice-002
sample-commercial-invoice-003
```

Outputs:

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

## 9.4 `src\build-canonical-rows-for-special-families.js`

Purpose:

```text
Builds canonical rows for invoice families that do not follow the Honeywell multiline item pattern.
```

Handles:

```text
sample-commercial-invoice-004 = Solstice customs invoice ISO tank layout
sample-commercial-invoice-005 = Navin India commercial invoice KG-rate layout
```

Outputs:

```text
outputs\sample-commercial-invoice-004-special-family-canonical-lines.json
outputs\sample-commercial-invoice-004-special-family-canonical-lines.csv
outputs\sample-commercial-invoice-005-special-family-canonical-lines.json
outputs\sample-commercial-invoice-005-special-family-canonical-lines.csv
outputs\special-family-canonical-lines-summary.json
```

---

## 9.5 `src\reconcile-invoice-weight-totals.js`

Purpose:

```text
Compares line-item net/gross weights against invoice bottom total net/gross weights for Honeywell-style invoices.
```

Handles:

```text
sample-commercial-invoice-001
sample-commercial-invoice-002
sample-commercial-invoice-003
```

Core logic:

```text
1. Reads OCR text and deterministic canonical invoice JSON.
2. Extracts invoice bottom total net and gross weights.
3. Extracts raw line-level net/gross weight strings from OCR.
4. Generates numeric candidates for European/US notation.
5. Patches ambiguous European-dot weights only when totals prove the correction.
6. Adds source validation flags if line-level totals do not reconcile with invoice bottom totals.
7. Writes per-invoice weight reconciliation diagnostics.
```

Important numeric examples:

```text
23,580 KG → 23.580 KG
2.495,934 KG → 2495.934 KG
2.268 KG → ambiguous: 2.268 KG or 2268 KG
```

Important rule:

```text
Invoice tare is not used to repair line-item weights.
If line-item net/gross totals do not match invoice bottom totals after valid candidate repair, emit validation flags.
```

Outputs:

```text
outputs\sample-commercial-invoice-001-weight-reconciliation.json
outputs\sample-commercial-invoice-002-weight-reconciliation.json
outputs\sample-commercial-invoice-003-weight-reconciliation.json
outputs\weight-reconciliation-summary.json
```

---

## 9.6 `src\build-master-canonical-output.js`

Purpose:

```text
Combines all individual canonical invoice outputs into one master JSON file and one master CSV file.
Also carries forward validation flags from source invoice JSON files into the master output.
```

Inputs:

```text
outputs\sample-commercial-invoice-001-deterministic-canonical-lines.json
outputs\sample-commercial-invoice-002-deterministic-canonical-lines.json
outputs\sample-commercial-invoice-003-deterministic-canonical-lines.json
outputs\sample-commercial-invoice-004-special-family-canonical-lines.json
outputs\sample-commercial-invoice-005-special-family-canonical-lines.json
```

Outputs:

```text
outputs\master-canonical-invoice-lines.json
outputs\master-canonical-invoice-lines.csv
outputs\master-validation-flags.csv
```

Important rule:

```text
The master output must not report 0 validation flags if source invoice JSON files contain validation flags.
Source validation flags must be carried forward into master-canonical-invoice-lines.json and master-validation-flags.csv.
```

---

## 9.7 `src\run-private-document-pipeline.js`

Purpose:

```text
Main orchestrator script. Runs the entire pipeline in one command.
```

Current intended steps:

```text
STEP 1: OCR PDF invoices with Tesseract
STEP 2: Segment OCR invoice items
STEP 3: Build deterministic canonical rows from segmented Honeywell invoices
STEP 4: Build canonical rows for special invoice families
STEP 5: Reconcile invoice weight totals
STEP 6: Build master canonical JSON and CSV output
```

Main command:

```powershell
cd H:\DataHermetica\local-ai-document-core
node src\run-private-document-pipeline.js
```

Expected output files:

```text
outputs\weight-reconciliation-summary.json
outputs\master-canonical-invoice-lines.json
outputs\master-canonical-invoice-lines.csv
outputs\master-validation-flags.csv
outputs\master-pipeline-run-summary.json
```

---

## 9.8 `src\extract-canonical-invoice-lines.js`

Purpose:

```text
Earlier local AI extraction experiment using Qwen2.5:7B through Ollama.
```

This was used to test local AI extraction against clean and raw invoice text samples.

---

## 9.9 `src\extract-canonical-invoice-lines-from-ocr.js`

Purpose:

```text
Earlier local AI extraction experiment using Qwen2.5:7B against real Tesseract OCR text.
```

Result:

```text
Qwen could extract rows from OCR but whole-document extraction was weaker than deterministic segmentation for known invoice families.
For invoice 001, whole-document Qwen extracted fewer rows than deterministic segmentation.
```

Current philosophy:

```text
Use deterministic parsers for obvious structured fields.
Use AI for ambiguity, repair, layout complexity, and future fallback reasoning.
```

---

# 10. Installed Local Tools

## 10.1 Tesseract OCR

Installed and working.

Version observed:

```text
tesseract v5.5.0.20241111
```

Tessdata path set:

```text
H:\Tesseract-OCR\tessdata
```

Verified language data includes:

```text
eng
```

Test commands:

```powershell
tesseract --version
tesseract --list-langs
```

---

## 10.2 Poppler

Installed and working.

Executable path:

```text
H:\Poppler\poppler-25.12.0\Library\bin\pdftoppm.exe
```

Test command:

```powershell
&H:\Poppler\poppler-25.12.0\Library\bin\pdftoppm.exe -h
```

---

## 10.3 Ollama and Qwen

Ollama installed and working.

Model installed:

```text
qwen2.5:7b
```

Ollama model storage configured to:

```text
H:\OllamaModels
```

API endpoint used by Node:

```text
http://127.0.0.1:11434/api/generate
```

Important note:

```text
If Node fetch fails, start Ollama manually in a second normal PowerShell window:
ollama serve
```

API test:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get
```

---

# 11. Validation Logic

The system validates:

```text
Expected row count
Required columns
Missing product numbers
Missing line numbers
Missing quantities
Missing unit prices
Missing line amounts
Duplicate line numbers
Quantity × UnitPriceUSD vs LineAmountUSD
NetWeightKG greater than GrossWeightKG
Missing fields normalized to N/A
Invoice bottom Total Net weight vs sum(line NetWeightKG)
Invoice bottom Total Gross weight vs sum(line GrossWeightKG)
Source validation flags carried forward into master output
```

Arithmetic tolerance:

```text
absolute tolerance USD = 0.5
relative tolerance percent = 0.0005
allowed tolerance = max(absolute tolerance, relative tolerance)
```

Weight reconciliation rules:

```text
1. Do not use invoice tare to repair line items.
2. Patch ambiguous European-dot weights only when invoice totals prove the correction.
3. If line-level net/gross totals still do not match invoice bottom totals, emit validation flags.
4. Master output must carry source validation flags forward.
5. Master output must create outputs\master-validation-flags.csv.
```

---

# 12. Number Normalization

Examples:

```text
23,580 KG → 23.580
1.132,560 KG → 1132.560
2.495,934 KG → 2495.934
2.268 KG → ambiguous: 2.268 or 2268.000
12.000 → 12
$40,000.00 → 40000
12,781.95 → 12781.95
```

Missing values are normalized to:

```text
N/A
```

---

# 13. Current Portfolio Summary

Project title:

```text
Private AI Document Intelligence Pipeline for Logistics and Customs Invoice Automation
```

Portfolio summary:

```text
Built a local-first invoice document intelligence pipeline that extracts structured line-item data from logistics/customs PDFs into canonical JSON and CSV. The system processes 5 sample invoices across 3 invoice families, extracts 58/58 expected rows, and adds weight-total reconciliation to flag source inconsistencies between line-item net/gross weights and invoice bottom totals.
```

Resume summary:

```text
Built a local private document intelligence pipeline for logistics and customs invoices using Node.js, Poppler, Tesseract OCR, deterministic segmentation, invoice-family-specific parsers, canonical JSON/CSV generation, and validation logic. The pipeline processes multiple invoice formats locally, generates Excel-ready master outputs, and carries source validation flags forward through a master validation report.
```

Strong resume bullet:

```text
Built a local-first invoice automation pipeline that processed 5 logistics/customs PDF invoices across 3 invoice families into 58 canonical line items, generating per-invoice and master JSON/CSV outputs with row-count validation, arithmetic checks, field normalization, and invoice-level weight reconciliation.
```

---

# 14. Current README Status

A `README.md` file was created in the project root:

```text
H:\DataHermetica\local-ai-document-core\README.md
```

Windows initially created it as:

```text
README.md.txt
```

It was corrected using PowerShell:

```powershell
Rename-Item -Path "README.md.txt" -NewName "README.md"
```

Markdown preview in VS Code:

```text
Ctrl + Shift + V
```

---

# 15. Current Strategic Build Philosophy

Correct philosophy:

```text
Use rules where fields are obvious.
Use AI where layout, wording, or ambiguity breaks rules.
Validate everything deterministically.
```

Do not rely on one giant LLM prompt for all invoice extraction.

Correct production approach:

```text
PDF
→ local rendering
→ OCR
→ layout/family detection
→ deterministic parsers where possible
→ AI fallback where rules fail
→ validation always
→ reconciliation always
→ human review for unresolved exceptions
```

---

# 16. Long-Term Target Architecture

Future intended architecture:

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

---

# 17. BitNet and RAG Placement

BitNet fits, but not as the primary extraction engine.

Correct role:

```text
CPU micro-reasoner
rule interpretation
exception triage
field alias mapping
low-risk mapping suggestions
audit explanations
RAG query expansion
```

Bad role for BitNet:

```text
main invoice extraction
visual layout reasoning
final schema enforcement
arithmetic validation
ground-truth evaluation
```

RAG placement:

```text
RAG is before the AI model when the AI needs business rules or vendor-specific context.
RAG retrieves relevant rules, then gives those rules to BitNet or Qwen.
```

Correct flow:

```text
Validation flags
→ RAG retrieves vendor/document-family rules
→ BitNet interprets retrieved rules cheaply on CPU
→ deterministic code accepts/rejects mapping suggestions
→ Qwen/VL only handles harder ambiguity
```

---

# 18. Recommended Next Build Steps

## Immediate next build option A: Runner integration

Ensure `src\run-private-document-pipeline.js` includes the weight reconciliation step before master output generation.

The full runner should check for:

```text
outputs\weight-reconciliation-summary.json
outputs\master-validation-flags.csv
```

## Immediate next build option B: README polish and screenshots

Create portfolio-ready evidence:

```text
Terminal screenshot of successful full pipeline run
Master CSV screenshot in Excel
Master validation flags CSV screenshot
VS Code project structure screenshot
Example input invoice screenshot
Example JSON output screenshot
Architecture diagram
```

## Immediate next build option C: Dataverse schema

Create Power Platform extension:

```text
Invoice Batch table
Invoice Line table
Validation Issue table
Processing Run table
Vendor Rule table
Review Action table
```

Goal:

```text
Import master-canonical-invoice-lines.csv and master-validation-flags.csv into Dataverse and build a model-driven review console.
```

## Immediate next build option D: Power Automate exception workflow

Build:

```text
When extraction run completes
→ check validation flags
→ if 0 flags mark ready for export
→ if flags exist create review task
→ notify reviewer
→ update Dataverse status
```

Recommended next project layer:

```text
Power Platform Review Console over the extracted invoice rows and validation flags
```

This should use Dataverse + model-driven app + Power Automate.

---

# 19. Planned Power Platform Tables

## 19.1 Invoice Batch

Fields:

```text
Batch ID
Invoice Number
Invoice Date
Source File
Invoice Family
Source Parser
Shipment Number
Total Line Amount USD
Row Count
Validation Flag Count
Processing Status
Created On
Processed On
```

## 19.2 Invoice Line

Fields:

```text
Invoice Batch lookup
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
ShipmentNumber
OrderNumber
NetWeightKG
GrossWeightKG
ReviewStatus
```

## 19.3 Validation Issue

Fields:

```text
Invoice Batch lookup
Invoice Line lookup
Field
Issue
Severity
Resolved
Resolution Note
```

## 19.4 Processing Run

Fields:

```text
Run ID
Pipeline Version
Started At
Finished At
DurationMs
PDF Job Count
Canonical Job Count
Expected Rows
Extracted Rows
Validation Flags
Status
```

## 19.5 Vendor Rule

Fields:

```text
Vendor Name
Invoice Family
Field Target
Rule Type
Rule Text
Priority
Effective Date
Active
```

## 19.6 Review Action

Fields:

```text
Invoice Batch lookup
Invoice Line lookup
Action Type
Previous Value
New Value
Reviewer
Review Timestamp
Review Note
```

---

# 20. Main Commands

Run full pipeline:

```powershell
cd H:\DataHermetica\local-ai-document-core
node src\run-private-document-pipeline.js
```

Run only OCR:

```powershell
node src\ocr-pdf-with-tesseract.js
```

Run only segmentation:

```powershell
node src\segment-ocr-invoice-items.js
```

Run only Honeywell canonical builder:

```powershell
node src\build-canonical-rows-from-segments.js
```

Run only special-family canonical builder:

```powershell
node src\build-canonical-rows-for-special-families.js
```

Run only weight reconciliation:

```powershell
node src\reconcile-invoice-weight-totals.js
```

Run only master output builder:

```powershell
node src\build-master-canonical-output.js
```

Open README in VS Code:

```powershell
code README.md
```

Preview Markdown in VS Code:

```text
Ctrl + Shift + V
```

---

# 21. Known Current Behavior

Poppler may print syntax warnings such as:

```text
Syntax Error: No display font for 'Symbol'
Syntax Error: No display font for 'ArialUnicode'
Bad FCHECK in flate stream
```

These warnings did not prevent successful rendering/OCR/extraction.

Invoices 004 and 005 show `itemStartCount = 0` in the generic segmentation summary. That is expected because they are not handled by the Honeywell item segmenter. They are handled by the special-family parser.

Current known reconciliation flags are expected until missing/misread source weights are investigated and repaired.

---

# 22. Current State Summary

The current system is working, but validation is now more rigorous.

It has a one-command runner:

```powershell
node src\run-private-document-pipeline.js
```

It produces:

```text
outputs\master-canonical-invoice-lines.json
outputs\master-canonical-invoice-lines.csv
outputs\master-validation-flags.csv
outputs\master-pipeline-run-summary.json
outputs\weight-reconciliation-summary.json
```

Current extraction metrics:

```text
5 PDFs
3 invoice families
58 expected rows
58 extracted rows
343420.71 USD grand total
```

Current reconciliation truth:

```text
Weight reconciliation can produce validation flags when line-item net/gross weights do not reconcile to invoice bottom totals.
The master output must carry those source validation flags forward.
```

The next best engineering step:

```text
Make sure src\run-private-document-pipeline.js includes the weight reconciliation step before master output generation.
```

The next best portfolio/business layer:

```text
Power Platform extension using Dataverse, Power Apps, and Power Automate.
```

---

# 23. Ultra-Short One-Line Context for New Chat

```text
I am building Data Hermetica Private Document Intelligence Pipeline v0.1, a local Node.js/Poppler/Tesseract invoice automation system at H:\DataHermetica\local-ai-document-core that processes 5 logistics/customs invoice PDFs across 3 invoice families into 58 canonical invoice rows, runs weight-total reconciliation against invoice bottom totals, carries source validation flags into master outputs, and produces master JSON/CSV plus master-validation-flags.csv. Main command: node src\run-private-document-pipeline.js. Next goal: ensure reconciliation is integrated into the full runner, then build the Power Platform layer with Dataverse tables, Power Apps review console, and Power Automate approval/exception flow.
```