# Security

## Assets

- Source documents and the data extracted from them.
- Request audits and raw model responses, which contain document text.
- The integrity of published results.

## Threats and controls

| Threat | Control | Enforced by |
|---|---|---|
| Unintended documents enter the pipeline | The flow starts only for email carrying the private subject code and accepts only non-inline PDF, PNG, JPG and JPEG attachments. | Power Automate flow |
| Attachment name collision or overwrite | Every saved file is prefixed with a new GUID. | Power Automate flow |
| Partially synced file is processed | Size and modification time must hold across consecutive checks; the file is re-checked after hashing. | `supervisor.py`, `prepare.py` |
| Duplicate processing | Documents are identified by SHA-256. A single-instance OS lock prevents overlapping supervisors. | `supervisor.py`, `worker.py` |
| Instructions embedded in a document steer the model | The prompt defines document text as source content. The response must match a strict JSON Schema. The worker executes nothing from the response. | prompt, `worker.py` |
| Model fabricates or drops line items | Printed item numbers in the source text are compared with extracted rows. Duplicate item numbers are rejected. | `worker.py` |
| Model returns values outside the contract | Extra properties, wrong types and non-canonical prices fail schema validation. | `worker.py` |
| Numeric misreading by normalization | Ambiguous comma notation is rejected. A price that disagrees with its raw expression is rejected. | `worker.py` |
| Hidden reasoning consumes the output budget or alters behaviour | A preflight must return zero reasoning tokens before each extraction. | `worker.py` |
| Silent truncation | The context budget is checked before the call. A response that ends at the token limit is rejected. | `worker.py` |
| Document content sent to an external service | The reference configuration uses a loopback model endpoint. The flow moves files only. | configuration |
| Credentials in source control | The repository contains no credentials. The optional endpoint token is read from an environment variable. | repository policy |
| Document content in audit files | Page images are replaced by hash and size in the request audit. | `worker.py` |

## Not enforced by this software

- **Field accuracy.** Validation establishes structure and consistency. A value can pass validation and still differ from the source. Human review against the source document is required before any use in an entry.
- **Network egress.** The software does not block outbound connections. Pointing `lm_studio_base_url` at a non-local host sends document content to that host.
- **Endpoint authentication.** The model endpoint is unauthenticated unless the inference server is configured with a token.
- **Encryption at rest.** Runtime folders are protected by operating-system access control and disk encryption, not by the application.
- **Malware scanning.** Attachments are not scanned by the pipeline. PDF parsing is delegated to Poppler; keep it current.
- **Access control on results.** Published results inherit the permissions of the OneDrive folders.

## Data handling

Request audits contain page text, and responses contain extracted data. Both are runtime data under `work/`, which is excluded from version control together with `state/` and `logs/`. Sample material in this repository is fictional.
