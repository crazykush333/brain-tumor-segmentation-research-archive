from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from brats_uncertainty.evaluation.lifecycle import B_GATES, unlock_eligible

REPO_ROOT = Path(__file__).resolve().parents[1]
FAKE_ROUTE = "SYNTHETIC-TEST-ROUTE"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


def _copy_basics(tmp_path: Path) -> None:
    (tmp_path / "evidence").mkdir(parents=True, exist_ok=True)
    (tmp_path / "evidence" / "gate.md").write_text("fake test evidence\n", encoding="utf-8")
    (tmp_path / "docs/research").mkdir(parents=True, exist_ok=True)
    for rel in (
        "docs/research/FINAL_RESEARCH_PROTOCOL_v1.0.md",
        "docs/research/19_GATE_A_CLOSURE_AUDIT.md",
    ):
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    (tmp_path / "docs/data").mkdir(parents=True, exist_ok=True)
    for rel in ("docs/data/B1_DATA_ROUTE_AUTHORIZATION.md", "docs/data/TCIA_DATA_ROUTE_INQUIRY.md"):
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    (tmp_path / "configs/protocol").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "configs/protocol/protocol_v1.0.yaml", tmp_path / "configs/protocol/")


def fake_record_evidence(root: Path, gid: str, *, synthetic: bool = False, status: str = "") -> str:
    """Minimal gate-record JSON used as evidence in FAKE temporary repositories only."""
    rel = f"evidence/{gid}_record.json"
    body = {"gate": gid, "synthetic": synthetic, "schema_version": 2}
    if gid == "B6":
        body["status"] = status or "VERIFIED_FROM_SOURCE"
    (root / rel).write_text(json.dumps(body), encoding="utf-8")
    return rel


def make_status_repo(tmp_path: Path, closed: set[str]) -> Path:
    """A temporary *fake* repository whose status closes/passes the given gates.

    Used only to test the guards' and stages' positive paths. B gates in
    ``closed`` become PASSED (B2-B6 with minimal fake record evidence), other
    gates CLOSED; newly eligible B gates are unlocked (AUTHORIZED).
    """
    raw = yaml.safe_load((REPO_ROOT / "docs/project_status.yaml").read_text(encoding="utf-8"))
    _copy_basics(tmp_path)
    for g in raw["gates"]:
        if g["id"] in closed:
            is_b = g["id"] in B_GATES
            g["status"] = "PASSED" if is_b else "CLOSED"
            g["evidence"] = (
                fake_record_evidence(tmp_path, g["id"])
                if g["id"] in ("B2", "B3", "B4", "B5", "B6")
                else "evidence/gate.md"
            )
            g["closed_on"] = "2000-01-01"
    status_of = unlock_eligible({g["id"]: g["status"] for g in raw["gates"] if g["id"] in B_GATES})
    for g in raw["gates"]:
        if g["id"] in status_of:
            g["status"] = status_of[g["id"]]
    if "B1" in closed:
        raw["data"]["authorization"] = "APPROVED"
        raw["data"]["approved_route"] = FAKE_ROUTE
    if "B2" in closed:
        raw["data"]["acquired"] = True
    (tmp_path / "docs/project_status.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    return tmp_path


def make_verbatim_status_repo(tmp_path: Path) -> Path:
    """Fake repository with a byte-identical copy of the real status file (for line-edit tests)."""
    _copy_basics(tmp_path)
    shutil.copy(REPO_ROOT / "docs/project_status.yaml", tmp_path / "docs/project_status.yaml")
    return tmp_path
