"""Repository hygiene checks: prohibited files, secrets and protocol integrity.

Run in CI and before every commit (``brats-uncertainty check-repo``). Scans all
tracked files plus untracked files that are not git-ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from brats_uncertainty.protocol import load_protocol
from brats_uncertainty.utils.git import git_tracked_files

PROHIBITED_SUFFIXES = (
    ".nii",
    ".nii.gz",
    ".dcm",
    ".mha",
    ".mhd",
    ".nrrd",
    ".mgz",
    ".h5",
    ".hdf5",
    ".npz",
    ".npy",
    ".pkl",
    ".pickle",
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".pem",
    ".key",
    ".zip",
    ".tar",
    ".tgz",
    ".7z",
    ".xlsx",
    ".xls",
)
PROHIBITED_NAMES = (
    "kaggle.json",
    ".env",
    ".synapseConfig",
    ".netrc",
    "BraTS2021_MappingToTCIA.xlsx",
)
PROHIBITED_NAME_PATTERNS = (
    re.compile(r"^UCSF-PDGM-metadata.*\.csv$"),
    re.compile(r"^BraTS-Africa_TCIA_datainfo.*\.xlsx$"),
    re.compile(r"^credentials.*\.json$"),
    re.compile(r"^\.env\..+$"),
)
ALLOWED_NAMES = (".env.example",)
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private key block", re.compile("-----BEGIN [A-Z ]*" + "PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Kaggle API key", re.compile(r"\"key\"\s*:\s*\"[0-9a-f]{32}\"")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "generic API key assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret[_-]?key|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]"
        ),
    ),
)
MAX_FILE_BYTES = 5 * 1024 * 1024
TEXT_SUFFIXES = (
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".txt",
    ".cfg",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
    ".css",
    ".csv",
    ".sh",
    ".ini",
    ".cff",
    "Makefile",
    "Dockerfile",
)
FROZEN_PROTOCOL = "docs/research/FINAL_RESEARCH_PROTOCOL_v1.0.md"
_PROTOCOL_NAME = re.compile(r"(?i)FINAL_RESEARCH_PROTOCOL")


@dataclass(frozen=True)
class Finding:
    path: str
    problem: str


def _is_text(path: str) -> bool:
    return path.endswith(TEXT_SUFFIXES)


def check_paths(files: list[str], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in files:
        name = Path(rel).name
        low = rel.lower()
        if name in ALLOWED_NAMES:
            continue
        if low.endswith(PROHIBITED_SUFFIXES):
            findings.append(Finding(rel, "prohibited file type (imaging/array/checkpoint/key)"))
        if name in PROHIBITED_NAMES or any(p.match(name) for p in PROHIBITED_NAME_PATTERNS):
            findings.append(Finding(rel, "prohibited file (credentials or licensed metadata)"))
        if (
            _PROTOCOL_NAME.search(name)
            and rel != FROZEN_PROTOCOL
            and not rel.startswith("docs/research/archive/")
        ):
            findings.append(Finding(rel, "file could be mistaken for the active protocol"))
        p = root / rel
        if p.is_file():
            if p.stat().st_size > MAX_FILE_BYTES:
                findings.append(
                    Finding(rel, f"file larger than {MAX_FILE_BYTES // (1024 * 1024)} MiB")
                )
            if _is_text(rel):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for label, pat in SECRET_PATTERNS:
                    if pat.search(text):
                        findings.append(Finding(rel, f"possible secret: {label}"))
    return findings


def check_repository(root: str | Path) -> list[Finding]:
    root = Path(root)
    findings = check_paths(git_tracked_files(root), root)
    if not (root / FROZEN_PROTOCOL).is_file():
        findings.append(Finding(FROZEN_PROTOCOL, "frozen protocol missing"))
    else:
        try:
            load_protocol(root)
        except Exception as exc:  # report, do not crash the scan
            findings.append(Finding(FROZEN_PROTOCOL, f"protocol integrity: {exc}"))
    return findings
