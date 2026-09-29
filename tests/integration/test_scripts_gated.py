"""Every data/training/evaluation script must refuse to run in the current project state."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

GATED = [
    [
        "scripts/data/build_manifest.py",
        "--dataset-config",
        "configs/dataset/brats2021.yaml",
        "--data-root",
        "nonexistent",
        "--out",
        "nonexistent.json",
    ],
    ["scripts/experiments/train.py", "--dataset-id", "1", "--arm", "B", "--seed", "0"],
    [
        "scripts/data/record_acquisition.py",
        "--dataset",
        "d",
        "--dataset-version",
        "v",
        "--doi",
        "10.1/x",
        "--source-url",
        "https://example.org",
        "--route",
        "r",
        "--acquisition-date",
        "2000-01-01",
        "--acquired-by",
        "t",
        "--out",
        "nonexistent.json",
        "pyproject.toml",
    ],
    [
        "scripts/data/hash_metadata.py",
        "--gate",
        "B3",
        "--file",
        "BraTS2021_MappingToTCIA.xlsx",
        "--source-url",
        "https://example.org",
        "--doi",
        "10.1/x",
        "--out",
        "nonexistent.json",
    ],
    [
        "scripts/data/validate_data.py",
        "--dataset-config",
        "configs/dataset/brats2021.yaml",
        "--data-root",
        "nonexistent",
    ],
    [
        "scripts/data/derive_counts.py",
        "--crosswalk",
        "BraTS2021_MappingToTCIA.xlsx",
        "--b3-record",
        "nonexistent.json",
        "--out",
        "nonexistent.json",
    ],
    ["scripts/evaluation/analyze_primary.py", "--units", "nonexistent.csv", "--out", "x.json"],
]


@pytest.mark.parametrize("argv", GATED, ids=[a[0] for a in GATED])
def test_gated_script_refuses(repo_root: Path, argv: list[str]) -> None:
    proc = subprocess.run(
        [sys.executable, *argv], cwd=repo_root, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode != 0
    assert "ResearchGateError" in (proc.stderr + proc.stdout)
    assert not (repo_root / "nonexistent.json").exists()
    assert not (repo_root / "x.json").exists()


def test_safe_scripts_run(repo_root: Path) -> None:
    for script in ("scripts/checks/check_repository.py", "scripts/reporting/export_site_data.py"):
        args = [sys.executable, script] + (["--check"] if "export" in script else [])
        proc = subprocess.run(args, cwd=repo_root, capture_output=True, text=True, timeout=120)
        assert proc.returncode == 0, proc.stderr
