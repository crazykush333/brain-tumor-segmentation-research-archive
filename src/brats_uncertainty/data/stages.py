"""Gated execution stages for the data gates B2-B6.

Each stage:
1. calls ``require_action`` (fails with ResearchGateError until the preceding
   gates are CLOSED, with evidence, in docs/project_status.yaml);
2. reads or hashes only files that actually exist;
3. writes one provenance-stamped record and never overwrites an existing one.

Nothing here downloads data. Acquisition itself (B2) happens through the route
approved at B1 and is performed by the operator; ``stage_record_acquisition``
then hashes the acquired files and records where they came from.

Closing a gate remains a separate, deliberate step: the owner reviews the
record, commits it (IDs/hashes/counts only) and sets the gate to CLOSED with
the record as evidence.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from brats_uncertainty.data.crosswalk import derive_cohorts, parse_rows, read_table_records
from brats_uncertainty.data.integrity import IntegrityReport, validate_dataset_tree
from brats_uncertainty.data.manifest import MANIFEST_SCHEMA_VERSION, Manifest, build_manifest
from brats_uncertainty.data.records import (
    B6_TARGETS,
    CROSSWALK_FILENAME,
    UCSF_METADATA_FILENAME,
    AcquisitionRecord,
    CountsRecord,
    HashedFile,
    MetadataFileRecord,
    SourceInfo,
    make_stamp,
    read_metadata_record,
    write_record,
)
from brats_uncertainty.data.schema import load_schema
from brats_uncertainty.errors import DataValidationError, ProvenanceError, ResearchGateError
from brats_uncertainty.evaluation.guards import require_action
from brats_uncertainty.evaluation.status import load_status
from brats_uncertainty.protocol import load_protocol
from brats_uncertainty.utils.hashing import sha256_bytes, sha256_file
from brats_uncertainty.utils.io import read_yaml, write_json

METADATA_GATES = {
    "B3": ("record_crosswalk_hash", "crosswalk", CROSSWALK_FILENAME),
    "B4": ("record_ucsf_metadata_hash", "ucsf_pdgm_metadata", UCSF_METADATA_FILENAME),
}


def _approved_route(repo_root: Path) -> str:
    data = load_status(repo_root).raw["data"]
    route = data.get("approved_route")
    if data.get("authorization") != "APPROVED" or not route:
        raise ResearchGateError("no approved data route is recorded (gate B1)")
    return str(route)


def stage_record_acquisition(
    repo_root: Path,
    source: SourceInfo,
    files: Sequence[Path],
    *,
    acquisition_date: str,
    acquired_by: str,
    out: Path,
    notes: str = "",
    require_clean_commit: bool = True,
) -> AcquisitionRecord:
    """Gate B2: hash the files obtained through the approved route and record their source."""
    require_action("acquire_data", repo_root)
    approved = _approved_route(repo_root)
    if source.route != approved:
        raise ProvenanceError(f"route {source.route!r} is not the B1-approved route {approved!r}")
    missing = [str(f) for f in files if not Path(f).is_file()]
    if missing:
        raise DataValidationError(f"acquired files not found: {missing}")
    record = AcquisitionRecord(
        gate="B2",
        source=source,
        acquisition_date=acquisition_date,
        acquired_by=acquired_by,
        files=tuple(HashedFile.from_path(f) for f in files),
        stamp=make_stamp(repo_root, require_clean_commit=require_clean_commit),
        notes=notes,
    )
    write_record(out, record)
    return record


def stage_hash_metadata(
    repo_root: Path,
    gate: str,
    path: Path,
    *,
    source_url: str,
    doi: str,
    out: Path,
    require_clean_commit: bool = True,
) -> MetadataFileRecord:
    """Gates B3/B4: exact SHA-256 of the crosswalk or the UCSF-PDGM metadata file as used."""
    if gate not in METADATA_GATES:
        raise ValueError("gate must be B3 or B4")
    action, kind, filename = METADATA_GATES[gate]
    require_action(action, repo_root)
    if path.name != filename:
        raise DataValidationError(f"gate {gate} requires the file {filename!r}, got {path.name!r}")
    record = MetadataFileRecord(
        gate=gate,
        kind=kind,
        file=HashedFile.from_path(path),
        source_url=source_url,
        doi=doi,
        stamp=make_stamp(repo_root, require_clean_commit=require_clean_commit),
    )
    write_record(out, record)
    return record


def stage_validate_data(
    repo_root: Path,
    dataset_config: Path,
    data_root: Path,
    *,
    deep: bool = True,
    manifest: Manifest | None = None,
) -> IntegrityReport:
    """Integrity audit of acquired files (gated: requires B1-B2)."""
    require_action("validate_data", repo_root)
    cfg = read_yaml(dataset_config)
    shape = cfg.get("layout", {}).get("expected_shape")
    return validate_dataset_tree(
        data_root,
        load_schema(dataset_config),
        require_labels=True,
        deep=deep,
        expected_shape=shape,
        manifest=manifest,
    )


def stage_build_manifest(
    repo_root: Path,
    dataset_config: Path,
    data_root: Path,
    out: Path,
    *,
    require_clean_commit: bool = True,
) -> Manifest:
    """Gate B5: integrity audit, then a hashed manifest (IDs, relative paths, sizes, SHA-256)."""
    require_action("build_manifest", repo_root)
    report = validate_dataset_tree(data_root, load_schema(dataset_config), deep=True)
    if not report.ok:
        raise DataValidationError(
            f"integrity audit failed with {len(report.errors)} error(s); first: {report.errors[0]}"
        )
    manifest = build_manifest(data_root, load_schema(dataset_config))
    stamp = make_stamp(repo_root, require_clean_commit=require_clean_commit)
    write_json(
        out,
        {
            "gate": "B5",
            "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
            "manifest_sha256": manifest.sha256,
            "n_cases": len(manifest.entries),
            "integrity": report.to_dict(),
            "stamp": asdict(stamp),
            "manifest": manifest.to_dict(),
        },
    )
    return manifest


def _ids_sha256(ids: Sequence[str]) -> str:
    return sha256_bytes(("\n".join(sorted(ids)) + "\n").encode("utf-8"))


def stage_derive_counts(
    repo_root: Path,
    crosswalk: Path,
    b3_record: Path,
    dataset_config: Path,
    out: Path,
    *,
    require_clean_commit: bool = True,
) -> CountsRecord:
    """Gate B6: re-derive 1,251 / 511 / 740 from the hashed crosswalk.

    The crosswalk is re-hashed and must equal the B3 record. The record is
    written whether or not the targets match (a mismatch is logged as
    FAILED_SR3 and then raised); success is never assumed.
    """
    require_action("derive_counts", repo_root)
    b3 = read_metadata_record(b3_record)
    if b3.gate != "B3":
        raise ProvenanceError("b3_record is not a gate-B3 crosswalk record")
    if crosswalk.name != CROSSWALK_FILENAME:
        raise DataValidationError(f"expected {CROSSWALK_FILENAME!r}, got {crosswalk.name!r}")
    actual = sha256_file(crosswalk)
    hash_ok = actual == b3.file.sha256
    cfg: dict[str, Any] = read_yaml(dataset_config)
    spec = load_protocol(repo_root)
    cohorts_cfg = spec.raw["cohorts"]
    hoi_site = str(cohorts_cfg["hoi_site_id"])
    targets = {
        "total": int(cohorts_cfg["brats2021_training_total"]),
        "held_out_institution": int(cohorts_cfg["hoi_count"]),
        "development": int(cohorts_cfg["development_count_before_grouping"]),
    }
    if targets != B6_TARGETS:
        raise ProvenanceError("protocol mirror counts differ from the B6 targets")
    rows = parse_rows(
        read_table_records(crosswalk, cfg["crosswalk"].get("sheet")),
        cfg["crosswalk"]["columns"],
        case_id_pattern=cfg["layout"]["case_id_pattern"],
    )
    hoi = [r.case_id for r in rows if r.site_id == hoi_site]
    dev = [r.case_id for r in rows if r.site_id != hoi_site]
    counts = {"total": len(rows), "held_out_institution": len(hoi), "development": len(dev)}
    matches = counts == targets
    record = CountsRecord(
        gate="B6",
        crosswalk_sha256=actual,
        b3_record_sha256_matches=hash_ok,
        counts=counts,
        targets=targets,
        matches_targets=matches,
        hoi_site_id=hoi_site,
        stamp=make_stamp(repo_root, require_clean_commit=require_clean_commit),
        development_ids_sha256=_ids_sha256(dev),
        hoi_ids_sha256=_ids_sha256(hoi),
        status="PASSED" if (matches and hash_ok) else "FAILED_SR3",
    )
    write_record(out, record)
    if not hash_ok:
        raise ProvenanceError("crosswalk SHA-256 differs from the B3 record; stop (SR3)")
    if not matches:
        # derive_cohorts raises the protocol's SR3 error with the exact differences
        derive_cohorts(
            rows,
            hoi_site_id=hoi_site,
            expected_total=targets["total"],
            expected_hoi=targets["held_out_institution"],
            expected_development=targets["development"],
        )
    return record
