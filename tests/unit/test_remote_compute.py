"""Remote compute package: probe classification, resumable training jobs, re-acquisition check,
Kaggle notebooks. No GPU, no network and no data are used (facts are injected)."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from brats_uncertainty.cli import main
from brats_uncertainty.compute import jobs as jobs_mod
from brats_uncertainty.compute.jobs import decide_training, load_jobs, read_record, run_training_job
from brats_uncertainty.compute.probe import (
    COMPUTE_CONFIG,
    GIB,
    STATUSES,
    classify,
    collect_facts,
    detect_environment,
)
from brats_uncertainty.data.records import InventoryEntry, inventory, verify_inventory
from brats_uncertainty.errors import ProvenanceError, ResearchGateError
from brats_uncertainty.models.nnunet import (
    RunSpec,
    run_results_dir,
    train_command,
    train_environment,
)
from brats_uncertainty.results.site_export import list_amendments
from tests.conftest import REPO_ROOT, make_status_repo

CFG = yaml.safe_load((REPO_ROOT / COMPUTE_CONFIG).read_text(encoding="utf-8"))
H = "a" * 64


def _facts(**over: Any) -> dict[str, Any]:
    f: dict[str, Any] = {
        "environment": "vm",
        "python": "3.11.0",
        "platform": "Linux",
        "cpu_count": 8,
        "ram_total_bytes": 32 * GIB,
        "ram_available_bytes": 28 * GIB,
        "work_dir": "/tmp/brats",
        "disk_free_bytes": 200 * GIB,
        "disk_total_bytes": 500 * GIB,
        "gpu": {
            "source": "torch",
            "cuda_available": True,
            "name": "SYNTHETIC GPU",
            "vram_bytes": 16 * GIB,
            "cuda_version": "12.1",
        },
        "packages": {"torch": "2.3.0", "nnunetv2": "2.5.1", "nibabel": "5.2", "openpyxl": "3.1"},
        "transfer_client": {"ascli": True, "ascp": True},
        "internet": {u: "HTTP 200" for u in CFG["requirements"]["internet"]["probe_urls"]},
        "git": {"commit": "f" * 40, "dirty": False},
        "protocol": {"version": "v1.0", "verified": True},
    }
    f.update(over)
    return f


# ================================================================ probe classification
def test_ready_vm_and_kaggle_limits() -> None:
    assert classify(_facts(), CFG, "JOB-02").status == "READY"
    k = classify(_facts(environment="kaggle"), CFG, "JOB-02")
    assert k.status == "READY_WITH_LIMITS"
    assert any("session_limit_h" in x for x in k.limits)


@pytest.mark.parametrize(
    ("over", "job", "needle"),
    [
        (
            {"gpu": {"cuda_available": False, "name": None, "vram_bytes": None}},
            "JOB-02",
            "no CUDA GPU",
        ),
        (
            {"gpu": {"cuda_available": True, "name": "x", "vram_bytes": 8 * GIB}},
            "JOB-02",
            "GPU memory 8.0 GiB < minimum",
        ),
        ({"ram_total_bytes": int(7.4 * GIB)}, "JOB-02", "RAM 7.4 GiB < minimum"),
        ({"packages": {"torch": "2.3", "nnunetv2": None}}, "JOB-02", "nnunetv2 not installed"),
        ({"disk_free_bytes": 10 * GIB}, "JOB-02", "free disk 10.0 GiB"),
        ({"transfer_client": {"ascli": False, "ascp": False}}, "JOB-01", "transfer client"),
        (
            {"internet": {"https://faspex.cancerimagingarchive.net/": "UNREACHABLE (x)"}},
            "JOB-01",
            "unreachable",
        ),
        ({"protocol": {"verified": False, "error": "hash"}}, "JOB-02", "frozen protocol"),
    ],
)
def test_blockers_make_environment_not_ready(over: dict[str, Any], job: str, needle: str) -> None:
    r = classify(_facts(**over), CFG, job)
    assert r.status == "NOT_READY"
    assert any(needle in b for b in r.blockers), r.blockers


def test_b2_job_needs_no_gpu_but_needs_the_transfer_client() -> None:
    no_gpu = {"gpu": {"cuda_available": False, "name": None, "vram_bytes": None}}
    assert classify(_facts(**no_gpu, packages={}), CFG, "JOB-01").status == "READY"
    r = classify(_facts(**no_gpu), CFG, "JOB-02")
    assert r.status == "NOT_READY"


def test_soft_limits_and_offline() -> None:
    r = classify(_facts(ram_total_bytes=16 * GIB, internet=None), CFG, "JOB-02")
    assert r.status == "READY_WITH_LIMITS"
    assert any("below the recommended" in x for x in r.limits)
    assert any("--offline" in x for x in r.limits)
    down = {"https://pypi.org/simple/nnunetv2/": "UNREACHABLE (x)"}
    assert classify(_facts(internet=down), CFG, "JOB-02").status == "READY_WITH_LIMITS"
    assert classify(_facts(git={"commit": "f" * 40, "dirty": True}), CFG, "JOB-02").limits
    with pytest.raises(ValueError, match="unknown job"):
        classify(_facts(), CFG, "JOB-99")


def test_detect_environment() -> None:
    assert detect_environment({"KAGGLE_KERNEL_RUN_TYPE": "Interactive"}) == "kaggle"
    assert detect_environment({"COLAB_RELEASE_TAG": "x"}) == "colab"
    assert detect_environment({}) == "vm"


def test_collect_facts_uses_head_requests_only(tmp_path: Path) -> None:
    seen: list[str] = []

    def fake_head(url: str, timeout: float) -> str:
        seen.append(url)
        return "HTTP 200"

    facts = collect_facts(REPO_ROOT, tmp_path, head=fake_head)
    assert seen == CFG["requirements"]["internet"]["probe_urls"]
    assert all(u.startswith("https://") for u in seen)
    assert facts["protocol"]["verified"] is True
    assert set(facts) >= {"gpu", "ram_total_bytes", "disk_free_bytes", "packages", "git"}
    assert collect_facts(REPO_ROOT, tmp_path, offline=True, head=fake_head)["internet"] is None
    assert len(seen) == len(CFG["requirements"]["internet"]["probe_urls"])


def test_compute_preflight_cli_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "probe.json"
    rc = main(["compute-preflight", "--offline", "--work-dir", str(tmp_path), "--json", str(out)])
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] in STATUSES
    assert rc == (1 if report["status"] == "NOT_READY" else 0)


# ================================================================ training runs
def test_per_run_results_dirs_and_resume_flag(tmp_path: Path) -> None:
    roots = {run_results_dir(tmp_path, RunSpec(a, s)) for a in "AB" for s in (0, 1, 2)}
    assert len(roots) == 6  # seeds never share an nnU-Net output folder
    env = train_environment(RunSpec("B", 2), tmp_path)
    assert env["nnUNet_results"].endswith("armB_seed2") and env["BRATS_UNC_SEED"] == "2"
    assert "nnUNet_results" not in train_environment(RunSpec("A", 0))
    assert train_command(501, RunSpec("A", 0))[-1] != "--c"
    assert train_command(501, RunSpec("A", 0), resume=True)[-1] == "--c"


def test_job_plan_is_exactly_the_protocol_runs() -> None:
    jobs = load_jobs(REPO_ROOT)
    runs = sorted((j.arm, j.seed) for j in jobs.values() if j.kind == "training")
    assert runs == [("A", 0), ("A", 1), ("A", 2), ("B", 0), ("B", 1), ("B", 2)]
    assert all(j.gated_action == "train_main" for j in jobs.values() if j.kind == "training")
    assert jobs["JOB-01"].gated_action == "acquire_data" and not jobs["JOB-01"].needs_gpu


def _ckpt(root: Path, name: str) -> Path:
    p = root / "Dataset501_X" / "Trainer__plans__3d_fullres" / "fold_0" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"synthetic checkpoint")
    return p


def test_training_decisions(tmp_path: Path) -> None:
    run_root = tmp_path / "armA_seed0"
    assert decide_training(None, run_root, allow_restart=False).action == "start"
    rec = {"status": "FAILED"}
    assert decide_training(rec, run_root, allow_restart=False).action == "refuse"
    assert decide_training(rec, run_root, allow_restart=True).action == "restart"
    _ckpt(run_root, "checkpoint_latest.pth")
    d = decide_training(rec, run_root, allow_restart=False)
    assert d.action == "resume" and d.checkpoint is not None
    assert (
        decide_training(None, run_root, allow_restart=True).action == "refuse"
    )  # unknown provenance
    assert decide_training({"status": "COMPLETED"}, run_root, allow_restart=True).action == "refuse"


def test_training_job_is_gated(tmp_path: Path, repo_root: Path) -> None:
    job = load_jobs(repo_root)["JOB-02"]
    for root in (repo_root, make_status_repo(tmp_path / "pending", closed=set())):
        with pytest.raises(ResearchGateError):
            run_training_job(
                root,
                job,
                dataset_id=501,
                results_root=tmp_path / "res",
                state_root=tmp_path / "state",
                manifest_sha256=H,
                split_sha256=H,
                runner=lambda c, e: pytest.fail("must not run"),  # type: ignore[arg-type,return-value]
            )
    assert not (tmp_path / "state").exists()


def test_training_job_resumes_and_records(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "repo"
    monkeypatch.setattr(jobs_mod, "require_action", lambda action, repo: None)  # gates tested above
    monkeypatch.setattr(jobs_mod, "git_commit", lambda r: "f" * 40)
    monkeypatch.setattr(jobs_mod, "git_is_dirty", lambda r: False)
    job = load_jobs(REPO_ROOT)["JOB-05"]  # arm B seed 0
    calls: list[tuple[list[str], dict[str, str]]] = []
    run_root = tmp_path / "res" / "armB_seed0"

    def interrupted(cmd: list[str], env: dict[str, str]) -> int:
        calls.append((cmd, env))
        _ckpt(run_root, "checkpoint_latest.pth")
        return 1

    def finishes(cmd: list[str], env: dict[str, str]) -> int:
        calls.append((cmd, env))
        _ckpt(run_root, "checkpoint_final.pth")
        return 0

    kw: dict[str, Any] = {
        "dataset_id": 501,
        "results_root": tmp_path / "res",
        "state_root": tmp_path / "state",
        "manifest_sha256": H,
        "split_sha256": "b" * 64,
    }
    rec = run_training_job(REPO_ROOT, job, runner=interrupted, **kw)  # type: ignore[arg-type]
    assert rec["status"] == "INTERRUPTED" and rec["attempts"][0]["action"] == "start"
    assert "--c" not in calls[0][0]
    assert calls[0][1]["nnUNet_results"] == str(run_root)
    rec = run_training_job(REPO_ROOT, job, runner=finishes, **kw)  # type: ignore[arg-type]
    assert rec["status"] == "COMPLETED" and calls[1][0][-1] == "--c"
    assert rec["attempts"][1]["resumed_from"] == "checkpoint_latest.pth"
    assert (rec["arm"], rec["seed"], rec["split_sha256"]) == ("B", 0, "b" * 64)
    assert read_record(tmp_path / "state", "JOB-05") == rec
    with pytest.raises(ProvenanceError, match="COMPLETED"):
        run_training_job(REPO_ROOT, job, runner=finishes, **kw)  # type: ignore[arg-type]
    assert root.exists() is False


def test_training_job_failures_are_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jobs_mod, "require_action", lambda action, repo: None)
    monkeypatch.setattr(jobs_mod, "git_commit", lambda r: "f" * 40)
    monkeypatch.setattr(jobs_mod, "git_is_dirty", lambda r: False)
    job = load_jobs(REPO_ROOT)["JOB-03"]
    kw: dict[str, Any] = {
        "dataset_id": 501,
        "results_root": tmp_path / "res",
        "state_root": tmp_path / "state",
        "manifest_sha256": H,
        "split_sha256": H,
    }
    rec = run_training_job(REPO_ROOT, job, runner=lambda c, e: 2, **kw)  # type: ignore[arg-type]
    assert rec["status"] == "FAILED"
    with pytest.raises(ProvenanceError, match="no checkpoint"):  # never a silent restart
        run_training_job(REPO_ROOT, job, runner=lambda c, e: 0, **kw)  # type: ignore[arg-type]

    def crash(c: list[str], e: dict[str, str]) -> int:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_training_job(  # type: ignore[arg-type]
            REPO_ROOT, job, runner=crash, allow_restart=True, **kw
        )
    rec2 = read_record(tmp_path / "state", "JOB-03")
    assert rec2 is not None and rec2["status"] == "FAILED"
    assert [a["action"] for a in rec2["attempts"]] == ["start", "restart"]
    with pytest.raises(ProvenanceError, match="split_sha256 changed"):
        run_training_job(  # type: ignore[arg-type]
            REPO_ROOT,
            job,
            runner=lambda c, e: 0,
            allow_restart=True,
            **{**kw, "split_sha256": "c" * 64},
        )
    with pytest.raises(ProvenanceError, match="SHA-256"):
        run_training_job(REPO_ROOT, job, **{**kw, "manifest_sha256": "abc"})


# ================================================================ re-acquisition check
def test_verify_inventory(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.bin").write_bytes(b"x")
    (tmp_path / "y.bin").write_bytes(b"y")
    inv = inventory(tmp_path)
    assert verify_inventory(inv, tmp_path) == {"missing": [], "mismatched": [], "unexpected": []}
    (tmp_path / "a" / "x.bin").write_bytes(b"changed")
    (tmp_path / "y.bin").unlink()
    (tmp_path / "z.bin").write_bytes(b"z")
    assert verify_inventory(inv, tmp_path) == {
        "missing": ["y.bin"],
        "mismatched": ["a/x.bin"],
        "unexpected": ["z.bin"],
    }
    assert verify_inventory([InventoryEntry("q", "0" * 64, 1)], tmp_path)["missing"] == ["q"]


# ================================================================ notebooks and docs
def _load_generator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "mk", REPO_ROOT / "scripts/remote/make_kaggle_notebooks.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_notebooks_are_generated_and_safe() -> None:
    gen = _load_generator()
    kdir = REPO_ROOT / "experiments/kaggle"
    for name, nb in gen.NOTEBOOKS.items():
        on_disk = json.loads((kdir / name).read_text(encoding="utf-8"))
        assert on_disk == json.loads(json.dumps(nb)), f"{name} is stale: rerun the generator"
        text = (kdir / name).read_text(encoding="utf-8")
        for bad in ("kaggle datasets", "kaggle.json", "password", "api_key", "dataset-metadata"):
            assert bad not in text.lower(), (name, bad)
        hosts = set(re.findall(r"https://([a-z0-9.-]+)", text))
        assert hosts <= {"www.cancerimagingarchive.net"}, (name, hosts)
    probe_nb = json.loads((kdir / "00_environment_probe.ipynb").read_text(encoding="utf-8"))
    code = "\n".join(c["source"] for c in probe_nb["cells"] if c["cell_type"] == "code")
    for downloading in ("acquire", "urlretrieve", "RECEIVE_CMD", "--execute", "packages receive"):
        assert downloading not in code, downloading  # the probe notebook transfers no data


def test_amendment_list_excludes_administrative_entries(repo_root: Path) -> None:
    assert [a["id"] for a in list_amendments(repo_root)] == ["v1.0-A1"]
    assert (
        repo_root / "docs/research/protocol-amendments/2026-10-01_compute-environment.md"
    ).is_file()
