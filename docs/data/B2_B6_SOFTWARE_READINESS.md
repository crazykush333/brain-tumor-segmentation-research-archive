# B2–B6 software readiness (final adversarial audit)

| Field | Value |
|---|---|
| Date | 2026-09-30 |
| Protocol | v1.0, FROZEN, tag `protocol-v1.0` (tag object `0f46a83` → commit `4ef7ef7`), unchanged |
| Scope | Software only. No data were downloaded, acquired or processed. No real B2–B6, no B7, no split, no training, no analysis. |
| Verdict | **SOFTWARE_READY_FOR_AUTHORIZED_EXECUTION** |

**Definition.** SOFTWARE_READY_FOR_AUTHORIZED_EXECUTION means: *the software infrastructure is technically ready to execute authorized B2–B6 workflows, but no real-data execution has occurred.* Real-data execution remains blocked until B1 data-route authorization is actually obtained and recorded.

## 1. Current gate status (observed from `docs/project_status.yaml`)

| Gate | Status |
|---|---|
| B1 | PENDING |
| B2, B3, B4, B5, B6 | LOCKED |
| B7–B12 | LOCKED |
| Data | authorization PENDING, `acquired: false`, no approved route |
| Training / evaluation | NOT_STARTED |
| Results | UNAVAILABLE |
| B6 counts | targets EXPECTED_BY_PROTOCOL (1,251 / 511 / 740); verification UNAVAILABLE |

## 2. State-machine audit

- **Graph.** `B1 → B2 → {B3, B4} → B5 → B6 → B7 → … → B12`.
- **Statuses.** LOCKED, PENDING (B1), AUTHORIZED, RUNNING, PASSED, FAILED, BLOCKED.
- **Invariants** (validated on every load of the status file):
  - a gate is LOCKED exactly while a prerequisite has not PASSED;
  - PASSED follows protocol order.
- **Rejected transitions (tested):**
  - B1 PENDING→AUTHORIZED; B1 is authorized only by reaching PASSED with machine-checkable evidence;
  - B2 LOCKED→AUTHORIZED before B1;
  - LOCKED→PASSED; any skipped prerequisite;
  - B4 passing before B3; B7 before B6 has PASSED;
  - FAILED→PASSED, FAILED→AUTHORIZED, FAILED→RUNNING;
  - FAILED/BLOCKED without evidence; unblocking without an owner-decision document.
- **Transition writer.**
  - It validates the current file first and applies the change.
  - It re-validates everything, including evidence contents.
  - It edits only the affected lines, and the re-parsed file must equal the validated mapping exactly.
  - It writes atomically, and only with `--apply`.

## 3. Evidence audit

B1 PASSED requires `docs/data/B1_EVIDENCE_<date>.md` with exactly one `Evidence type:` (TCIA written confirmation or owner-approved alternative) and `Approved route:` equal to `data.approved_route`. Documentation, the inquiry and the template are rejected.

B2–B6 PASSED require the gate's own execution record, meeting all of these checks:

| Check | Rejected case (tested) |
|---|---|
| schema and fingerprint re-validated with the typed reader | hand-written minimal JSON; edited record |
| record belongs to the gate | B4 record offered for B3 |
| `data_class: REAL_RESEARCH_DATA` and `synthetic: false` | genuine synthetic record; relabelled synthetic record |
| clean committed checkout | `code_dirty: true`; missing commit |
| frozen protocol version and hash | protocol `v0.5`; other protocol hash |
| commit exists and is an ancestor of HEAD | unknown commit; commit from a rewritten or orphan history |
| hashed configuration files still unchanged | configuration edited or deleted after the record |
| dataset identity: name and DOI from `configs/dataset/brats2021.yaml` `evidence_identity` | other dataset name; other DOI |
| official source (TCIA / Synapse prefixes) | mirror URL |
| committed or staged, not git-ignored, safe in-repo path | untracked file; git-ignored file even if force-added; `../`, absolute or drive paths |
| cross-gate links: B5 → B2/B3/B4 fingerprints; B6 → B3 fingerprint and crosswalk SHA-256; B6 status VERIFIED_FROM_SOURCE | unlinked B5; B6 with another crosswalk hash; failed B6 record |

Residual limitation: fingerprints are not cryptographically keyed. A deliberate forger with write access and a real commit could fabricate a consistent record. The controls stop accidental, stale, synthetic and mismatched evidence; they do not stop intentional fraud. Git history and review cover that.

## 4. Acquisition audit

- **Dry run is the default.** `acquire` without `--execute` only prints the plan; no network, no disk.
- **Real execution needs all of:**
  - B1 PASSED;
  - B2 AUTHORIZED/RUNNING;
  - `data.authorization: APPROVED`;
  - adapter route equal to `data.approved_route`;
  - a default clock (no fabricated timestamps);
  - a storage root that is not a link and, inside the repository, only under the git-ignored `data/`;
  - an empty storage root.

  Otherwise it fails with "Real-data acquisition is locked because B1 data-route authorization has not been recorded."
- **No synthetic data through real adapters.** SYNTHETIC_TEST_DATA cannot be delivered through the real `local-import` adapter, and a marker appearing in real storage aborts the run.
- **Repository-wide search.**
  - `urllib.request.urlopen` in `data/acquisition.py` is the single network call. It is reachable only via `stage_acquire(execute=True)` after the checks above.
  - No `requests`, Kaggle API, boto/cloud uploads, wget/curl, `shell=True` or `os.system`.
  - The data and evaluation packages contain no `subprocess` and read no environment variables.
  - No notebooks.
  - The website and scripts contain no fetch or download calls.
  - The CLI has no force, skip, bypass or override options, and stage functions have no such parameters.

## 5. Synthetic/real audit

- Every record and manifest carries an explicit `data_class`. Relabelling breaks the fingerprint.
- Synthetic mode accepts only unmodified files listed with their SHA-256 in the tree's `SYNTHETIC_TEST_DATA.json` marker, outside the repository.
- Tested rejections:
  - marker removed;
  - marker copied next to an unrelated real-looking file;
  - marker label edited;
  - modified synthetic file;
  - synthetic input in real mode;
  - synthetic tree through the real adapter.
- A synthetic B6 success is `SYNTHETIC_TEST_ONLY`, never `VERIFIED_FROM_SOURCE`.

## 6. Manifest audit (B5)

- **Pipeline tested end to end:** synthetic source → inventory → hashes → provenance → schema validation → manifest → manifest hash → reload.
- Two independent runs over identical bytes gave identical files, ordering, duplicates and `manifest_sha256`.
- **Hashing order.** The hash is computed after all final fields, including `gate` and `integrity`; any later change fails validation.
- **Metadata links.** Real B5 requires the B3/B4 records; a metadata file changed after hashing is rejected.
- **Raw vs derived.** Derived manifests link to their parent hash.
- **Rejected:** empty and partial manifests, duplicate paths or slots, unsafe paths.

## 7. Hashing audit (B3/B4)

- SHA-256 is computed over exact file bytes:
  - same bytes give the same hash;
  - changing one byte gives a different hash;
  - a renamed copy has the same content hash;
  - a missing file fails with "input not found";
  - a wrong file fails with "requires the file".
- No real B3/B4 hash exists in the repository.
- Records reject malformed hashes such as `TODO-hash`.
- Placeholder-shaped values appear only in tests and temporary fake repositories.

## 8. B6 verification audit

| State | When | Tested |
|---|---|---|
| EXPECTED_BY_PROTOCOL | protocol targets; always displayed as "Protocol verification targets" | yes |
| UNAVAILABLE | B6 has not produced a result (current state; also B6 AUTHORIZED) | yes |
| VERIFIED_FROM_SOURCE | only from a PASSED B6 whose REAL_RESEARCH_DATA record verified the counts derived from the hashed crosswalk | yes (fake repository) |
| FAILED_VERIFICATION | wrong counts, or crosswalk ≠ B3 hash (record written with diagnostics, run stops per SR3) | yes |
| SYNTHETIC_TEST_ONLY | synthetic source matching the targets (software test only) | yes |

The protocol targets alone can never produce VERIFIED_FROM_SOURCE. The record validator, the evidence validator and the display layer each refuse it.

## 9. Atomicity and path-safety audit

- **Atomic writes:**
  - JSON writes use temp file plus `os.replace`;
  - the status file is written atomically, with the `.part` file cleaned up;
  - the manifest CSV and acquisition copies go through `.part` then rename.
- **Simulated failures leave nothing behind:** after a failure the previous status is intact and valid, and no `.part` or partial JSON/CSV files remain (tested).
- **Refused destinations:** a destination that exists, is a directory, is a link, or is a broken link.
- **Links:** symbolic links and Windows directory junctions (`is_link`) are refused in deliveries, storage, data trees, synthetic trees and stage inputs. The integrity audit reports links as errors and does not follow them.
- **Relative paths:** checked by one platform-independent rule; `/abs`, `C:/`, `..` and backslashes are rejected on every OS.
- **Where it was tested:** the link tests ran on this Windows machine using junctions. One older POSIX-symlink test is skipped here because symlink creation needs privileges; it runs on Linux CI.

## 10. Defects found and fixed in this final pass

1. `GitView.ignored` used text-mode stdin, so on Windows git received `path\r` and never matched. Git-ignored evidence would have been accepted on Windows. Fixed with NUL-separated binary I/O (`-z`); regression test uses a real temporary git repository.
2. Evidence identity (dataset, DOI, official source) was not checked. Now enforced.
3. Stale configuration (hashed configs changed afterwards) was not detected. Now enforced.
4. Commits from a foreign or rewritten history were accepted. They must now be ancestors of HEAD.
5. Windows directory junctions were not recognised as links. `is_link` is now used everywhere.
6. The write helper could replace a link or broken link, and gave an unclear error for directories. It now refuses both.
7. Failed transition and CSV writes could leave `.part` files. They are now cleaned up.
8. Synthetic trees could be offered through the real adapter. Now refused.
9. There was no explicit UNAVAILABLE B6 state; `count_verification_state` now derives it from status and evidence only.
10. Non-object JSON records raised AttributeError. They now raise a clear ProvenanceError.

The earlier audit's fixes (evidence re-validation, B1 evidence format, FAILED/BLOCKED rules, B5 linkage, data_class, transition writer, relative-path rule, and more) remain in force and are covered by tests.

## 11. Validation (observed)

| Check | Result |
|---|---|
| `pytest` | **275 passed, 1 skipped** (POSIX symlink creation not permitted on this Windows account; the junction equivalent ran) |
| `ruff check .` / `ruff format --check .` | clean / 165 files formatted |
| `mypy` (configured scope: `src`, strict defs) | no issues in 72 files |
| package build / imports | sdist and wheel built; all 71 package modules import (`nnunet_trainers` without torch/nnunet) |
| `brats-uncertainty check-repo` | pass: prohibited types, magic-byte sniffing (NIfTI/DICOM/gzip/ZIP), credentials, personal paths, look-alike protocol files |
| tracked-file inspection | no imaging, arrays, checkpoints, archives, spreadsheets, credentials, split files, result JSON or ledgers; 0 tracked CSV; no gzip/ZIP magic in any tracked file |
| protocol integrity | `git show protocol-v1.0:<file>` and `git show HEAD:<file>` are byte-identical (`cmp`); working copy equals the tag blob after CRLF→LF (Windows checkout); SHA-256 `704c0b49…d9811` |
| tag integrity | `protocol-v1.0` → tag object `0f46a83` → commit `4ef7ef7`; not moved, no retag |
| website `tsc` and `next build` | pass; overview renders Protocol ✓ Frozen, B1 ⏳ Pending, B2–B7 🔒 Locked, Training ○ Not started, Results ○ Not available; counts only as "Protocol verification target"; B6 verification UNAVAILABLE |

## 12. Remaining risks

1. Unkeyed fingerprints; deliberate fraud is out of scope (see §3).
2. PASSED is terminal. Invalidating a passed gate (SR5) requires a logged administrative entry and a validated manual status edit.
3. Changing `configs/dataset/brats2021.yaml` after B5/B6 evidence exists invalidates that evidence by design. Set `expected_shape` and confirm the crosswalk headers before running B5/B6.
4. The TCIA challenge download requires IBM Aspera Connect. Its compatibility with a runtime-only route is unconfirmed (part of the TCIA inquiry).
5. The nnU-Net trainer glue is an unverified template (separate D1/M1 concern).

Next authorized step: obtain and record written data-route confirmation (or an owner-approved alternative) before B2 data acquisition.
