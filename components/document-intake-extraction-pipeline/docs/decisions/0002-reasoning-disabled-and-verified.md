# 2. Reasoning disabled and verified by a preflight

## Context

Reasoning-capable models can emit reasoning tokens before the final answer. In a structured-extraction call this consumes the completion budget, can leave the final content empty or truncated, and makes run time unpredictable. Whether reasoning is active is a property of how the model is loaded in the inference server, outside the request.

## Decision

Before each extraction the worker sends a minimal structured request with the same sampling parameters. The preflight passes only if the response contains final content equal to the expected object, zero reasoning tokens and no reasoning text. On failure the document is not submitted and the job is marked for review with instructions to disable reasoning and reload the model. The worker refuses to start when `require_reasoning_disabled` is not `true`. The preflight response is retained per document.

## Consequences

- A misconfigured model is detected before document content is sent.
- Every extraction has recorded evidence of the runtime state it ran under.
- Each document costs one additional short request.
