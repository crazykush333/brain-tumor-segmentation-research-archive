"""Git helpers used to stamp every artifact with the exact code commit."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, timeout=30
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip()


def git_commit(repo_root: str | Path) -> str | None:
    """Full SHA of HEAD, or None if not a git checkout."""
    return _git(["rev-parse", "HEAD"], Path(repo_root))


def git_is_dirty(repo_root: str | Path) -> bool | None:
    """True if tracked files have uncommitted changes; None if unknown."""
    out = _git(["status", "--porcelain", "--untracked-files=no"], Path(repo_root))
    if out is None:
        return None
    return bool(out)


def git_tag_commit(repo_root: str | Path, tag: str) -> str | None:
    """Commit SHA a tag points to, or None if the tag does not exist."""
    return _git(["rev-parse", f"{tag}^{{commit}}"], Path(repo_root))


def git_tracked_files(repo_root: str | Path) -> list[str]:
    """Tracked files plus untracked-but-not-ignored files (relative paths)."""
    root = Path(repo_root)
    tracked = _git(["ls-files"], root) or ""
    untracked = _git(["ls-files", "--others", "--exclude-standard"], root) or ""
    files = {f for f in (tracked + "\n" + untracked).splitlines() if f.strip()}
    return sorted(files)
