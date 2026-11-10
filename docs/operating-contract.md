# From an instruction to an accepted result

I define five things before implementation: the intended outcome, authoritative inputs, who owns the work, which changes are authorized and observable acceptance conditions. These are operating instructions around Codex, not a modification of the model's native security controls.

## Example: prepare three product listings

| Contract item | Concrete decision |
| --- | --- |
| Input | Merchant descriptions plus the ERP's exact item identifiers |
| Owner | Catalog specialist; product-asset specialist resolves image gaps |
| Allowed output | Draft listing package and exception report |
| Separate authorization | Creating products, publishing and changing inventory |
| Acceptance | Every variant traceable to its source; unresolved fields visible; no unauthorized writes |

The source Skill supplies the detailed process. A task record tracks the current result and pending exceptions. Those are different artifacts: the Skill is reusable; the task record belongs to one execution.

## Recovery after an interrupted listing request

A real listing task lost its response after the product and media existed but before the variant image was linked. Recovery read the live record, completed only the missing steps and verified the result. It did not blindly run creation again.

The executable [recovery example](../examples/recovery.py) isolates that behavior with a fake adapter. It deliberately leaves inventory untouched and requires separate publication approval. The accompanying test also retries twice, proving this demo does not duplicate creation or upload.

In a production adapter, the saved item IDs, fresh read, operation receipt and conflict handling are essential. A local flag alone cannot prove that a remote write succeeded.
