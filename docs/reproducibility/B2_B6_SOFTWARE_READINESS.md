# B2–B6 software readiness report (adversarial audit)

| Field | Value |
|---|---|
| Date | 2026-09-30 |
| Protocol | v1.0, frozen, tag `protocol-v1.0` (tag object `0f46a83`, commit `4ef7ef7`), unchanged |
| Scope | Software only. No data were downloaded, acquired or processed; no real B2–B6 run; no B7, split, training or analysis. |
| Verdict | **Software B2–B6 infrastructure is READY for authorized real-data execution.** Real-data execution remains **blocked** until B1 authorization is actually established. |

## 1. Gate status at the time of this report

| Gate | Status |
|---|---|
| B1 | **PENDING** (TCIA inquiry prepared, not sent; no B1 evidence exists) |
| B2, B3, B4, B5, B6 | **LOCKED** |
| B7–B12 | **LOCKED** |
| data | authorization PENDING, acquired false |
| training | NOT_STARTED |
| evaluation | internal NOT_STARTED, external NOT_STARTED |
| results | UNAVAILABLE |
| B6 counts | EXPECTED_BY_PROTOCOL (targets 1,251 / 511 / 740; not verified from any source) |

## 2. Defects found and fixed in this audit

| # | Defect | Risk | Fix |
|---|---|---|---|
| 1 | Gate evidence was checked only for `gate` and `synthetic: false` | a hand-written two-line JSON, or a record from a dirty or uncommitted checkout, could pass B2–B6 | `data/evidence.py` re-validates each evidence record in full (schema, fingerprint, `data_class`, clean existing commit, frozen protocol hash) and checks the links between gates (B5 → B2/B3/B4; B6 → B3 fingerprint and crosswalk SHA-256) |
| 2 | Evidence could be git-ignored (e.g. `data/manifests/`) or outside the repository | a gate could close on uncommitted or private files | evidence must be a safe repository-relative path, not git-ignored, and in the git index |
| 3 | B1 accepted any file as evidence | documentation could have been used as authorization | B1 evidence must be `docs/data/B1_EVIDENCE_<date>.md`, declaring exactly one evidence type and the same approved route; the B1 record, the inquiry and the template are rejected |
| 4 | FAILED → AUTHORIZED was allowed with no record; FAILED/BLOCKED needed no evidence | a failed gate could be silently re-run | FAILED → BLOCKED only; transitions into FAILED or BLOCKED, and out of BLOCKED, require an evidence document |
| 5 | B5 did not verify the B3/B4 records | a manifest could include a metadata file changed after hashing | real B5 requires both B3 and B4 records; each file must still match its recorded hash, and the manifest carries `metadata_records` fingerprints |
| 6 | Synthetic B6 success was labelled VERIFIED_FROM_SOURCE | synthetic counts could be confused with verification | synthetic success is `SYNTHETIC_TEST_ONLY`; VERIFIED_FROM_SOURCE is only possible for REAL_RESEARCH_DATA |
| 7 | No explicit data class | reliance on a boolean only | `data_class` (`SYNTHETIC_TEST_DATA` / `REAL_RESEARCH_DATA`) is in every record and manifest, covered by the fingerprint and checked on read |
| 8 | Transition writer did not validate the current state, compared only part of the re-parsed file, and wrote non-atomically | an inconsistent state could propagate or be corrupted | the current state is validated first; the full re-parsed mapping must equal the validated result; writes are atomic |
| 9 | Symbolic links were not rejected; one path crashed with `ValueError` | reads outside the permitted root | links are refused in deliveries, storage inventories, data trees, synthetic trees and stage inputs |
| 10 | `/abs` was not treated as absolute on Windows | path escape on one platform | a shared platform-independent `is_safe_relpath` is used everywhere |
| 11 | Real storage could be placed in a tracked repository folder | acquired data could be committed | real storage inside the repository is only allowed under the git-ignored `data/` |
| 12 | A fixed test clock was accepted in real mode | fabricated execution timestamps | a custom clock is refused unless the run is SYNTHETIC_TEST_DATA |
| 13 | Real-mode stages checked inputs before the gate | an unauthorized call could fail with a data error rather than the gate error | real mode checks the gate first |
| 14 | Malformed status entries raised KeyError | unclear failures | malformed or partial status input raises ConfigError |
| 15 | Empty data tree gave an empty manifest | vacuous B5 | empty trees and empty raw manifests are rejected |
| 16 | Repository scan used file names only | a renamed NIfTI/DICOM file could be committed | content sniffing for NIfTI-1/2, DICOM, gzip and ZIP/XLSX magic bytes |
| 17 | Some website status sentences were hand-typed | the page could drift from the status file | they are now derived from `status.json` |
| 18 | Status-validation git checks were slow (many subprocesses per load) | CI time | batched `GitView` (a few git calls per validation) |

## 3. Audit findings with no defect

- **Hidden downloaders or uploads.** The whole repository was searched for Kaggle API, TCIA/NBIA/Aspera/Synapse clients, boto/cloud uploads, wget/curl subprocesses and notebooks. The only network call is `urllib.request.urlopen` in `data/acquisition.py`, reachable only through `HttpsFileAdapter.execute` via `stage_acquire(execute=True)` after the real-acquisition gate. There are no notebooks. The only other subprocess calls are git and nnU-Net training (`scripts/experiments/train.py`, gated by `train_main`). No credentials are embedded, and no credential environment variables are read.
- **Placeholder hashes.** Placeholder-looking hashes (`0`×64, `f`×40 commits, `a`×64) appear only in tests or temporary fake repositories. They are labelled as test values and cannot pass as evidence in the real repository (the commit must exist in git). No such value appears in `docs/`, configs or the status file.

## 4. Invariants (tested in `tests/unit/test_b2_b6_audit.py`)

| | Invariant | Status |
|---|---|---|
| A | B1 authorization is a prerequisite to real B2 acquisition | tested |
| B | calling acquisition does not complete B2 (status unchanged) | tested |
| C/D | B3/B4 require the exact designated files, and evidence of the right gate | tested |
| E | B5 requires B3/B4 records, and its evidence must link B2/B3/B4 | tested |
| F | B6 counts come from an actual source file; missing source fails; real mode is blocked | tested |
| G | EXPECTED_BY_PROTOCOL ≠ SYNTHETIC_TEST_ONLY ≠ VERIFIED_FROM_SOURCE | tested |
| H | B7 stays LOCKED until B6 PASSES (also after B6 FAILED) | tested |
| I | no transition skips earlier gates; PASSED follows protocol order | tested |
| J | FAILED never becomes PASSED; recovery needs documented decisions | tested |
| K | a source changed after hashing invalidates the evidence | tested |
| L | a configuration change changes the configuration hash | tested |
| M | a manifest content change changes `manifest_sha256`; provenance-only edits do not | tested |
| N | synthetic data are never presented as research data (relabelling breaks the fingerprint; marker tricks fail; evidence rejects synthetic data) | tested |

Edge cases covered by tests:

- empty manifest; duplicate file or slot; missing or corrupted hash;
- changed configuration; malformed or partial status;
- illegal transition; missing evidence; missing source; wrong counts;
- synthetic presented as real and real as synthetic;
- path traversal; absolute and relative paths on every platform;
- symbolic links (skipped where the OS forbids creating them);
- interrupted writes of JSON and of the status file;
- partial manifest and partial provenance record;
- JSON round trips for all record types, and the manifest CSV round trip;
- determinism; an end-to-end fake chain B1 → B6 → B7 eligible.

## 5. Validation

| Check | Result |
|---|---|
| pytest | 251 passed, 1 skipped (symlink creation not permitted on the Windows dev account; runs on Linux CI) |
| ruff check / ruff format --check | clean |
| mypy (strict defs, 72 source files) | clean |
| `python -m build` and import check | sdist and wheel built; modules import |
| website `tsc` and `next build` | pass; 8 pages exported |
| `brats-uncertainty check-repo` | pass (tracked and unignored content, including magic-byte sniffing) |
| tracked-file inspection | no imaging, arrays, checkpoints, archives, spreadsheets, credentials, split files or ledgers; no CSV tracked; no file with many BraTS IDs |
| protocol integrity | the working copy's LF-normalized SHA-256 equals the tag blob (`704c0b49…d9811`); `git diff protocol-v1.0` is empty |
| tag integrity | `protocol-v1.0` → tag object `0f46a83` (2026-09-28) → commit `4ef7ef7`; not moved |

## 6. Remaining risks (accepted and documented)

1. The evidence fingerprint is unkeyed. A deliberate forger with repository write access could fabricate a self-consistent record. The system prevents accidents and inconsistencies, not intentional fraud; git history and review are the control for that.
2. PASSED is terminal. Invalidating a gate after a later discovery (SR5) needs a logged protocol administrative entry and a manual, validated status edit.
3. Synthetic mode can be pointed at a tree whose marker was edited to list other files. The resulting records are SYNTHETIC_TEST_DATA and can never close a gate; this is a local data-handling concern only.
4. The TCIA download of the challenge package requires IBM Aspera Connect. Its compatibility with a runtime-only route (Route B) is unconfirmed and is part of the TCIA inquiry.
5. The nnU-Net trainer glue is still an unverified template (a separate gate: D1 and M1 pinning).

## 7. What "READY" means

- **Only** that the B2–B6 software is implemented, integrated, audited and tested on SYNTHETIC_TEST_DATA and fake evidence.
- Real-data execution remains blocked. Every real-mode path fails with `ResearchGateError` until gate B1 is PASSED with committed evidence in `docs/data/B1_EVIDENCE_<date>.md` via `brats-uncertainty gate-transition`.

Next authorized step: obtain and record written data-route confirmation before B2 data acquisition.
