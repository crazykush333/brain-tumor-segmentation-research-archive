"""Validation of gate evidence (what a gate may legitimately PASS, FAIL or BLOCK on).

Called by ``evaluation.status.validate_status`` for every gate that carries
evidence. Rules:

All evidence
    Repository-relative path using safe characters, inside the repository,
    existing, not git-ignored and (in a git checkout) in the git index, i.e.
    committed or staged.

B1 PASSED
    ``docs/data/B1_EVIDENCE_<response date>.md`` recording *external written*
    authorization (see B1_EVIDENCE_TEMPLATE.md): every field of the template
    exactly once and filled in, an external evidence type (TCIA Help Desk,
    official TCIA instruction, other authoritative written authorization), the
    protocol dataset and DOI, ``Approved route: <data.approved_route>``,
    ``Authorization status: AUTHORIZED``, ``Conclusion: APPROVED`` and the
    provider's exact wording quoted. The B1 record, the inquiry and the
    template are documentation, never authorization.

B2-B6 PASSED
    The gate's own execution record, fully re-validated (schema, fingerprint),
    with ``data_class: REAL_RESEARCH_DATA``, produced from a clean committed
    checkout (the commit must exist in a git checkout) against the frozen
    protocol hash, and linked to the evidence of earlier gates:
    B5 -> B2/B3/B4 fingerprints, B6 -> B3 fingerprint and crosswalk SHA-256,
    and B6 status VERIFIED_FROM_SOURCE.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

from brats_uncertainty.data.manifest_doc import validate_manifest_doc
from brats_uncertainty.data.records import (
    REAL_RESEARCH_DATA,
    read_acquisition_record,
    read_counts_record,
    read_metadata_record,
    read_record_body,
)
from brats_uncertainty.errors import ConfigError, DataValidationError, ProvenanceError
from brats_uncertainty.utils.git import GitView
from brats_uncertainty.utils.hashing import sha256_file
from brats_uncertainty.utils.io import read_json, read_yaml
from brats_uncertainty.utils.paths import is_safe_relpath, is_within

_SAFE_PATH = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*$")
_B1_EVIDENCE = re.compile(r"^docs/data/B1_EVIDENCE_\d{4}-\d{2}-\d{2}\.md$")
_B1_TYPES = (
    "TCIA Help Desk written response",
    "Official TCIA written instruction",
    "Other authoritative written authorization",
)
_B1_ROUTE_CATEGORIES = ("A", "B", "C")
_B1_FIELDS = (
    "Protocol version",
    "Dataset",
    "DOI",
    "Inquiry date",
    "Recipient",
    "Sender",
    "Proposed route",
    "Route category",
    "Evidence type",
    "Provider/source",
    "Response date",
    "Evidence reference",
    "Interpretation",
    "Restrictions",
    "Attribution requirements",
    "Approved route",
    "Authorization status",
    "Conclusion",
)
_B1_PLACEHOLDER = re.compile(r"<[^>]*>|\b(?:TBD|TODO|PENDING|FILL)\b|^\?+$", re.IGNORECASE)
_B1_TEMPLATE_MARKER = "TEMPLATE - NOT EVIDENCE"
_COMMIT = re.compile(r"^[0-9a-f]{40}$")


def check_evidence_path(gid: str, evidence: str, repo_root: Path) -> Path:
    """Static checks of one evidence path (git checks: ``check_evidence_committed``)."""
    rel = evidence.split("#")[0]
    if not _SAFE_PATH.match(rel) or not is_safe_relpath(rel):
        raise ConfigError(
            f"gate {gid}: evidence must be a safe repository-relative path: {evidence!r}"
        )
    path = repo_root / rel
    if not is_within(path, repo_root):
        raise ConfigError(f"gate {gid}: evidence escapes the repository: {evidence!r}")
    if not path.is_file():
        raise ConfigError(f"gate {gid}: evidence path does not exist: {evidence}")
    return path


def check_evidence_committed(evidence: Mapping[str, str], git: GitView) -> None:
    """In a git checkout, every evidence file must be in the index and not git-ignored."""
    if not git.is_repo:
        return
    rels = {gid: e.split("#")[0] for gid, e in evidence.items()}
    ignored = git.ignored(sorted(set(rels.values())))
    tracked = git.tracked()
    for gid, rel in sorted(rels.items()):
        if rel in ignored:
            raise ConfigError(
                f"gate {gid}: evidence is git-ignored (private), not committed: {rel}"
            )
        if rel not in tracked:
            raise ConfigError(f"gate {gid}: evidence must be committed or staged in git: {rel}")


def _b1_fields(text: str) -> dict[str, str]:
    """Each machine-checked B1 field exactly once at the start of a line, with a real value."""
    out: dict[str, str] = {}
    for name in _B1_FIELDS:
        found = re.findall(rf"(?m)^{re.escape(name)}:[ \t]*(.*?)[ \t]*$", text)
        if len(found) != 1:
            raise ConfigError(f"gate B1: evidence must contain exactly one '{name}:' line")
        value = found[0]
        if not value or _B1_PLACEHOLDER.search(value):
            raise ConfigError(f"gate B1: evidence field '{name}:' is empty or a placeholder")
        out[name] = value
    return out


def _b1_date(name: str, value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ConfigError(f"gate B1: evidence '{name}:' must be YYYY-MM-DD: {value!r}") from exc


def check_b1_evidence(
    rel: str,
    path: Path,
    approved_route: str | None,
    *,
    identity: Mapping[str, Any],
    protocol_version: str,
) -> None:
    """B1 may pass only on recorded external written authorization (never inferred)."""
    if not _B1_EVIDENCE.match(rel):
        raise ConfigError(
            "gate B1: evidence must be docs/data/B1_EVIDENCE_<YYYY-MM-DD>.md "
            "(documentation such as the B1 record, the inquiry or the template is not "
            "authorization)"
        )
    text = path.read_text(encoding="utf-8")
    if _B1_TEMPLATE_MARKER in text or "<FILL" in text:
        raise ConfigError("gate B1: evidence is an unfilled copy of the template")
    f = _b1_fields(text)
    if f["Evidence type"] not in _B1_TYPES:
        raise ConfigError(
            f"gate B1: 'Evidence type:' must be one of {_B1_TYPES} (external written "
            "authorization only; public downloadability, web pages, the licence, Kaggle "
            "availability, a test download or API availability are not authorization)"
        )
    if f["Protocol version"] != protocol_version:
        raise ConfigError(f"gate B1: evidence 'Protocol version:' must be {protocol_version}")
    if f["Dataset"] != identity["dataset"] or f["DOI"] != identity["doi"]:
        raise ConfigError(
            f"gate B1: evidence must name dataset {identity['dataset']!r} "
            f"and DOI {identity['doi']!r}"
        )
    if f["Route category"] not in _B1_ROUTE_CATEGORIES:
        raise ConfigError(f"gate B1: 'Route category:' must be one of {_B1_ROUTE_CATEGORIES}")
    if not approved_route or f["Approved route"] != approved_route:
        raise ConfigError("gate B1: evidence 'Approved route:' must equal data.approved_route")
    inquiry = _b1_date("Inquiry date", f["Inquiry date"])
    response = _b1_date("Response date", f["Response date"])
    if response < inquiry:
        raise ConfigError("gate B1: 'Response date:' precedes 'Inquiry date:'")
    if not rel.endswith(f"B1_EVIDENCE_{response.isoformat()}.md"):
        raise ConfigError("gate B1: evidence file name must carry the 'Response date:'")
    if f["Authorization status"] != "AUTHORIZED" or f["Conclusion"] != "APPROVED":
        raise ConfigError(
            "gate B1: evidence must record 'Authorization status: AUTHORIZED' and "
            "'Conclusion: APPROVED' (anything else keeps B1 PENDING, FAILED or BLOCKED)"
        )
    wording = re.search(r"(?ms)^## Exact provider wording[ \t]*$(.*?)(?=^#{1,2} |\Z)", text)
    quoted = [ln for ln in (wording.group(1) if wording else "").splitlines() if ln.startswith(">")]
    if not any(ln.lstrip("> ").strip() for ln in quoted):
        raise ConfigError(
            "gate B1: evidence must quote the provider's exact wording ('> ' lines) under "
            "'## Exact provider wording'"
        )


IDENTITY_CONFIG = Path("configs/dataset/brats2021.yaml")


def load_evidence_identity(repo_root: Path) -> dict[str, Any]:
    """Dataset identity that real evidence must carry (fails closed if absent)."""
    path = repo_root / IDENTITY_CONFIG
    try:
        ident = read_yaml(path)["evidence_identity"]
        out = {
            "dataset": str(ident["dataset"]),
            "doi": str(ident["doi"]),
            "prefixes": tuple(str(p) for p in ident["official_source_prefixes"]),
        }
    except (OSError, KeyError, TypeError) as exc:
        raise ConfigError(f"evidence identity missing in {IDENTITY_CONFIG}: {exc}") from exc
    if not out["prefixes"] or not all(p.startswith("https://") for p in out["prefixes"]):
        raise ConfigError("evidence identity: official_source_prefixes must be https URLs")
    return out


def _check_identity(gid: str, body: Mapping[str, Any], identity: Mapping[str, Any]) -> None:
    """Evidence must describe the protocol dataset from an official source (not another dataset)."""
    if gid == "B2":
        src = body["source"]
        dataset, doi, url = src["dataset"], src["doi"], src["source_url"]
    elif gid == "B5":
        dataset, doi, url = body["dataset"], body["doi"], body["source_url"]
    elif gid == "B3":
        dataset, doi, url = identity["dataset"], body["doi"], body["source_url"]
    elif gid == "B4":  # UCSF-PDGM collection: official source required, DOI not compared
        dataset, doi, url = identity["dataset"], identity["doi"], body["source_url"]
    else:
        return
    if dataset != identity["dataset"] or doi != identity["doi"]:
        raise ConfigError(
            f"gate {gid}: evidence describes dataset {dataset!r} (doi {doi!r}), "
            f"not {identity['dataset']!r} (doi {identity['doi']!r})"
        )
    if not str(url).startswith(tuple(identity["prefixes"])):
        raise ConfigError(f"gate {gid}: evidence source {url!r} is not an official source")


def _check_config_fresh(gid: str, stamp: Mapping[str, Any], repo_root: Path) -> None:
    """Every configuration hashed into the record must still exist unchanged (no stale evidence)."""
    for rel, sha in dict(stamp.get("config_sha256") or {}).items():
        path = repo_root / str(rel)
        if not path.is_file():
            raise ConfigError(f"gate {gid}: stale evidence: configuration {rel} no longer exists")
        if sha256_file(path) != sha:
            raise ConfigError(
                f"gate {gid}: stale evidence: configuration {rel} changed after the record"
            )


def _check_stamp(gid: str, stamp: Mapping[str, Any], git: GitView, protocol_sha256: str) -> None:
    commit = str(stamp.get("code_commit") or "")
    if not _COMMIT.match(commit) or stamp.get("code_dirty") is not False:
        raise ConfigError(
            f"gate {gid}: evidence record was not produced from a clean committed checkout"
        )
    if stamp.get("protocol_sha256") != protocol_sha256 or stamp.get("protocol_version") != "v1.0":
        raise ConfigError(
            f"gate {gid}: evidence record was not produced against the frozen protocol v1.0"
        )
    if git.is_repo and not git.commit_exists(commit):
        raise ConfigError(
            f"gate {gid}: evidence record commit {commit[:12]} does not exist in this repository"
        )
    if git.is_repo and not git.is_ancestor(commit):
        raise ConfigError(
            f"gate {gid}: stale evidence: commit {commit[:12]} is not in the history of HEAD"
        )


def check_record_evidence(
    gid: str,
    path: Path,
    git: GitView,
    protocol_sha256: str,
    passed_evidence: Mapping[str, Path],
    *,
    repo_root: Path,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    """Re-validate a B2-B6 execution record used as PASSED evidence; return its body."""
    if path.suffix != ".json":
        raise ConfigError(f"gate {gid}: evidence must be the gate's JSON execution record")
    try:
        if gid == "B5":
            body: dict[str, Any] = read_json(path)
            if body.get("gate") != "B5":
                raise ConfigError(f"gate B5: evidence record belongs to gate {body.get('gate')!r}")
            validate_manifest_doc(body)
        else:
            body = read_record_body(path)
            if body.get("gate") != gid:
                raise ConfigError(
                    f"gate {gid}: evidence record belongs to gate {body.get('gate')!r}"
                )
            reader = {
                "B2": read_acquisition_record,
                "B3": read_metadata_record,
                "B4": read_metadata_record,
                "B6": read_counts_record,
            }[gid]
            reader(path)
    except (
        ProvenanceError,
        DataValidationError,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
    ) as exc:
        raise ConfigError(f"gate {gid}: evidence record invalid: {exc}") from exc
    if body.get("synthetic") is not False or body.get("data_class") != REAL_RESEARCH_DATA:
        raise ConfigError(f"gate {gid}: synthetic or unlabelled records can never close a gate")
    _check_stamp(gid, body["stamp"], git, protocol_sha256)
    _check_config_fresh(gid, body["stamp"], repo_root)
    _check_identity(gid, body, identity)

    def fp(g: str) -> str:
        if g not in passed_evidence:
            raise ConfigError(f"gate {gid}: evidence of prerequisite {g} is missing")
        linked = read_json(passed_evidence[g])
        if g == "B5":
            return str(linked["manifest_sha256"])
        return str(linked["record_fingerprint"])

    if gid == "B5":
        if body["acquisition"]["record_fingerprint"] != fp("B2"):
            raise ConfigError("gate B5: manifest is not linked to the B2 evidence record")
        meta = body["metadata_records"]
        for g in ("B3", "B4"):
            if g not in meta or meta[g]["record_fingerprint"] != fp(g):
                raise ConfigError(f"gate B5: manifest is not linked to the {g} evidence record")
    if gid == "B6":
        if body["status"] != "VERIFIED_FROM_SOURCE":
            raise ConfigError("gate B6 can only pass on a VERIFIED_FROM_SOURCE counts record")
        if body["b3_record_fingerprint"] != fp("B3"):
            raise ConfigError("gate B6: counts record is not linked to the B3 evidence record")
        b3 = read_json(passed_evidence["B3"])
        if body["crosswalk_sha256"] != b3["file"]["sha256"]:
            raise ConfigError("gate B6: crosswalk SHA-256 differs from the B3 evidence")
    return body
