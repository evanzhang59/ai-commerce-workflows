---
name: shopify-product-listing-package
description: Prepare and validate moderate-completeness, REVIEW_FIRST Shopify product listing packages for new products or product batches. Use when Codex needs to organize product and variant data, audit and optimize merchant-supplied long descriptions, fill evidence-backed content gaps, create SEO titles and meta descriptions, map approved image manifests and alt text, apply store and category profiles, detect missing or conflicting listing information, or prepare a user-reviewable CSV/XLSX before a separately approved Shopify import. The Skill adapts to beauty, apparel, candy, food, home, electronics, and new categories without hard-coding one store's section names. It never invents hard facts, changes inventory, uploads files, or writes Shopify or marketplace data.
---

# Shopify Product Listing Package

Read [source-authority-and-replay.md](references/source-authority-and-replay.md) when combining merchant sheets, official-site data and historical imported packages.

## Objective

Turn merchant, ERP, supplier, and approved official-source information into a
moderate-completeness Shopify listing package. Treat the merchant-supplied
description as the primary content draft: audit, preserve, improve, and fill
evidence-backed gaps instead of rewriting it by default.

Produce review artifacts only. Do not upload or mutate online data.

Read:

- [listing-manifest-contract.md](references/listing-manifest-contract.md) before
  creating the product/variant manifest.
- [adaptive-content-framework.md](references/adaptive-content-framework.md)
  before auditing descriptions or defining a new category profile.
- [shopify-import-guardrails.md](references/shopify-import-guardrails.md)
  before shaping a Shopify CSV.

## Establish The Listing Contract

State before processing:

- Store and target Shopify market.
- Product and variant population with control counts.
- Declared truth source for SKU, barcode, price, weight, dimensions, claims,
  ingredients/materials, and other hard facts.
- Store profile and category profiles used for this batch.
- Default completeness tier: `MODERATE`.
- Whether content is `OPTIMIZE_SUPPLIED`, `SOURCE_BACKED_SUPPLEMENT`, or the
  exceptional `SOURCE_BACKED_CREATE`.
- Image-manifest source and image audit status.
- Explicitly excluded fields and online systems.

Do not silently fall back from `MODERATE` to `MINIMUM`.

## Apply The Three Completeness Tiers

- `MINIMUM`: platform-required fields only. Use only when explicitly requested.
- `MODERATE`: required fields, legal/safety facts, purchase-decision facts,
  search/discovery fields, operational identity, and useful images. This is
  the default.
- `FULL`: deep storytelling, expanded FAQs, comparisons, and exhaustive
  supporting content. Use only when explicitly requested.

Legal, safety, allergen, compatibility, and regulated claims are never treated
as optional merely because the selected tier is lower.

## Separate Core Logic From Profiles

Keep the Skill universal. Put store tone, title patterns, SEO limits, allowed
claims, and category-specific decision fields into a task-local store profile.

For each represented category:

1. Select an approved existing category profile.
2. If none applies, inspect the supplied description, taxonomy, official
   sources, and the customer's purchase decision.
3. Draft a category profile listing required and important facts.
4. Mark it `REVIEW_FIRST` until approved.
5. Reuse it only after approval and canonical closeout.

Do not hard-code `How to Use`, `Size Guide`, `Ingredients`, or any other
category section into the universal workflow.

## Respect Source Authority

Use the source hierarchy declared for the task. Typical responsibilities:

- ERP or supplier master: SKU, UPC/barcode, MSRP, approved dimensions, weight,
  or other explicitly governed hard data.
- Merchant product sheet: intended assortment, merchandising title, supplied
  description, price decision, and launch scope.
- Brand official source: product facts, ingredients/materials, usage/care,
  compatibility, claims, and approved imagery.
- Existing Shopify export: current platform identifiers and values, but not a
  replacement for a declared upstream truth source.

Never infer a missing SKU, UPC, price, weight, ingredient, allergen, material,
certification, dimension, compatibility claim, or legal claim.

Use `sku-upc-exact-reconciliation` when identifiers disagree. Use
`product-image-asset-pipeline` for image identity and quality. A future write
must use `shopify-product-data-safe-update`.

## Audit And Optimize Supplied Content

1. Preserve the original description and source reference.
2. Extract facts and identify repetition, poor translation, weak hierarchy,
   missing purchase-decision facts, and unsupported claims.
3. Retain substantive merchant information unless it is demonstrably
   incorrect, duplicated, or disallowed.
4. Supplement only from approved evidence.
5. Record additions, removals, material rewrites, sources, and unresolved
   gaps.
6. Arrange content according to the approved category profile.
7. Put the clearest purchase-decision summary first.
8. Generate SEO title, meta description, and keyword intent from verified
   content rather than mechanically truncating the long description.

Default to conservative optimization. Do not replace a complete merchant
description with generic marketing copy.

## Build And Validate The Manifest

Create a UTF-8 CSV following
[listing-manifest-contract.md](references/listing-manifest-contract.md).
Preserve SKU and barcode as text.

Run:

```powershell
python scripts/validate_listing_manifest.py `
  --manifest listing-manifest.csv `
  --profile store-profile.json `
  --output-dir listing-audit
```

The validator is local and read-only. It creates:

- `REVIEW_FIRST_listing_normalized.csv`
- `REVIEW_FIRST_listing_gaps.csv`
- `AUDIT_listing_summary.json`

It validates identifiers, variant uniqueness, product-level consistency,
prices, compare-at prices, weights, options, SEO length, source evidence,
content mode, category facts, image status, alt text, prohibited inventory
fields, and control-count closure.

## Interpret Readiness

- `READY`: meets the approved moderate profile with no unresolved blockers or
  warnings.
- `READY_WITH_WARNINGS`: import preparation may continue, but non-critical
  useful information remains missing or under review.
- `BLOCKED`: hard identity, price, legal/safety, required category fact,
  product/variant structure, source, or image requirement is missing or
  conflicting.

Never rename a review or blocked file `UPLOAD_THIS`.

## Prepare Review Deliverables

Provide:

1. `REVIEW_FIRST` product/variant workbook or CSV.
2. Original and optimized descriptions.
3. SEO title, meta description, and keyword intent.
4. Source register.
5. Content-change register.
6. Missing/conflict report.
7. Image-manifest reference and image readiness.
8. Machine-readable audit with control counts.

Use the current store export or official Shopify template when creating the
eventual import shape. Do not assume that one historical CSV schema is safe
for another store.

For a large batch, stop at the reviewed CSV/XLSX and let the user upload unless
the user separately authorizes another method. For roughly 1-10 products,
individual Admin entry may be appropriate, but it is still a separate write
task.

## Hard Boundaries

- Do not write Shopify, ERP, Nordstrom/Mirakl, Target, Dropbox, or another
  platform.
- Do not change or populate inventory.
- Do not create identifiers or hard facts from names, images, or sequence.
- Do not convert a warning into a fact.
- Do not use a Shopify CDN URL when a partner workflow requires separately
  hosted direct image URLs.
- Do not treat an image filename as proof of variant identity.
- Do not overwrite the merchant's source file.
- Do not label an artifact upload-ready before user approval and import-shape
  validation.

## Closeout

Record the listing scope, completeness tier, truth sources, store/category
profiles, control counts, content changes, unresolved gaps, image audit,
artifacts, validations, and systems not touched. Use
`canonical-task-closeout` before reporting completion.
