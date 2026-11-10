# Shopify Import Guardrails

## Review Before Conversion

The normalized listing manifest is not automatically a Shopify upload file.
Obtain a current Shopify export or official template for the target store
before converting columns.

## Variant Safety

- Preserve one exact row per intended variant.
- Keep option tuples unique inside a product.
- Preserve SKU and barcode as text.
- Do not split or merge variants from title similarity.
- Do not introduce a new option to fix missing data.
- Keep product-level values consistent before adapting them to Shopify's row
  repetition rules.

## Field Safety

- Do not include inventory quantities or location inventory.
- Do not use blank import cells to clear existing data unless explicitly
  approved.
- Do not assume dimensions are native Shopify CSV fields; use approved
  metafields or a separate fulfillment system when required.
- Validate price and compare-at price at variant level.
- Use the store's current SEO-title behavior to avoid duplicated vendor/store
  text.
- Keep Body HTML and SEO Description separate.

## Image Safety

- Use an approved image manifest.
- Preserve the approved main-image order.
- Bind variant images only by exact identity.
- Do not upload partner-only derivatives into Shopify unless approved.
- Do not use an image filename as proof of SKU/UPC identity.

## Approval States

- `REVIEW_FIRST`: safe for human review, not import.
- `USER_APPROVED`: content/data accepted, but import shape and current-state
  checks may still be outstanding.
- `UPLOAD_THIS`: may be used only after the exact Shopify template shape,
  control counts, protected fields, and user approval are complete.

Bulk uploads normally remain user-operated. Direct Admin/API writes require a
separate `shopify-product-data-safe-update` workflow.
