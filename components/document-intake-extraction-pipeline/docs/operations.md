# Operations

## Prerequisites

| Requirement | Check |
|---|---|
| Windows 11 with the account that will run the supervisor | |
| Python 3.12 on `PATH` | `python --version` |
| Poppler on `PATH` | `pdfinfo -v`, `pdftotext -v`, `pdftoppm -v` |
| OneDrive for Business signed in with the account used by the intake flow, with the intake folder kept on the device | `$env:OneDriveCommercial` |
| OpenAI-compatible local inference server with the configured vision-capable model loaded, reasoning disabled | `GET <base_url>/models` |

Poppler does not perform OCR. It extracts selectable text and renders pages; the model reads rendered pages directly.

## Engine root

The engine root is the directory named by `DATA_HERMETICA_INVOICE_ENGINE_ROOT`.

```
<ENGINE_ROOT>/
  config/engine_config.json        copied from engine_config.example.json
  config/supervisor_config.json    copied from supervisor_config.example.json
  config/extraction_schema.json
  prompts/extraction_system_prompt.txt
  state/   work/   logs/           runtime data, created at run time
```

A checkout of this component can serve as the engine root; the runtime folders and the two copied configuration files are excluded from version control. Create `logs` before the first direct worker run:

```powershell
New-Item -ItemType Directory -Force -Path (Join-Path $env:DATA_HERMETICA_INVOICE_ENGINE_ROOT 'logs') | Out-Null
```

## Configuration

`config/engine_config.json`

| Key | Reference value | Meaning |
|---|---|---|
| `lm_studio_base_url` | `http://127.0.0.1:1234/v1` | Model endpoint. |
| `model` | `qwen/qwen3.8-27b` | Model identifier that must be listed by the endpoint. |
| `context_length` | 112896 | Context length the model is loaded with. |
| `max_output_tokens` | 32768 | Completion limit, reserved in the context budget. |
| `safety_margin_tokens` | 4096 | Additional reserve in the context budget. |
| `temperature`, `top_p`, `top_k`, `presence_penalty`, `repeat_penalty` | 0.7, 0.8, 20, 1.5, 1.0 | Sampling parameters sent with the preflight and the extraction. |
| `timeout_seconds` | 1800 | Extraction request timeout. |
| `preflight_max_tokens` | 256 | Completion limit of the preflight. |
| `require_reasoning_disabled` | `true` | Must be `true`; the worker refuses to run otherwise. |
| `allow_automatic_batching` | `false` | Must be `false`; the worker refuses to run otherwise. |
| `system_prompt_file`, `schema_file` | | Paths relative to `config/`. |

`config/supervisor_config.json`

| Key | Reference value | Meaning |
|---|---|---|
| `intake_directory` | `null` | Intake folder. When `null`, `InvoiceIntake/Incoming` below `OneDriveCommercial`. |
| `poll_interval_seconds` | 30 | Interval between scans; minimum 5. |
| `stable_check_interval_seconds`, `stable_checks` | 5, 2 | File-stability criteria. |
| `lm_studio_readiness_timeout_seconds` | 5 | Timeout of the model-listing check. |
| `prepare_timeout_seconds`, `worker_process_timeout_seconds` | 900, 2100 | Child-process timeouts. |
| `log_max_bytes`, `log_backup_count` | 5000000, 5 | Supervisor log rotation. |

## Run as a scheduled task

```powershell
.\scripts\Test-EngineEnvironment.ps1 -EngineRoot <ENGINE_ROOT>
.\scripts\Register-SupervisorTask.ps1 -EngineRoot <ENGINE_ROOT>
Start-ScheduledTask -TaskName 'DataHermetica-InvoiceEngine-Supervisor'
```

The task starts at logon, runs `pythonw.exe` without a console window under the current user with limited privileges, ignores a second start while running, and restarts up to three times at one-minute intervals. The registration script refuses to replace an existing task.

## Health checks

```powershell
Get-ScheduledTask -TaskName 'DataHermetica-InvoiceEngine-Supervisor' | Select-Object TaskName, State
Get-Content -LiteralPath (Join-Path $env:DATA_HERMETICA_INVOICE_ENGINE_ROOT 'logs\invoice-supervisor.log') -Tail 40
```

A running task shows that the supervisor is alive. It does not show that a given document completed; read the log and the result folders for that. The [Pipeline Observability Dashboard](../../pipeline-observability-dashboard) presents the same evidence per document.

## Routine procedures

| Situation | Procedure |
|---|---|
| Document in `ReviewRequired` | Read `validation-error.txt` and the preserved response. Correct the cause, then rerun with `worker.py --sha256 <sha256> --force`. |
| Model not loaded | No action on the pipeline. Files stay in the intake folder and are processed on the first scan after the model is listed. |
| Preflight failure | Disable reasoning for the loaded model in the inference server, reload the model, rerun. The document was not submitted. |
| Context budget failure | The document exceeds the configured context. Load the model with a larger context and update `context_length`, or process the document manually. The worker does not batch. |
| Same file delivered twice | No action. The second copy has the same SHA-256 and is recorded as already completed. |

Do not delete rows from the state databases or copy a file under a new name to force a retry.

## Maintenance

Wait for an active extraction to finish before stopping the task, and confirm that no child Python process remains before backing up the engine root. Back up the SQLite databases together with their `-wal` and `-shm` files. Install an upgrade into a new directory and switch the engine root; do not overwrite a running installation.

Runtime folders contain document text, model responses and identifiers. Keep them out of version control and out of shared locations.
