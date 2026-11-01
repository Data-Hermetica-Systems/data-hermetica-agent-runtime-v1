# Release status and acceptance boundaries

**Release:** Data Hermetica Invoice Engine Master 1.0.2  
**Runtime versions:** invoice engine v1.3; local supervisor v1.1  
**Release type:** extraction-prompt and LM Studio API request-configuration update.

## Changes in 1.0.2

The Python worker now explicitly sends the non-thinking sampling values from the supplied Master Settings V1 profile: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5, and repeat_penalty 1.0. The same sampling parameters are used for the readiness preflight and document-extraction request.

The production worker continues to send a strict JSON Schema through response_format. The manual Chat UI setting "Structured Output: Off" does not disable this separate API-level response_format field. The worker also retains max_tokens=32768 for invoice extraction and the existing context budget guard.

The revised system prompt adds semantic field identification, combined Quantity/Net Weight handling, explicit project mapping from item-level BOL to Shipment Number when no explicit Shipment Number exists, and stricter preservation of complete item-description text. It maintains the approved output schema and null behavior for unsupported values.

## Reference deployment status — October 31, 2026

The user confirms the automated end-to-end system has successfully processed many invoices, including PDFs containing image content. The October 31 status report confirmed the scheduled supervisor was running, the configured model alias was visible to LM Studio, and the supervisor continued scanning the intake folder.

The original v1.0.1 reference status report showed the installed preparation, worker, supervisor, extraction schema, baseline prompt, and supervisor configuration matching its release manifest. It showed installed engine_config version 2 while v1.0.1 packaged version 3; the other recorded runtime settings matched. Version 1.0.2 changes the worker payload and prompt, so its hashes are intentionally different from the prior installed runtime. This package has not been installed on the Windows reference machine.

## Evidence limits and remaining acceptance work

- The successful multi-invoice and image-bearing-PDF outcomes are user-confirmed; this release has not been run against the user's live LM Studio endpoint.
- The sampling values are taken from the supplied saved Master Settings profile. This release has not independently benchmarked alternatives or established that the same values are optimal for every invoice type.
- The manual LM Studio profile and production API path are not identical: production uses strict JSON Schema and a 32768-token max_tokens ceiling.
- Exact accuracy across fields, suppliers, page layouts, and image-only scans remains to be quantified against labeled source ground truth.
- Windows installation wrappers and this new prompt/request configuration have not been installed or acceptance-tested on the active machine.
- The local engine root must not be overwritten while the supervisor or worker is processing. Use a reviewed backup and upgrade procedure before installing any release over an existing engine.
- Schema validity and row-count checks do not prove every extracted value is source-correct.
- The historical SOP contains internal test chronology and Honeywell/Solstice invoice identifiers; review and sanitize it before external distribution.

This release packages a configuration and prompt change. It does not certify universal invoice accuracy or customer deployment readiness.
