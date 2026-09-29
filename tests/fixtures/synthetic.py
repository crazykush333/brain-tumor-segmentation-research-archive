"""Synthetic generators for tests. NOT BraTS data; never used as results."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from brats_uncertainty.statistics.units import UnitTable

SYNTHETIC_PREFIX = "SYN-"


def sphere(
    shape: tuple[int, int, int], center: tuple[float, float, float], radius: float
) -> NDArray[np.bool_]:
    grid = np.indices(shape).astype(np.float64)
    d2 = sum((grid[i] - center[i]) ** 2 for i in range(3))
    return np.asarray(d2 <= radius**2)


def synthetic_image(
    rng: np.random.Generator, shape: tuple[int, int, int] = (12, 12, 10)
) -> NDArray[np.float32]:
    """Four-channel synthetic volume with a zero background and a non-zero 'brain'."""
    brain = sphere(shape, tuple(s / 2 for s in shape), min(shape) / 2 - 1)  # type: ignore[arg-type]
    img = rng.normal(100.0, 20.0, size=(4, *shape)).astype(np.float32)
    img[:, ~brain] = 0.0
    return img


def synthetic_member_probs(
    rng: np.random.Generator, shape: tuple[int, int, int] = (16, 16, 16), noise: float = 0.2
) -> list[NDArray[np.float32]]:
    """Three synthetic 'member' probability maps around a random sphere."""
    center = tuple(float(rng.uniform(5, s - 5)) for s in shape)
    base = sphere(shape, center, float(rng.uniform(2, 4))).astype(np.float32)  # type: ignore[arg-type]
    out = []
    for _ in range(3):
        p = np.clip(base * 0.8 + rng.normal(0, noise, size=shape), 0, 1).astype(np.float32)
        out.append(p)
    return out


def synthetic_units(
    n_groups: int = 30,
    conditions: tuple[str, ...] = ("Full", "-T1", "-T1c", "-T2", "-FLAIR"),
    seed: int = 0,
    signal: float = 0.8,
    multi_case_every: int = 5,
) -> UnitTable:
    """Synthetic case-condition units. ``signal`` couples U1 to (1 - risk)."""
    rng = np.random.default_rng(seed)
    case_id, group_id, cond, risk, u1 = [], [], [], [], []
    for g in range(n_groups):
        n_cases = 2 if g % multi_case_every == 0 else 1
        for k in range(n_cases):
            cid = f"{SYNTHETIC_PREFIX}{g:03d}-{k}"
            for c in conditions:
                r = float(np.clip(rng.beta(2, 5), 0, 1))
                noise = rng.normal(0, 0.15)
                case_id.append(cid)
                group_id.append(f"SYN-G{g:03d}")
                cond.append(c)
                risk.append(r)
                u1.append(float(np.clip(signal * (1 - r) + (1 - signal) * 0.5 + noise, 0, 1)))
    return UnitTable.from_columns(case_id, group_id, cond, risk, {"U1": u1})
