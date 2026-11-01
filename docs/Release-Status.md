# Release status and acceptance boundaries

**Source release:** Data Hermetica Invoice Engine Master 1.0.2
**Runtime versions:** invoice engine 1.3; local supervisor 1.1
**Audit checkpoint:** November 1, 2026

## Verified live installation

The read-only live directory audit confirms the engine is installed at `H:\DataHermetica\InvoiceEngine` on Windows device `HERMETICA`; the Task Scheduler supervisor was `Running` under the user's logon session. The task launches Python 3.12 `pythonw.exe` with `app\invoice_supervisor.py --continuous`. OneDrive sync roots point to `InvoiceIntake\Incoming` and `InvoiceResults` folders. LM Studio's local OpenAI-compatible endpoint is `http://127.0.0.1:1234/v1`, and the configured alias `qwen/qwen3.8-27b` was visible. Sampling configuration recorded by the audit: temperature 0.7, top_p 0.8, top_k 20, presence penalty 1.5.

All nine installed runtime code/config/test files were reported to match the 1.0.2 package manifest. The uploaded source archive SHA-256 is `f1adfc8a98b39f5392d86ce2102ed756fcc36e9f85a2b0612843961a91fc7c0d`. The source files in this repository preserve the package's runtime bytes. This establishes release integrity and a running supervisor at the audit time; the audit was not a fresh invoice accuracy run and did not query job databases.

## What 1.0.2 does

- Power Automate cloud flow moves eligible email attachments into OneDrive intake.
- OneDrive sync makes files available to the Windows host.
- Python supervisor watches intake, checks model availability, suppresses duplicate work and coordinates processing.
- Poppler extracts selectable PDF text and renders pages without a useful text layer. The local Qwen vision-language model reads the text and page images and extracts invoice fields using the prompt and strict JSON Schema.
- Python normalizes selected values, validates structure/business conditions, records job state and publishes completed or review-required outputs.

The local model performs variable-layout invoice reading. The deterministic code does not parse invoice families. There is no Tesseract stage.

## Release and deployment boundaries

The 1.0.2 source ZIP includes `Install-Engine.ps1` for fresh installation, `Test-EngineEnvironment.ps1`, `Register-SupervisorTask.ps1`, and `Verify-Release.ps1`. The live audit found the active installation, but does not establish that the packaged fresh-install or registration scripts performed it.

A separate in-place 1.0.2 updater was used on the live installation, but that script was not included in the source ZIP supplied for this repository audit. Its source has not been reviewed here and it is not included in this repository. Do not substitute the fresh installer for an in-place upgrade, and do not run an unreviewed updater against a live engine. Stop/backup/upgrade/rollback procedures need a source-reviewed, tested updater before being treated as reproducible deployment automation.

The live installation root contains runtime `state`, `work`, `logs`, backups and customer files that must stay outside GitHub. The installation has no `.git`; the repository contains only reviewed source, configuration, scripts, tests and documentation.

## Acceptance limits and next gates

- The live audit establishes that the task was running and model endpoint visible, not that every waiting source file completed or that each extracted field was correct.
- Historical user-reported successful processing exists, but broad field-level accuracy across suppliers and image-only documents still needs a labeled truth set and measured results.
- The included automated suite is narrow: it covers unit-price parsing/normalization. Add sanitized parser/worker integration fixtures and source-to-field accuracy tests before making broad accuracy claims.
- Power Automate export is not supplied; the manual flow recreation guide remains the setup path.
- HTS classification, PGA/OGA determination, and Forms 3461/7501 generation are not implemented in the audited installation or this release. The required dataset is developed separately and unavailable here; classification must remain disabled until approved data is integrated.
- No filing/ACE/ABI transmission adapter is implemented or authorized by this release.

The live invoice extraction stage is operationally installed. This does not certify field accuracy, customs classification, entry form generation, filing compliance, or customer deployment readiness.
