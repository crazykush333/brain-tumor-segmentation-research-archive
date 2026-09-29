"""Research-gate safeguards: every gated action must fail loudly in the current state."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from brats_uncertainty.errors import ConfigError, ProvenanceError, ResearchGateError
from brats_uncertainty.evaluation.guards import ACTION_REQUIREMENTS, check_action, require_action
from brats_uncertainty.evaluation.ledger import read_ledger, record_evaluation
from brats_uncertainty.evaluation.status import load_status, validate_status
from brats_uncertainty.experiments.metadata import ExperimentMetadata, load_experiment
from tests.conftest import make_status_repo


@pytest.mark.parametrize("action", sorted(ACTION_REQUIREMENTS))
def test_every_gated_action_is_blocked_now(repo_root: Path, action: str) -> None:
    with pytest.raises(ResearchGateError, match="not authorized"):
        require_action(action, repo_root)


def test_unknown_action_rejected(repo_root: Path) -> None:
    with pytest.raises(ResearchGateError):
        check_action("train_on_test_set", repo_root)


def test_current_status_matches_reported_state(repo_root: Path) -> None:
    st = load_status(repo_root)
    assert st.headline == "Protocol v1.0 frozen. Experimental execution pending."
    assert all(st.gate(f"A{i}").status in ("CLOSED", "OWNER_WAIVED") for i in range(1, 10))
    assert st.gate("B1").status == "PENDING"
    for gid in [*(f"B{i}" for i in range(2, 7)), *(f"C{i}" for i in range(1, 7))]:
        assert st.gate(gid).status == "NOT_STARTED", gid
    for gid in (f"D{i}" for i in range(1, 7)):
        assert st.gate(gid).status == "NOT_STARTED", gid
    for gid in (f"B{i}" for i in range(7, 13)):
        assert st.gate(gid).status == "LOCKED", gid
    assert st.results_available is False
    raw = st.raw
    assert raw["data"]["acquired"] is False
    assert raw["data"]["authorization"] == "PENDING"
    assert raw["data"]["approved_route"] is None
    assert raw["training"]["status"] == "NOT_STARTED"
    assert raw["evaluation"] == {"internal": "NOT_STARTED", "external": "NOT_STARTED"}
    assert raw["results"]["status"] == "UNAVAILABLE"


def test_guard_passes_only_when_gates_closed(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path, closed={"B1", "B2"})
    assert check_action("record_crosswalk_hash", root) == []
    assert check_action("validate_data", root) == []
    assert any(x.startswith("B3") for x in check_action("build_manifest", root))
    unmet = check_action("create_split", root)
    assert any(u.startswith("B3") for u in unmet)


def test_status_rejects_closure_without_evidence(tmp_path: Path, repo_root: Path) -> None:
    raw = yaml.safe_load((repo_root / "docs/project_status.yaml").read_text(encoding="utf-8"))
    raw["gates"][9]["status"] = "CLOSED"  # B1 without evidence
    with pytest.raises(ConfigError, match="without evidence"):
        validate_status(raw, repo_root)


def test_status_rejects_out_of_order_b_gates(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path, closed={"B2"})
    with pytest.raises(ConfigError, match="earlier gate"):
        load_status(root)


def test_status_rejects_waiver_outside_gate_a(repo_root: Path) -> None:
    raw = yaml.safe_load((repo_root / "docs/project_status.yaml").read_text(encoding="utf-8"))
    raw["gates"][9].update(status="OWNER_WAIVED", evidence="README.md", closed_on="2000-01-01")
    with pytest.raises(ConfigError, match="only gate-A"):
        validate_status(raw, repo_root)


def test_status_rejects_results_without_evidence(repo_root: Path) -> None:
    raw = yaml.safe_load((repo_root / "docs/project_status.yaml").read_text(encoding="utf-8"))
    raw["results"]["available"] = True
    with pytest.raises(ConfigError, match=r"results\.available"):
        validate_status(raw, repo_root)


def test_evaluation_ledger_single_evaluation(tmp_path: Path) -> None:
    p = tmp_path / "ledger.jsonl"
    record_evaluation(p, "internal_test", "B", "a" * 40, "eval-v1")
    with pytest.raises(ResearchGateError, match="SR4"):
        record_evaluation(p, "internal_test", "B", "a" * 40, "eval-v1")
    record_evaluation(
        p, "internal_test", "B", "b" * 40, "eval-v1", reevaluation_reason="bug fix (SR5)"
    )
    assert len(read_ledger(p)) == 2
    with pytest.raises(ValueError):
        record_evaluation(p, "training", "B", "a" * 40, "eval-v1")


def test_exp001_metadata_is_planned(repo_root: Path) -> None:
    m = load_experiment(repo_root / "experiments/EXP-001/metadata.yaml")
    assert m.status == "PLANNED"
    assert m.authorization is None and m.provenance is None and m.outputs == {}


def _meta() -> ExperimentMetadata:
    return ExperimentMetadata("EXP-999", "synthetic", "PLANNED", "v1.0", [], [])


def test_experiment_lifecycle_enforced() -> None:
    m = _meta()
    with pytest.raises(ResearchGateError, match="illegal transition"):
        m.transition("COMPLETED", on="2000", by="t", reason="r")
    with pytest.raises(ResearchGateError, match="requires authorization"):
        m.transition("AUTHORIZED", on="2000", by="t", reason="r")
    assert m.status == "PLANNED"
    m.authorization = {"authorized_by": "owner", "authorized_on": "2000-01-01", "reference": "ref"}
    m.transition("AUTHORIZED", on="2000", by="t", reason="r")
    m.transition("RUNNING", on="2000", by="t", reason="r")
    with pytest.raises(ProvenanceError, match="without provenance"):
        m.transition("COMPLETED", on="2000", by="t", reason="r")
    assert m.status == "RUNNING"
    m.transition("FAILED", on="2000", by="t", reason="r")
    m.transition("INVALIDATED", on="2000", by="t", reason="r")
    assert [h["to"] for h in m.history] == ["AUTHORIZED", "RUNNING", "FAILED", "INVALIDATED"]


def test_experiment_invalid_ids_and_versions() -> None:
    with pytest.raises(ConfigError):
        ExperimentMetadata("EXP-1", "t", "PLANNED", "v1.0", [], []).validate()
    with pytest.raises(ConfigError):
        ExperimentMetadata("EXP-001", "t", "PLANNED", "v0.5", [], []).validate()
    with pytest.raises(ConfigError):
        ExperimentMetadata("EXP-001", "t", "DONE", "v1.0", [], []).validate()
