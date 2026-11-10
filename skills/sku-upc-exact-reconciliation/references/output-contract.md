# Reconciliation Output Contract

## Matrix Columns

The reconciliation matrix should include:

- Status and match mode.
- Truth and target row numbers.
- Raw and normalized SKU/UPC values.
- Truth and target titles.
- Truth and target explicit group IDs.
- Truth and target platform IDs.
- UPC quality flags.
- Human-readable reason.
- `safe_for_automatic_write = false`.

## Required Files

- `REVIEW_FIRST_identifier_reconciliation.csv`: all truth rows plus target-only
  rows.
- `REVIEW_FIRST_identifier_conflicts_and_gaps.csv`: every state other than
  `EXACT_BOTH`.
- `AUDIT_identifier_reconciliation_summary.json`: mappings, counts, duplicate
  values, quality checks, controls, and zero-write declaration.

Do not create `UPLOAD_THIS` during reconciliation.

## Handoff Boundary

A later correction handoff must add:

- Fresh target object ID.
- Current target value.
- Proposed value.
- Authoritative source reference.
- User approval status.
- Protected fields.
- Rollback value.

That handoff belongs to a platform-specific safe-update workflow, not this
Skill.

## Status Interpretation

| State | Automatic write |
| --- | --- |
| `EXACT_BOTH` | No update needed |
| Missing target identifier | Never; review then approve |
| Identifier conflict | Never |
| Duplicate | Never |
| Truth-only | Never; investigate scope/listing |
| Target-only | Never; investigate archive/deletion/scope |
| Invalid GTIN | Never |

