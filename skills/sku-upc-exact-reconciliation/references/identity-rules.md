# Identifier Rules

## Authority

Authority is field-specific and must be declared.

| Field | Possible authority | Never infer from |
| --- | --- | --- |
| SKU | ERP, approved supplier master | Title, UPC sequence, neighboring row |
| UPC/EAN/GTIN | ERP, GS1-backed supplier master | Image, shade name, marketplace row |
| SPU/parent | ERP parent ID, Shopify Product ID, Mirakl VGC | Removing shade words from title |
| Platform ID | Current platform export/API | Old workbook without fresh verification |
| MSRP | ERP or approved brand pricing source | Current sale price |

One system may be authoritative for SKU/UPC while another owns customer-facing
copy or images.

## Raw And Normalized Values

Always retain:

- Raw source value.
- Normalized comparison value.
- Source filename, sheet, and row.
- Column name.
- Record title and variant for human review.

Normalization may remove surrounding whitespace and standard barcode spaces or
hyphens. It must not:

- Drop leading zeros.
- Convert scientific notation into a guessed integer.
- Uppercase or rewrite literal SKU by default.
- Remove meaningful prefixes.
- Change check digits.

## Duplicate Meaning

A duplicate identifier is not automatically an error in the source, but it is
unsafe for automatic matching.

Investigate:

- Duplicate export rows.
- Same barcode reused for a multipack or bundle.
- Parent and child rows sharing a code.
- Incorrect variant entry.
- Marketplace shadow/catalog records.

Keep every affected row visible until the business meaning is proven.

## Match Strength

| Match | Meaning |
| --- | --- |
| Exact platform object ID | Strongest within the same platform snapshot |
| Exact unique UPC | Strong cross-system variant identity |
| Exact unique SKU | Strong when both systems preserve the same seller SKU |
| UPC and SKU agree | Fully reconciled identity pair |
| Title/variant similarity | Review clue only |
| Image similarity | Review clue only |

## SPU Rules

An SPU contains variants only when an explicit parent relationship proves it.
Mixed status, missing images, or variant titles do not change identity.

Keep product grouping and variant identifier reconciliation in separate
columns so a grouping correction cannot silently rewrite SKU or UPC.

