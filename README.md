# AI-assisted commerce workflows

**Huiyin Zhang — operational judgment, reusable procedures, and software delivery.**

I use experience in commerce operations, SEO and product development to define what the AI should do, which records it should trust and how the result should be checked. Codex assists with implementation; I direct the requirements, review exceptions and make delivery decisions.

This repository makes that work inspectable: original bounded Skill modules, their supporting validators, and small executable demonstrations of two engineering patterns. It is a portfolio companion, not a production integration or the source of my employer's applications.

## Three perspectives

| Question | Evidence |
| --- | --- |
| How is an AI task organized? | [Operating contract and interrupted-task recovery](docs/operating-contract.md) |
| How does a recurring task become repeatable? | [Listing preparation](skills/shopify-product-listing-package), [exact product matching](skills/sku-upc-exact-reconciliation), [image preparation](skills/product-image-asset-pipeline) |
| What makes the resulting system dependable? | [Architecture decisions](docs/architecture.md), [release contract](docs/release-contract.md), executable tests |

## Run the examples

Python 3.10+; the two engineering examples and tests use only the standard library. No credentials or external API calls are required.

```sh
python -m examples.recovery
python -m examples.verified_sync
python -m unittest discover -s tests -v
node --test tests/cart.test.mjs
python skills/sku-upc-exact-reconciliation/scripts/reconcile_identifiers.py --truth fixtures/truth.csv --target fixtures/target.csv --truth-sku sku --truth-upc upc --target-sku sku --target-upc upc --output-dir artifacts/reconciliation
```

The reconciliation fixture intentionally includes a missing barcode and a conflict. Review outputs should expose those problems, not silently invent a match. Read the generated audit alongside the review matrix.

For the original image auditor, install `python -m pip install -r requirements.txt`; its complete input contract and CLI are inside the Skill directory. The listing validator likewise requires the declared store/category profile. Neither needs live-store access.

## What the tests establish

- Recovery after an uncertain response reuses the existing product and image.
- A preparation run cannot publish and does not change inventory.
- A downstream update transfers changed identities, not repeated unchanged records.
- An incomplete batch, duplicate source ID, revision gap or corrupted payload fails before replacing trusted data.
- Removal is represented explicitly and verified with the complete result.
- The cart model passes exact variants/quantities, prevents duplicate pending requests and recovers from a failed request. Its tests require Node.js 18+.

These are deterministic demonstrations with synthetic fixtures. They do not measure production uptime, prove a distributed transaction across remote APIs, or certify an integration. Real adapters also need authentication, rate-limit handling, concurrency control and observability.

## Source and authorship

The three Skill modules are snapshots from my working collection, including full workflows, referenced local guides and Python validators. `SKILL.md` duplicates each module's original `WORKFLOW.md` to provide a conventional entry point. Original bytes are recorded in [source-manifest.json](docs/source-manifest.json).

The engineering examples are newly written, self-contained explanations of patterns used in my projects. They use fake products and records. Private system identifiers, credentials, customer data and company application source are excluded.

References to broader Skills (for example deployment or task acceptance) describe separate boundaries; this collection does not install those modules or provide access to any business account.
