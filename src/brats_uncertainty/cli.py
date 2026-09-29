"""Command-line interface: ``brats-uncertainty <command>``.

Safe commands (no data access): ``verify-protocol``, ``status``, ``check-repo``,
``check-action``, ``export-site-data``. Data-stage commands are gated and fail
with a ResearchGateError until their protocol gates are closed.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from brats_uncertainty import PROTOCOL_VERSION, __version__
from brats_uncertainty.errors import BratsUncertaintyError, ConfigError
from brats_uncertainty.utils.paths import find_repo_root


def _cmd_verify_protocol(root: Path, _: argparse.Namespace) -> int:
    from brats_uncertainty.protocol import load_protocol

    spec = load_protocol(root)
    print(
        f"protocol {spec.version} OK: {spec.raw['protocol']['file']} "
        f"sha256={spec.raw['protocol']['sha256']}"
    )
    return 0


def _cmd_status(root: Path, _: argparse.Namespace) -> int:
    from brats_uncertainty.evaluation.status import load_status

    st = load_status(root)
    print(st.headline)
    for g in st.gates.values():
        print(f"  {g.id:<4} {g.status:<13} {g.title}")
    return 0


def _cmd_check_repo(root: Path, _: argparse.Namespace) -> int:
    from brats_uncertainty.repo_checks import check_repository

    findings = check_repository(root)
    for f in findings:
        print(f"PROHIBITED: {f.path}: {f.problem}", file=sys.stderr)
    if not findings:
        print(
            "repository check passed: no prohibited files, secrets or protocol integrity problems"
        )
    return 1 if findings else 0


def _cmd_check_action(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.evaluation.guards import check_action

    unmet = check_action(args.action, root)
    if unmet:
        print(f"NOT AUTHORIZED: {args.action}; unmet: {', '.join(unmet)}")
        return 2
    print(f"authorized: {args.action}")
    return 0


def _cmd_export_site(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.results.site_export import export_site_data

    changed = export_site_data(root, check=args.check)
    if args.check:
        if changed:
            print(
                f"website data out of sync: {changed}. Run `brats-uncertainty export-site-data`.",
                file=sys.stderr,
            )
            return 1
        print("website data in sync")
    else:
        print(f"wrote: {changed or 'nothing (already up to date)'}")
    return 0


DATA_SUBDIRS = ("raw", "manifests", "derived", "cache")


def _cmd_init_data_dirs(root: Path, _: argparse.Namespace) -> int:
    """Create the git-ignored local data layout (safe: creates empty folders only)."""
    for sub in DATA_SUBDIRS:
        (root / "data" / sub).mkdir(parents=True, exist_ok=True)
    print(f"created (git-ignored): {', '.join(f'data/{s}/' for s in DATA_SUBDIRS)}")
    return 0


def _source(args: argparse.Namespace) -> Any:
    from brats_uncertainty.data.records import SourceInfo

    return SourceInfo(
        dataset=args.dataset,
        dataset_version=args.dataset_version,
        doi=args.doi,
        source_url=args.source_url,
        route=args.route,
    )


def _cmd_acquire(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.data.acquisition import (
        AcquisitionPlan,
        HttpsFileAdapter,
        LocalImportAdapter,
        SyntheticFixtureAdapter,
        stage_acquire,
    )

    adapter: Any
    if args.adapter == "synthetic-fixture":
        adapter = SyntheticFixtureAdapter(root, n_cases=args.n_cases)
    elif args.adapter == "local-import":
        if not args.delivered:
            raise ConfigError("--delivered is required for the local-import adapter")
        adapter = LocalImportAdapter(_source(args), Path(args.delivered))
    else:
        urls = dict(item.split("=", 1) for item in (args.url or []))
        if not urls:
            raise ConfigError("--url REL=https://... is required for the https-file adapter")
        adapter = HttpsFileAdapter(_source(args), urls)
    result = stage_acquire(
        root,
        adapter,
        storage_root=Path(args.storage_root),
        out_record=Path(args.out),
        acquired_by=args.acquired_by,
        execute=args.execute,
        storage_label=args.storage_label,
    )
    if isinstance(result, AcquisitionPlan):
        print(result.describe())
        print(
            "No files were acquired (dry run). Real execution needs --execute AND B1 authorization."
        )
    else:
        print(
            f"B2 record: {args.out} ({len(result.inventory)} files, synthetic={result.synthetic})"
        )
    return 0


def _cmd_hash_metadata(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.data.stages import stage_hash_metadata

    rec = stage_hash_metadata(
        root,
        args.gate,
        Path(args.file),
        source_url=args.source_url,
        doi=args.doi,
        out=Path(args.out),
        path_reference=args.path_reference,
        synthetic=args.synthetic,
    )
    print(
        f"{args.gate} record written: {args.out} "
        f"({rec.file.file_name}, {rec.file.size_bytes} bytes, "
        f"sha256={rec.file.sha256}, synthetic={rec.synthetic})"
    )
    return 0


def _cmd_validate_data(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.data.stages import stage_validate_data
    from brats_uncertainty.utils.io import write_json

    report = stage_validate_data(
        root,
        Path(args.dataset_config),
        Path(args.data_root),
        deep=not args.quick,
        synthetic=args.synthetic,
    )
    if args.out:
        write_json(args.out, report.to_dict())
    print(
        f"integrity: {report.n_case_dirs} case dirs, {report.n_complete_cases} complete, "
        f"{len(report.errors)} error(s), {len(report.issues) - len(report.errors)} warning(s)"
    )
    return 0 if report.ok else 1


def _cmd_build_manifest(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.data.stages import stage_build_manifest

    doc = stage_build_manifest(
        root,
        Path(args.dataset_config),
        Path(args.data_root),
        Path(args.acquisition_record),
        Path(args.out),
        out_csv=Path(args.out_csv) if args.out_csv else None,
        metadata_files=[Path(m) for m in args.metadata_file or []],
        synthetic=args.synthetic,
    )
    print(f"B5 raw manifest: {doc['summary']} manifest_sha256={doc['manifest_sha256']}")
    return 0


def _cmd_derive_counts(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.data.stages import stage_derive_counts

    rec = stage_derive_counts(
        root,
        Path(args.crosswalk),
        Path(args.b3_record),
        Path(args.dataset_config),
        Path(args.out),
        synthetic=args.synthetic,
    )
    print(f"B6 record written: {args.out} status={rec.status} counts={rec.counts}")
    return 0


def _cmd_count_targets(_: Path, __: argparse.Namespace) -> int:
    from brats_uncertainty.data.records import protocol_count_targets

    t = protocol_count_targets()
    print(f"{t['status']}: {t['label']}")
    for k, v in t["targets"].items():
        print(f"  {k}: {v}")
    return 0


def _cmd_gate_transition(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.evaluation.transitions import write_transition

    changes = write_transition(
        root,
        args.gate,
        args.new_status,
        evidence=args.evidence,
        on=args.on,
        approved_route=args.approved_route,
        apply=args.apply,
    )
    print(("APPLIED" if args.apply else "DRY RUN (use --apply to write)") + ":")
    for c in changes:
        print(f"  {c}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="brats-uncertainty", description=__doc__)
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__} (protocol {PROTOCOL_VERSION})",
    )
    p.add_argument("--repo-root", default=None, help="repository root (default: auto-detect)")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-protocol", help="verify the frozen protocol hash").set_defaults(
        func=_cmd_verify_protocol
    )
    sub.add_parser("status", help="print project status and gates").set_defaults(func=_cmd_status)
    sub.add_parser("check-repo", help="scan for prohibited files and secrets").set_defaults(
        func=_cmd_check_repo
    )
    ca = sub.add_parser("check-action", help="check whether a gated action is authorized")
    ca.add_argument("action")
    ca.set_defaults(func=_cmd_check_action)
    ex = sub.add_parser("export-site-data", help="export website/data JSON from sources of truth")
    ex.add_argument(
        "--check", action="store_true", help="only verify the committed files are in sync"
    )
    ex.set_defaults(func=_cmd_export_site)
    sub.add_parser(
        "init-data-dirs", help="create the git-ignored local data/ layout (no data)"
    ).set_defaults(func=_cmd_init_data_dirs)
    src_help = "as shown on the official source page"
    aq = sub.add_parser("acquire", help="B2 acquisition (dry run by default; real runs gated)")
    aq.add_argument(
        "--adapter", required=True, choices=["local-import", "https-file", "synthetic-fixture"]
    )
    aq.add_argument("--delivered", help="local-import: operator-delivered file or folder")
    aq.add_argument("--url", action="append", help="https-file: REL=https://... (repeatable)")
    aq.add_argument("--n-cases", type=int, default=3, help="synthetic-fixture: number of cases")
    aq.add_argument("--dataset", default="RSNA-ASNR-MICCAI-BraTS-2021")
    aq.add_argument("--dataset-version", default="unset", help=src_help)
    aq.add_argument("--doi", default="10.7937/jc8x-9874")
    aq.add_argument(
        "--source-url",
        default="https://www.cancerimagingarchive.net/analysis-result/rsna-asnr-miccai-brats-2021/",
    )
    aq.add_argument("--route", default="unset", help="must equal the B1-approved route")
    aq.add_argument("--storage-root", required=True)
    aq.add_argument("--storage-label", default=None, help="logical label (no absolute paths)")
    aq.add_argument("--acquired-by", required=True)
    aq.add_argument("--out", required=True, help="B2 record path")
    aq.add_argument("--execute", action="store_true", help="actually acquire (default: dry run)")
    aq.set_defaults(func=_cmd_acquire)
    hm = sub.add_parser("hash-metadata", help="B3/B4: exact SHA-256 of a metadata file (gated)")
    hm.add_argument("--gate", required=True, choices=["B3", "B4"])
    hm.add_argument("--file", required=True)
    hm.add_argument("--source-url", required=True)
    hm.add_argument("--doi", required=True)
    hm.add_argument("--path-reference", default=None, help="logical/relative location label")
    hm.add_argument("--out", required=True)
    hm.add_argument("--synthetic", action="store_true", help="SYNTHETIC_TEST_DATA inputs only")
    hm.set_defaults(func=_cmd_hash_metadata)
    vd = sub.add_parser("validate-data", help="integrity audit of acquired data (gated)")
    vd.add_argument("--dataset-config", required=True)
    vd.add_argument("--data-root", required=True)
    vd.add_argument("--quick", action="store_true", help="headers only; skip full gzip CRC read")
    vd.add_argument("--out", default=None)
    vd.add_argument("--synthetic", action="store_true", help="SYNTHETIC_TEST_DATA inputs only")
    vd.set_defaults(func=_cmd_validate_data)
    bm = sub.add_parser("build-manifest", help="B5: integrity audit + raw data manifest (gated)")
    bm.add_argument("--dataset-config", required=True)
    bm.add_argument("--data-root", required=True)
    bm.add_argument("--acquisition-record", required=True, help="B2 record")
    bm.add_argument("--metadata-file", action="append", help="crosswalk / UCSF file (repeatable)")
    bm.add_argument("--out", required=True, help="manifest JSON")
    bm.add_argument("--out-csv", default=None, help="manifest file table as CSV")
    bm.add_argument("--synthetic", action="store_true", help="SYNTHETIC_TEST_DATA inputs only")
    bm.set_defaults(func=_cmd_build_manifest)
    dc = sub.add_parser("derive-counts", help="B6: counts from the hashed crosswalk (gated)")
    dc.add_argument("--crosswalk", required=True)
    dc.add_argument("--b3-record", required=True)
    dc.add_argument("--dataset-config", default="configs/dataset/brats2021.yaml")
    dc.add_argument("--out", required=True)
    dc.add_argument("--synthetic", action="store_true", help="SYNTHETIC_TEST_DATA inputs only")
    dc.set_defaults(func=_cmd_derive_counts)
    sub.add_parser(
        "count-targets", help="print the B6 protocol verification targets (EXPECTED_BY_PROTOCOL)"
    ).set_defaults(func=_cmd_count_targets)
    gt = sub.add_parser("gate-transition", help="owner: move a B gate (dry run unless --apply)")
    gt.add_argument("gate")
    gt.add_argument("new_status")
    gt.add_argument("--evidence", default=None, help="committed evidence path (for PASSED)")
    gt.add_argument("--on", default=None, help="date YYYY-MM-DD (for PASSED)")
    gt.add_argument("--approved-route", default=None, help="B1 only: the approved data route")
    gt.add_argument("--apply", action="store_true")
    gt.set_defaults(func=_cmd_gate_transition)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = Path(args.repo_root) if args.repo_root else find_repo_root()
        return int(args.func(root, args))
    except BratsUncertaintyError as exc:
        print(f"ERROR [{type(exc).__name__}]: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
