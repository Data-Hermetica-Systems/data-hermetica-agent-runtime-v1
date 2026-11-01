# Customs entry automation roadmap

## Where the project is now

The current baseline is the local invoice engine 1.0.2. Outlook and Power Automate cloud move qualifying attachments to OneDrive; OneDrive sync places them on the Windows PC; a Python supervisor and Poppler prepare PDFs; a local LM Studio model extracts invoice fields to structured outputs; deterministic code normalizes and validates output. The reference deployment has user-confirmed multi-invoice and image-bearing-PDF runs. Unit-price regression tests are packaged. Exact model artifact identity, comprehensive field accuracy, Windows installer acceptance, Power Automate export, restart recovery, and broader supplier coverage remain open acceptance items.

The retired JavaScript/Tesseract invoice-family prototype has been removed. The active model-led extraction code is in `app/`: the local model interprets variable layouts and bounded code validates/normalizes results. No tested implementation currently creates customs entry forms or determines HTS/PGA/OGA requirements.

## End goal

Prepare accurate, auditable draft CBP Forms 3461 and 7501 from reconciled import-document evidence; match material descriptions to current U.S. HTS tariff entries and determine potentially relevant PGA/OGA programs from a maintained authoritative dataset; show evidence and uncertainty; route unresolved cases to a qualified reviewer. Do not file or transmit entries automatically without a separate compliance, security, operational and legal approval gate.

## Phased implementation

| Phase | Deliverable and software | PowerShell / operational steps | Models and tests | Qdrant |
|---|---|---|---|---|
| 0. Reproduce baseline | Windows 11, Python 3.12, Poppler, OneDrive, Power Automate cloud, LM Studio; engine 1.0.2 | Verify release hashes; install to a fresh root; run environment check and unit tests; run one controlled invoice and compare to labeled ground truth; register scheduled task only after acceptance | Local Qwen model via LM Studio API for extraction; unit tests plus source-to-output field review | Not needed |
| 1. Harden evidence extraction | Python schemas, provenance/page references, invoice/BOL/packing-list intake, deterministic reconciliation | Add safe backup/upgrade and explicit acceptance scripts; test sync delay, duplicate, restart, corrupt/encrypted and image-only files | Keep local vision-capable model for scanned pages; tests for page coverage, field provenance, totals, weights, duplicate suppression and manual-review routing | Not needed |
| 2. Import maintained reference data | Versioned HTS plus PGA/OGA dictionary from separate workstream; normalized local SQLite/Parquet or relational tables, with immutable source snapshots | Add import/validation script that checks schema, provenance, effective dates, duplicate keys, required references, checksum and row counts; reject incomplete releases | No model is authoritative for code/agency selection. Rule/unit tests and reviewed golden classifications required | Usually not needed; start with exact/structured filters |
| 3. Candidate material matching | Local retrieval service over normalized product history and approved reference text; lexical + attribute/rule retrieval | Build/rebuild index from a pinned dataset version; verify returned candidates cite version and source rows; test no-match and ambiguous cases | Local embedding model may retrieve candidates; local reranker/LLM may explain or rank candidates, always constrained to retrieved records. Human confirmation required | Optional. Qdrant becomes useful if corpus size, semantic search, filtering and update needs exceed a simple local index. It retrieves candidates; it does not determine the legally correct HTS or PGA flags |
| 4. Draft entry forms | Canonical entry model, reviewed mapping to current official 3461/7501 field instructions/templates, PDF/CSV output and validation | Add form-generation command and dry-run/verify script; validate required fields, totals, units, party consistency, cross-document evidence, HTS version/effective date and review status | LLM may extract/explain; deterministic mapping fills only supported fields. Golden form fixtures, schema tests, arithmetic tests and independent reviewer sign-off | Optional for candidate lookup only |
| 5. Controlled operations | Local audit database, case review UI/work queue, release monitoring and retention controls | Test backup/restore, scheduled startup, safe upgrades, audit completeness and rollback on a clean Windows workstation | Acceptance suite across suppliers, formats, image quality and edge cases; measure field-level precision/recall and false-safe rate | Deploy only if measured need justifies it; snapshot/version the collection and verify reproducible index builds |

## Placeholder dataset contract

`data/reference/README.md` is the only placeholder today. The matching API must treat the dictionary as unavailable and return no classification or agency flags. Do not create placeholder tariff codes or sample PGA determinations that could be mistaken for real data. Once the separate dataset arrives, require official source provenance, effective dates, version/checksum, schema, update cadence, licensed-use review and reviewed golden cases before matching is enabled.

## Model roles

- **Invoice vision/extraction:** local LM Studio model. The reference package identifies `qwen/qwen3.8-27b`, Q6_K in the observed interface; verify actual artifact hash, license, vision support, runtime and context on the PC. Version the prompt and parameters with each release.
- **Embeddings:** optional local embedding model for semantic candidate recall after approved reference data exists. Pin model and index build metadata.
- **Reranking/reasoning:** optional local model to order/explain retrieved candidates using only supplied source evidence. It cannot invent missing tariff entries or certify a classification.
- **Forms:** deterministic transformations and validators; no generative model should silently fill unsupported legal fields.

## Qdrant decision

Qdrant is not required for the current pipeline, the dataset-import stage, or basic HTS exact lookups. Start with local SQLite/Parquet plus text search and explicit rules. Add local Qdrant only if evaluation demonstrates that material-description candidate recall at scale benefits from vector retrieval and that metadata filters can enforce jurisdiction, effective date, chapter, agency and dataset version. Keep source rows, citations, rule checks and human approval authoritative. Never use nearest-neighbor similarity as the final classification decision.

## Release gates

1. Dataset owner supplies and versions the complete approved HTS/PGA/OGA corpus.
2. Every output retains source document/page/field and dataset record/version provenance.
3. No-match, ambiguity, stale data, missing evidence and conflicting documents all fail closed to review.
4. 7501/3461 field maps cite current CBP instructions and have reviewed golden fixtures.
5. Field-level accuracy and false-safe rates meet targets set by customs/compliance owners.
6. Human review, audit, access, retention, backup/restore and rollback are accepted.
7. Filing/transmission remains disabled until separately authorized and tested.
