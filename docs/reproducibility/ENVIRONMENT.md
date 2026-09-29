# Environment

## Software (this stage)

| Component | Requirement | Notes |
|---|---|---|
| Python | ≥ 3.11 | CI tests 3.11 and 3.12. Local development was also verified on 3.13 |
| Core deps | numpy ≥ 1.26, scipy ≥ 1.11, pyyaml ≥ 6.0 | `pyproject.toml` |
| Extras | `viz` (matplotlib), `io` (nibabel, openpyxl), `nnunet` (nnunetv2 ≥ 2.5, torch ≥ 2.2), `dev` (pytest, ruff, mypy, build, …) | install only what a stage needs |
| Node.js | ≥ 20 (for `website/`) | static export; no server runtime |

```bash
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Docker (CPU; tests and tooling only; no data, no GPU):

```bash
docker build -t brats-uncertainty .
docker run --rm brats-uncertainty make check-python
```

## Pinning for experiments

The exact **nnU-Net v2, PyTorch, CUDA and Python** versions are pinned at M1 / EXP-001 and recorded in each run's `environment.json` (`utils/environment.capture_environment`). They are **not** assumed here. The main study uses the same versions as EXP-001 (EXP-001 spec §0.4). A lock file (`pip freeze` output) is committed with the EXP-001 record.

## Environment variables

| Variable | Purpose |
|---|---|
| `BRATS_UNCERTAINTY_ROOT` | repository root, if not auto-detected |
| `BRATS2021_DATA_ROOT`, `BRATS_AFRICA_DATA_ROOT` | local data locations (outside the repository) |
| `nnUNet_raw`, `nnUNet_preprocessed`, `nnUNet_results` | nnU-Net v2 folders (outside the repository) |
| `BRATS_UNC_SEED`, `BRATS_UNC_ARM` | set by `models/nnunet.train_environment` for the guarded trainers |

No variable holds a secret in the repository. Platform credentials live in platform secret stores.
