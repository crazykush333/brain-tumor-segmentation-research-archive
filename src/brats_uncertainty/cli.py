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


def _cmd_build_manifest(root: Path, args: argparse.Namespace) -> int:
    from brats_uncertainty.pipeline import stage_build_manifest

    m = stage_build_manifest(root, Path(args.dataset_config), Path(args.data_root), Path(args.out))
    print(f"manifest: {len(m.entries)} cases, sha256={m.sha256}")
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
    bm = sub.add_parser("build-manifest", help="[gated B2+] hash a local dataset into a manifest")
    bm.add_argument("--dataset-config", required=True)
    bm.add_argument("--data-root", required=True)
    bm.add_argument("--out", required=True)
    bm.set_defaults(func=_cmd_build_manifest)
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
