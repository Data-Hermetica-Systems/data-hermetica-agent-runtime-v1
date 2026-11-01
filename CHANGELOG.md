# Changelog

## 1.0.2 — October 31, 2026

Invoice extraction prompt and LM Studio request-configuration update. Package base: 1.0.1. Engine worker version: 1.3. Supervisor version: 1.1.

- Replaced the invoice system prompt with a revised evidence-first contract that handles combined Quantity/Net Weight headings and item-level Bill of Lading identifiers.
- Added semantic label matching while retaining null for unsupported fields and preserving document/item boundaries.
- Added the manual LM Studio chat prompt and model-request configuration guide.
- Updated Python worker payloads to explicitly send temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5, and repeat_penalty 1.0 on both preflight and extraction requests.
- Kept the production API's strict JSON Schema response_format. This is separate from the LM Studio Chat UI's Structured Output setting.
- Kept the bounded extraction response ceiling and context budget guard; documented their difference from the manual Chat UI's response-length setting.
- No change to supervisor behavior, OneDrive intake, output schema, or Task Scheduler configuration.

## 1.0.1 — October 31, 2026

Documentation and acceptance-evidence update only. Runtime scripts, prompts, schema, supervisor config, and canonical engine config are unchanged from 1.0.0.

- Recorded the user-confirmed end-to-end automated workflow, including successful processing of PDFs containing image content.
- Added the October 31 read-only Windows status findings.
- Resolved the local/package engine_config.json difference: the sole content difference is config_version 2 versus 3; the worker does not use this marker, and the remaining bytes/settings match.
- Distinguished active runtime acceptance from acceptance of the new clean-install and task-registration wrappers.
- Clarified that result-folder file counts are not invoice/job counts and that unresolved ReviewRequired and Incoming job states were not queried.
- Flagged the historical SOP as internal reference material that should be reviewed before external distribution.

## 1.0.0 — October 31, 2026

Initial master package combining invoice engine v1.2, local supervisor v1.1, deployment wrappers, documentation, tests, and release manifest.

## Customs-entry plan alignment — November 1, 2026

- Made the Python/LM Studio local vision-language invoice extractor the sole active invoice pipeline in the repository.
- Removed the retired JavaScript/Tesseract OCR, invoice-family segmentation, and fixed-layout row builders, along with their package manifest, prompts, and sample artifacts.
- Clarified that Poppler supplies selectable PDF text and rendered page images to the local model; no OCR engine is used.
- Kept deterministic code for bounded normalization, schema/business validation, reconciliation checks and exception routing, not variable invoice parsing.
- Refreshed project context, prerequisites, architecture and release manifest. HTS/PGA/OGA, classification and 3461/7501 work remains planned and dataset-gated.

## Live audit alignment — November 1, 2026

- Reconciled repository release status with the read-only live directory audit: installed 1.0.2 source files match the package manifest and the supervisor was running; this is not a fresh accuracy test.
- Documented the separate live runtime root and excluded state, work, customer documents, logs, backups and generated artifacts from source control.
- Redacted invoice identifiers, file names, document hashes and user-specific installation details from operational acceptance documentation.
- Clarified that the fresh installer differs from the separate in-place updater, whose source was not included in the audited ZIP.
- Added a source tree/data-boundary guide and expanded ignore rules for live runtime artifacts.
