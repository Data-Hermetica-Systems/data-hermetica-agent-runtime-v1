# Changelog

All notable changes to this component are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.2.0] - 2026-11-12

### Added

- Power Automate intake flow definition with the attachment condition, the telemetry payload expression and the telemetry contract (`schema_version` 1).
- Unit-price canonicalization that keeps `unit_price_raw`, `price_basis_quantity` and `price_basis_unit`, with a normalization record for every document.
- Migration utility for results in the previous output format.
- Fictional sample invoice with expected JSON, Markdown and CSV outputs.
- Unit tests for decimal normalization, schema validation, completeness, price-basis consistency and the CSV contract.
- Continuous integration on Linux and Windows.

### Changed

- Source packaged as `document_pipeline`. The supervisor locates the preparation and worker modules beside its own module.
- The engine root must be supplied through `DATA_HERMETICA_INVOICE_ENGINE_ROOT` or `--engine-root`.
- The supervisor configuration file is `config/supervisor_config.json`.
- Layout-specific guidance in the extraction prompt is expressed as supplier-neutral rules with synthetic examples.
