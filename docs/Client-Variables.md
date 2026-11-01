# Client deployment variables and portability review

| Variable | Audited reference deployment | New deployment action |
|---|---|---|
| Windows engine root | `H:\DataHermetica\InvoiceEngine` | Choose a local root and configure `DATA_HERMETICA_INVOICE_ENGINE_ROOT` consistently |
| OneDrive root | Work OneDrive sync location | Resolve `$env:OneDriveCommercial`; verify cloud and local sync identity |
| Intake/results | `InvoiceIntake\Incoming`; `InvoiceResults\Completed` and `ReviewRequired` | Keep Power Automate cloud folder and local sync-relative folder aligned |
| Mail trigger | Outlook V3, subject marker `DH-CE-INV` | Confirm mailbox, shared-mailbox permissions, folder and subject routing |
| Supervisor task | `DataHermetica-InvoiceEngine-Supervisor`, running at user logon in the audit | Register only after controlled acceptance; task identity must own OneDrive and LM Studio session |
| Python | Python 3.12 | Verify executable and `pythonw.exe` paths for the task account |
| PDF tools | Poppler `pdfinfo`, `pdftotext`, `pdftoppm` | Verify all commands resolve for the scheduled account |
| LM Studio API | `http://127.0.0.1:1234/v1` | Keep local to the Windows PC unless a separately reviewed architecture is approved |
| Model alias | `qwen/qwen3.8-27b` visible during audit | Record exact model file, quantization, checksum, license, vision support and runtime settings |
| Sampling | temperature 0.7; top_p 0.8; top_k 20; presence penalty 1.5 | Version changes and re-evaluate on labeled invoices |
| Context | Worker budget guard 112896; model load profile is host configuration | Verify actual loaded context and hardware capacity; guard does not load or resize model |
| API authentication | No token demonstrated in the audited setup | If authentication is enabled, ensure worker and supervisor readiness requests both send supported credentials before deployment |
| Currency and numeric formats | Schema labels price/amount as USD; invoice evidence varies | Define supported currency/decimal policy and fail closed on ambiguity |
| HTS/PGA/OGA data | Not present in the audited installation | Keep matching disabled until a complete, versioned, approved data release is available |
| Form output | No 3461/7501 mapper in the audited installation | Build and verify mappings against current CBP field dictionaries/CATAIR; require reviewer approval |
| Retention and access | Live data kept outside GitHub | Set customer-owned access, retention, backup and audit policies before broader deployment |

The audited task ran interactively at user logon. A signed-out service deployment, multi-tenant operation, automatic startup of LM Studio/model, and successful reboot recovery have not been established by this audit.
