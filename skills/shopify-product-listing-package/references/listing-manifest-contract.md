# Listing Manifest Contract

## Purpose

Use one row per Shopify variant. Repeat product-level fields exactly on every
variant row; an eventual Shopify CSV adapter may collapse them according to the
current official import schema.

Save CSV as UTF-8 and preserve identifier columns as text.

## Required Columns

### Product identity and organization

- `product_key`: stable batch-local product/SPU key.
- `variant_key`: stable batch-local variant key.
- `handle`
- `title`
- `vendor`
- `category`
- `product_type`
- `status`: `draft`, `active`, or `archived`.

### Options and variant identity

- `option1_name`
- `option1_value`
- `option2_name`
- `option2_value`
- `option3_name`
- `option3_value`
- `sku`
- `barcode`

Use `Default Title` as the option value for a true single-variant product when
appropriate. Do not create fake color or size values.

### Commercial and fulfillment facts

- `price`
- `compare_at_price`
- `weight`
- `weight_unit`: `g`, `kg`, `oz`, or `lb`.

Inventory fields do not belong in this manifest.

### Content and SEO

- `body_html`
- `original_description_ref`
- `seo_title`
- `seo_description`
- `keyword_intent`
- `category_profile`
- `category_facts_json`
- `content_mode`
- `content_change_summary`
- `unresolved_content_gaps`

`category_facts_json` is a JSON object. Keys must match the selected category
profile. Values may be strings, arrays, numbers, booleans, or nested objects.

Use `NONE` for a deliberately empty gap/change summary; do not leave the field
ambiguous.

Allowed `content_mode` values:

- `OPTIMIZE_SUPPLIED`
- `SOURCE_BACKED_SUPPLEMENT`
- `SOURCE_BACKED_CREATE`

### Merchandising

- `tags`
- `collections`
- `metafields_json`

Use JSON for metafields. Do not flatten unreviewed hard facts into arbitrary
tags.

### Image handoff

- `main_image_ref`
- `main_image_status`: `READY`, `REVIEW`, or `BLOCKED`.
- `variant_image_required`: `TRUE` or `FALSE`.
- `variant_image_ref`
- `variant_image_status`: `READY`, `REVIEW`, `BLOCKED`, or `NOT_REQUIRED`.
- `alt_text`
- `image_manifest_ref`

The image reference may be a canonical local manifest key, approved direct
URL, or other explicitly declared handoff ID. It is not identity evidence by
itself.

### Provenance and workflow state

- `product_source`
- `identity_source`
- `price_source`
- `content_source`
- `supplement_sources`
- `approval_status`

Allowed approval values:

- `DRAFT`
- `REVIEW_FIRST`
- `USER_APPROVED`

This Skill does not execute `USER_APPROVED` rows; that state only records a
later review decision.

## Store Profile JSON

Use:

```json
{
  "store_name": "Example Store",
  "completeness_tier": "MODERATE",
  "seo_description_min": 120,
  "seo_description_max": 160,
  "body_text_min_chars": 120,
  "require_sku": true,
  "require_barcode": false,
  "require_weight": true,
  "require_main_image": true,
  "required_product_fields": [],
  "required_variant_fields": [],
  "category_profiles": {
    "candy": {
      "required_facts": ["ingredients", "allergens", "net_weight"],
      "important_facts": ["flavor", "texture", "storage", "country_of_origin"]
    }
  }
}
```

The supplied profile must use `MODERATE` unless the user explicitly chooses
another tier.

Missing `required_facts` blocks readiness. Missing `important_facts` creates a
warning. A new category profile may be drafted during the task, but it remains
review-first until approved.

## Product-Level Consistency

All rows sharing `product_key` must agree on:

- handle, title, vendor, category, product type, status
- body HTML, original description reference, SEO title, SEO description,
  keyword intent
- category profile and category facts
- tags, collections, metafields
- product/content sources and content-change records
- product main image and image manifest

Options, SKU, barcode, price, compare-at price, weight, and exact variant image
may differ by variant.
