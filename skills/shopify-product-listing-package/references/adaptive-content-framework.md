# Adaptive Content Framework

## Principle

Use the merchant's supplied description as the primary draft. The job is to
check completeness, preserve verified facts, improve readability, remove
repetition, and add only evidence-backed missing information.

## Universal Moderate Structure

Every optimized description should provide:

1. A concise purchase-decision summary.
2. Verified differentiators or benefits.
3. Category-specific decision information.
4. Necessary safety, care, compatibility, or regulatory information.

Section labels and HTML hierarchy belong to the store/category profile, not
the universal Skill.

## Category Discovery

For an unrecognized category:

1. Identify what a customer must know before buying.
2. Separate legal/safety facts from optional merchandising details.
3. Inspect the merchant description for coverage.
4. Check approved official sources for missing facts.
5. Draft `required_facts` and `important_facts`.
6. Ask for approval only when a business or compliance decision cannot be
   derived from evidence.
7. Save the approved profile for reuse during canonical closeout.

## Example Profiles

Examples are starting points, not universal mandates.

### Beauty

- Required depends on product: usage, shade/size, ingredients when available,
  warnings or suitability.
- Important: finish, texture, skin type, coverage, key ingredients.

### Apparel

- Required: material, size/fit, care; safety or composition disclosures where
  applicable.
- Important: silhouette, stretch, closure, model measurements, styling.

### Candy and food

- Required: ingredients, allergens, net weight, applicable warnings.
- Important: flavor, texture, storage, serving, origin, dietary attributes.
- Never infer vegan, gluten-free, halal, kosher, organic, or allergen-free
  status.

### Home

- Required: material, dimensions, care/assembly, safety where applicable.
- Important: finish, room/use case, package contents.

### Electronics

- Required: specifications, compatibility, power, package contents, safety,
  warranty source.
- Important: use cases, connectivity, dimensions, setup.

## Content Change Register

For each product record:

- Original description location/hash.
- Optimized description.
- Facts added and their sources.
- Facts removed and why.
- Material rewrites.
- Unsupported claims removed or flagged.
- Remaining gaps.

Use `OPTIMIZE_SUPPLIED` when the supplied description is substantially
complete. Use `SOURCE_BACKED_SUPPLEMENT` when verified facts are added. Use
`SOURCE_BACKED_CREATE` only when the merchant did not provide usable content.

## SEO Derivation

Create SEO fields from verified listing information:

- SEO title: product/brand/category intent according to the store profile.
- Meta description: natural summary of product identity, strongest verified
  differentiator, and search intent within the configured length.
- Keyword intent: a short internal planning field, not keyword stuffing and
  not automatically a Shopify meta-keywords field.

Do not mechanically cut the long description at a character limit. Do not
repeat one generic description across products.
