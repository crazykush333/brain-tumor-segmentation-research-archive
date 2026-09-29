"""Machine-readable execution records for gates B2-B6.

Every record is created by code from files that actually exist on disk. There
is no constructor path that accepts a typed hash: hashes are always computed
here from the bytes read. Every record carries a ``ProvenanceStamp`` with the
exact code commit, protocol version and hash, package version and environment.

Records contain only identifiers, file names, sizes, hashes, counts and
metadata. They never contain images, labels or patient-level clinical data, so
they can be published as derived public artifacts after the gate is closed.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from brats_uncertainty import __version__
from brats_uncertainty.errors import ProvenanceError
from brats_uncertainty.protocol import load_protocol
from brats_uncertainty.utils.environment import capture_environment
from brats_uncertainty.utils.git import git_commit, git_is_dirty
from brats_uncertainty.utils.hashing import sha256_file
from brats_uncertainty.utils.io import read_json, write_json

RECORD_SCHEMA_VERSION = 1
_SHA = re.compile(r"^[0-9a-f]{64}$")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Exact file names fixed by the protocol (§5, gates B3/B4).
CROSSWALK_FILENAME = "BraTS2021_MappingToTCIA.xlsx"
UCSF_METADATA_FILENAME = "UCSF-PDGM-metadata_v5.csv"

# Protocol verification targets for B6 (design parameters; NOT verified facts
# until computed from the hashed crosswalk).
B6_TARGETS = {"total": 1251, "held_out_institution": 511, "development": 740}


@dataclass(frozen=True)
class ProvenanceStamp:
    created_at: str
    code_commit: str | None
    code_dirty: bool | None
    package_version: str
    protocol_version: str
    protocol_sha256: str
    environment: dict[str, Any]


def make_stamp(repo_root: Path, *, require_clean_commit: bool = True) -> ProvenanceStamp:
    """Stamp a record with the exact code state.

    By default the working tree must be a clean git checkout so that the record
    can be reproduced from the recorded commit.
    """
    spec = load_protocol(repo_root)
    commit = git_commit(repo_root)
    dirty = git_is_dirty(repo_root)
    if require_clean_commit and (commit is None or dirty is not False):
        raise ProvenanceError(
            "B2-B6 records must be produced from a clean, committed checkout "
            f"(commit={commit}, dirty={dirty}). Commit or stash changes first."
        )
    return ProvenanceStamp(
        created_at=datetime.now(UTC).isoformat(),
        code_commit=commit,
        code_dirty=dirty,
        package_version=__version__,
        protocol_version=spec.version,
        protocol_sha256=str(spec.raw["protocol"]["sha256"]),
        environment=capture_environment(),
    )


@dataclass(frozen=True)
class HashedFile:
    file_name: str
    sha256: str
    size_bytes: int

    @classmethod
    def from_path(cls, path: str | Path) -> HashedFile:
        p = Path(path)
        return cls(file_name=p.name, sha256=sha256_file(p), size_bytes=p.stat().st_size)


@dataclass(frozen=True)
class SourceInfo:
    """Where the data came from. Entered by the operator from the official page."""

    dataset: str
    dataset_version: str
    doi: str
    source_url: str
    route: str  # must be the route approved at gate B1

    def validate(self) -> None:
        for k, v in asdict(self).items():
            if not str(v).strip():
                raise ProvenanceError(f"source field {k!r} is empty")
        if not self.source_url.startswith("https://"):
            raise ProvenanceError("source_url must be an https URL of the official source")
        if not self.doi.startswith("10."):
            raise ProvenanceError("doi must be a DOI (10.xxxx/...)")


@dataclass(frozen=True)
class AcquisitionRecord:
    """Gate B2: official files acquired via the approved route."""

    gate: str
    source: SourceInfo
    acquisition_date: str
    acquired_by: str
    files: tuple[HashedFile, ...]
    stamp: ProvenanceStamp
    schema_version: int = RECORD_SCHEMA_VERSION
    notes: str = ""

    def validate(self) -> None:
        if self.gate != "B2":
            raise ProvenanceError("acquisition records belong to gate B2")
        self.source.validate()
        if not _ISO_DATE.match(self.acquisition_date):
            raise ProvenanceError("acquisition_date must be YYYY-MM-DD")
        if not self.acquired_by.strip():
            raise ProvenanceError("acquired_by is required")
        if not self.files:
            raise ProvenanceError("an acquisition record must hash at least one acquired file")
        _check_hashes(self.files)


@dataclass(frozen=True)
class MetadataFileRecord:
    """Gates B3/B4: exact SHA-256 of a metadata file as used."""

    gate: str
    kind: str
    file: HashedFile
    source_url: str
    doi: str
    stamp: ProvenanceStamp
    schema_version: int = RECORD_SCHEMA_VERSION

    def validate(self) -> None:
        expected = {
            "B3": ("crosswalk", CROSSWALK_FILENAME),
            "B4": ("ucsf_pdgm_metadata", UCSF_METADATA_FILENAME),
        }
        if self.gate not in expected:
            raise ProvenanceError("metadata file records belong to gate B3 or B4")
        kind, name = expected[self.gate]
        if self.kind != kind or self.file.file_name != name:
            raise ProvenanceError(f"gate {self.gate} requires file {name!r} (kind {kind!r})")
        if not self.source_url.startswith("https://"):
            raise ProvenanceError("source_url must be an https URL of the official source")
        _check_hashes((self.file,))


@dataclass(frozen=True)
class CountsRecord:
    """Gate B6: counts re-derived from the hashed crosswalk."""

    gate: str
    crosswalk_sha256: str
    b3_record_sha256_matches: bool
    counts: dict[str, int]
    targets: dict[str, int]
    matches_targets: bool
    hoi_site_id: str
    stamp: ProvenanceStamp
    development_ids_sha256: str
    hoi_ids_sha256: str
    schema_version: int = RECORD_SCHEMA_VERSION
    status: str = field(default="")

    def validate(self) -> None:
        if self.gate != "B6":
            raise ProvenanceError("counts records belong to gate B6")
        for h in (self.crosswalk_sha256, self.development_ids_sha256, self.hoi_ids_sha256):
            if not _SHA.match(h):
                raise ProvenanceError("malformed SHA-256 in counts record")
        if self.status not in ("PASSED", "FAILED_SR3"):
            raise ProvenanceError("counts record status must be PASSED or FAILED_SR3")
        if (self.status == "PASSED") != (self.matches_targets and self.b3_record_sha256_matches):
            raise ProvenanceError("counts record status inconsistent with its checks")


def _check_hashes(files: tuple[HashedFile, ...]) -> None:
    for f in files:
        if not _SHA.match(f.sha256):
            raise ProvenanceError(f"malformed SHA-256 for {f.file_name}")
        if f.size_bytes <= 0:
            raise ProvenanceError(f"empty file recorded: {f.file_name}")


Record = AcquisitionRecord | MetadataFileRecord | CountsRecord


def write_record(path: str | Path, record: Record) -> Path:
    record.validate()
    return write_json(path, asdict(record))


def read_metadata_record(path: str | Path) -> MetadataFileRecord:
    raw = read_json(path)
    rec = MetadataFileRecord(
        gate=raw["gate"],
        kind=raw["kind"],
        file=HashedFile(**raw["file"]),
        source_url=raw["source_url"],
        doi=raw["doi"],
        stamp=ProvenanceStamp(**raw["stamp"]),
        schema_version=int(raw["schema_version"]),
    )
    rec.validate()
    return rec
