# Channel Image Rules

## Common Identity Rules

- Match by exact UPC, exact SKU, explicit platform variant ID, or approved
  product/variant mapping.
- Preserve original files and source URLs.
- Never infer a shade from color appearance, title similarity, file order, or
  neighboring folders.
- Treat logos, text, watermarks, packaging mismatch, model crops, and
  promotional layouts as human visual-review items.

## Shopify

These are Skin Note operating rules, not universal Shopify platform limits:

- Product media position 1: approved white-background complete product image,
  normally the default or representative variant.
- Product media position 2: exact texture or deterministic supporting image
  when available.
- Later media: packaging, texture, lifestyle/model, detail, swatch, then other
  exact variant mains as appropriate.
- Every selectable color variant must bind to its exact white-background
  variant image.
- A one-variant `Default Title` product may not expose a variant-image selector;
  keep its approved white main at product-media position 1.
- Preserve current media order unless reordering is explicitly approved.
- Alt text belongs to the later product-listing/content workflow; this Skill
  may retain a proposed alt-text field but does not write it online.

Shopify has no project-wide fixed 2:3 requirement. Do not force square Shopify
assets into a marketplace canvas in the source folder.

## Nordstrom / Mirakl

Verified supplied guideline:

- Portrait/vertical only; Nordstrom uses a 2:3 crop.
- Product background: RGB 255 white.
- JPG preferred; flattened TIF, PNG, and PSD are accepted by the guideline.
- Recommended: 2600 x 4000 pixels or larger.
- Minimum: 1300 x 2000 pixels; exception only and not guaranteed approval.
- Photographs only; no CAD renderings or illustrations.
- No logos, text, or watermarks.
- Post-production must already be complete.
- File naming should be deterministic and traceable to the item/color.

Project implementation accepts 2600 x 4000 as the proven ready canvas. A large
white canvas does not repair low-resolution source pixels.

## Target Project Policy

The approved Judydoll Target image package reused the Nordstrom-ready technical
profile:

- RGB JPG.
- 2600 x 4000.
- Portrait 2:3 family.
- White corners/background.
- Product-only primary image.
- No model, lifestyle, swatch-only, promotional text, or decorative background
  as the primary image.
- One deterministic file per UPC.

Final partner URLs were per-file Dropbox direct-render links. Shopify CDN,
Mirakl-hosted, folder-level, blank, and unvalidated links were prohibited in
the final image column.

This is a proven project policy, not a claim about every Target program.
Confirm a newer partner guideline when supplied.

## Generic Partner Package

When no target-system guide exists:

- Preserve the original.
- Prefer a clean white-background main image.
- Keep exact variant identity.
- Use deterministic filenames.
- Report dimensions, format, color mode, alpha, file size, and duplicates.
- Do not invent technical requirements.
- Mark channel compliance `REVIEW` until the receiving partner confirms rules.

## URL Handoff

This Skill does not upload files or produce final online URLs.

When a separately approved Dropbox workflow is used:

- Upload individual files to a clean channel folder.
- Obtain one share link per file, never a folder URL.
- Convert and validate the approved direct-render form.
- Confirm HTTP success and image MIME type.
- Require zero forbidden domains and zero blanks before workbook replacement.
- Change only the approved image URL field and compare all non-image fields.
