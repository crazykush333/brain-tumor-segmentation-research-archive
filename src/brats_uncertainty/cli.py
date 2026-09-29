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

from brats_uncertainty import PROTOCOL_VERSION, __version__
from brats_uncertainty.errors import BratsUncertaintyError
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


def _cmd_record_acquisition(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.data.records import SourceInfo
    from brats_uncertainty.data.stages import stage_record_acquisition

    source = SourceInfo(
        dataset=args.dataset,
        dataset_version=args.dataset_version,
        doi=args.doi,
        source_url=args.source_url,
        route=args.route,
    )
    rec = stage_record_acquisition(
        root,
        source,
        [Path(f) for f in args.files],
        acquisition_date=args.acquisition_date,
        acquired_by=args.acquired_by,
        out=Path(args.out),
        notes=args.notes,
    )
    print(f"B2 record written: {args.out} ({len(rec.files)} file(s) hashed)")
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
    )
    print(f"{args.gate} record written: {args.out} ({rec.file.file_name} sha256={rec.file.sha256})")
    return 0


def _cmd_validate_data(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.data.stages import stage_validate_data
    from brats_uncertainty.utils.io import write_json

    report = stage_validate_data(
        root, Path(args.dataset_config), Path(args.data_root), deep=not args.quick
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

    m = stage_build_manifest(root, Path(args.dataset_config), Path(args.data_root), Path(args.out))
    print(f"B5 manifest: {len(m.entries)} cases, sha256={m.sha256}")
    return 0


def _cmd_derive_counts(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.data.stages import stage_derive_counts

    rec = stage_derive_counts(
        root, Path(args.crosswalk), Path(args.b3_record), Path(args.dataset_config), Path(args.out)
    )
    print(f"B6 record written: {args.out} status={rec.status} counts={rec.counts}")
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
    ra = sub.add_parser("record-acquisition", help="[gated B1] B2: hash acquired files + source")
    ra.add_argument("--dataset", required=True)
    ra.add_argument("--dataset-version", required=True, help="as shown on the official page")
    ra.add_argument("--doi", required=True)
    ra.add_argument("--source-url", required=True)
    ra.add_argument("--route", required=True, help="must equal the B1-approved route")
    ra.add_argument("--acquisition-date", required=True, help="YYYY-MM-DD")
    ra.add_argument("--acquired-by", required=True)
    ra.add_argument("--notes", default="")
    ra.add_argument("--out", required=True)
    ra.add_argument("files", nargs="+", help="acquired archives/files to hash")
    ra.set_defaults(func=_cmd_record_acquisition)
    hm = sub.add_parser("hash-metadata", help="[gated B1-B2/B3] B3/B4: hash a metadata file")
    hm.add_argument("--gate", required=True, choices=["B3", "B4"])
    hm.add_argument("--file", required=True)
    hm.add_argument("--source-url", required=True)
    hm.add_argument("--doi", required=True)
    hm.add_argument("--out", required=True)
    hm.set_defaults(func=_cmd_hash_metadata)
    vd = sub.add_parser("validate-data", help="[gated B1-B2] integrity audit of acquired data")
    vd.add_argument("--dataset-config", required=True)
    vd.add_argument("--data-root", required=True)
    vd.add_argument("--quick", action="store_true", help="headers only; skip full gzip CRC read")
    vd.add_argument("--out", default=None)
    vd.set_defaults(func=_cmd_validate_data)
    bm = sub.add_parser("build-manifest", help="[gated B1-B4] B5: integrity audit + manifest")
    bm.add_argument("--dataset-config", required=True)
    bm.add_argument("--data-root", required=True)
    bm.add_argument("--out", required=True)
    bm.set_defaults(func=_cmd_build_manifest)
    dc = sub.add_parser("derive-counts", help="[gated B1-B5] B6: counts from the hashed crosswalk")
    dc.add_argument("--crosswalk", required=True)
    dc.add_argument("--b3-record", required=True)
    dc.add_argument("--dataset-config", default="configs/dataset/brats2021.yaml")
    dc.add_argument("--out", required=True)
    dc.set_defaults(func=_cmd_derive_counts)
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
