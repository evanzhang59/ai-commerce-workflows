# Asset Manifest Contract

Use UTF-8 CSV. Treat UPC and SKU as text.

## Required Columns

| Column | Rule |
|---|---|
| `asset_id` | Unique row ID. |
| `file_path` | Absolute path or path relative to `--asset-root`. |
| `product_key` | Explicit product/group identifier. |
| `asset_role` | `PRODUCT_MAIN`, `VARIANT_MAIN`, `PACKAGING`, `TEXTURE`, `LIFESTYLE`, `DETAIL`, `SWATCH`, or `MODEL`. |
| `approval_status` | `APPROVED`, `REVIEW`, or `REJECTED`. |
| `visual_review_status` | `PASS`, `PENDING`, or `FAIL`. |
| `identity_basis` | Exact evidence used to bind the image. |

At least one of `upc` or `sku` is required. `VARIANT_MAIN` also requires
`variant_key`.

## Recommended Columns

| Column | Purpose |
|---|---|
| `upc` | Exact UPC/EAN/GTIN as text. |
| `sku` | Exact SKU as text. |
| `variant_key` | Shade, option, or platform variant ID. |
| `variant_name` | Human-readable shade/option name. |
| `source_tier` | `ERP`, `BRAND_OFFICIAL`, `APPROVED_MARKETPLACE`, `SHOPIFY`, `SUPPLIER`, or `EXTERNAL_REVIEW`. |
| `source_url` | Original source URL when known. |
| `fallback_scope` | Blank, `EXACT_VARIANT`, or approved product-level fallback. |
| `media_position` | Proposed channel media order. |
| `output_filename` | Approved deterministic destination filename. |
| `proposed_alt_text` | Handoff only; this Skill does not write it online. |
| `notes` | Packaging conflicts, discontinued status, resolution caveats, or approvals. |

## Identity Basis Values

Accepted exact values:

- `UPC_EXACT`
- `SKU_EXACT`
- `UPC_AND_SKU_EXACT`
- `EXPLICIT_VARIANT_ID`
- `APPROVED_PRODUCT_LEVEL_FALLBACK`

Do not use title, filename, color appearance, folder proximity, or a model
guess as identity.

## Deterministic Filenames

Prefer a stable brand prefix plus exact identifier:

- Main: `JUD-6970000000000-01-main.jpg`
- Packaging: `JUD-6970000000000-02-packaging.jpg`
- Texture: `JUD-6970000000000-03-texture.jpg`
- Lifestyle/model: `JUD-6970000000000-04-lifestyle.jpg`
- Swatch/detail: `JUD-6970000000000-05-swatch.jpg`

Use the exact UPC when available; otherwise use an exact SKU. Do not shorten or
regenerate identifiers.

## Status Rules

An asset cannot be `READY` when:

- The file is missing or corrupt.
- Both UPC and SKU are blank.
- `VARIANT_MAIN` lacks `variant_key`.
- Identity is inferred rather than exact.
- Approval is not `APPROVED`.
- Visual review is not `PASS`.
- A required channel rule fails.

Duplicates, product-level fallbacks, nonpreferred formats, and recommended-size
misses normally require `REVIEW`; they are not silently discarded.

Read [derived-asset-acceptance](../../../references/derived-asset-acceptance.md) for the additional conditional acceptance checks. Existing permissions and preservation requirements remain.
