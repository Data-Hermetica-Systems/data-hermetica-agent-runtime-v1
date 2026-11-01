# Manual LM Studio Chat Prompt

Use the following as the user/chat prompt when manually testing extraction in LM Studio. The full field contract is in [the baseline system prompt](../config/invoice_system_prompt_baseline.txt).

---

Extract invoice details and every merchandise item from all attached invoice pages.

Use the system prompt's field definitions. Read page text and images together whenever both are attached. Use page layout, labels, column headings, row alignment, item boundaries, and continuation context. Do not rely only on exact label matching.

Check specifically for:
- Combined headings such as "Qnty/Net Weight": when a row value and unit align under this heading, extract the numeric value as Quantity and the value plus unit as Net Weight.
- Bill of Lading, B/L, or BOL numbers: when associated with an item and no separate Shipment Number is provided for that item, use the BOL number for Shipment Number. Do not put it in Delivery Note.
- Complete item descriptions: retain meaningful text and ambiguous inline fragments from the item's description area rather than silently dropping or reinterpreting them.
- The difference between item-level values and invoice- or shipment-level values.
- All pages, including continuation pages and invoice instructions.

Keep unrelated invoices and attachments separate. Join item continuations only when the documents support the association. Preserve printed item order and keep repeated products as separate rows.

Return only these two sections:

A. Invoice Details

| Invoice Number | Invoice Date | Customer No. | Ship To | Bill To | Shipper Details |
| --- | --- | --- | --- | --- | --- |

B. Merchandise Items — Invoice [source invoice number]

| Item | Product Number | Material Description | Unit | Quantity | Unit Price (USD) | Total Amount (USD) | Country of Origin | Delivery Note | Gross Weight | Net Weight | Commodity Code | Shipment Number |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

For multiple invoices:
- Return one Invoice Details row per invoice.
- Return a separate Merchandise Items table for each invoice.
- Identify each merchandise table using its source invoice number.
- Preserve invoice and item order.

Use null for fields not established by the source. Do not add observations, classifications, totals rows, evidence columns, or other sections.

