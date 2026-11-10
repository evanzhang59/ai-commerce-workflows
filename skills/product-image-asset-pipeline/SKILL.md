---
name: product-image-asset-pipeline
description: Audit, reconcile, classify, and safely stage product image assets for Shopify, Nordstrom/Mirakl, Target, supplier, and partner deliverables without guessing variant identity or writing online data. Use when Codex needs to match images to exact SKU/UPC/variant records, find missing or duplicate images, validate white-background main images, check dimensions/ratio/RGB/alpha/file size, preserve Shopify media order, prepare channel-specific filenames and folders, produce image manifests or gap reports, or verify assets before a separately approved Dropbox upload or product update. The first version never edits source pixels, uploads files, or changes Shopify, marketplaces, inventory, orders, customers, or finance.
---

# Product Image Asset Pipeline

## Objective

Turn a mixed product-image folder and an exact product/variant manifest into a
reviewable asset register, channel QA report, and byte-identical staging
package. Keep source images untouched and online systems unchanged.

Read [channel-image-rules.md](references/channel-image-rules.md) before applying
channel rules. Read
[asset-manifest-contract.md](references/asset-manifest-contract.md) before
creating the input manifest.
Read [acquisition-and-recovery-handoff.md](references/acquisition-and-recovery-handoff.md) for supplier naming, swatches, import failures and gallery recovery.

## Establish The Contract

Before touching files, state:

- Source folder and immutable-original boundary.
- Product/variant population and control count.
- Authority for SKU, UPC, product key, variant key, and image selection.
- Target channel: `shopify`, `nordstrom`, `target`, or `generic`.
- Allowed roles: product main, variant main, packaging, texture, lifestyle,
  detail, swatch, or model.
- Whether the task is audit-only or includes local staging.
- Explicit exclusions and online systems that must remain untouched.

Do not infer image identity from title similarity, folder adjacency, image
color, or filename order. Use an exact UPC, exact SKU, exact platform variant
ID, or an explicitly approved product-level fallback.

## Preserve The Sources

1. Keep supplier, official-site, Shopify, Dropbox, or marketplace downloads in
   an immutable source directory.
2. Never overwrite, crop, upscale, remove backgrounds, add canvas, sharpen, or
   recompress a source file in this Skill.
3. Put audit outputs and staging copies in new dated directories.
4. Record source URL and source tier when known.
5. Keep ambiguous or low-quality images in `REVIEW`; do not improve their
   status by enlarging the canvas.

## Build The Manifest

Create a UTF-8 CSV following
[asset-manifest-contract.md](references/asset-manifest-contract.md). Preserve
SKU and UPC as text. Every row must identify one physical file and include at
least one exact product identifier.

For `VARIANT_MAIN`, require:

- `variant_key`.
- Exact identity evidence such as `UPC_EXACT`, `SKU_EXACT`,
  `UPC_AND_SKU_EXACT`, or `EXPLICIT_VARIANT_ID`.
- An approved white-background image for that exact variant.

Product-level fallback is allowed only when the user or approved source states
that the same image legitimately represents multiple UPCs or variants. Record
that decision; never hide it.

## Run The Audit

Use the bundled read-only auditor:

```powershell
python scripts/audit_image_assets.py `
  --manifest image-manifest.csv `
  --asset-root source-original `
  --channel nordstrom `
  --output-dir image-audit
```

It creates:

- `REVIEW_FIRST_image_asset_audit.csv`
- `REVIEW_FIRST_image_asset_gaps.csv`
- `AUDIT_image_asset_summary.json`

The auditor reads images only. It records file hashes, format, dimensions,
ratio, mode, alpha, edge-white score, file size, exact duplicate groups,
perceptual duplicate candidates, channel findings, and final status.

Treat perceptual duplicates as review signals, not proof of identity.

## Interpret Status

- `READY`: exact identity, approved visual review, valid file, and required
  channel checks pass.
- `REVIEW`: usable evidence exists, but quality, duplicate, source, fallback,
  or non-blocking channel questions remain.
- `BLOCKED`: missing file, corrupt image, missing exact identity, failed
  required dimensions/background/mode, or unapproved visual review.

Do not rename `REVIEW` or `BLOCKED` assets as upload-ready.

## Stage Ready Assets

After reviewing the audit, copy only `READY` rows into a clean local package:

```powershell
python scripts/stage_ready_assets.py `
  --audit image-audit/REVIEW_FIRST_image_asset_audit.csv `
  --output-dir staged-ready
```

The staging script:

- Copies bytes exactly; it does not modify image pixels.
- Refuses to overwrite existing files.
- Uses the audited deterministic filename.
- Verifies source and staged SHA-256 values match.
- Produces `STAGED_image_asset_manifest.csv` and
  `STAGED_image_asset_summary.json`.

Staging is not approval to upload. Dropbox, Shopify, Nordstrom/Mirakl, Target,
or partner writes require separate explicit authorization and a
platform-specific workflow.

## Maintain Media Order

For Shopify product media:

1. Put the approved default/exact white-background product image first.
2. Put exact texture or deterministic supporting media second when available.
3. Follow with packaging, texture, lifestyle/model, detail, and swatch media.
4. Bind each selectable color variant to its exact white-background
   `VARIANT_MAIN`.
5. For a one-variant `Default Title` product without a variant-image selector,
   keep the approved white main at product-media position 1.

Do not reorder existing Shopify media unless the user approved that exact
scope.

For Nordstrom and Target, use channel rules in the reference and prepare
separate derivatives or packages outside this first-version Skill. Never use a
Shopify CDN URL as the final partner image URL when the approved workflow
requires Dropbox-hosted files.

## Required QA

Close all controls:

- Manifest rows and unique physical files.
- Unique UPC/SKU/variant counts.
- READY, REVIEW, BLOCKED totals.
- Missing and corrupt files.
- Exact and perceptual duplicate groups.
- Main-image channel pass counts.
- Variant-main exact-binding counts.
- Source hashes and staged hashes.
- Staged rows equal READY rows.
- Original file modification count equals zero.

Visually inspect contact sheets or representative files before approving a
large batch. Automated white-edge or duplicate signals do not replace human
review for logos, text, watermarks, packaging mismatch, model crops, or
incorrect shades.

## Failure Rules

- **Similar filename but no exact identifier:** leave unbound.
- **Exact binary reused across different UPCs:** flag for review unless an
  approved product-level fallback explains it.
- **Low-resolution image placed on a large canvas:** keep the original
  resolution warning; do not call it high resolution.
- **Wrong variant or packaging generation:** block the asset.
- **Folder-level Dropbox link:** reject it as a final image URL.
- **Shopify CDN in a partner workbook:** replace only after a separately
  approved local asset and per-file direct URL workflow.
- **Source image has text or watermark:** require visual review; do not try to
  remove it automatically.
- **Need background removal, expansion, retouching, or image generation:** use
  an image-editing workflow with separate approval and preserve the original.

## Closeout

Record source roots, manifest, authority decision, channel, control counts,
audit/staging paths, hash verification, visual-review limitations, and systems
not touched. Use `canonical-task-closeout` before reporting completion.
