# 3. Reject ambiguous numbers instead of guessing

## Context

Suppliers print numbers in different conventions. `1,234` is one thousand two hundred thirty-four in one convention and one point two three four in another. A silent choice produces a value that is wrong by a factor of one thousand and still looks valid.

## Decision

Normalization converts a printed number to canonical period notation only when its structure is unambiguous: both separators present, a single comma followed by other than three digits, or consistent three-digit grouping. A single comma followed by exactly three digits raises a validation failure. The printed expression is kept in `unit_price_raw`, the price basis in `price_basis_quantity` and `price_basis_unit`, and a canonical price that disagrees with its raw expression is rejected. Every transformation is written to `unit-price-normalization.json`.

## Consequences

- A document with an ambiguous price is routed to review instead of being published.
- Downstream consumers receive a numeric unit price with its basis preserved.
- Review volume increases for suppliers that print three-decimal prices with a comma.
