# 1. Whole-document extraction without batching

## Context

A merchandise item on an invoice can continue across a page break, and header fields such as the shipment number can apply to items on later pages. Splitting a document into page batches breaks these associations and requires a merge step that can duplicate or drop items.

## Decision

The worker sends every page of a document in one request. It never batches. Before the call it estimates the input size conservatively (characters ÷ 3, plus 4,096 tokens per image), adds the maximum output and a safety margin, and compares the sum with the configured context length. If the document does not fit, the run stops with a context-budget failure. The worker also refuses to start when `allow_automatic_batching` is not `false`.

## Consequences

- Item continuity and field association are decided by the model with the full document in view.
- The largest processable document is bounded by the loaded context length.
- An oversized document becomes an explicit review case, not a partial result.
- Throughput is one document at a time.
