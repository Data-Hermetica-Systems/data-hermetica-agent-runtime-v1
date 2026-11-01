# Acceptance and operations record

## Current reference deployment update — October 31, 2026

The user confirms that the end-to-end email intake, OneDrive synchronization, local supervisor, LM Studio extraction, validation, and result publication workflow has successfully processed many invoices, including PDFs containing image content. The exact number of invoices, whether each image-bearing file was fully scanned or mixed text/image, and aggregate field-level ground-truth scores were not provided; do not infer those metrics.

The supplied read-only Windows status report showed:

- Scheduled task `DataHermetica-InvoiceEngine-Supervisor`: `Running`; action invokes Python 3.12 `pythonw.exe` with `invoice_supervisor.py --continuous`; logon trigger for the current user.
- Task result `267009` / `0x41301`: Task Scheduler's current-running status.
- LM Studio `/v1/models`: endpoint responded and configured model `qwen/qwen3.8-27b` was visible.
- Recent supervisor log: model readiness succeeded and scans repeatedly found five intake files but processed/reviewed zero new jobs during those scans. Source files remain in Incoming by design; the report did not establish each file's durable job status.
- Recursive local folder counts: 24 files in Completed and 2 files in ReviewRequired. These are artifact counts, not invoice counts. The job databases could not be hashed while held open by the running process; no database state query was performed.
- Installed hashes for preparation, worker, supervisor, extraction schema, baseline prompt, and supervisor configuration matched the Master release manifest.
- Historical v1.0.1 reference: installed engine_config.json reported config version 2 while that package used version 3; recorded runtime values otherwise matched. Release 1.0.2 intentionally changes the configuration to version 4 and adds explicit API sampling parameters. Do not copy the new config over an active engine without backing up current files and stopping the supervisor after active work completes.

The active runtime is therefore operationally confirmed on the reference PC. The report does not prove that the new Master release's fresh-install or task-registration wrapper scripts were the scripts used to install it; the observed task action omits the explicit `--engine-root` argument used by the new registration wrapper. Both task configurations are supported by the supervisor's environment/script-location behavior, but wrapper acceptance remains a separate release item.

## 12. Automatic email acceptance


1. Keep OneDrive and LM Studio available and task Running.
2. Send an email with the marker and a previously unprocessed controlled invoice.
3. Confirm Power Automate run history and local Incoming file.
4. Observe discovery, preparation, worker status, local result, and subsequent scans without duplicate processing.

```powershell
$incoming = Join-Path $env:OneDriveCommercial 'InvoiceIntake\Incoming'
Get-ChildItem -LiteralPath $incoming -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 5 Name, Length, LastWriteTime |
    Format-Table -AutoSize
Get-Content -LiteralPath (Join-Path $env:DATA_HERMETICA_INVOICE_ENGINE_ROOT 'logs\invoice-supervisor.log') -Tail 10 -Wait
```

Ctrl+C stops this log reader, not the independently scheduled supervisor. Use the actual log timestamp when interpreting results: the new file in the test was timestamped 21:38:53 and the previous scan was 21:38:34, so that earlier log could not establish processing of the new file.

## 13. Result acceptance and evidence

Observed automatic run: Solstice invoice 97699205; source shipment filename `7000385095 252554817`; hash `1a26c38cefc0a63bf675d256da12397f900518e6aa72978feb0e143946294fb6`; 13 text pages; no image pages; estimated input 21461; discovery at 21:39:14; preparation at 21:39:17; completion at 21:42:36 on October 30, 2026 Oklahoma local time. Validation passed with 31 rows, JSON 31, CSV 31, issues empty, output CSV `97699205.csv`. Later scans processed zero documents. This establishes automatic processing and structural validation; full source-to-field accuracy was not supplied.

Earlier evidence:
- Invoice 97612503: 22 text pages, 62 rows, JSON/CSV/validation counts 62, item numbers 1–62, no missing/unexpected/duplicate numbers or header differences. Hash `7df63d395df1de454fe888fe4e42a7008df76d5358a8c90d05cfd1e95cdefa95`.
- v1.2 migration: 62 numeric-only unit prices, zero slash-containing prices, first raw price `11.1542 / EA`, canonical `11.1542`, basis quantity `1`, basis unit `EA`.
- Invoice 97627224: 4 text pages, 3 rows, validation passed, OneDrive result folder exists. Hash `1ac56e83fd4d2bb4ec42b2743f6947692950a27883c8b504bf864d78c63ebfc1`.

The following acceptance script uses the actual 31-row test identity. For a client test replace the two clearly named test values with its independently established document hash and expected row count. The script is complete and runnable for this recorded test.

```powershell
$ErrorActionPreference = 'Stop'
$documentSha256 = '1a26c38cefc0a63bf675d256da12397f900518e6aa72978feb0e143946294fb6'
$expectedRows = 31
$resultDirectory = Join-Path (Join-Path $env:DATA_HERMETICA_INVOICE_ENGINE_ROOT 'work\output_staging') $documentSha256
$publishedDirectory = Join-Path (Join-Path $env:OneDriveCommercial 'InvoiceResults\Completed') $documentSha256
$validation = Get-Content -LiteralPath (Join-Path $resultDirectory 'validation.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$extraction = Get-Content -LiteralPath (Join-Path $resultDirectory 'extraction.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$csvFiles = @(Get-ChildItem -LiteralPath $resultDirectory -File -Filter '*.csv')
if ($csvFiles.Count -ne 1) { throw 'This acceptance case requires exactly one invoice CSV.' }
$rows = @(Import-Csv -LiteralPath $csvFiles[0].FullName)
$jsonRows = @($extraction.invoices | ForEach-Object { $_.merchandise_items })
$expectedHeaders = @('Item','Product Number','Material Description','Unit','Quantity','Unit Price (USD)','Total Amount (USD)','Country of Origin','Delivery Note','Gross Weight','Net Weight','Commodity Code','Shipment Number')
if ($rows.Count -eq 0) { throw 'CSV is empty.' }
$actualHeaders = @($rows[0].PSObject.Properties.Name)
if (($expectedHeaders -join '|') -cne ($actualHeaders -join '|')) { throw 'CSV column order or names differ.' }
if ($validation.status -ne 'passed' -or $rows.Count -ne $expectedRows -or $jsonRows.Count -ne $expectedRows -or $validation.merchandise_row_count -ne $expectedRows) { throw 'Status or row-count acceptance failed.' }
[pscustomobject]@{
    ValidationStatus = $validation.status
    CsvRows = $rows.Count
    JsonRows = $jsonRows.Count
    CsvFile = $csvFiles[0].Name
    LocalOneDriveFolderExists = Test-Path -LiteralPath $publishedDirectory -PathType Container
} | Format-List
$validation | Format-List *
$rows | Format-List *
```

`Format-List` displays every field; the earlier wide `Format-Table -AutoSize` hid later columns at the console width. Compare all required fields to the source/approved spreadsheet. Check OneDrive web separately to prove cloud availability. Local folder presence alone proves only local publication.

## 14. Field contract and normalization

Invoice details: Invoice Number, Invoice Date, Customer No., Ship To, Bill To, Shipper Details. If issuer is printed but shipper role is not established, label issuer explicitly.

Merchandise CSV: Item, Product Number, Material Description, Unit, Quantity, Unit Price (USD), Total Amount (USD), Country of Origin, Delivery Note, Gross Weight, Net Weight, Commodity Code, Shipment Number, in precisely that order.

Primary Product Number uses structural alignment with the item/quantity/price row rather than the closest catalog code in a description. Eight digits alone is not sufficient because commodity codes can also have eight digits. Keep repeated products as separate items. Join page continuations and associate notes and weights to the correct item. Never distribute combined weights across items without evidence.

Descriptions must preserve source-supported substance, solution/solid form, concentration and relevant grade. Do not infer liquid form from a commodity code or expand abbreviations into unsupported chemical claims. The displayed 31-row output contains phrases such as “free from detection of nitrogen”; source review is needed before accepting those expansions.

Unit price normalization retains `unit_price_raw`, `price_basis_quantity`, and `price_basis_unit` internally; exported unit price contains only the canonical numeric string. Plain numeric input remains valid; `/ EA` and other explicit bases are parsed rather than removed by an unconditional slash split. An explicit `/ 100 KG` basis is retained; the numeric price is not silently recalculated to per KG. Ambiguous punctuation is rejected. See full parser, test cases and prompt below.

Commodity Code is printed evidence, not a legally verified HTS classification. This SOP makes no claim of customs filing compliance from extraction alone.

## 15. Routine operations and recovery

To inspect task state and recent runs:

```powershell
Get-ScheduledTask -TaskName 'DataHermetica-InvoiceEngine-Supervisor' | Select-Object TaskName, State
Get-ScheduledTaskInfo -TaskName 'DataHermetica-InvoiceEngine-Supervisor' | Format-List *
Get-Content -LiteralPath (Join-Path $env:DATA_HERMETICA_INVOICE_ENGINE_ROOT 'logs\invoice-supervisor.log') -Tail 40
```

State Running means the process is active; it does not prove model accuracy or successful document processing. Restart settings cover a process exiting unsuccessfully, not every failed document caught in the scan loop.

For planned maintenance, let active extraction complete, then stop the task before changing code/config:

```powershell
Stop-ScheduledTask -TaskName 'DataHermetica-InvoiceEngine-Supervisor'
Get-ScheduledTask -TaskName 'DataHermetica-InvoiceEngine-Supervisor' | Select-Object TaskName, State
```

Stopping the supervisor is not proof that any spawned Python worker has exited. Check processes before editing files or backing up databases:

```powershell
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -in @('python.exe','pythonw.exe') } |
    Select-Object ProcessId, ParentProcessId, ExecutablePath, CommandLine
```

Do not kill unrelated Python processes. Back up application/configuration and state only after verifying this instance is quiescent; supervisor SQLite uses WAL, so copying only a live `.db` file can omit changes. No automated backup/retention implementation has been demonstrated.

Manual retry after investigating a failed/review-required document uses the exact known hash and the worker `--force` option. The following is the historical successful 62-row rerun command, not a command to blindly rerun production files:

```powershell
python "H:\DataHermetica\InvoiceEngine\app\invoice_worker.py" `
    --sha256 '7df63d395df1de454fe888fe4e42a7008df76d5358a8c90d05cfd1e95cdefa95' `
    --force
```

Archive prior outputs/raw responses before intentional retry: paths are hash-keyed and may be reused. Supervisor state may still record an old failure for an unchanged path even after a manual worker rerun; state reconciliation is not implemented as an operator CLI. Do not delete state databases or invent reset flags. Inspect both databases and design an audited reconciliation before claiming a retry is fully cleared.

Price-only historical migration without a new model call:

```powershell
$sha256 = '7df63d395df1de454fe888fe4e42a7008df76d5358a8c90d05cfd1e95cdefa95'
python "H:\DataHermetica\InvoiceEngine\app\invoice_upgrade_output.py" `
    --input "H:\DataHermetica\InvoiceEngine\work\output_staging\$sha256\extraction.json" `
    --output "H:\DataHermetica\InvoiceEngine\work\output_staging\$sha256-v1.2"
if ($LASTEXITCODE -ne 0) { throw 'Price migration failed.' }
```

PowerShell `$ErrorActionPreference='Stop'` does not alone guarantee native Python exit failures throw in Windows PowerShell. Capture/check `$LASTEXITCODE` immediately after native commands. Paste complete `if/elseif/else` statements together: the earlier user entered `elseif` as a separate command and PowerShell rejected it.

## 16. Failure cases and limitations requiring client acceptance

| Symptom/issue | Verified cause or behavior | Operator action |
|---|---|---|
| Only a few item rows from big invoice in chat | Chat UI injected retrieval excerpts | Full prepared payload through API; no chat-attachment retrieval in this worker |
| Empty final JSON, finish_reason length | Earlier run used 32768 completion tokens in reasoning; 85803 reasoning characters, zero final characters | Correct server reasoning settings; inspect preserved response; rerun intentionally |
| Worker rejects --preflight | Not an implemented CLI flag | Use --help; actual run includes probe |
| ZIP installer not found | Earlier v1.0 ZIP included extra deliverables wrapper | Discover exactly one installer path; do not select arbitrarily among multiple results |
| New file not yet in log | Latest scan predates arrival; stability check adds delay | Compare timestamps; watch next scan |
| Model unavailable before scan | v1.1 gate returns false | Files remain pending; next scan retries readiness |
| API outage after readiness | Readiness is a point-in-time test | Worker can fail; no general automatic document retry guaranteed |
| API authentication enabled | Supervisor readiness lacks Authorization header | Source adaptation and acceptance required |
| FAILED/REVIEW_REQUIRED file remains | Supervisor deliberately skips terminal observations | Investigate and perform controlled recovery; unchanged-file resend may not retry |
| Text candidate false confidence | >=80 alphanumeric characters is heuristic | Review low-quality/mixed scans; image path only covers pages below threshold |
| Missing scan items | Completeness regex operates on extracted text, not image-ground-truth count | Independently compare expected items for image invoices |
| JSON schema passed, wrong value | Structural validation cannot prove source truth | Ground-truth field comparison |
| Published folder exists, cloud absent | Local copy is not cloud-sync confirmation | Check OneDrive sync and web output |
| Partial published folder visible | Files copied one by one; no explicit commit marker transaction | Downstream consumer needs completion protocol before production integration |
| Task starts after reboot, dependencies unavailable | Only supervisor startup implemented | Verify sign-in, OneDrive, server/model startup; perform restart recovery acceptance |
| Multiple tenants/instances | Task name, user env, output relative paths fixed | Isolate and adapt code/config before deployment |

No lossless end-to-end “exactly once” guarantee is established. Existing state suppresses repeated work for the demonstrated hashes, but crash/retry/cloud publication behavior needs fault testing.

## 17. Client release gates

Record each result and evidence; pending entries must not be marked complete:

| Gate | Reference deployment | Client required evidence |
|---|---|---|
| Environment/tools inventory | Executables observed; some versions missing | Versions, paths, model hash/backend, account and storage |
| Email intake | Passed | Flow run and correct attachment bytes |
| Text PDF manual | Passed (62 and 3 rows) | Source-ground-truth comparison |
| Automated invoice processing | User confirms many invoices completed end to end, including PDFs with image content; the supplied status report confirms the scheduled supervisor and model endpoint are active | Record per-document source hash, expected/actual rows, field-level ground truth, image/page route, and remote OneDrive publication |
| Price numeric-only | Passed 62-row migration and 3-row output | Multiple price formats, basis preservation |
| Duplicate content | Subsequent scans skipped completed files | Same PDF resent with new name, no unwanted new inference |
| Model absent before arrival | Gate source inspected; failure scenario not shown | Pending file resumes after model available |
| Image-bearing PDF | User confirms successful end-to-end processing for image-bearing PDFs; exact scan/mixed composition and per-field scores were not supplied | Record representative fully scanned and mixed-page samples, page routing, row coverage, and field-level ground-truth results |
| Mixed text/image PDF | Not separately characterized in supplied evidence | Confirm page-by-page route, associations, and field-level accuracy on labeled samples |
| Corrupt/encrypted/unsupported | Not demonstrated | Observable failure without false completion |
| Context/output overflow | Rejection source implemented; earlier truncation diagnosed | Oversized input and length-finish rejection |
| Crash/restart and sign-in | Task started manually; logon test not shown | No lost jobs or concurrent duplicate requests |
| Cloud publish completion | Local OneDrive folder observed | Confirm files on OneDrive web, consistent set |
| Audit, access, retention | Not finalized | Approved policies and operational ownership |

