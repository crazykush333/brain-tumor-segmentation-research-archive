"""Repository-root discovery. No absolute paths are hard-coded anywhere."""

from __future__ import annotations

import os
from pathlib import Path

ENV_ROOT = "BRATS_UNCERTAINTY_ROOT"
_MARKERS = ("pyproject.toml", "configs/protocol")


def find_repo_root(start: str | Path | None = None) -> Path:
    """Locate the repository root.

    Order: the ``BRATS_UNCERTAINTY_ROOT`` environment variable, then the first
    ancestor of ``start`` (default: current directory) containing both
    ``pyproject.toml`` and ``configs/protocol``.
    """
    env = os.environ.get(ENV_ROOT)
    if env:
        root = Path(env).expanduser().resolve()
        if not all((root / m).exists() for m in _MARKERS):
            raise FileNotFoundError(f"{ENV_ROOT}={root} is not a brats-uncertainty repository root")
        return root
    here = Path(start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if all((candidate / m).exists() for m in _MARKERS):
            return candidate
    raise FileNotFoundError(
        "repository root not found; run inside the repository or set " + ENV_ROOT
    )


def is_within(path: str | Path, parent: str | Path) -> bool:
    """True if ``path`` resolves to a location inside ``parent``."""
    try:
        Path(path).resolve().relative_to(Path(parent).resolve())
    except ValueError:
        return False
    return True
