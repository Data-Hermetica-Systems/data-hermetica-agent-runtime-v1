## 4. Client deployment variables and portability review

| Variable | This installation | New-client action |
|---|---|---|
| Tenant/environment | User's Power Platform environment | Choose client-owned environment and record ID, region, permissions, connection owners |
| Mailbox and folder | Connected Outlook Inbox | Identify account; shared mailbox requires appropriate trigger/permissions and original mailbox setting |
| Subject marker | DH-CE-INV | Agree exact marker; configure trigger and client instructions together |
| Email body conditions | None implemented | Do not promise body routing; add separately only if specified |
| OneDrive account | Data Hermetica work account | Sign in client account; verify cloud connector and local sync refer to same drive |
| Local sync root | O: path above | Resolve `$env:OneDriveCommercial`; do not hardcode another user's organization folder |
| Intake relative path | InvoiceIntake\Incoming | Cloud and local must match; worker default/installer use this name |
| Output relative paths | InvoiceResults\Completed / ReviewRequired | Hardcoded in worker; source change required to rename |
| EngineRoot | H:\DataHermetica\InvoiceEngine | Choose existing fixed local drive; update user and current-process environment |
| Task name | DataHermetica-InvoiceEngine-Supervisor | Hardcoded installer/removal script; change both for multiple installations |
| User identity | FB | Installer captures current Windows identity; use intended runtime account |
| Python path | Program Files\Python312 | Resolve executable and adjacent pythonw.exe; new installation may differ |
| Poppler path/version | WinGet package location | Verify all three programs resolve under scheduled-user PATH |
| Model ID | qwen/qwen3.8-27b | Obtain actual API ID, model file/checksum, license and vision capability |
| GPU/runtime/context | User's model deployment | Record actual GPU/driver/backend and loaded model settings; capacity is not based on line count alone |
| API host/port | 127.0.0.1:1234 | Same-machine loopback baseline; network server is a separate deployment requiring verification |
| Authentication | No token demonstrated | Worker supports LM_STUDIO_API_TOKEN; supervisor v1.1 readiness GET does NOT send token—must fix before authenticated deployment |
| Prompt/schema | Included v1.2 versions | Version and evaluate against client's spreadsheet ground truth |
| Currency | Headers explicitly USD | No automatic FX conversion; non-USD invoices require an agreed policy/schema adjustment |
| Number/weight formats | Source-specific | Preserve source meaning; validate decimal separators, unit basis, signs and scale |
| Supplier layouts | Mainly Honeywell/Solstice | Evaluate other suppliers; completeness regex is layout-dependent |
| Polling and timeouts | 30 sec; 900 prepare; 2100 worker | Size for workload; serial processing means arrivals wait during extraction |
| Retention/backup/access | Not finalized | Decide before production; raw requests/responses contain invoice data |
| Availability | Signed-in desktop session | Windows Server/service/signed-out operation is not validated by this SOP |
| Expected item count | Test-specific | Obtain from source/spreadsheet, never infer correctness from model count alone |

A separate client instance requires isolated state, outputs, account, configuration, task name, and root. This build is not a multi-tenant service. An environment variable at user scope can select only one default engine root for that user.

