# Customs entry engine backlog

## Current release integration
- [ ] Run `deployment/Verify-Release.ps1` and Python regression suite against the exact imported package.
- [ ] Confirm package-manifest hashes after migration.
- [ ] Validate clean Windows installation and scheduled-task behavior without overwriting an active runtime.
- [ ] Obtain/export the Power Automate flow artifact.

## Evidence and extraction
- [ ] Build a versioned labeled corpus with field/page evidence across supplier and scan types.
- [ ] Measure field-level accuracy and record false-safe errors; expand deterministic reconciliation and provenance.
- [ ] Add controlled BOL and packing-list ingestion and cross-document reconciliation.

## Customs reference data and forms
- [ ] Integrate the separately maintained authoritative HTS/PGA/OGA dataset; until then matching remains unavailable.
- [ ] Confirm dataset licensing, effective dates, provenance, update process and golden examples.
- [ ] Map reviewed entry data to current CBP 3461/7501 specifications and test draft generation.
- [ ] Keep human review mandatory for classifications, agency applicability and form release.

## Operations
- [ ] Define measured need before adopting Qdrant; exact/rule-based data access is the initial design.
- [ ] Test backup/restore, duplicate/retry behavior, restart recovery, retention and rollback on Windows.
- [ ] Keep automated filing/transmission out of scope pending separate approval and acceptance.
