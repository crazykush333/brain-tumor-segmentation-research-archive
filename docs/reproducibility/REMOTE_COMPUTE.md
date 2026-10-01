# Remote GPU execution

**Status (2026-10-01): the remote execution package is ready; no remote environment has been probed yet; no data acquired; B2 AUTHORIZED (not executed).**

The study cannot run on the owner's local Windows machine. `compute-preflight` measured it on 2026-10-01 as **NOT_READY**: no CUDA GPU, 7.4 GiB RAM, no PyTorch or nnU-Net. All execution therefore moves to a private remote GPU environment, which runs the same repository at an exact commit. Machine-readable requirements and the job plan are in [`configs/compute/remote_compute.yaml`](../../configs/compute/remote_compute.yaml).

## 0. Checks made from the owner's machine (2026-10-01; no data downloaded)

| Check | Result |
|---|---|
| `compute-preflight --job JOB-02` (local Windows machine) | **NOT_READY**: no CUDA GPU (integrated AMD Radeon); 7.4 GiB RAM; PyTorch and nnU-Net not installed |
| HEAD request to the TCIA BraTS 2021 page | HTTP 200 |
| HEAD request to the TCIA Faspex host (`faspex.cancerimagingarchive.net`) | HTTP 200 |
| HEAD request to `BraTS2021_MappingToTCIA.xlsx` (official URL) | HTTP 200, server-reported 80,000 bytes |
| HEAD request to `UCSF-PDGM-metadata_v5.csv` (official URL) | HTTP 200, server-reported 58,149 bytes |
| Aspera transfer from a remote environment | **not yet tested** (notebook 00 must run in the remote session) |

Server-reported sizes are not the B3/B4 evidence. B3 and B4 hash the actual downloaded bytes.

## 1. Requirements

Every value here is **ESTIMATE** until EXP-001 measures it (protocol §17).

| Item | Requirement |
|---|---|
| GPU | NVIDIA, CUDA available; ≥ 11 GiB VRAM minimum, 16 GiB recommended (ESTIMATE, nnU-Net v2 3d_fullres) |
| RAM | ≥ 12 GiB minimum, 32 GiB recommended (ESTIMATE) |
| Disk | B2 (JOB-01): 2 × the measured selection + margin (`storage-preflight` uses the size the transfer client reports). Training (JOB-02..07): raw + nnU-Net preprocessed + checkpoints, about 70 GiB (ESTIMATE). |
| Python | ≥ 3.10 |
| Packages | `pip install -e ".[io,nnunet]"`: PyTorch ≥ 2.2, nnU-Net v2 ≥ 2.5. The exact version is pinned at EXP-001. |
| System | git; Ruby (for the IBM Aspera CLI) |
| Internet | Needed for setup and B2: the TCIA page, the TCIA Faspex host and PyPI |
| Official transfer | IBM Aspera CLI. IBM/aspera-cli README: `gem install aspera-cli`, then `ascli config transferd install`. The public-link receive syntax and folder selection are **confirmed in the session** (notebook 00), never assumed. |
| Checkpoints | nnU-Net `checkpoint_latest.pth` / `checkpoint_final.pth`, in a separate `nnUNet_results` folder per run; kept in persistent output between sessions |
| Result sync | Records, reports, checkpoints and result artifacts only (`export/`). The owner commits evidence. **Raw data are never synchronised.** |

## 2. Data route in a remote session

The approved route is the owner-approved alternative ([amendment v1.0-A1](../research/protocol-amendments/2026-10-01_B1_data-route.md)): *direct official TCIA access into a private, access-restricted computational environment*. External provider authorization: NONE.

The owner's instruction of 2026-10-01 applies it to remote compute as follows; it is logged in [2026-10-01_compute-environment.md](../research/protocol-amendments/2026-10-01_compute-environment.md). An owner-controlled private GPU environment (a private VM, or a private Kaggle or Colab session) is such an environment only if:
- the data come directly from the official TCIA source;
- they live in that environment's private storage (ephemeral for Kaggle and Colab);
- **no** Kaggle Dataset, mirror, upload or shared copy is created.

If the official transfer cannot run in an environment, that environment is not used. In that case report "Kaggle cannot execute the approved official transfer route" and switch to the VM workflow; never substitute an unofficial source.

## 3. Jobs

Every job is resumable and configuration-driven, and keeps a run record (`compute.jobs`).

| Job | Work | Gate |
|---|---|---|
| JOB-01 | Probe → storage preflight → official transfer of `BraTS2021_TrainingSet` + `.sums` + the two metadata files → `verify-checksums` → `acquire` (local import, hierarchy preserved) → export of the B2 record | `acquire_data` |
| JOB-02..07 | Arm A/B × seed 0/1/2. Re-download, then `verify-inventory` against the committed B2 record, then `job-run` | `train_main` |
| JOB-08+ | Inference, thresholds (C5), external evaluation, statistics, figures | C gates, `eval-v1` |

How a training job decides what to do (`brats-uncertainty job-run`):
- **COMPLETED:** never re-run.
- **Earlier attempt with a latest checkpoint:** resumed with nnU-Net `--c`, and the attempt is recorded.
- **Earlier attempt without a checkpoint:** refused, unless `--restart-without-checkpoint` is given; the restart is recorded.
- **Checkpoints without a run record:** refused (unknown provenance).
- **Non-zero exit:** the run is recorded as `INTERRUPTED` if a checkpoint exists, otherwise `FAILED`.
- **Success:** requires `checkpoint_final.pth`.

Every record carries the protocol version and hash, git commit, config hashes, dataset manifest hash, split hash, arm, seed and the hardware of each attempt.

Ephemeral sessions such as Kaggle and Colab lose `/tmp` when they end. Every session that needs data re-downloads them from TCIA and must pass `brats-uncertainty verify-inventory --record <committed B2 record> --root <raw>`, proving the tree is byte-identical to the acquired B2 tree, before any use.

## 4. Procedure

**Kaggle** ([`experiments/kaggle/`](../../experiments/kaggle/README.md)):
1. The owner pushes this repository to GitHub, then creates a private notebook from `00_environment_probe.ipynb` with GPU and Internet enabled.
2. Set `REPO_URL` and `COMMIT`.
3. Run the notebook and download `export/`.
4. If the probe reports `READY` or `READY_WITH_LIMITS` for JOB-01 and the receive syntax is confirmed, run `01_b2_acquisition.ipynb`.

**Private VM** ([`experiments/vm/setup_vm.sh`](../../experiments/vm/setup_vm.sh)):
1. Run `REPO_URL=… COMMIT=… WORK=/private/disk bash setup_vm.sh`.
2. The owner installs the Aspera CLI.
3. Run the same CLI steps as notebook 01.

After each job, the owner reviews the exported records, commits them as evidence and moves the gate with `brats-uncertainty gate-transition` in the owner's checkout.

## 5. Never

- Create a Kaggle Dataset or any mirror containing BraTS data.
- Save raw data as notebook output.
- Upload raw data to GitHub, Git LFS, Drive, S3 or Hugging Face.
- Expose raw data through the website.
- Put credentials in cells, configs or logs.
- Report a planning estimate as a measurement.
