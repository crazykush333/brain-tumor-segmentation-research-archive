from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


def make_status_repo(tmp_path: Path, closed: set[str]) -> Path:
    """A temporary *fake* repository whose status closes the given gates.

    Used only to test the guards' positive path. Evidence files are empty
    placeholders inside the temporary directory.
    """
    raw = yaml.safe_load((REPO_ROOT / "docs/project_status.yaml").read_text(encoding="utf-8"))
    (tmp_path / "evidence").mkdir()
    ev = tmp_path / "evidence" / "gate.md"
    ev.write_text("synthetic test evidence\n", encoding="utf-8")
    (tmp_path / "docs/research").mkdir(parents=True)
    for rel in (
        "docs/research/FINAL_RESEARCH_PROTOCOL_v1.0.md",
        "docs/research/19_GATE_A_CLOSURE_AUDIT.md",
    ):
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    for g in raw["gates"]:
        if g["id"] in closed:
            g["status"] = "CLOSED"
            g["evidence"] = "evidence/gate.md"
            g["closed_on"] = "2000-01-01"
    (tmp_path / "docs/project_status.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    return tmp_path
