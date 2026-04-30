# Validation Rules

## Purpose

Validation proves whether extracted invoice data is structurally complete, mathematically consistent, and reconcilable against invoice-level totals.

The pipeline must not treat successful extraction as proof of source accuracy.

The current design separates:

```text
Extraction success
+
Reconciliation truth
=
production-grade output confidence
```

---

## Core Row Validation

The system validates:

```text
Expected row count
Required canonical columns
Missing product numbers
Missing line numbers
Missing quantities
Missing unit prices
Missing line amounts
Duplicate line numbers
Quantity × UnitPriceUSD versus LineAmountUSD
NetWeightKG greater than GrossWeightKG
Missing fields normalized to N/A
```

---

## Expected Row Count Validation

Each parser job has an expected row count.

Current expected row counts:

```text
sample-commercial-invoice-001: 47
sample-commercial-invoice-002: 2
sample-commercial-invoice-003: 6
sample-commercial-invoice-004: 2
sample-commercial-invoice-005: 1
```

Total expected canonical rows:

```text
58
```

The system should flag if actual extracted rows do not equal expected rows.

---

## Required Canonical Columns

Master canonical columns:

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

Every master row should contain every required canonical column.

---

## Missing Field Policy

Missing values must be represented as:

```text
N/A
```

Do not use:

```text
null
undefined
empty string
```

for finalized canonical outputs unless a future schema explicitly allows it.

---

## Line Amount Arithmetic Validation

For invoice line amount checks:

```text
expected line amount = Quantity × UnitPriceUSD
```

The comparison uses tolerance because vendor invoices can use internal precision or rounded unit prices.

Current tolerance:

```text
absolute tolerance USD = 0.5
relative tolerance percent = 0.0005
allowed tolerance = max(absolute tolerance, relative tolerance)
```

Reason:

```text
Invoices with large quantities and 4-decimal unit prices can have small differences due to vendor rounding or hidden internal precision.
```

Example:

```text
Quantity = 6000
UnitPriceUSD = 11.4355
Quantity × UnitPriceUSD = 68613.00
Vendor amount = 68612.76
Difference = 0.24
This is within absolute tolerance.
```

---

## Weight Total Validation

If invoice bottom total net/gross weights exist:

```text
sum(line NetWeightKG) must match invoice Total Net weight
sum(line GrossWeightKG) must match invoice Total Gross weight
```

If totals do not match after valid candidate repairs, the system must emit validation flags.

---

## Weight Reconciliation Rules

1. Do not use invoice tare to repair line items.
2. Do not invent fake line weights to force totals.
3. Patch ambiguous European-dot weights only when invoice totals prove the correction.
4. If line-level net/gross totals still do not match invoice bottom totals, emit validation flags.
5. Master output must carry source validation flags forward.
6. Master output must create `outputs\master-validation-flags.csv`.
7. Extraction success and reconciliation truth are separate.
8. A pipeline run can be structurally successful while still producing validation flags.

---

## Number Normalization Examples

European decimal comma:

```text
23,580 KG → 23.580
40,056 KG → 40.056
529,920 KG → 529.920
```

European thousands-dot plus decimal-comma:

```text
1.132,560 KG → 1132.560
2.495,934 KG → 2495.934
```

Dot-only values are ambiguous:

```text
2.268 KG → 2.268 or 2268.000
```

Dot-only values should be patched to thousands interpretation only when invoice totals prove it.

Other examples:

```text
12.000 → 12
$40,000.00 → 40000
12,781.95 → 12781.95
```

---

## Source Validation Carry Forward

The master output must carry source validation flags forward.

The master output cannot report:

```text
Validation flags: 0
```

if any source invoice JSON contains validation flags.

Source validation flags should appear in:

```text
outputs\master-canonical-invoice-lines.json
outputs\master-validation-flags.csv
```

The master output should separately report:

```text
Master validation flags
Source validation flags carried forward
Total validation flags
```

Current verified behavior:

```text
Master validation flags: 0
Source validation flags carried forward: 5
Total validation flags: 5
```

---

## Current Known Validation Status

The extraction pipeline can currently produce:

```text
5 invoices
3 invoice families
58 expected rows
58 extracted rows
343420.71 USD line amount grand total
```

The reconciliation layer can currently produce source validation flags for Honeywell invoice weights when line-item net/gross totals do not match invoice bottom totals.

This is expected and correct behavior.

---

## Current Known Weight Reconciliation Flags

Known current reconciliation behavior:

```text
sample-commercial-invoice-001:
Net weight reconciled after candidate repair.
Gross weight still does not reconcile to invoice bottom total.

sample-commercial-invoice-002:
Net and gross invoice totals do not reconcile to extracted line-item totals.

sample-commercial-invoice-003:
Net and gross invoice totals do not reconcile to extracted line-item totals.
```

Current total source validation flags:

```text
5
```

---

## Severity Model

Suggested current severity model:

```text
error:
- row count mismatch
- missing required product number
- missing required line number
- invoice bottom total net/gross mismatch after candidate repairs
- source validation flags carried forward from reconciliation

warning:
- line amount within questionable but tolerated rounding range
- missing optional fields
- OCR artifact in description
- invoice family detected but some non-critical metadata missing

info:
- expected special-family segmentation itemStartCount = 0
- Poppler font warnings that do not block extraction
```

---

## Production Rule

A production-ready output is not merely:

```text
rows extracted successfully
```

A production-ready output should also report:

```text
row counts matched
line amounts validated
required fields present
weight totals reconciled or explicitly flagged
source validation flags carried forward
human review queue populated for unresolved flags
```