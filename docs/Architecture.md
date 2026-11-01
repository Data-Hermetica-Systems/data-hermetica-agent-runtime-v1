## 3. Complete pipeline and physical paths

```mermaid
flowchart TD
  A["Outlook Inbox: subject contains DH-CE-INV"] --> B["Power Automate: attachment loop and condition"]
  B --> C["Get Attachment V2 → OneDrive Create file<br/>/InvoiceIntake/Incoming"]
  C --> D["OneDrive local sync<br/>O:\\DH-OneDrive\\OneDrive - Data Hermetica\\InvoiceIntake\\Incoming"]
  D --> E["Scheduled supervisor<br/>H:\\DataHermetica\\InvoiceEngine\\app\\invoice_supervisor.py"]
  E --> F{"API model visible and input stable?"}
  F -->|No| E
  F -->|Yes| G["SHA-256 and preparation<br/>app\\invoice_prepare.py"]
  G --> H{"Per-page text candidate?"}
  H -->|Yes| I["UTF-8 layout text<br/>work\\prepared\\SHA256\\page-NNNN.txt"]
  H -->|No| J["180 DPI PNG via Poppler<br/>work\\prepared\\SHA256\\page-NNNN.png"]
  I --> K["manifest.json + complete document payload<br/>app\\invoice_worker.py"]
  J --> K
  K --> L["Budget gate + small runtime probe<br/>logs\\SHA256.runtime-preflight.json"]
  L --> M["One full document extraction request<br/>http://127.0.0.1:1234/v1/chat/completions"]
  M --> N["Raw response<br/>work\\responses\\SHA256.response.json"]
  N --> O{"Normalize and validate"}
  O -->|Pass| P["Local outputs<br/>work\\output_staging\\SHA256"]
  P --> Q["OneDrive local results<br/>O:\\DH-OneDrive\\OneDrive - Data Hermetica\\InvoiceResults\\Completed\\SHA256"]
  O -->|Review| R["state\\jobs.db + logs<br/>Some validation failures publish InvoiceResults\\ReviewRequired\\SHA256"]
  E -.-> S["State and lock<br/>state\\supervisor.db; state\\supervisor.lock"]
  K -.-> T["Job state<br/>state\\jobs.db"]
```

Paths below `app`, `work`, `logs`, and `state` in the diagram are relative to `H:\DataHermetica\InvoiceEngine`. SHA256 is a runtime content hash, not a literal folder name to create. The active invoice model receives page text extracted by Poppler or rendered page images directly; there is no OCR stage. The model performs the variable-layout invoice reading.

“One extraction request” means one complete-document extraction call. A separate tiny JSON readiness inference also runs beforehand. Do not describe this as exactly one HTTP request total.

| Directory/file | Role |
|---|---|
| `app\invoice_prepare.py` | Stable source hash; per-page text/image preparation |
| `app\invoice_worker.py` | Assemble payload, preflight, extract, normalize, validate, publish |
| `app\invoice_upgrade_output.py` | Migrate previous output without inference |
| `app\invoice_supervisor.py` | Poll Incoming and orchestrate preparation/worker |
| `config\engine_config.json` | Model, API, budget, prompt/schema filenames |
| `config\invoice_system_prompt_baseline.txt` | Approved extraction definitions |
| `config\invoice_extraction_schema.json` | JSON output contract |
| `config\invoice_supervisor_config.json` | Polling, stability, timeouts, logs |
| `work\prepared\<hash>\manifest.json` | Page routing and source identity |
| `work\requests\<hash>.request.json` | Request audit; image bytes omitted, text retained |
| `work\responses\<hash>.response.json` | Original API response |
| `work\output_staging\<hash>` | extraction.json, extraction.md, invoice CSV, validation.json, unit-price-normalization.json |
| `state\jobs.db` | Worker SQLite job state |
| `state\supervisor.db` | Supervisor observations and document state; WAL mode |
| `state\supervisor.lock` | OS-held single-process lock |
| `logs\invoice-supervisor.log` | Rotating supervisor log |
| `logs\<hash>.runtime-preflight.json` | Successful runtime probe response |
| `logs\<hash>.configuration-error.txt` | Context or runtime configuration rejection |
| `logs\<hash>.failure.log` | Worker exception traceback |
| `backup\supervisor_before_install_<timestamp>` | Installer backup of replaced supervisor/config |
| `quarantine` | Earlier reserved directory; no automatic quarantine movement demonstrated |
| `tests` | Unit-price parser tests from v1.2 package |

Do not use the old top-level `prepared` directory. Current prepared files belong under `work\prepared`.

