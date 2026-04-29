# Data Hermetica Private Document Intelligence Pipeline v0.1

A local-first private document processing system for extracting structured line-item data from logistics, customs, commercial, and proforma invoice PDFs.

The system converts invoice PDFs into validated canonical JSON and CSV outputs using local PDF rendering, OCR, invoice-family recognition, item segmentation, deterministic parsing, field normalization, and validation.

---

## Current Status

Working end-to-end.

Current benchmark run:

| Metric | Result |
|---|---:|
| PDF invoices processed | 5 |
| Invoice families supported | 3 |
| Expected canonical rows | 58 |
| Extracted canonical rows | 58 |
| Validation flags | 0 |
| Row counts matched | true |
| Master JSON output | created |
| Master CSV output | created |
| Runtime | about 53 seconds |

---

## Supported Invoice Families

| Invoice Family | Description | Parser Type |
|---|---|---|
| Honeywell multiline proforma invoice | Multi-page invoice with repeated line items, material numbers, quantities, unit prices, amounts, commodity codes, origin, delivery notes, shipment numbers, order numbers, and weights | OCR segmentation + deterministic canonical row builder |
| Solstice customs invoice ISO tank layout | Customs-value invoice with ISO tank customs value and residual contained material | Special-family deterministic parser |
| Navin India commercial invoice KG-rate layout | India export commercial invoice with container number, KG quantity, USD/KG rate, HSN code, origin, vessel, and total amount | Special-family deterministic parser |

---

## Pipeline Overview

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
→ individual JSON output
→ individual CSV output
→ master JSON output
→ master CSV output
→ master pipeline summary