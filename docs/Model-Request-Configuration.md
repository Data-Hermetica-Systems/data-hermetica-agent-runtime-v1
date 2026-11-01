# Model request configuration

## Values sent by the Python worker

The worker sends these inference-time parameters on both its startup preflight request and invoice extraction request:

| Parameter | Value | Meaning in this release |
| --- | ---: | --- |
| temperature | 0.7 | Matches the user's proven non-thinking LM Studio profile. |
| top_p | 0.8 | Matches the user's saved profile. |
| top_k | 20 | Matches the user's saved profile. |
| presence_penalty | 1.5 | Matches the user's saved profile. |
| repeat_penalty | 1.0 | No repeat penalty, matching Repeat Penalty Off. |
| max_tokens | 32768 for extraction; 256 for preflight | A request-level ceiling retained for bounded response and the engine's context budget check. |
| response_format | strict JSON Schema | Keeps the production worker's machine-readable contract. |

The production request uses LM Studio's OpenAI-compatible Chat Completions endpoint. LM Studio documents top_p, top_k, temperature, presence_penalty, and repeat_penalty as supported chat-completion payload parameters. The worker explicitly sends the values above rather than relying on whichever sampling values happen to be set in the LM Studio Chat UI.

## Settings managed in LM Studio

These are model-load or application settings, not inference parameters sent by this Python worker:

- LM Studio loaded context length: 113664 tokens, matching the supplied Master Settings V1 profile.
- Engine request-budget context guard: 112896 tokens. This is not a model-load command; the lower guard leaves budget headroom within the loaded context.
- GPU Offload: 65.
- CPU Thread Pool Size: 2.
- Evaluation Batch Size: 2048.
- Physical Batch Size: 512.
- Unified KV Cache: On.
- Context Checkpoints: 32.
- Offload KV Cache to GPU Memory: On.
- Keep Model in Memory: On.
- Try mmap: On.
- Speculative Decoding: MTP, draft tokens 3.
- Flash Attention: On.
- K/V cache quantization: Off.
- Enable Thinking: Off.
- Preserve Thinking: Off.
- Chat Template: model default.
- Stop strings: none.
- Random seed: unset.

These settings must be applied to the loaded model in LM Studio. The Python worker does not control GPU offload, CPU threads, cache, context checkpoints, speculative decoding, chat template, or model loading.

## Structured output distinction

The saved LM Studio master profile says Structured Output Off for manual Chat UI use. The production worker sends an explicit JSON Schema in the API request's response_format field. That API-level schema remains enabled because the worker validates and processes structured JSON. The GUI toggle and the API request field are separate configuration paths.

## Reasoning

The worker does not send a reasoning_effort value. Keep Enable Thinking and Preserve Thinking Off for the loaded model; the worker preflight rejects a response that contains hidden reasoning or lacks valid final structured content. The saved profile's "Reasoning Effort: Extra High" custom field is not sent by this worker and must not re-enable thinking.

## Context and response-length guard

The Python configuration's context_length is a guard used by the worker's preflight token-budget calculation; it does not load or resize the model in LM Studio. The model must already be loaded with a compatible context length. The request also keeps max_tokens=32768 for extraction to retain a bounded-response and context-safety check. This is distinct from the manual Chat UI's "Limit Response Length: Off" setting. If a response reaches this ceiling, the worker rejects it instead of accepting truncated JSON.

## Profile provenance

Sampling values match the supplied LM Studio Master Settings V1 profile for Qwen 3.8-27B Q6_K in non-thinking mode. This release sends those sampling values explicitly. It does not claim to reproduce hardware/load-time values through the API.
