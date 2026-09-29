# Protocol amendments and administrative entries

**There are no amendments to protocol v1.0.**

Rules (protocol v1.0, "Freeze rule" and §25):

1. The frozen file `docs/research/FINAL_RESEARCH_PROTOCOL_v1.0.md` is never edited in place.
2. Any **design change** requires a logged amendment recording the date, version, sections, change, reason and whether any test data had been seen. The owner must approve it. No change is allowed after any test-set evaluation.
3. **Execution records** from gates B–D are appended as logged **administrative entries**. They include hashes, counts, the computed T_screen value, patient groups, split hashes and EXP-001 measurements, and do not change the pre-registered design.
4. Each amendment or administrative entry is a separate file in this directory: `YYYY-MM-DD_<gate-or-topic>.md`. Its effect on the machine-readable mirror (`configs/protocol/`) and on `docs/project_status.yaml` is committed in the same change.

| Date | Type | Gate / sections | File | Test data seen? |
|---|---|---|---|---|
| — | — | — | *(none)* | — |
