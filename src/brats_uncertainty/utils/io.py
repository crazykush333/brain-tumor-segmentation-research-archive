"""Atomic, deterministic file writing."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


def write_json(path: str | Path, obj: Any, *, overwrite: bool = False) -> Path:
    """Write ``obj`` as pretty, key-sorted JSON atomically.

    Refuses to overwrite an existing file unless ``overwrite=True`` so that
    frozen artifacts (manifests, splits, groupings) cannot be silently replaced.
    """
    p = Path(path)
    if p.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".tmp-", suffix=p.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return p


def read_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as fh:
        return json.load(fh)


def read_yaml(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)
