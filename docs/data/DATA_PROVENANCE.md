# Data provenance

**Status: no provenance records exist yet, because no data have been acquired.** Nothing below may be filled in by hand. Every value is produced by the code from the actual files at the stated gate.

## What will be recorded, and when

| Gate | Record | Produced by | Committed? |
|---|---|---|---|
| B1 | Approved data route and evidence reference (e.g. the TCIA reply) | owner | Yes (reference only) |
| B2 | Acquisition date, source, route, acquirer | `DatasetProvenance` | Yes |
| B3 | SHA-256 of `BraTS2021_MappingToTCIA.xlsx` as used | `sha256_file` | Hash only |
| B4 | SHA-256 of `UCSF-PDGM-metadata_v5.csv` as used | `sha256_file` | Hash only |
| B5 | Data manifest: case ID, relative path, size and SHA-256 per file; manifest hash | `build-manifest` | Manifest summary and hash; per-file manifest only if the licence permits |
| B6 | Counts re-derived from the hashed crosswalk (expected 1,251 / 511 / 740; SR3 on mismatch) | `derive_cohorts` | Yes |
| B7 | T_screen record: value, positive-control Dice values, label hashes | `compute_t_screen` | Yes |
| B7–B9 | Flagged pair IDs, review CSV (IDs, decision, reviewer, timestamp, reason), grouping audit | `grouping/*` | Yes (IDs only) |
| B10–B12 | Split CSV (IDs, group IDs, partitions), strata counts, SHA-256 hashes | `splitting/split.py` | Yes (IDs only) |
| C1–C3 | BraTS-Africa label/sequence verification and eligible count | owner + code | Yes |
| C4 | HOI patient grouping (same §6.2 rule and T_screen value) | `grouping/*` | Yes (IDs only) |

Each record is also appended to protocol §25 as an **administrative entry** via [protocol-amendments/](../research/protocol-amendments/README.md). Such entries do not change the design.

## Provenance guarantees built into the code

- Hashes come only from bytes read from disk (`utils/hashing.py`). No API accepts a typed hash as a measurement.
- `DatasetProvenance.validate()` rejects empty fields and malformed hashes.
- Every result artifact carries the experiment ID, git commit, config hash, protocol hash and input hashes (`results/artifacts.py`). Tampering is detected by a content hash.
- Synthetic test data are labelled `synthetic: true` and refused in `results/` and by the website export.
