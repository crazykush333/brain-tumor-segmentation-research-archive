"""Generate experiments/kaggle/*.ipynb from this file (reproducible; do not hand-edit them).

The notebooks are a COMPUTE ENVIRONMENT, not a dataset mirror:
- raw data live only in ephemeral session storage (WORK = /tmp/brats) and are deleted
  with the session; they are never saved as notebook output or as a Kaggle Dataset;
- only records, reports and checkpoints are written to EXPORT/RESULTS under
  /kaggle/working (owner downloads them; evidence is committed from the owner's checkout);
- every research step is the repository's gated CLI, run at an exact commit.

Usage: python scripts/remote/make_kaggle_notebooks.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "experiments" / "kaggle"

HEADER = (
    "**Private compute session - not a dataset mirror.** Raw BraTS data are downloaded "
    "only from the official TCIA source into ephemeral session storage (`WORK`) and are "
    "never written to notebook output, a Kaggle Dataset, GitHub or the website. "
    "B1 basis: owner-approved alternative (amendment v1.0-A1); no TCIA authorization is "
    "claimed. Enable **GPU** and **Internet** in the notebook settings. Never paste "
    "credentials into a cell; use Kaggle Secrets if a private repository needs a token."
)

PARAMS = """# PARAMETERS - set before running (no secrets here)
REPO_URL = ""   # https URL of this research repository (GitHub)
COMMIT = ""     # exact commit SHA or tag to run (never a moving branch)
WORK = "/tmp/brats"                     # ephemeral session storage (raw data stay here)
EXPORT = "/kaggle/working/export"       # records/reports only - never raw data
assert REPO_URL and COMMIT, "set REPO_URL and COMMIT first"
"""

SETUP = """import os
os.makedirs(WORK, exist_ok=True)
os.makedirs(EXPORT, exist_ok=True)
!git clone --quiet {REPO_URL} /kaggle/working/repo
%cd /kaggle/working/repo
!git checkout --quiet {COMMIT}
!git rev-parse HEAD
!pip install --quiet -e ".[io,nnunet]"
!brats-uncertainty verify-protocol"""


def _nb(title: str, cells: list[tuple[str, str]]) -> dict[str, object]:
    out: list[dict[str, object]] = [
        {"cell_type": "markdown", "metadata": {}, "source": f"# {title}\n\n{HEADER}"}
    ]
    for kind, src in cells:
        cell: dict[str, object] = {"cell_type": kind, "metadata": {}, "source": src}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        out.append(cell)
    return {
        "cells": out,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


NOTEBOOKS: dict[str, dict[str, object]] = {
    "00_environment_probe.ipynb": _nb(
        "00 - Environment probe and official-transfer-client test (NO data download)",
        [
            ("code", PARAMS),
            ("code", SETUP),
            (
                "markdown",
                "## Compute preflight\nMeasured GPU/CUDA/VRAM/RAM/disk/packages/internet. "
                "`NOT_READY` means this environment cannot run the job; the blockers are listed.",
            ),
            (
                "code",
                "!brats-uncertainty compute-preflight --work-dir {WORK} "
                "--json {EXPORT}/probe_general.json\n"
                "!brats-uncertainty compute-preflight --job JOB-02 --work-dir {WORK} "
                "--json {EXPORT}/probe_JOB-02.json",
            ),
            (
                "markdown",
                "## Official transfer client (IBM Aspera CLI)\nInstalls IBM's official "
                "command-line client into this ephemeral session (README of IBM/aspera-cli: "
                "`gem install aspera-cli`, `ascli config transferd install`) and prints its "
                "own help for Faspex 5 public links. **Nothing is transferred here.** Record "
                "the exact receive syntax and whether a single folder of a package can be "
                "selected; notebook 01 uses that confirmed command.",
            ),
            (
                "code",
                "!apt-get -qq update && apt-get -qq install -y ruby-full > /dev/null\n"
                "!gem install aspera-cli --no-document\n"
                "!ascli config transferd install\n"
                "!ascli --version\n"
                "!ascli faspex5 -h 2>&1 | head -200",
            ),
            (
                "code",
                "!brats-uncertainty compute-preflight --job JOB-01 --work-dir {WORK} "
                "--json {EXPORT}/probe_JOB-01.json",
            ),
            (
                "markdown",
                "## Result\nDownload `/kaggle/working/export/` (probe JSON files) and give "
                "them to the owner's checkout. They contain no data and no credentials.",
            ),
        ],
    ),
    "01_b2_acquisition.ipynb": _nb(
        "01 - JOB-01: B2 official acquisition (gated)",
        [
            ("code", PARAMS),
            ("code", SETUP),
            (
                "code",
                "!brats-uncertainty compute-preflight --job JOB-01 --work-dir {WORK} "
                "--json {EXPORT}/probe_JOB-01.json",
            ),
            (
                "markdown",
                "## Storage preflight\nEnter the selection size the transfer client reports "
                "for `BraTS2021_TrainingSet` + `RSNA-ASNR-MICCAI-BraTS-2021.sums`. "
                "Do not guess it. The transfer starts only on `PREFLIGHT OK`.",
            ),
            (
                "code",
                "SELECTED_GIB = None  # from the transfer client listing\n"
                'assert SELECTED_GIB, "enter the measured selection size"\n'
                "!brats-uncertainty storage-preflight --selected-gib {SELECTED_GIB} "
                "--delivery-dir {WORK}/delivery --storage-dir {WORK}/raw",
            ),
            (
                "markdown",
                "## Official transfer\nSource: the **DOWNLOAD (142GB)** public package link on "
                "https://www.cancerimagingarchive.net/analysis-result/rsna-asnr-miccai-brats-2021/ "
                "(TCIA Faspex). Select ONLY `RSNA-ASNR-MICCAI-BraTS-2021.sums` and "
                "`RSNA-ASNR-MICCAI-BraTS-2021/BraTS2021_TrainingSet`. Do not download the "
                "`_dcm` or validation folders. Keep the hierarchy exactly as delivered.",
            ),
            (
                "code",
                'DELIVERY = f"{WORK}/delivery"\n'
                "os.makedirs(DELIVERY, exist_ok=True)\n"
                "# Exact ascli receive command, as confirmed by notebook 00's help output.\n"
                'RECEIVE_CMD = ""\n'
                'assert RECEIVE_CMD, "confirm the receive command in notebook 00 first"\n'
                "!{RECEIVE_CMD}",
            ),
            (
                "code",
                "# The two official B3/B4 files, saved byte-for-byte (never opened or re-saved)\n"
                "import urllib.request\n"
                "for name, url in [\n"
                '    ("BraTS2021_MappingToTCIA.xlsx", "https://www.cancerimagingarchive.net/'
                'wp-content/uploads/BraTS2021_MappingToTCIA.xlsx"),\n'
                '    ("UCSF-PDGM-metadata_v5.csv", "https://www.cancerimagingarchive.net/'
                'wp-content/uploads/UCSF-PDGM-metadata_v5.csv"),\n'
                "]:\n"
                '    urllib.request.urlretrieve(url, f"{DELIVERY}/{name}")\n'
                "!ls -la {DELIVERY}",
            ),
            (
                "code",
                "!brats-uncertainty verify-checksums --sums {DELIVERY}/"
                "RSNA-ASNR-MICCAI-BraTS-2021.sums --root {DELIVERY} "
                "--select RSNA-ASNR-MICCAI-BraTS-2021/BraTS2021_TrainingSet "
                "--out {EXPORT}/B2_provider_checksums.json",
            ),
            (
                "code",
                'ROUTE = "Direct official TCIA access into a private, access-restricted '
                'computational environment"\n'
                'ACQUIRED_BY = ""  # owner name\n'
                'VERSION = "Version 1 (2023/08/25)"\n'
                "assert ACQUIRED_BY\n"
                "common = (\n"
                '    f"--adapter local-import --delivered {DELIVERY} "\n'
                '    f\'--dataset-version "{VERSION}" --route "{ROUTE}" \'\n'
                '    f"--storage-root {WORK}/raw "\n'
                "    f'--storage-label \"ephemeral private compute session storage\" '\n"
                "    f'--acquired-by \"{ACQUIRED_BY}\" --out {EXPORT}/B2.json'\n"
                ")\n"
                "print(common)\n"
                "!brats-uncertainty acquire {common}   # dry run",
            ),
            ("code", "!brats-uncertainty acquire {common} --execute"),
            (
                "markdown",
                "## Hand-over\nDownload `/kaggle/working/export/` (`B2.json`, "
                "`B2_provider_checksums.json`, probe JSON). The owner reviews them, commits "
                "them as evidence and moves B2 with `gate-transition` in the owner's checkout. "
                "Raw data are deleted with this session; later sessions re-download and "
                "check `brats-uncertainty verify-inventory --record B2.json --root <raw>`.",
            ),
        ],
    ),
    "02_training_job.ipynb": _nb(
        "02 - JOB-02..07: one resumable training run (gated: B1-B12, D1-D6)",
        [
            ("code", PARAMS),
            ("code", SETUP),
            (
                "code",
                'JOB = ""             # JOB-02 ... JOB-07 (arm/seed from remote_compute.yaml)\n'
                "DATASET_ID = None    # nnU-Net dataset id\n"
                'MANIFEST_SHA256 = ""  # committed B5 manifest_sha256\n'
                'SPLIT_SHA256 = ""     # committed B12 split hash\n'
                'RESULTS_ROOT = "/kaggle/working/nnunet_results"  # checkpoints persist as output\n'
                'STATE_ROOT = "/kaggle/working/job_state"\n'
                "assert JOB and DATASET_ID and MANIFEST_SHA256 and SPLIT_SHA256",
            ),
            (
                "markdown",
                "## Preconditions\n1. Re-acquire the official files exactly as in notebook 01 "
                "and run `verify-inventory` against the committed B2 record: the tree must be "
                "byte-identical.\n2. Build the nnU-Net raw dataset from the frozen split "
                "(dataset writer added with the B10-B12 execution; training is gated until "
                "then).\n3. To resume, attach the previous session's output and copy "
                "`nnunet_results/` and `job_state/` back before running.",
            ),
            (
                "code",
                "!brats-uncertainty compute-preflight --job {JOB} --work-dir {WORK}\n"
                "!brats-uncertainty job-run {JOB} --dataset-id {DATASET_ID} "
                "--results-root {RESULTS_ROOT} --state-root {STATE_ROOT} "
                "--manifest-sha256 {MANIFEST_SHA256} --split-sha256 {SPLIT_SHA256}",
            ),
        ],
    ),
    "03_evaluation_job.ipynb": _nb(
        "03 - JOB-08: evaluation (gated: C gates, eval-v1)",
        [
            ("code", PARAMS),
            ("code", SETUP),
            (
                "markdown",
                "Runs only after B1-B12, D1-D6 and C1-C6 are closed and from the commit "
                "tagged `eval-v1` (SR4). Thresholds come from internal validation only and are "
                "frozen (C5) before any test or external evaluation.",
            ),
            ("code", "!python scripts/evaluation/analyze_primary.py --help"),
        ],
    ),
    "04_export_results.ipynb": _nb(
        "04 - Export results (provenance-checked artifacts only)",
        [
            ("code", PARAMS),
            ("code", SETUP),
            (
                "markdown",
                "Collect result artifacts (metrics, tables, figures, reports) with their "
                "provenance stamps into `/kaggle/working/export/results/`. Never images, "
                "predictions, labels or raw data. The owner commits them; the website is "
                "regenerated with `brats-uncertainty export-site-data`.",
            ),
            ("code", "!ls -R /kaggle/working/export | head -100"),
        ],
    ),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, nb in NOTEBOOKS.items():
        (OUT / name).write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
