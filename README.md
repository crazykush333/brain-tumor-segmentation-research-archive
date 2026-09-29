# Case-level reliability of glioma segmentation under missing MRI sequences

> **Status: Protocol v1.0 frozen. Experimental execution pending.**

A pre-registered empirical evaluation study. **No data have been acquired, no model has been trained, no split has been created, and no results exist.** This repository contains the frozen research protocol plus the software and reproducibility infrastructure that will carry it out once the protocol's gates are passed.

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-informational)](.github/workflows/ci.yml)
[![Protocol](https://img.shields.io/badge/protocol-v1.0%20frozen-blue)](docs/research/FINAL_RESEARCH_PROTOCOL_v1.0.md)
[![Results](https://img.shields.io/badge/results-none%20yet-lightgrey)](results/README.md)

## Research question

> When MRI sequences are missing at inference, does the case-level ensemble uncertainty of a modality-dropout nnU-Net discriminate unreliable enhancing-tumour segmentations *within* a given missing-sequence condition, i.e. beyond what the known identity of the missing sequence provides? How does this vary with which sequence is missing, and do the discrimination and operating thresholds transfer to a held-out institution and an external population?

**Primary hypothesis (H-W).** On the internal test set, for the modality-dropout (arm B) ensemble, the equal-weight mean over the four single-missing conditions C4 = {−T1, −T1c, −T2, −FLAIR} of the within-condition ET ΔAURC_c = AURC_c(U1) − AURC_c(I) is below 0. U1 is the ensemble pairwise-Dice confidence, I is the missingness-indicator baseline, and risk is 1 − ET Dice. H-W is supported if the patient-group bootstrap 95% CI lies entirely below 0.

The authoritative definition of everything above is the frozen protocol:
**[docs/research/FINAL_RESEARCH_PROTOCOL_v1.0.md](docs/research/FINAL_RESEARCH_PROTOCOL_v1.0.md)**, git tag `protocol-v1.0`, SHA-256 `704c0b495917344f44b93e7548ade0e32a71220265419516a2c83d626fcd9811`.

## Current status

| Stage | Status |
|---|---|
| Gate A (protocol freeze blockers A1–A9) | **Closed.** Frozen as v1.0 on 2026-09-28; A7 and A8 are owner-waived with mandatory pre-submission re-checks |
| Research software and reproducibility infrastructure | Implemented and tested on synthetic inputs only |
| B1: approved data route (TCIA confirmation) | **Pending.** Authorization record and a ready-to-send TCIA inquiry (not sent) are in [docs/data/](docs/data/B1_DATA_ROUTE_AUTHORIZATION.md) |
| B2–B6: data acquisition, metadata hashes, manifest, counts | Not started (gated tooling prepared and tested on synthetic files) |
| B7–B12: same-patient screen, groups, final split | **Locked** pending B2–B6 |
| D1–D6: EXP-001 compute pilot | Not started |
| C1–C6: pre-external-evaluation gates | Not started |
| Training, inference, evaluation, results | Not started. **No results exist.** |

The machine-readable state is [docs/project_status.yaml](docs/project_status.yaml). The research-gate guards and the website both read that file.

## Repository layout

```
configs/            protocol mirror (protocol_v1.0.yaml), dataset, experiment, evaluation, compute configs
docs/research/      frozen protocol v1.0, audits, changelogs; archive/ holds superseded drafts
docs/data/          data access, provenance and dictionary
docs/reproducibility/ reproducibility, environment and compute documentation
docs/project_status.yaml  single source of truth for project state
experiments/        experiment metadata (EXP-001: PLANNED, not authorized)
results/            placeholders only; no results exist
splits/             empty until gate B10
scripts/            thin entry points for gated pipeline stages and reporting
src/brats_uncertainty/  the Python package
tests/              unit, integration and regression tests (synthetic fixtures only)
website/            Next.js research website (static export)
```

## Package overview (`src/brats_uncertainty`)

| Module | Purpose | Protocol |
|---|---|---|
| `protocol.py` | loads `configs/protocol/protocol_v1.0.yaml`; fails if the frozen protocol's SHA-256 changes | freeze rule |
| `preprocessing/` | 15 modality subsets, C4/C5, missingness (normalized channel = 0), label/region mapping | §8, §10 |
| `models/` | arm-B dropout policy (p_full 0.5, 14 subsets); nnU-Net v2 adapter; guarded trainer template | §9, §10 |
| `inference/` | 3-member mean ensemble, threshold 0.5; frozen inference settings | §9 |
| `uncertainty/` | U1 (primary), U2 (descriptive), U3 (exploratory), I | §11 |
| `metrics/` | Dice (empty conventions), risk–coverage, AURC with expected tie handling, e-AURC, ECE, Brier, volume failure; HD95 deferred to gate C6 | §3, §4, §12 |
| `statistics/` | patient-group bootstrap (10,000, seed 12345), percentile and BCa CIs, bootstrap p-values, Holm within family, H-W statistic, τ_q rule, threshold transfer | §4 S7, §13–§15 |
| `grouping/` | WT-label Dice screen, T_screen record (computed only from positive controls), review resolution, transitive grouping | §6.1–§6.2 |
| `splitting/` | stratified patient-group 70/10/20 split, seed 20260927, §6.3 assertions, hashes | §6.3 |
| `data/` | manifests with SHA-256 from bytes on disk, crosswalk parsing and cohort counts, provenance records | §5, §24 |
| `evaluation/` | research-gate guards, `eval-v1` tag check, single-evaluation ledger (SR4), status schema | lifecycle, SR4 |
| `experiments/`, `results/` | experiment lifecycle (PLANNED → … → COMPLETED/FAILED/INVALIDATED); provenance-stamped artifacts; website export | §24 |
| `repo_checks.py` | prohibited-file and secret scan | data policy |

Every gated pipeline stage (manifest, T_screen, screen, grouping, split, training, evaluation) raises `ResearchGateError` until its gates are closed, with evidence, in `docs/project_status.yaml`.

## Quick start (software only; no data needed)

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
make check          # ruff, mypy, pytest, repository scan, website-data sync
brats-uncertainty verify-protocol
brats-uncertainty status
brats-uncertainty check-action create_split          # reports the unmet gates
```

Website: see [website/README.md](website/README.md).

## Data policy

This repository never contains MRI scans, NIfTI files, patient-level labels, licensed metadata files (for example `BraTS2021_MappingToTCIA.xlsx`), credentials or model checkpoints. `.gitignore` and `brats-uncertainty check-repo` (run in CI) enforce this. Datasets must be obtained from the official providers under their terms and the route approved at gate B1: see [docs/data/DATA_ACCESS.md](docs/data/DATA_ACCESS.md), [docs/data/DATA_PROVENANCE.md](docs/data/DATA_PROVENANCE.md) and [data/README.md](data/README.md). The local `data/` tree is git-ignored except its README. Test fixtures are synthetic and are never described or used as BraTS data.

## Reproducibility

See [docs/reproducibility/REPRODUCIBILITY.md](docs/reproducibility/REPRODUCIBILITY.md), [ENVIRONMENT.md](docs/reproducibility/ENVIRONMENT.md) and [COMPUTE.md](docs/reproducibility/COMPUTE.md). Implementation choices that the protocol leaves open (for example the dilation structuring element) are listed there for owner confirmation before `eval-v1`.

## Citation, licence, conduct

- Cite via [CITATION.cff](CITATION.cff) (software; no paper exists yet).
- Code licence: [Apache-2.0](LICENSE). *The licence choice is pending owner confirmation (docs/research/08 §2).* The licence covers code only; dataset licences are separate.
- [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [SECURITY.md](SECURITY.md)

## Historical design documents

Documents 01–11 in `docs/research/` record the research-design phase and are **superseded by the frozen protocol** wherever they differ; see [docs/research/README.md](docs/research/README.md).
