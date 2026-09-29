# experiments/

One directory per registered experiment (`EXP-xxx/metadata.yaml`), validated by
`brats_uncertainty.experiments.metadata`. Status lifecycle:
PLANNED -> AUTHORIZED -> RUNNING -> COMPLETED | FAILED, and any of these -> INVALIDATED.
An experiment cannot be AUTHORIZED without an owner authorization record, and cannot be
COMPLETED without full provenance and output hashes.

| ID | Status | Description |
|---|---|---|
| EXP-001 | PLANNED (not authorized, not run) | Compute pilot; see docs/experiments/EXP-001_COMPUTE_PILOT_SPEC.md |

`evaluation_ledger.jsonl` (created at the first tagged evaluation) records every
test-set and external evaluation (SR4).
