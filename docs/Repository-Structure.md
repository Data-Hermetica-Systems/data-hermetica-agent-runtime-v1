# Source repository structure and data boundary

This checkout contains versioned application source, release configuration, deployment scripts, sanitized tests and the customs-entry plan. It is not the live Windows runtime directory.

- app/: four Python runtime modules for PDF preparation, invoice extraction, local supervision and output upgrade.
- config/: engine settings, extraction schema, supervisor settings and model prompt.
- data/reference/: placeholder contract for the separate HTS/PGA/OGA dictionary workstream; it contains no usable tariff data.
- deployment/: fresh install, environment test, task registration and source release verification.
- docs/: architecture, audit status, operations, setup and customs-entry plan.
- power-automate/: flow recreation and export status.
- tests/: sanitized automated tests and future approved fixtures.
- README.md, PROJECT_CONTEXT.md, TODO.md, CHANGELOG.md and release-manifest.json: project entry points and version evidence.

The live Windows installation has separate mutable state, work, logs, backup, backups, quarantine and runtime release directories. These stay outside GitHub. OneDrive InvoiceIntake, InvoiceResults and InvoiceArchive are external operational folders and must not be copied into this checkout.

Never commit source/customer PDFs, extracted customer data, model request/response bodies, customer-file hashes, SQLite state/WAL files, logs, backups, model weights, credentials or local installation records. The root .gitignore covers common runtime paths and extensions, but review git status --ignored and the staged file list before every commit. Ignore rules do not replace inspection.

The supplied Power Automate flow export and the separate in-place 1.0.2 updater source were not included in the audited ZIP. Do not invent either artifact. The manual flow recreation guide remains; the package fresh installer must not be used as an in-place updater.
