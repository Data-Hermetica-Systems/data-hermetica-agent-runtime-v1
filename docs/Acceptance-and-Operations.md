# Acceptance and operations

## Live installation audit checkpoint — November 1, 2026

A read-only audit confirmed the Windows invoice engine 1.0.2 installation at `H:\DataHermetica\InvoiceEngine`, with the scheduled Python 3.12 supervisor running at logon and the configured local LM Studio model visible. Nine installed code/config/test files matched the 1.0.2 package manifest. This is an integrity and process-state check, not a new invoice accuracy test. See [Release Status](Release-Status.md).

Customer PDFs, extracted outputs, request/response payloads, hashes, invoice identifiers, logs, and SQLite state are local runtime data. Do not copy them into GitHub. Keep `state/`, `work/`, `logs/`, backups and OneDrive intake/results outside the source checkout.

## Prerequisites

- Windows 11 session for the audited deployment pattern.
- Python 3.12 and Poppler tools (`pdfinfo`, `pdftotext`, `pdftoppm`) available to the task account.
- OneDrive for Business signed in and syncing the same account used by the Power Automate flow.
- LM Studio local server running with the configured vision-capable model loaded at `http://127.0.0.1:1234/v1`.
- Power Automate cloud flow configured to save eligible attachment bytes to `InvoiceIntake/Incoming`.

Poppler does not OCR scanned pages. It extracts selectable PDF text and renders pages; the local vision-language model reads rendered images directly. Do not install or configure Tesseract for this engine.

## Verify source release

From the repository root in PowerShell:

```powershell
& .\deployment\Verify-Release.ps1
python -m unittest discover -s .\tests -p 'test_*.py' -v
if ($LASTEXITCODE -ne 0) { throw 'Regression tests failed.' }
& .\deployment\Test-EngineEnvironment.ps1 -EngineRoot $env:DATA_HERMETICA_INVOICE_ENGINE_ROOT
```

The environment check confirms required local tools and LM Studio model visibility. It does not run invoice extraction or prove field accuracy.

## Inspect the live installation

```powershell
$engineRoot = $env:DATA_HERMETICA_INVOICE_ENGINE_ROOT
if ([string]::IsNullOrWhiteSpace($engineRoot)) { throw 'Engine root is not configured.' }
$taskName = 'DataHermetica-InvoiceEngine-Supervisor'
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State
Get-ScheduledTaskInfo -TaskName $taskName | Format-List *
Get-Content -LiteralPath (Join-Path $engineRoot 'logs\invoice-supervisor.log') -Tail 40
```

A Running task is not evidence that a file completed. Consult logs and job state using the supported application workflow; do not infer job counts from files in Completed or ReviewRequired.

## Controlled invoice acceptance

1. Use an authorized, sanitized test invoice with independently prepared expected values.
2. Confirm the attachment bytes arrive in OneDrive Incoming and finish syncing locally.
3. Run `invoice_prepare.py` for the file, calculate its SHA-256, then run the worker in `--dry-run` mode and inspect the request estimate.
4. Run the worker against the prepared document and inspect `validation.json`, JSON, CSV, Markdown and preserved raw response.
5. Compare every header and merchandise field to source ground truth, including missing values, repeated items, page continuation, amount/quantity/price arithmetic, units, weights, origin and identifiers.
6. Verify publication locally and in OneDrive web. Verify duplicate suppression and review routing separately.
7. Record release/model/prompt/config versions, test-set version, field-level results, exceptions and reviewer. Do not use schema validity or row count as an accuracy score.

Example commands (replace paths with an approved local fixture; never embed customer hashes in repository instructions):

```powershell
$engineRoot = $env:DATA_HERMETICA_INVOICE_ENGINE_ROOT
$testPdf = 'C:\ApprovedTestData\invoice.pdf'
python (Join-Path $engineRoot 'app\invoice_prepare.py') --file $testPdf
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed.' }
$documentSha256 = (Get-FileHash -LiteralPath $testPdf -Algorithm SHA256).Hash.ToLowerInvariant()
python (Join-Path $engineRoot 'app\invoice_worker.py') --sha256 $documentSha256 --dry-run
if ($LASTEXITCODE -ne 0) { throw 'Dry run failed.' }
python (Join-Path $engineRoot 'app\invoice_worker.py') --sha256 $documentSha256
if ($LASTEXITCODE -ne 0) { throw 'Extraction failed.' }
Get-Content -LiteralPath (Join-Path $engineRoot "work\output_staging\$documentSha256\validation.json") -Raw
```

## Email intake acceptance

Send a controlled email with the configured subject marker and a known test invoice. Verify the flow's trigger, attachment filter, Get Attachment result, OneDrive Create file result, synced local file, supervisor discovery, completed/review output and next-scan duplicate behavior. The Power Automate export is not included; follow [Power Automate Setup](Power-Automate-Setup.md) and retain the export in the organization's approved deployment store.

## Safe maintenance and upgrade

Wait for active extraction to finish before stopping the scheduled task. Confirm child Python processes have exited before backing up or modifying files. Preserve a consistent SQLite backup, including WAL state, using an application-aware procedure.

The repository's `Install-Engine.ps1` is for a fresh target directory. It is not an in-place upgrade tool. The live 1.0.2 installation used a separate updater whose source was not included in the supplied ZIP; that updater is not reproduced or recommended here. Until an in-place updater has been reviewed and tested, use a new isolated target and a documented rollback plan rather than overwriting a working installation.

Do not run the historical supervisor installer scripts. They are not part of this repository's active deployment path.
