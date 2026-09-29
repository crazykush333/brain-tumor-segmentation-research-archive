"""B2-B6 preparation: integrity validators, provenance records and gated stages.

Everything here runs on SYNTHETIC files in pytest temporary directories. The
positive-path stage tests use a temporary *fake* repository whose status closes
gates; they never touch the real repository status, and no real data exist.
"""

from __future__ import annotations

import gzip
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from brats_uncertainty.data.crosswalk import parse_rows, read_table_records
from brats_uncertainty.data.integrity import (
    CorruptFileError,
    check_gzip_stream,
    read_nifti_header,
    validate_dataset_tree,
)
from brats_uncertainty.data.manifest import build_manifest
from brats_uncertainty.data.records import (
    CROSSWALK_FILENAME,
    UCSF_METADATA_FILENAME,
    AcquisitionRecord,
    CountsRecord,
    HashedFile,
    MetadataFileRecord,
    ProvenanceStamp,
    SourceInfo,
    make_stamp,
)
from brats_uncertainty.data.schema import DatasetSchema
from brats_uncertainty.data.stages import (
    stage_build_manifest,
    stage_derive_counts,
    stage_hash_metadata,
    stage_record_acquisition,
)
from brats_uncertainty.errors import (
    ConfigError,
    DataValidationError,
    ProvenanceError,
    ResearchGateError,
)
from brats_uncertainty.evaluation.status import validate_status
from brats_uncertainty.results.site_export import build_overview
from tests.conftest import make_status_repo
from tests.fixtures.synthetic import write_synthetic_nifti

SCHEMA = DatasetSchema(
    name="synthetic",
    case_id_pattern=r"SYN-\d{3}",
    modality_suffixes={"T1": "_t1", "T1c": "_t1c", "T2": "_t2", "FLAIR": "_flair"},
    label_suffix="_seg",
    file_ending=".nii.gz",
    verified_on_files=False,
)
SYN_SOURCE_URL = "https://example.org/synthetic-source"  # test-only placeholder URL


def _tree(root: Path, n: int = 3, shape: tuple[int, ...] = (4, 4, 3)) -> Path:
    for i in range(n):
        cid = f"SYN-{i:03d}"
        for m in ("T1", "T1c", "T2", "FLAIR"):
            write_synthetic_nifti(root / cid / SCHEMA.image_name(cid, m), shape)
        write_synthetic_nifti(root / cid / SCHEMA.label_name(cid), shape)
    return root


def _codes(report: object) -> set[str]:
    return {i.code for i in report.issues}  # type: ignore[attr-defined]


# ---------------------------------------------------------------- headers
@pytest.mark.parametrize(("version", "endian"), [(1, "<"), (1, ">"), (2, "<"), (2, ">")])
def test_nifti_header_parsing(tmp_path: Path, version: int, endian: str) -> None:
    p = write_synthetic_nifti(tmp_path / "x.nii.gz", (5, 6, 7), version=version, endian=endian)
    info = read_nifti_header(p)
    assert info.version == version
    assert info.shape == (5, 6, 7)


def test_corrupt_files_detected(tmp_path: Path) -> None:
    p = write_synthetic_nifti(tmp_path / "x.nii.gz")
    data = p.read_bytes()
    (tmp_path / "trunc.nii.gz").write_bytes(data[: len(data) // 2])
    with pytest.raises(CorruptFileError):
        check_gzip_stream(tmp_path / "trunc.nii.gz")
    with gzip.open(tmp_path / "bad.nii.gz", "wb") as fh:
        fh.write(b"not a nifti header" * 30)
    with pytest.raises(CorruptFileError, match="NIfTI"):
        read_nifti_header(tmp_path / "bad.nii.gz")
    (tmp_path / "plain.nii.gz").write_bytes(b"\x00" * 10)
    with pytest.raises(CorruptFileError):
        read_nifti_header(tmp_path / "plain.nii.gz")


# ---------------------------------------------------------------- integrity
def test_clean_tree_passes(tmp_path: Path) -> None:
    r = validate_dataset_tree(
        _tree(tmp_path), SCHEMA, expected_case_ids=["SYN-000", "SYN-001", "SYN-002"]
    )
    assert r.ok, r.issues
    assert r.n_case_dirs == r.n_complete_cases == r.n_cases_with_label == 3
    assert r.shapes == {"[4, 4, 3]": 3}


def test_integrity_issue_detection(tmp_path: Path) -> None:
    root = _tree(tmp_path, n=5)
    (root / "SYN-000" / SCHEMA.image_name("SYN-000", "T2")).unlink()  # missing modality
    (root / "SYN-001" / SCHEMA.label_name("SYN-001")).unlink()  # missing label
    write_synthetic_nifti(
        root / "SYN-002" / SCHEMA.image_name("SYN-002", "FLAIR"), (4, 4, 4)
    )  # dims
    target = root / "SYN-003" / SCHEMA.image_name("SYN-003", "T1")
    target.write_bytes(target.read_bytes()[:20])  # corrupt
    (root / "SYN-004" / "notes.txt").write_text("x", encoding="utf-8")  # unexpected in case
    (root / "readme.txt").write_text("x", encoding="utf-8")  # unexpected top level
    (root / "bad_case").mkdir()  # invalid case ID
    r = validate_dataset_tree(
        root, SCHEMA, expected_case_ids=["SYN-000", "SYN-001", "SYN-002", "SYN-003", "SYN-009"]
    )
    codes = _codes(r)
    assert {
        "missing_modality",
        "missing_label",
        "dimension_mismatch",
        "corrupt_file",
        "unexpected_file",
        "invalid_case_id",
        "missing_case",
        "unexpected_case",
    } <= codes
    assert not r.ok
    assert r.to_dict()["n_errors"] == len(r.errors)


def test_hash_mismatch_against_manifest(tmp_path: Path) -> None:
    root = _tree(tmp_path, n=2)
    manifest = build_manifest(root, SCHEMA)
    write_synthetic_nifti(root / "SYN-001" / SCHEMA.label_name("SYN-001"), (4, 4, 3), endian=">")
    r = validate_dataset_tree(root, SCHEMA, manifest=manifest)
    assert "hash_mismatch" in _codes(r)


def test_expected_shape_warning(tmp_path: Path) -> None:
    r = validate_dataset_tree(_tree(tmp_path, n=1), SCHEMA, expected_shape=(240, 240, 155))
    assert r.ok
    assert "unexpected_shape" in _codes(r)


def test_missing_root(tmp_path: Path) -> None:
    assert not validate_dataset_tree(tmp_path / "nope", SCHEMA).ok


# ---------------------------------------------------------------- metadata
COLS = {
    "case_id": "BraTS2021 ID",
    "site_id": "Site ID",
    "collection": "Data Collection",
    "tcia_subject_id": "TCIA PatientID",
}


def test_malformed_crosswalk_detected() -> None:
    good = {
        "BraTS2021 ID": "SYN-001",
        "Site ID": "18",
        "Data Collection": "x",
        "TCIA PatientID": "y",
    }
    with pytest.raises(DataValidationError, match="missing expected columns"):
        parse_rows([{"BraTS2021 ID": "SYN-001"}], COLS)
    with pytest.raises(DataValidationError, match="malformed case ID"):
        parse_rows([{**good, "BraTS2021 ID": "bad id"}], COLS, case_id_pattern=r"SYN-\d{3}")
    with pytest.raises(DataValidationError, match="missing site ID"):
        parse_rows([{**good, "Site ID": " "}], COLS)
    with pytest.raises(DataValidationError, match="duplicate"):
        parse_rows([good, good], COLS)
    with pytest.raises(DataValidationError, match="incomplete"):
        parse_rows([good], {**COLS, "site_id": ""})
    with pytest.raises(DataValidationError, match="no records"):
        parse_rows([], COLS)
    rows = parse_rows([{**good, "Site ID": "1.0"}], COLS)
    assert rows[0].site_id == "1"


def test_read_table_records_formats(tmp_path: Path) -> None:
    (tmp_path / "t.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    assert read_table_records(tmp_path / "t.csv") == [{"a": "1", "b": "2"}]
    (tmp_path / "t.json").write_text("{}", encoding="utf-8")
    with pytest.raises(DataValidationError, match="unsupported"):
        read_table_records(tmp_path / "t.json")
    with pytest.raises(DataValidationError, match="not found"):
        read_table_records(tmp_path / "missing.csv")


# ---------------------------------------------------------------- records
def _stamp() -> ProvenanceStamp:
    return ProvenanceStamp("2000-01-01T00:00:00+00:00", None, None, "0.1.0", "v1.0", "0" * 64, {})


def _src(route: str = "SYNTHETIC-TEST-ROUTE") -> SourceInfo:
    return SourceInfo("SYNTHETIC", "v-test", "10.0000/synthetic", SYN_SOURCE_URL, route)


def test_record_validation_rules(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"synthetic")
    hf = HashedFile.from_path(f)
    assert len(hf.sha256) == 64
    AcquisitionRecord("B2", _src(), "2000-01-01", "tester", (hf,), _stamp()).validate()
    with pytest.raises(ProvenanceError):
        AcquisitionRecord("B2", _src(), "01/01/2000", "tester", (hf,), _stamp()).validate()
    with pytest.raises(ProvenanceError):
        AcquisitionRecord("B2", _src(), "2000-01-01", "tester", (), _stamp()).validate()
    with pytest.raises(ProvenanceError):
        AcquisitionRecord(
            "B2", _src(), "2000-01-01", "t", (HashedFile("a", "abc", 1),), _stamp()
        ).validate()
    with pytest.raises(ProvenanceError, match="https"):
        SourceInfo("d", "v", "10.1/x", "http://insecure", "r").validate()
    with pytest.raises(ProvenanceError, match="requires file"):
        MetadataFileRecord("B3", "crosswalk", hf, SYN_SOURCE_URL, "10.1/x", _stamp()).validate()
    with pytest.raises(ProvenanceError, match="status inconsistent"):
        CountsRecord(
            "B6", "a" * 64, True, {}, {}, False, "1", _stamp(), "b" * 64, "c" * 64, status="PASSED"
        ).validate()


def test_stamp_requires_clean_commit(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path, closed=set())
    with pytest.raises(ProvenanceError, match="clean, committed"):
        make_stamp(root)
    s = make_stamp(root, require_clean_commit=False)
    assert s.protocol_version == "v1.0"
    assert s.code_commit is None


# ---------------------------------------------------------------- gated stages (fake repo)
def _b(n: int) -> set[str]:
    return {f"B{i}" for i in range(1, n + 1)}


def test_stages_blocked_without_gates(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path / "repo", closed=set())
    f = tmp_path / CROSSWALK_FILENAME
    f.write_bytes(b"synthetic")
    with pytest.raises(ResearchGateError):
        stage_record_acquisition(
            root,
            _src(),
            [f],
            acquisition_date="2000-01-01",
            acquired_by="t",
            out=tmp_path / "b2.json",
            require_clean_commit=False,
        )
    with pytest.raises(ResearchGateError):
        stage_hash_metadata(
            root,
            "B3",
            f,
            source_url=SYN_SOURCE_URL,
            doi="10.1/x",
            out=tmp_path / "b3.json",
            require_clean_commit=False,
        )
    assert not (tmp_path / "b2.json").exists()
    assert not (tmp_path / "b3.json").exists()


def test_record_acquisition_requires_approved_route(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path / "repo", closed=_b(1))
    f = tmp_path / "archive.bin"
    f.write_bytes(b"synthetic archive bytes")
    with pytest.raises(ProvenanceError, match="not the B1-approved route"):
        stage_record_acquisition(
            root,
            _src("OTHER"),
            [f],
            acquisition_date="2000-01-01",
            acquired_by="t",
            out=tmp_path / "b2.json",
            require_clean_commit=False,
        )
    rec = stage_record_acquisition(
        root,
        _src(),
        [f],
        acquisition_date="2000-01-01",
        acquired_by="t",
        out=tmp_path / "b2.json",
        require_clean_commit=False,
    )
    assert rec.files[0].file_name == "archive.bin"
    with pytest.raises(FileExistsError):
        stage_record_acquisition(
            root,
            _src(),
            [f],
            acquisition_date="2000-01-01",
            acquired_by="t",
            out=tmp_path / "b2.json",
            require_clean_commit=False,
        )


def test_hash_metadata_exact_filenames(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path / "repo", closed=_b(3))
    wrong = tmp_path / "crosswalk_copy.xlsx"
    wrong.write_bytes(b"synthetic")
    with pytest.raises(DataValidationError, match="requires the file"):
        stage_hash_metadata(
            root,
            "B3",
            wrong,
            source_url=SYN_SOURCE_URL,
            doi="10.1/x",
            out=tmp_path / "b3.json",
            require_clean_commit=False,
        )
    ucsf = tmp_path / UCSF_METADATA_FILENAME
    ucsf.write_text("synthetic,metadata\n", encoding="utf-8")
    rec = stage_hash_metadata(
        root,
        "B4",
        ucsf,
        source_url=SYN_SOURCE_URL,
        doi="10.1/x",
        out=tmp_path / "b4.json",
        require_clean_commit=False,
    )
    assert rec.kind == "ucsf_pdgm_metadata"


def _synthetic_config(tmp_path: Path) -> Path:
    repo = Path(__file__).resolve().parents[2]
    cfg = yaml.safe_load((repo / "configs/dataset/brats2021.yaml").read_text(encoding="utf-8"))
    cfg["name"] = "synthetic"
    cfg["layout"].update(
        case_id_pattern=r"SYN-\d{4}",
        modality_suffixes={"T1": "_t1", "T1c": "_t1c", "T2": "_t2", "FLAIR": "_flair"},
    )
    p = tmp_path / "synthetic_dataset.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def _synthetic_crosswalk(path: Path, n_site1: int, n_other: int) -> Path:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["BraTS2021 ID", "Site ID", "Data Collection", "TCIA PatientID"])
    for i in range(n_site1 + n_other):
        ws.append(
            [f"SYN-{i:04d}", 1 if i < n_site1 else 18, "SYNTHETIC", "new-not-previously-in-TCIA"]
        )
    wb.save(path)
    return path


@pytest.mark.parametrize(("n1", "n2", "status"), [(511, 740, "PASSED"), (3, 5, "FAILED_SR3")])
def test_derive_counts(tmp_path: Path, n1: int, n2: int, status: str) -> None:
    root = make_status_repo(tmp_path / "repo", closed=_b(5))
    xw = _synthetic_crosswalk(tmp_path / CROSSWALK_FILENAME, n1, n2)
    stage_hash_metadata(
        root,
        "B3",
        xw,
        source_url=SYN_SOURCE_URL,
        doi="10.1/x",
        out=tmp_path / "b3.json",
        require_clean_commit=False,
    )
    cfg = _synthetic_config(tmp_path)
    if status == "PASSED":
        rec = stage_derive_counts(
            root, xw, tmp_path / "b3.json", cfg, tmp_path / "b6.json", require_clean_commit=False
        )
        assert rec.counts == {"total": 1251, "held_out_institution": 511, "development": 740}
    else:
        with pytest.raises(DataValidationError, match="SR3"):
            stage_derive_counts(
                root,
                xw,
                tmp_path / "b3.json",
                cfg,
                tmp_path / "b6.json",
                require_clean_commit=False,
            )
    written = yaml.safe_load((tmp_path / "b6.json").read_text(encoding="utf-8"))
    assert written["status"] == status


def test_derive_counts_detects_changed_crosswalk(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path / "repo", closed=_b(5))
    xw = _synthetic_crosswalk(tmp_path / CROSSWALK_FILENAME, 511, 740)
    stage_hash_metadata(
        root,
        "B3",
        xw,
        source_url=SYN_SOURCE_URL,
        doi="10.1/x",
        out=tmp_path / "b3.json",
        require_clean_commit=False,
    )
    _synthetic_crosswalk(xw, 511, 741)  # file changed after B3
    with pytest.raises(ProvenanceError, match="differs from the B3 record"):
        stage_derive_counts(
            root,
            xw,
            tmp_path / "b3.json",
            _synthetic_config(tmp_path),
            tmp_path / "b6.json",
            require_clean_commit=False,
        )
    written = yaml.safe_load((tmp_path / "b6.json").read_text(encoding="utf-8"))
    assert written["status"] == "FAILED_SR3"
    assert written["b3_record_sha256_matches"] is False


def test_build_manifest_stage(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path / "repo", closed=_b(4))
    cfg = _synthetic_config(tmp_path)
    data = tmp_path / "data"
    for i in range(2):
        cid = f"SYN-{i:04d}"
        for suf in ("_t1", "_t1c", "_t2", "_flair", "_seg"):
            write_synthetic_nifti(data / cid / f"{cid}{suf}.nii.gz")
    m = stage_build_manifest(root, cfg, data, tmp_path / "b5.json", require_clean_commit=False)
    assert len(m.entries) == 2
    shutil.rmtree(data / "SYN-0001")
    (data / "SYN-0001").mkdir()
    with pytest.raises(DataValidationError, match="integrity audit failed"):
        stage_build_manifest(root, cfg, data, tmp_path / "b5b.json", require_clean_commit=False)


# ---------------------------------------------------------------- status rules and overview
def _raw(repo_root: Path) -> dict:  # type: ignore[type-arg]
    return yaml.safe_load((repo_root / "docs/project_status.yaml").read_text(encoding="utf-8"))


def _gate(raw: dict, gid: str) -> dict:  # type: ignore[type-arg]
    return next(g for g in raw["gates"] if g["id"] == gid)


def test_status_consistency_rules(repo_root: Path) -> None:
    raw = _raw(repo_root)
    _gate(raw, "B3")["status"] = "LOCKED"
    with pytest.raises(ConfigError, match="B7-B12 may be LOCKED"):
        validate_status(raw, repo_root)
    for mutate, msg in [
        (
            lambda r: r["data"].update(authorization="APPROVED", approved_route="x"),
            "APPROVED exactly",
        ),
        (lambda r: r["data"].update(approved_route="x"), "approved_route is set"),
        (lambda r: r["data"].update(acquired=True), "B2 is not CLOSED"),
        (lambda r: r["training"].update(status="IN_PROGRESS"), "B12"),
        (lambda r: r["evaluation"].update(internal="COMPLETED"), "C5 and C6"),
        (lambda r: r["results"].update(status="AVAILABLE"), "disagree"),
    ]:
        raw = _raw(repo_root)
        mutate(raw)
        with pytest.raises(ConfigError, match=msg):
            validate_status(raw, repo_root)


def test_locked_rejected_once_data_gates_closed(tmp_path: Path) -> None:
    root = make_status_repo(tmp_path, closed=_b(6))
    raw = _raw(root)
    _gate(raw, "B7")["status"] = "LOCKED"
    with pytest.raises(ConfigError, match="all closed"):
        validate_status(raw, root)


def test_overview_reflects_current_state(repo_root: Path) -> None:
    raw = _raw(repo_root)
    overview = {
        o["key"]: o["status"]
        for o in build_overview(raw, {g["id"]: g["status"] for g in raw["gates"]})
    }
    assert overview == {
        "protocol": "FROZEN",
        "b1": "PENDING",
        "data": "NOT_STARTED",
        "grouping": "LOCKED",
        "split": "LOCKED",
        "training": "NOT_STARTED",
        "evaluation": "NOT_STARTED",
        "results": "NOT_AVAILABLE",
    }


def test_private_data_paths_are_gitignored(repo_root: Path) -> None:
    paths = [
        "data/raw/BraTS2021_00001/BraTS2021_00001_t1.nii.gz",
        "data/raw/BraTS2021_00001_seg.nii",
        "data/manifests/B5_manifest.json",
        "data/derived/x.npy",
        "data/cache/tmp.bin",
        "BraTS2021_MappingToTCIA.xlsx",
        "meta/UCSF-PDGM-metadata_v5.csv",
        "kaggle.json",
        ".kaggle/kaggle.json",
        ".env",
        "archive.zip",
        "scan.dcm",
        "model.pth",
    ]
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "--no-index", *paths],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except OSError:
        pytest.skip("git not available")
    ignored = set(proc.stdout.split())
    assert ignored == set(paths)
    readme = subprocess.run(
        ["git", "check-ignore", "--no-index", "data/README.md"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert readme.returncode == 1  # README is NOT ignored
