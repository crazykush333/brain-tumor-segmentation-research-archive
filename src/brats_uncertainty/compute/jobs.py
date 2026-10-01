"""Resumable remote jobs (configs/compute/remote_compute.yaml ``jobs``).

Each job keeps a run record (``<state_root>/<JOB>/run_record.json``) with its
provenance and every attempt. Rules:

- a COMPLETED job is never re-run;
- a training job with an earlier attempt resumes only from its own verified
  latest checkpoint (nnU-Net ``--c``); without one, it refuses unless the
  operator passes an explicit restart, which is recorded as such (never a
  silent restart from scratch);
- a non-zero exit is recorded as FAILED (or INTERRUPTED when a later resume is
  still possible); success requires ``checkpoint_final.pth``;
- execution is gated (``train_main``: B1-B12 and D1-D6 closed) and stamped with
  the protocol version/hash, git commit, config hashes, dataset manifest hash,
  split hash, seed and hardware.

Each training run has its own ``nnUNet_results`` root (models.nnunet.run_results_dir),
so the three seeds of an arm never overwrite each other.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from brats_uncertainty.compute.probe import COMPUTE_CONFIG
from brats_uncertainty.errors import ProvenanceError
from brats_uncertainty.evaluation.guards import require_action
from brats_uncertainty.models.nnunet import (
    RunSpec,
    run_results_dir,
    train_command,
    train_environment,
)
from brats_uncertainty.utils.git import git_commit, git_is_dirty
from brats_uncertainty.utils.hashing import sha256_file
from brats_uncertainty.utils.io import read_yaml

TRAINING_CONFIG = Path("configs/experiments/main_training.yaml")
RECORD_NAME = "run_record.json"
JOB_STATUSES = ("RUNNING", "INTERRUPTED", "FAILED", "COMPLETED")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    kind: str
    gated_action: str
    needs_gpu: bool
    arm: str | None = None
    seed: int | None = None

    @property
    def run(self) -> RunSpec:
        if self.kind != "training" or self.arm is None or self.seed is None:
            raise ValueError(f"{self.job_id} is not a training job")
        return RunSpec(self.arm, self.seed)


def load_jobs(repo_root: Path) -> dict[str, JobSpec]:
    cfg = read_yaml(repo_root / COMPUTE_CONFIG)
    jobs = {}
    for jid, j in cfg["jobs"].items():
        jobs[jid] = JobSpec(
            jid,
            str(j["kind"]),
            str(j["gated_action"]),
            bool(j["needs_gpu"]),
            j.get("arm"),
            None if j.get("seed") is None else int(j["seed"]),
        )
    runs = sorted((s.arm, s.seed) for s in jobs.values() if s.kind == "training")
    expected = sorted((a, sd) for a in ("A", "B") for sd in (0, 1, 2))
    if runs != expected:
        raise ProvenanceError(f"training jobs must be exactly arms A/B x seeds 0/1/2, got {runs}")
    return jobs


def _now() -> str:
    return datetime.now(UTC).isoformat()


def read_record(state_root: Path, job_id: str) -> dict[str, Any] | None:
    p = state_root / job_id / RECORD_NAME
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def _write_record(state_root: Path, job_id: str, record: dict[str, Any]) -> None:
    p = state_root / job_id / RECORD_NAME
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".part")
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(p)


def find_checkpoint(run_root: Path, name: str) -> Path | None:
    """nnU-Net writes <root>/<Dataset>/<trainer>__<plans>__<config>/fold_0/<name>."""
    hits = sorted(run_root.glob(f"*/*/fold_0/{name}")) if run_root.is_dir() else []
    if len(hits) > 1:
        raise ProvenanceError(f"ambiguous checkpoints under {run_root.name}: {len(hits)}")
    return hits[0] if hits else None


@dataclass(frozen=True)
class TrainingDecision:
    action: str  # "start" | "resume" | "restart" | "refuse"
    reason: str
    checkpoint: Path | None = None


def decide_training(
    record: dict[str, Any] | None, run_root: Path, *, allow_restart: bool
) -> TrainingDecision:
    """Start, resume from a verified checkpoint, explicitly restart, or refuse (pure)."""
    final = find_checkpoint(run_root, "checkpoint_final.pth")
    latest = find_checkpoint(run_root, "checkpoint_latest.pth")
    if record is None:
        if final or latest:
            return TrainingDecision(
                "refuse", "checkpoints exist without a run record (unknown provenance)"
            )
        return TrainingDecision("start", "no earlier attempt")
    if record["status"] == "COMPLETED":
        return TrainingDecision("refuse", "job already COMPLETED; never re-run")
    if latest is not None:
        return TrainingDecision("resume", "earlier attempt; latest checkpoint found", latest)
    if allow_restart:
        return TrainingDecision("restart", "earlier attempt without checkpoint; explicit restart")
    return TrainingDecision(
        "refuse",
        "earlier attempt but no checkpoint to resume from; pass an explicit restart "
        "(recorded) rather than silently starting from scratch",
    )


def _hardware() -> dict[str, Any]:
    from brats_uncertainty.compute.probe import _gpu_facts, _ram_bytes, detect_environment

    return {
        "environment": detect_environment(),
        "gpu": _gpu_facts(),
        "ram_total_bytes": _ram_bytes()[0],
        "cpu_count": os.cpu_count(),
    }


def run_training_job(
    repo_root: Path,
    job: JobSpec,
    *,
    dataset_id: int,
    results_root: Path,
    state_root: Path,
    manifest_sha256: str,
    split_sha256: str,
    allow_restart: bool = False,
    runner: Callable[[Sequence[str], dict[str, str]], int] | None = None,
) -> dict[str, Any]:
    """Execute (or resume) one protocol training run. Gated; recorded; never silent."""
    require_action(job.gated_action, repo_root)  # B1-B12 and D1-D6 closed
    for name, h in (("manifest_sha256", manifest_sha256), ("split_sha256", split_sha256)):
        if not _HEX64.match(h):
            raise ProvenanceError(f"{name} must be a SHA-256 hex digest")
    commit = git_commit(repo_root)
    if commit is None or git_is_dirty(repo_root) is not False:
        raise ProvenanceError("training runs require a clean, committed checkout")
    from brats_uncertainty.protocol import load_protocol

    protocol = load_protocol(repo_root)
    run = job.run
    run_root = run_results_dir(results_root, run)
    record = read_record(state_root, job.job_id)
    decision = decide_training(record, run_root, allow_restart=allow_restart)
    if decision.action == "refuse":
        raise ProvenanceError(f"{job.job_id}: {decision.reason}")
    stamp = {
        "protocol_version": protocol.version,
        "protocol_sha256": str(protocol.raw["protocol"]["sha256"]),
        "git_commit": commit,
        "config_sha256": {
            str(p): sha256_file(repo_root / p) for p in (COMPUTE_CONFIG, TRAINING_CONFIG)
        },
        "dataset_manifest_sha256": manifest_sha256,
        "split_sha256": split_sha256,
    }
    if record is None:
        record = {
            "job_id": job.job_id,
            "kind": job.kind,
            "arm": run.arm,
            "seed": run.seed,
            "trainer": run.trainer,
            "run_id": run.run_id,
            "attempts": [],
            **stamp,
        }
    else:
        for k, v in stamp.items():
            if k != "git_commit" and record.get(k) != v:
                raise ProvenanceError(f"{job.job_id}: {k} changed since the first attempt")
    cmd = train_command(dataset_id, run, resume=decision.action == "resume")
    env = train_environment(run, results_root)
    attempt: dict[str, Any] = {
        "started_at": _now(),
        "action": decision.action,
        "reason": decision.reason,
        "resumed_from": decision.checkpoint.name if decision.checkpoint else None,
        "git_commit": commit,
        "command": cmd,
        "hardware": _hardware(),
    }
    record["attempts"].append(attempt)
    record["status"] = "RUNNING"
    _write_record(state_root, job.job_id, record)

    def _default(c: Sequence[str], e: dict[str, str]) -> int:
        return subprocess.run(list(c), env={**os.environ, **e}, check=False).returncode

    try:
        code = (runner or _default)(cmd, env)
    except BaseException:
        attempt.update(ended_at=_now(), exit_code=None)
        record["status"] = (
            "INTERRUPTED" if find_checkpoint(run_root, "checkpoint_latest.pth") else "FAILED"
        )
        _write_record(state_root, job.job_id, record)
        raise
    attempt.update(ended_at=_now(), exit_code=code)
    if code == 0 and find_checkpoint(run_root, "checkpoint_final.pth"):
        record["status"] = "COMPLETED"
    elif find_checkpoint(run_root, "checkpoint_latest.pth"):
        record["status"] = "INTERRUPTED"
    else:
        record["status"] = "FAILED"
    _write_record(state_root, job.job_id, record)
    return record
