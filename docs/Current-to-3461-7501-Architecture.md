# Current pipeline to 3461/7501 architecture

This document transcribes the supplied tldraw project diagram into repository documentation. “LIVE” means represented as deployed in the diagram and its October 31, 2026 installation evidence; “BUILD” and “TARGET” are proposed work, not present functionality. Proposed script names below are placeholders until implemented and tested.

## Deployed now: invoice engine 1.0.2

1. **Email intake — LIVE.** Outlook V3 watches for `DH-CE-INV`; Power Automate filters eligible attachments and saves them to OneDrive `InvoiceIntake/Incoming`. No AI is used here. Preserve message and attachment identity.
2. **Supervisor — LIVE.** Windows Task Scheduler starts `app/invoice_supervisor.py --continuous` at logon. `supervisor.db` records state and suppresses duplicates. `deployment/Register-SupervisorTask.ps1` registers the task.
3. **PDF preparation — LIVE.** `app/invoice_prepare.py` uses Poppler to preserve page order and prepare selectable text or page images plus a manifest. No additional AI model is used.
4. **Local extraction — LIVE.** `app/invoice_worker.py` calls the LM Studio local API with `qwen/qwen3.8-27b` Q6_K profile, system prompt and strict JSON schema, processing whole invoices with text and images.
5. **Validation and outputs — LIVE.** The engine emits header and 13 merchandise fields in JSON, CSV, Markdown and `validation.json`, tracks jobs in SQLite, and routes outputs to Completed or ReviewRequired. A 1.0.2 updater and a running scheduled task are reported in the diagram. Structural validation does not establish field truth.

Use release verification, fresh-install and environment-check PowerShell scripts documented in the package. The proposed separate in-place 1.0.2 updater should be treated as a distinct deployment path and run only with its own backup/acceptance procedure.

## Build next: complete shipment case

6. **Source document coverage — BUILD.** Add invoice, BOL/AWB, packing list, manifest, arrival, freight, permits and origin inputs. Power Automate/OneDrive adapters keep originals and hashes.
7. **Document workers — BUILD.** Proposed `bol_worker.py` and `packing_worker.py`. Benchmark the current Qwen vision model on a labeled field truth set before adopting it for these documents. Preserve text/image and page-level provenance.
8. **Link and reconcile — BUILD.** Proposed `assemble_entry_case.py` links invoice, shipment, BOL and containers; compares parties, quantities, weights and origin. Conflicts route to review; never silently merge.
9. **Approved master data — BUILD.** Store importer, broker, bond, surety, port, carrier, MID, entry type, freight and dates with operator-supplied facts and document evidence in a relational case store/event history.

## Build versioned official reference data

10. **USITC HTS sync — DATA SYNC.** Proposed `sync_usitc_hts.py` imports HTS text, chapter notes, rates and changelog. Select the revision effective for the entry date.
11. **CBP PGA references — DATA SYNC.** Proposed `sync_cbp_pga_refs.py` imports the Agency Tariff Code Reference Guide and PGA Flag Enforcement Table/entry types. Persist each flag, code, source, version and effective date.
12. **Agency guides — DATA SYNC.** Proposed `sync_agency_guides.py` indexes ACE PGA Message Set and Appendix PGA plus relevant FDA, EPA, APHIS, CPSC and other agency guides, permits, disclaimers and product conditions.
13. **Reference snapshots — BUILD.** Proposed `build_reference_snapshot.py` makes immutable, versioned releases from the source feeds and validated records. Exact source data and dates must be checked at sync time.

The diagram's November 1, 2026 checkpoint says the uploaded HTS was Revision 21 while USITC Revision 22 was published October 30. Treat that as a freshness warning from the diagram, not a live verification of current agency data. The full HTS/PGA/OGA dictionary is being developed separately and is currently unavailable here. Until the owner provides an approved, complete, versioned dataset, matching must return unavailable/no code/no inferred agency flags and route the case for review.

## Classification, PGA and entry preparation

14. **Decision and source data boundary.** This pipeline uses official versioned reference data, product facts, reviewed product history, applicable rules and source citations. A printed supplier commodity code is evidence only. A missing PGA flag cannot be interpreted as no obligation.
15. **Product facts — BUILD.** Capture composition, function, intended use and material; request missing facts from the importer. Models may extract or ask for missing evidence, not make final legal determinations.
16. **HTS candidates — BUILD.** Proposed `classify_candidates.py` uses GRI, notes, rulings and approved product history to rank 10-digit candidates and alternatives. A reviewer approves the final classification.
17. **PGA applicability — BUILD.** Proposed `evaluate_pga.py` applies reviewed HTS, flags, product facts, agency guides and entry-type conditions. Missing data and ambiguity fail closed to review.
18. **Value/duty — BUILD.** Proposed `calculate_entry.py` applies exact arithmetic to value, weights, units, charges, duty and fees with date-specific inputs, origin, Chapter 99 and AD/CVD handling where applicable. These rules require independent customs/compliance validation.
19. **Entry case validation — BUILD.** Proposed `validate_entry_case.py` checks conditional and mandatory fields, totals, cross-document and cross-line consistency, evidence and exception log.
20. **3461 and 7501 views — TARGET.** Proposed `map_3461.py` maps cargo-release fields; `map_7501.py` maps entry-summary lines and value, origin, duty, tax, fees and conditional PGA data. Proposed `render_3461.py` and `render_7501.py` produce draft PDFs plus a structured ACE-ready payload with evidence, missing values and approver. Verify mappings against current CBP field dictionaries and CATAIR.
21. **Approval and filing gate — TARGET.** An authorized filer approves classification, PGA and duty. Any broker software or ACE/ABI CATAIR adapter requires separate certification testing. Keep filing/transmission disabled until authorized and independently accepted.
22. **Feedback — TARGET.** Track ACE responses, corrections and audits; measure field accuracy, candidate recall and reviewer agreement.

## Software, model and Qdrant decisions

| Stage | Software and PowerShell | AI | Qdrant |
|---|---|---|---|
| Live invoice intake/runtime | Outlook, Power Automate, OneDrive, Task Scheduler, Python, Poppler, SQLite; existing release verification, environment, install and task scripts | Current Qwen via LM Studio for invoice extraction | None |
| BOL/packing document case | Proposed Python workers, adapters, case DB, reviewer UI; proposed `Install-DocumentCase.ps1` and `Test-DocumentCase.ps1` | Benchmark current Qwen VLM against labeled truth | None initially |
| Official references | USITC/CBP/agency source feeds, Python ingestion, versioned SQLite/PostgreSQL; proposed `Update-CustomsReferences.ps1` and `Test-ReferenceFreshness.ps1` | None for authoritative ingestion | Optional later, not needed for structured source data |
| HTS/PGA decisions | Python candidate search/rules, evidence UI; proposed `Test-ClassificationPipeline.ps1`, `Test-PgaApplicability.ps1` | Local extraction for facts; optional local embeddings/reranker after evaluation; reviewer makes decision | Only if hybrid retrieval improves measured recall over exact and lexical search |
| Forms and filing gate | Field dictionary, Python maps/renderers, audit DB, authorized filer; proposed `Test-EntryForms.ps1`, `Test-AceAdapter.ps1` | No AI for autonomous final classification, duty or filing | No role in final values |

Proposed scripts are design names, not commands present in the current package. Qdrant is not deployed. Start with exact code lookup and lexical HTS search. Consider Qdrant only after a benchmark demonstrates improved top-k recall; use hybrid search and reference-revision filters to retrieve candidates, never as the authority for final values.

## Acceptance gates

1. Build a field-level invoice truth set, then multi-document matching tests.
2. Accept and freshness-test a complete, approved versioned HTS/PGA dataset.
3. Measure candidate recall and reviewer agreement; keep ambiguity in the review queue.
4. Verify every form field against current form/CATAIR specifications and golden cases.
5. Complete ACE certification before enabling any filing adapter.
6. Preserve source/page, model, prompt, dataset revision, reviewer and decision provenance per entry.

## Diagram source

`Data Hermetica _ Customs Entry Automation Pipeline _Current to 3461_7501_.tldr`, provided by the user in this conversation. Source authority feeds named by the diagram: USITC HTS archive (`usitc.gov/harmonized_tariff_information/hts/archive/list`), CBP CATAIR (`cbp.gov/trade/automated/catair`), LM Studio OpenAI-compatible API, and Qdrant hybrid search documentation. Verify links and source revisions at implementation time.
