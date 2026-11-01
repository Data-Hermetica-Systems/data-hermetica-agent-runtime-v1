# Data Hermetica Customs Entry Automation Engine

This repository contains the local-model-first Data Hermetica invoice engine and its plan to prepare U.S. customs entries. The active invoice engine uses Microsoft Power Automate email intake, OneDrive sync, a Windows Python supervisor, Poppler for PDF text extraction/page rendering, and LM Studio local vision-language inference to extract highly variable invoice layouts into validated JSON/CSV. The local vision-language model is the primary extraction mechanism for highly variable invoice layouts; deterministic code performs bounded normalization and validation, not invoice parsing. The system does **not** yet classify HTS codes, determine PGA/OGA requirements, or populate CBP Forms 7501/3461.

## Current state

The release's reference deployment is user-confirmed to process multiple invoices, including image-bearing PDFs. It has structural and unit-price tests. Field accuracy remains supplier- and field-dependent and requires ground-truth review. The packaged PowerShell installation wrappers have not been accepted on the reference Windows machine. The Power Automate flow export is not included.

The tested extraction baseline is in `app/`, `config/`, `deployment/`, and `tests/`. See `docs/Release-Status.md` and `docs/Architecture.md` for evidence and limitations. The model reads page text and rendered images directly; the runtime does not run Tesseract or another OCR engine. Do not interpret a valid schema or matching row count as proof that values are correct.

## Target workflow

1. **Receive and preserve source documents**: Outlook + Power Automate cloud flow; save original attachments to OneDrive Incoming, sync to the Windows workstation, hash and track each source.
2. **Extract invoice and trade evidence locally**: Python 3.12, Poppler, LM Studio local inference (reference model alias `qwen/qwen3.8-27b`; verify exact model, quantization and hash on the target PC). Produce normalized invoice lines and retain source/page evidence.
3. **Join shipment evidence**: add bills of lading, packing lists and other entry documents; reconcile quantities, values, weights, parties, origin and transport data deterministically, with exceptions for human review.
4. **Match HTS and PGA/OGA requirements**: integrate the separately maintained authoritative, versioned dataset when supplied. Until then, use only the explicit placeholder contract in `data/reference/README.md`; never invent tariff codes or agency flags. Candidate matching must return evidence, dataset version and confidence/review state.
5. **Prepare CBP Forms 3461 and 7501**: map only verified source fields and reviewed classifications to form fields, validate totals and cross-form consistency, create draft outputs, and require qualified human review. Automated filing/transmission is out of scope until separately authorized and validated.
6. **Measure accuracy and operate**: compare every required field to labeled examples and official form rules; retain audit trail, release/version provenance, review outcomes and acceptance evidence.

See [Customs Entry Roadmap](docs/Customs-Entry-Roadmap.md) for software, PowerShell steps, local models, tests and Qdrant decision by phase.

## Develop and test

On Windows PowerShell with Python 3.12 and Poppler available on PATH:

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
```

No cloud model API is required for the unit tests. The invoice pipeline itself needs a running LM Studio OpenAI-compatible local server and a compatible local model. See `docs/Prerequisites.md` and `docs/Acceptance-and-Operations.md` before installing or running against real invoices.

## Project boundaries

- Keep inference local through LM Studio on the Windows workstation. Power Automate moves documents; it does not send their contents to an AI service.
- Use deterministic validation and human approval for legal/customs decisions.
- The HTS/PGA/OGA source data is an external dependency being developed separately. Placeholder data is not suitable for production matching.
- Qdrant is optional and not part of the working baseline. Consider it only for semantic candidate retrieval over approved product/classification references after the dataset exists; keep authoritative exact/rule lookups and final review outside vector similarity.
- Preserve existing source documents and generated evidence. Do not overwrite an active engine installation during upgrades.

## Repository map

- `app/` local Python invoice preparation, extraction and supervision
- `config/` schema, prompt and runtime configuration
- `deployment/` PowerShell installation, environment check, release verification and scheduled-task setup
- `docs/` reference deployment, acceptance, operations and customs-entry plan
- `power-automate/` cloud flow setup and export requirements
- `tests/` executable regression tests
- `data/reference/` placeholder contract for future approved HTS/PGA/OGA data; no real dictionary is included
- Python engine under `app/` is the active local-model runtime; retired JavaScript/Tesseract family-parser files, test fixtures, and Node package manifest have been removed
