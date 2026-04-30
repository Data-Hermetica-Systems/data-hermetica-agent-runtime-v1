# Weight Reconciliation

## Purpose

The weight reconciliation layer compares extracted line-item weights against invoice bottom total weights.

This layer exists because invoice extraction can produce the correct number of line items and still have wrong or incomplete weight normalization.

The goal is not only to extract rows, but to prove whether the extracted line-level weights reconcile to the final invoice totals.

---

## Current Script

```text
src\reconcile-invoice-weight-totals.js
```

Run manually:

```powershell
cd H:\DataHermetica\local-ai-document-core
node src\reconcile-invoice-weight-totals.js
```

This script is also intended to run inside the full pipeline runner before master output generation.

---

## Current Pipeline Placement

Weight reconciliation runs after deterministic and special-family row building and before master output generation:

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

Current runner step:

```text
STEP 5: Reconcile invoice weight totals
```

---

## Inputs

The script reads OCR text files:

```text
ocr\sample-commercial-invoice-001-tesseract-ocr.txt
ocr\sample-commercial-invoice-002-tesseract-ocr.txt
ocr\sample-commercial-invoice-003-tesseract-ocr.txt
```

It also reads deterministic canonical invoice JSON files:

```text
outputs\sample-commercial-invoice-001-deterministic-canonical-lines.json
outputs\sample-commercial-invoice-002-deterministic-canonical-lines.json
outputs\sample-commercial-invoice-003-deterministic-canonical-lines.json
```

---

## Outputs

The script writes per-invoice diagnostics:

```text
outputs\sample-commercial-invoice-001-weight-reconciliation.json
outputs\sample-commercial-invoice-002-weight-reconciliation.json
outputs\sample-commercial-invoice-003-weight-reconciliation.json
```

It also writes a summary:

```text
outputs\weight-reconciliation-summary.json
```

The master builder then carries source validation flags into:

```text
outputs\master-validation-flags.csv
outputs\master-canonical-invoice-lines.json
```

---

## Critical Rules

1. Do not use invoice tare to repair line items.
2. Patch ambiguous European-dot weights only when invoice totals prove the correction.
3. If line-level totals still do not match invoice bottom totals, emit validation flags.
4. Do not silently hide weight inconsistencies.
5. Carry weight validation flags into the master output.
6. Keep extraction success separate from reconciliation truth.
7. Do not invent fake product lines or fake weight rows to force totals.
8. Do not treat `0 parser errors` as equivalent to source truth.

---

## Numeric Interpretation Rules

European decimal comma:

```text
23,580 KG → 23.580 KG
40,056 KG → 40.056 KG
529,920 KG → 529.920 KG
577,500 KG → 577.500 KG
```

European thousands-dot plus decimal-comma:

```text
2.495,934 KG → 2495.934 KG
1.132,560 KG → 1132.560 KG
```

Dot-only values are ambiguous:

```text
2.268 KG
```

Candidate meanings:

```text
2.268 KG
2268.000 KG
```

The system selects `2268.000` only if it makes the invoice bottom total match.

---

## Current Known Reconciliation Behavior

For `sample-commercial-invoice-001`:

```text
Before net sum KG: 1955.264
Invoice total net KG: 4220.996
Line 45 raw net value: 2.268 KG
Corrected line 45 net value: 2268.000 KG
After net sum KG: 4220.996
Net reconciliation: matched_after_candidate_repair
```

This means line 45 `2.268 KG` must be treated as European thousands notation, not decimal notation.

For gross weights in `sample-commercial-invoice-001`:

```text
Invoice total gross KG: 5398.959
After gross sum KG: 4515.109
Gross reconciliation: failed_no_valid_candidate_match
```

The system must flag this instead of pretending the invoice is clean.

For `sample-commercial-invoice-002`:

```text
Invoice total net KG: 1800.4
Invoice total gross KG: 1853.86
Before net sum KG: 600.4
Before gross sum KG: 629.86
After net sum KG: 600.4
After gross sum KG: 629.86
Net reconciliation: failed_no_valid_candidate_match
Gross reconciliation: failed_no_valid_candidate_match
Validation flags now: 2
```

For `sample-commercial-invoice-003`:

```text
Invoice total net KG: 13563.9
Invoice total gross KG: 13745.513
Before net sum KG: 3973.5
Before gross sum KG: 4059.209
After net sum KG: 3973.5
After gross sum KG: 4059.209
Net reconciliation: failed_no_valid_candidate_match
Gross reconciliation: failed_no_valid_candidate_match
Validation flags now: 2
```

---

## Current Verified Reconciliation Summary

Current full pipeline verified:

```text
Weight reconciliation jobs: 3
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
Extraction is structurally successful.
The system correctly reports unresolved invoice weight mismatches.
The master output correctly carries source validation flags forward.
```

---

## Correct System Interpretation

Extraction success:

```text
PDFs
→ OCR
→ canonical rows
→ 58/58 rows extracted
```

Reconciliation truth:

```text
line-item net/gross weights
→ invoice bottom total net/gross weights
→ validation flags if totals do not match
```

These are separate. A pipeline can successfully extract rows and still correctly report reconciliation errors.

---

## Required Master Behavior

The master output must carry source validation flags forward.

It is wrong for the master output to say:

```text
Validation flags: 0
```

if any source invoice JSON contains weight reconciliation flags.

The master output must create:

```text
outputs\master-validation-flags.csv
```

This file should be Excel-readable and show each validation issue with:

```text
sourceFile
sourceParser
invoiceFamily
invoiceNumber
invoiceDate
shipmentNumber
field
row
severity
issue
```

---

## Future Improvements

Future weight-reconciliation improvements:

```text
1. Inspect invoice 001 gross mismatch from original PDF image/table.
2. Investigate invoice 002 missing net/gross source weights.
3. Investigate invoice 003 missing net/gross source weights.
4. Improve OCR/table extraction for page-boundary gross weights.
5. Add expected-value fixtures for invoice bottom totals.
6. Add regression tests for known candidate repairs.
7. Add a human review queue for unresolved weight flags.
8. Add Dataverse Validation Issue rows from master-validation-flags.csv.
```

---

## Production Rule

Do not force bad data to look clean.

Correct production behavior:

```text
If line weights reconcile:
    mark weight reconciliation as passed.

If line weights can be repaired with proven candidate normalization:
    patch the value, record the repair, and mark reconciliation as passed.

If line weights still do not reconcile:
    emit validation flags and route to review.
```