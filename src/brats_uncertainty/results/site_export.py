"""Export website data (``website/data/*.json``) from the single sources of truth.

Sources: ``docs/project_status.yaml`` (status, gates, timeline),
``configs/protocol/protocol_v1.0.yaml`` (design parameters),
``experiments/*/metadata.yaml`` (experiment lifecycle) and
``results/index.json`` (provenance-checked result artifacts, if any).

The website never contains hand-typed status or numbers. ``--check`` mode
compares a fresh export to the committed files (CI sync test). Synthetic
artifacts are refused.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brats_uncertainty import __version__
from brats_uncertainty.errors import ProvenanceError
from brats_uncertainty.evaluation.status import load_status
from brats_uncertainty.experiments.metadata import load_experiment
from brats_uncertainty.protocol import load_protocol
from brats_uncertainty.results.artifacts import read_artifact

SITE_DATA_RELPATH = Path("website/data")
NO_RESULTS_STATEMENT = (
    "Scientific results are not yet available. Experimental execution is pending."
)


def _results(root: Path, status_raw: dict[str, Any]) -> dict[str, Any]:
    index_path = root / "results" / "index.json"
    artifacts: list[dict[str, Any]] = []
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        for rel in index.get("artifacts", []):
            body = read_artifact(root / rel)
            if body["provenance"]["synthetic"]:
                raise ProvenanceError(f"synthetic artifact listed in results index: {rel}")
            artifacts.append({"path": rel, **body})
    available = bool(status_raw["results"].get("available")) and bool(artifacts)
    if bool(status_raw["results"].get("available")) != bool(artifacts):
        raise ProvenanceError(
            "results.available in project_status.yaml disagrees with results/index.json"
        )
    return {
        "available": available,
        "statement": status_raw["results"].get("statement", NO_RESULTS_STATEMENT),
        "artifacts": artifacts,
    }


_DONE = ("CLOSED", "OWNER_WAIVED")


def _aggregate(statuses: list[str]) -> str:
    """Summarize a run of gates as one stage status."""
    if all(s in _DONE for s in statuses):
        return "COMPLETED"
    if all(s == "LOCKED" for s in statuses):
        return "LOCKED"
    if all(s == "NOT_STARTED" for s in statuses):
        return "NOT_STARTED"
    if any(s == "BLOCKED" for s in statuses):
        return "BLOCKED"
    if any(s in _DONE or s == "IN_PROGRESS" for s in statuses):
        return "IN_PROGRESS"
    return "PENDING"


def build_overview(raw: dict[str, Any], gate_status: dict[str, str]) -> list[dict[str, str]]:
    """High-level stage overview for the website, derived only from the status file."""

    def run(prefix: str, lo: int, hi: int) -> str:
        return _aggregate([gate_status[f"{prefix}{i}"] for i in range(lo, hi + 1)])

    grouping = run("B", 7, 9)
    ev = raw["evaluation"]
    evaluation = (
        "NOT_STARTED"
        if ev["internal"] == ev["external"] == "NOT_STARTED"
        else ("COMPLETED" if ev["internal"] == ev["external"] == "COMPLETED" else "IN_PROGRESS")
    )
    return [
        {
            "key": "protocol",
            "label": f"Protocol {raw['protocol']['version']}",
            "status": str(raw["protocol"]["status"]),
            "detail": f"frozen {raw['protocol']['frozen_on']}, tag {raw['protocol']['git_tag']}",
        },
        {
            "key": "b1",
            "label": "B1 Data authorization",
            "status": gate_status["B1"],
            "detail": "written data-route confirmation required before any data acquisition",
        },
        {
            "key": "data",
            "label": "Data acquisition",
            "status": run("B", 2, 6),
            "detail": "gates B2-B6: acquisition, hashes, manifest, counts",
        },
        {
            "key": "grouping",
            "label": "Patient grouping",
            "status": grouping,
            "detail": "gates B7-B9: same-patient screen, manual review, patient groups",
        },
        {
            "key": "split",
            "label": "Final split",
            "status": run("B", 10, 12),
            "detail": "gates B10-B12; created once",
        },
        {
            "key": "training",
            "label": "Training",
            "status": str(raw["training"]["status"]),
            "detail": "arms A/B x seeds 0-2",
        },
        {
            "key": "evaluation",
            "label": "Evaluation",
            "status": evaluation,
            "detail": f"internal: {ev['internal']}; external: {ev['external']}",
        },
        {
            "key": "results",
            "label": "Results",
            "status": "AVAILABLE" if raw["results"]["status"] == "AVAILABLE" else "NOT_AVAILABLE",
            "detail": str(raw["results"]["statement"]),
        },
    ]


def build_site_data(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root)
    protocol = load_protocol(root)
    status = load_status(root)
    experiments = []
    for meta_path in sorted((root / "experiments").glob("EXP-*/metadata.yaml")):
        m = load_experiment(meta_path)
        experiments.append(
            {
                "id": m.experiment_id,
                "title": m.title,
                "status": m.status,
                "protocol_sections": m.protocol_sections,
                "required_gates": m.required_gates,
                "notes": m.notes,
            }
        )
    raw = status.raw
    gates = [
        {
            "id": g.id,
            "group": g.group,
            "title": g.title,
            "status": g.status,
            "closed_on": g.closed_on,
        }
        for g in status.gates.values()
    ]
    return {
        "status.json": {
            "headline": raw["headline"],
            "last_updated": raw.get("last_updated"),
            "package_version": __version__,
            "protocol": raw["protocol"],
            "gates": gates,
            "gate_groups": raw.get("gate_groups", {}),
            "next_step": raw.get("next_step"),
            "timeline": raw.get("timeline", []),
            "overview": build_overview(raw, {g.id: g.status for g in status.gates.values()}),
            "data": {
                k: raw["data"].get(k)
                for k in (
                    "authorization",
                    "approved_route",
                    "acquired",
                    "inquiry_sent",
                    "statement",
                )
            },
            "project": raw.get("project", {}),
        },
        "protocol.json": {
            "version": protocol.version,
            "sha256": protocol.raw["protocol"]["sha256"],
            "git_tag": protocol.raw["protocol"]["git_tag"],
            "frozen_on": protocol.raw["protocol"]["frozen_on"],
            "parameters": {k: v for k, v in protocol.raw.items() if k != "protocol"},
        },
        "experiments.json": {"experiments": experiments},
        "results.json": _results(root, raw),
    }


def _dump(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def export_site_data(repo_root: str | Path, *, check: bool = False) -> list[str]:
    """Write (or, with ``check``, compare) the website data files.

    Returns the list of files that differ (check mode) or were written.
    """
    root = Path(repo_root)
    out_dir = root / SITE_DATA_RELPATH
    data = build_site_data(root)
    changed: list[str] = []
    for name, obj in data.items():
        path = out_dir / name
        text = _dump(obj)
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current != text:
            changed.append(name)
            if not check:
                out_dir.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")
    return changed
