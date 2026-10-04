# Remote GPU execution

**Status (2026-10-01): remote execution infrastructure is ready. No remote environment has been probed yet. No data have been acquired. Scientific training has not been executed.** B2 is AUTHORIZED but not executed; B3–B12 are LOCKED; D1–D6 are NOT_STARTED.

The study cannot run on the owner's local Windows machine. The same repository therefore runs, at an exact commit, in a private remote GPU environment: a private VM, or a private Kaggle or Colab session. No code path is specific to Kaggle; only the notebooks' default folders are. Requirements and the job plan are in [`configs/compute/remote_compute.yaml`](../../configs/compute/remote_compute.yaml).

## 0. Measured facts vs estimates

**Measured** on the owner's machine, 2026-10-01; no data downloaded:

| Check | Result |
|---|---|
| `compute-preflight --job JOB-02` on the local Windows machine | **NOT_READY**: no CUDA GPU (integrated AMD Radeon), 7.4 GiB RAM, PyTorch and nnU-Net not installed |
| HEAD requests to the TCIA BraTS 2021 page and the TCIA Faspex host | HTTP 200 |
| HEAD request to `BraTS2021_MappingToTCIA.xlsx` (official URL) | HTTP 200, server-reported 80,000 bytes |
| HEAD request to `UCSF-PDGM-metadata_v5.csv` (official URL) | HTTP 200, server-reported 58,149 bytes |
| Aspera transfer from a remote environment | **not yet tested** (notebook 00 runs it in the session) |

Server-reported sizes are not B3/B4 evidence. B3 and B4 hash the actual downloaded bytes.

**Estimates** (protocol §17; replaced by EXP-001 and B2 measurements, never reported as measurements):

| Item | Minimum | Recommended |
|---|---|---|
| GPU | NVIDIA with CUDA, ≥ 11 GiB VRAM | 16 GiB VRAM |
| System RAM | ≥ 12 GiB | 32 GiB |
| Disk, JOB-01 (B2) | 2 × the measured selection + 10 % + 10 GiB reserve (`storage-preflight`) | — |
| Disk, training job | about 70 GiB (raw + nnU-Net preprocessed + checkpoints) | — |
| GPU-hours, whole study | 100–215 GPU-h | cap 220 GPU-h |

Software requirements:
- Python ≥ 3.10 (the package targets 3.11+).
- PyTorch ≥ 2.2 and nnU-Net v2 ≥ 2.5. The exact versions are **pinned at EXP-001** from the probe report (see [ENVIRONMENT.md](ENVIRONMENT.md)).
- A CUDA build of PyTorch matching the driver.
- git; Ruby, only for the IBM Aspera CLI.
- Internet for setup and B2.

## 1. Run isolation (never overwritten)

Every run owns its own nnU-Net results root:

```
<results_root>/<experiment_id>/[<label>_]arm_<a>_seed_<s>/
    run_manifest.json
    Dataset<ID>_<Name>/<trainer>__nnUNetPlans__3d_fullres/fold_0/checkpoint_{latest,final}.pth
```

`experiment_id` is `MAIN` for the six protocol runs and `EXP-001` for the compute pilot, whose runs take labels such as `P2`. Seeds, arms and experiments can never share a folder (`models.nnunet.run_namespace`). The protocol version and git commit are recorded in the run manifest; they are not path components.

## 2. Run manifest and statuses

`run_manifest.json` records:
- **identity:** experiment, arm, seed, trainer, protocol version and hash, the hashes of the compute config, the training config and the training code, the B5 dataset manifest hash, the B12 split hash, the dataset-conversion hash and the data class;
- **run state:** status, start and end time, checkpoint path and SHA-256, artifact paths;
- **every attempt:** action, git commit, environment hash, hardware and exit code.

| Status | Meaning |
|---|---|
| PLANNED | created, not started |
| RUNNING | an attempt is in progress, or a session died during one |
| COMPLETED | exit code 0 **and** `checkpoint_final.pth` present; never re-run |
| FAILED | non-zero exit or interruption; resumable only with `--resume` |
| INVALIDATED | set with `brats-uncertainty job-invalidate <run_dir> --reason …`; never resumed |

Resume rules (`brats-uncertainty job-run … --resume`, which uses nnU-Net `--c`):
- An earlier attempt is continued only with an explicit `--resume`.
- The checkpoint must be in the run's own folder, and the manifest identity must equal the current identity. If they differ, the run **fails closed**: the checkpoint belongs to another configuration.
- A recorded checkpoint hash must still match.
- Without a checkpoint, a restart from epoch 0 needs `--restart-without-checkpoint`, and is recorded.
- Checkpoints without a manifest are refused.

## 3. Gates (never bypassed; no override flag)

| Job | Gate (`check-action`) | Opens after |
|---|---|---|
| JOB-01 B2 (notebook 01) | `acquire_data` | B1 PASSED, B2 AUTHORIZED (now) |
| JOB-GROUPING B7–B12 (02) | `compute_t_screen` … `create_split` | B6 PASSED (B8 is human review) |
| JOB-PILOT EXP-001 (03) | `run_exp001` | B1, B2, D1 (owner authorization), D2 |
| JOB-02..07 training (04) | `train_main` | B1–B12 **and** D1–D6 |
| JOB-08 evaluation (05) | `evaluate_*` | plus C gates and the `eval-v1` tag |

`synthetic_test_mode` exists only in the Python API, for tests. It accepts only a `SYNTHETIC_TEST_DATA` dataset-conversion record, writes outside the repository and can never train on study data.

## 4. Official data access (B2)

Two supported paths, both ending in the existing gated `acquire --adapter local-import`, which keeps the official nested hierarchy:
- **A. Runtime acquisition** in the remote session with the IBM Aspera CLI. Install it with the commands from IBM/aspera-cli's README (`gem install aspera-cli`, `ascli config transferd install`). The command that receives a public package link, and whether one folder can be selected, are **confirmed from the client's own help output in notebook 00**. No command is assumed. `transferd install` puts `ascp` in ascli's SDK folder (default `$HOME/.aspera/sdk`), not on PATH, so `compute-preflight` locates it with `ascli config ascp show` (IBM aspera-cli manual).
- **B. Manual official delivery** on a private VM: the owner downloads with the official Aspera client and points `DELIVERY` at it. On Kaggle this path is impossible, because uploading data would create a dataset.

Then run `verify-checksums` with the provider `.sums` file exactly as delivered, `acquire`, and the export of the B2 record. Ephemeral sessions re-download in every session and must pass `verify-inventory` against the committed B2 record before any use. See [B2_OFFICIAL_DOWNLOAD_RUNBOOK.md](../data/B2_OFFICIAL_DOWNLOAD_RUNBOOK.md).

## 5. nnU-Net raw dataset (after B12; pilot after D2)

`brats-uncertainty build-nnunet-dataset --training-root <…>/BraTS2021_TrainingSet --out <nnUNet_raw>/Dataset<ID>_<Name> --dataset-id … --dataset-name … --case-ids <frozen IDs>` (gated by `train_main`, or `run_exp001` for the pilot):
- channels `_0000`–`_0003` = T1, T1c, T2, FLAIR (protocol order), copied byte for byte;
- labels mapped from BraTS {0,1,2,4} to nnU-Net {0,1,2,3}; unexpected values fail;
- `dataset.json` written;
- `conversion_provenance.json` and `.csv` written, mapping every derived file to its source collection, case, relative source path and source SHA-256, with the conversion-config hash and the git commit.

Missing or extra cases fail, and nothing is skipped. The output is atomic and deterministic. Real derived data are never written into the repository.

## 6. Results and synchronisation

- Every scientific number is a record in a `*.metrics.json` file following [`configs/schemas/result_metric.schema.json`](../../configs/schemas/result_metric.schema.json). Each record carries experiment, condition, metric, value, unit, population, dataset role, seed or ensemble, arm, protocol version, commit, and the dataset, split and config hashes. Check with `brats-uncertainty validate-metrics`. Synthetic records can never be published.
- `brats-uncertainty export-artifacts --source <remote export> --dest results/<EXPERIMENT>` copies only `.json .csv .md .png .svg .txt`. It validates metrics files and run manifests, and skips checkpoints, images, labels, archives and licensed metadata (they are listed, never copied). It refuses links, disguised imaging content and overwrites.
- The owner downloads the session's `export/` folder, runs `export-artifacts` into the repository, reviews, commits and regenerates the website with `brats-uncertainty export-site-data`. Raw data are never synchronised.

## 7. Packages

- **Kaggle:** [`experiments/kaggle/`](../../experiments/kaggle/README.md), notebooks 00–06 generated by `scripts/remote/make_kaggle_notebooks.py`.
- **Private VM:** [`experiments/vm/`](../../experiments/vm/README.md), the same CLI steps.
- **GitHub workflow:** [GITHUB_SETUP.md](GITHUB_SETUP.md).

## 8. Never

- Create a Kaggle Dataset or any mirror containing BraTS data.
- Save raw data as notebook output.
- Upload raw data to GitHub, Git LFS, Drive, S3 or Hugging Face.
- Expose raw data on the website.
- Put credentials in cells, configs or logs.
- Report an estimate as a measurement.
- Start training before B12 and D1–D6.
