---
name: sku-upc-exact-reconciliation
description: Reconcile SKU, UPC, EAN, GTIN, barcode, platform IDs, and explicit product or variant group identifiers across ERP, Shopify, Nordstrom/Mirakl, Target, supplier, and partner datasets without guessing or writing online data. Use when auditing identifier mismatches, finding products missing from a platform, validating a marketplace upload list, comparing current and authoritative exports, detecting duplicates or one-to-many links, separating SPUs from variants, or preparing a review-only correction handoff. Produces exact-match matrices, conflicts, gaps, identifier-quality checks, and closed control counts; never performs fuzzy name matching or mutates ERP, Shopify, marketplace, inventory, orders, customers, or finance.
---

# SKU UPC Exact Reconciliation

When joining operational datasets, freeze grain and source clocks as well as IDs. Product, variant, warehouse, order line and immutable snapshot are not interchangeable. Unknown, absent, stale, inactive and verified zero remain separate. A current barcode match does not prove package-size equivalence or historical inventory coverage. Route stock/history interpretation to `cloud-inventory-snapshot-reconciliation`; do not import one company's warehouse/STR policy as a generic identifier rule.

## Objective

Determine which identifier relationships are proven, missing, duplicated, or
conflicting before any product-data update. Keep this Skill read-only.

Use its outputs as evidence for a separately approved update workflow such as
`shopify-product-data-safe-update`. Never convert an audit result directly into
an online write.

## Establish The Contract

Before comparing files, state:

- Authoritative source for SKU, UPC/barcode, and product grouping.
- Target system being audited.
- Exact population in scope.
- File/sheet and row-count controls.
- Column mappings and data types.
- Whether leading zeros, prefixes, or literal punctuation are meaningful.
- Explicit exclusions.

Do not assume ERP is authoritative unless the user or project rules say so.
When ERP is declared authoritative, preserve its literal SKU and UPC values.

Read [identity-rules.md](references/identity-rules.md) before matching. Read
[output-contract.md](references/output-contract.md) before delivering results.

## Prepare The Inputs

1. Preserve untouched source files.
2. Convert only the relevant sheet to UTF-8 CSV when using the bundled script.
3. Import SKU and UPC columns as text.
4. Preserve leading zeros.
5. Retain raw value, normalized comparison value, source row, title, variant,
   group ID, and platform object ID when available.
6. Record duplicate source rows instead of silently deduplicating them.

Excel display, scientific notation, and formula errors are not identity truth.
Inspect the underlying cell value and source system.

## Exact Matching Hierarchy

Use only deterministic identity:

1. Exact platform object or variant ID when reconciling the same platform.
2. Exact unique UPC/barcode.
3. Exact unique SKU.
4. Exact UPC and SKU pointing to the same row.
5. Explicit parent/group identifier for SPU or variant-group reporting.

Product title, shade name, image, vendor, size, and neighboring rows are review
evidence only. Never create an identity link from similarity.

If exact UPC and exact SKU point to different target rows, classify
`CROSS_IDENTIFIER_CONFLICT`. Do not choose one silently.

## Keep SPU Grouping Separate

SKU/UPC matching is row identity. SPU grouping is a separate relationship.

Group variants only with an explicit source such as:

- ERP parent/product ID.
- Shopify Product ID or handle from a verified export.
- Mirakl Variant Group Code.
- Approved supplier parent code.

Do not strip shade names from titles and infer that rows belong to one SPU.
When no explicit group key exists, keep rows ungrouped and mark the SPU result
unknown.

## Run The Local Reconciler

The bundled script compares one authoritative CSV with one target CSV:

```powershell
python scripts/reconcile_identifiers.py `
  --truth authoritative.csv `
  --target target.csv `
  --truth-sku "SKU" `
  --truth-upc "UPC" `
  --target-sku "Variant SKU" `
  --target-upc "Variant Barcode" `
  --truth-title "Product Name" `
  --target-title "Title" `
  --truth-group "Parent ID" `
  --target-group "Product ID" `
  --output-dir reconciliation-output
```

Optional title and group columns are retained for review but never used for
matching.

Outputs:

- `REVIEW_FIRST_identifier_reconciliation.csv`
- `REVIEW_FIRST_identifier_conflicts_and_gaps.csv`
- `AUDIT_identifier_reconciliation_summary.json`

The script makes zero network calls and zero online writes.

## Interpret Results

Use these primary states:

- `EXACT_BOTH`: unique UPC and SKU agree.
- `MATCH_BY_UPC_SKU_MISSING_TARGET`: exact unique UPC; target SKU blank.
- `MATCH_BY_UPC_SKU_CONFLICT`: exact unique UPC; SKU values disagree.
- `MATCH_BY_SKU_UPC_MISSING_TARGET`: exact unique SKU; target UPC blank.
- `MATCH_BY_SKU_UPC_CONFLICT`: exact unique SKU; UPC values disagree.
- `EXACT_UPC_ONLY`: UPC proves the row; no authoritative SKU comparison.
- `EXACT_SKU_ONLY`: SKU proves the row; no authoritative UPC comparison.
- `CROSS_IDENTIFIER_CONFLICT`: UPC and SKU point to different target rows.
- `DUPLICATE_CONFLICT`: an identifier is not unique in truth or target.
- `TARGET_REUSED_CONFLICT`: multiple truth rows would consume one target row.
- `MISSING_IDENTIFIERS`: truth row has neither usable SKU nor UPC.
- `TRUTH_ONLY`: no exact target match.
- `TARGET_ONLY`: target row was not consumed by any exact match.

Only `EXACT_BOTH` is fully reconciled without qualification. Missing or
conflicting fields require human review and a separate update approval.

## Identifier Quality

For UPC/EAN/GTIN:

- Preserve the raw string.
- Normalize only Unicode width, surrounding whitespace, spaces, and hyphens.
- Require remaining characters to be digits.
- Preserve leading zeros.
- Record length.
- Validate standard GTIN lengths 8, 12, 13, or 14 and check digit.

An invalid GTIN check digit is a data-quality flag. It does not authorize
changing the value or matching by product name.

For SKU:

- Normalize Unicode width and surrounding whitespace for comparison.
- Preserve case and punctuation by default.
- Preserve unusual prefixes and literal formats.
- Do not generate or shorten SKU values.

## Close The Counts

Report:

- Truth rows and unique truth identifiers.
- Target rows and unique target identifiers.
- Duplicate values and affected row counts.
- Exact matched pairs.
- Each conflict/missing state.
- Truth-only and target-only rows.
- Invalid-format and invalid-check-digit counts.

Required controls:

- Every truth row appears once in the truth-side matrix.
- Every target row is either used by one final exact pair or emitted once as
  `TARGET_ONLY`.
- Final exact pairs do not reuse a target row.
- Output row counts match the summary JSON.

Do not call an audit complete when controls do not close.

## Prepare A Correction Handoff

When the user later approves changes:

1. Re-read current target records.
2. Keep only rows with exact platform object IDs and authoritative source
   evidence.
3. Separate fields by owning system.
4. Create a `REVIEW_FIRST` field-level plan.
5. Route it to the correct specialist.
6. Use a safe-update Skill or platform-specific workflow.

Do not label reconciliation output `UPLOAD_THIS`. Do not include inventory,
price, MSRP, images, descriptions, or taxonomy unless those fields were
separately sourced and approved.

## Failure Rules

- **Name looks identical but identifiers differ:** keep separate.
- **One UPC appears multiple times:** classify duplicate; investigate pack,
  bundle, typo, or source duplication.
- **SKU and UPC point to different rows:** stop with cross-identifier conflict.
- **Leading zero disappeared:** return to the original cell/source and import
  as text.
- **SPU variants split into separate products:** require an explicit parent
  key before regrouping.
- **A product exists without SKU but has exact UPC:** report missing target SKU;
  do not invent it.
- **A source file is filtered or deduplicated without audit:** restore the raw
  population and rebuild controls.
- **Source systems disagree:** preserve both raw values and ask which is
  authoritative.

## Closeout

Record source files, sheet names, column mappings, authority decision, raw and
unique counts, duplicate lists, output paths, validation, limitations, and
systems not touched. Use `canonical-task-closeout` before reporting completion.
