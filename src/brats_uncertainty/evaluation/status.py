"""Load and validate ``docs/project_status.yaml`` (single source of project state).

The website, the README status line and the research-gate guards all read this
file. A gate may only be recorded as CLOSED with an evidence path that exists
in the repository and a closure date; B-gates must close in protocol order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from brats_uncertainty.errors import ConfigError
from brats_uncertainty.utils.io import read_yaml
from brats_uncertainty.utils.paths import find_repo_root

STATUS_RELPATH = Path("docs/project_status.yaml")
GATE_STATUSES = ("CLOSED", "OWNER_WAIVED", "IN_PROGRESS", "PENDING", "NOT_STARTED", "BLOCKED")
EXPERIMENT_STATUSES = ("PLANNED", "AUTHORIZED", "RUNNING", "COMPLETED", "FAILED", "INVALIDATED")
_GATE_ID = re.compile(r"^[A-D](\d{1,2})?$")


@dataclass(frozen=True)
class Gate:
    id: str
    group: str
    title: str
    status: str
    evidence: str | None
    closed_on: str | None

    @property
    def is_closed(self) -> bool:
        return self.status == "CLOSED"


@dataclass(frozen=True)
class ProjectStatus:
    raw: dict[str, Any]
    gates: dict[str, Gate]
    repo_root: Path

    @property
    def headline(self) -> str:
        return str(self.raw["headline"])

    def gate(self, gate_id: str) -> Gate:
        if gate_id not in self.gates:
            raise ConfigError(f"unknown gate {gate_id!r}")
        return self.gates[gate_id]

    @property
    def results_available(self) -> bool:
        return bool(self.raw.get("results", {}).get("available", False))


def _order_key(gid: str) -> tuple[str, int]:
    return gid[0], int(gid[1:]) if len(gid) > 1 else 0


def validate_status(raw: dict[str, Any], repo_root: Path) -> dict[str, Gate]:
    for key in ("schema_version", "headline", "protocol", "gates", "experiments", "results"):
        if key not in raw:
            raise ConfigError(f"project_status.yaml missing key {key!r}")
    gates: dict[str, Gate] = {}
    for item in raw["gates"]:
        gid = str(item["id"])
        if not _GATE_ID.match(gid):
            raise ConfigError(f"invalid gate id {gid!r}")
        if gid in gates:
            raise ConfigError(f"duplicate gate id {gid!r}")
        status = str(item["status"])
        if status not in GATE_STATUSES:
            raise ConfigError(f"gate {gid}: invalid status {status!r}")
        if status == "OWNER_WAIVED" and not gid.startswith("A"):
            raise ConfigError(f"gate {gid}: only gate-A items may be owner-waived")
        evidence = item.get("evidence")
        if status in ("CLOSED", "OWNER_WAIVED"):
            if not evidence or not item.get("closed_on"):
                raise ConfigError(f"gate {gid} is {status} without evidence and closed_on")
            if not (repo_root / str(evidence).split("#")[0]).exists():
                raise ConfigError(f"gate {gid}: evidence path does not exist: {evidence}")
        gates[gid] = Gate(
            id=gid,
            group=gid[0],
            title=str(item.get("title", "")),
            status=status,
            evidence=str(evidence) if evidence else None,
            closed_on=str(item["closed_on"]) if item.get("closed_on") else None,
        )
    # B gates close strictly in protocol order
    b_ids = sorted((g for g in gates if g.startswith("B") and len(g) > 1), key=_order_key)
    seen_open = None
    for gid in b_ids:
        if gates[gid].is_closed and seen_open is not None:
            raise ConfigError(f"gate {gid} is CLOSED while earlier gate {seen_open} is not")
        if not gates[gid].is_closed and seen_open is None:
            seen_open = gid
    for exp_id, exp in raw["experiments"].items():
        if exp.get("status") not in EXPERIMENT_STATUSES:
            raise ConfigError(f"experiment {exp_id}: invalid status {exp.get('status')!r}")
    if raw["results"].get("available") and not raw["results"].get("evidence"):
        raise ConfigError("results.available is true without evidence")
    return gates


def load_status(repo_root: str | Path | None = None) -> ProjectStatus:
    root = Path(repo_root) if repo_root is not None else find_repo_root()
    path = root / STATUS_RELPATH
    if not path.is_file():
        raise ConfigError(f"missing {STATUS_RELPATH}")
    raw = read_yaml(path)
    if not isinstance(raw, dict):
        raise ConfigError("project_status.yaml must be a mapping")
    return ProjectStatus(raw=raw, gates=validate_status(raw, root), repo_root=root)
