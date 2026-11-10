# Two delivery paths, one review standard

## Website development

For Shopify, I use Liquid, CSS and JavaScript with Shopify CLI: retrieve the current theme, make scoped changes, run theme checks, push a review candidate, test desktop/mobile behavior, then promote the approved files and read them back.

For Zoho Commerce, the site uses its native templates and cart bindings. A custom interface still has to pass the exact selected variant and quantity to the existing cart. A previous fix preserved that binding and guarded against duplicate submission while a request was pending.

[cart-controller.mjs](../examples/cart-controller.mjs) is a small runnable model of that interaction contract, with four tests. It uses a fake adapter and is not the original private website code. In production, duplicate protection must also consider the service's idempotency guarantees; a disabled button alone cannot protect against retries after an uncertain network response.

| Scenario | Expected behavior | Evidence to retain |
| --- | --- | --- |
| Select a different variant | Cart receives that exact variant | Selection and resulting line item |
| Double-click while pending | One pending operation, no duplicate request | Request count and cart contents |
| Request fails | Control recovers; no false success message | Failure state and successful retry |
| Small viewport | Controls remain usable; no horizontal overflow | Mobile screenshot plus interaction check |
| Publish candidate | Only approved files reach the destination | Candidate/readback content hashes |

## Desktop software

A candidate is isolated from the daily-use copy. The release binds source, version and package hash; updates use a signed manifest and verified package. A manifest signature is not the same as Windows Authenticode signing. User data must survive an update.

Verification includes wrong signature, wrong checksum, network interruption, cancellation and version mismatch. A release is not accepted merely because a build command exits successfully. Historical releases can have documented gaps; this contract should not be read as claiming every version passed every physical-install test.

## My contribution

I turn operational needs into acceptance conditions, choose what must remain native to the platform, direct AI-assisted implementation and inspect the result. The useful evidence is the decision plus its observable behavior, with a release record as supporting traceability.
