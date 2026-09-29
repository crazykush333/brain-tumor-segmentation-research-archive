"""Guarded nnU-Net v2 trainer classes for arms A and B (requires the ``nnunet`` extra).

STATUS: TEMPLATE, NOT YET VERIFIED against the nnU-Net version that will be
pinned at M1/EXP-001. nnU-Net's trainer and transform APIs change between
releases. Before any training, this module must be checked against the pinned
version (see docs/reproducibility/COMPUTE.md). Training is additionally blocked
by research gates until B12 and D6 are closed.

To be discovered by nnU-Net, these classes must be importable from
``nnunetv2.training.nnUNetTrainer`` (e.g. by copying/symlinking this file into
that package at environment-setup time). They are not a new architecture:
they only fix the epoch count, the seed and (arm B) append the §10 dropout
transform after nnU-Net's own augmentation pipeline.
"""

from __future__ import annotations

import os
import random
from typing import Any

import numpy as np

from brats_uncertainty.evaluation.guards import require_action
from brats_uncertainty.models.dropout import ModalityDropoutPolicy
from brats_uncertainty.models.nnunet import PROTOCOL_EPOCHS, PROTOCOL_SEEDS

try:  # optional heavy dependency
    import torch
    from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer
except ImportError:  # pragma: no cover - exercised only with the nnunet extra
    nnUNetTrainer = None  # noqa: N816 - upstream class name
    torch = None


def _seed_from_env() -> int:
    raw = os.environ.get("BRATS_UNC_SEED")
    if raw is None:
        raise RuntimeError("BRATS_UNC_SEED must be set (protocol seeds 0, 1, 2)")
    seed = int(raw)
    if seed not in PROTOCOL_SEEDS:
        raise RuntimeError(f"seed {seed} not in protocol seeds {PROTOCOL_SEEDS}")
    return seed


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


class DropoutTransform:
    """Batch-level transform applying the §10 policy to the ``data`` entry.

    Applied after nnU-Net augmentation. Operates per sample on normalized data.
    """

    def __init__(self, seed: int) -> None:
        self.policy = ModalityDropoutPolicy()
        self.rng = np.random.default_rng(seed)

    def __call__(self, **data_dict: Any) -> dict[str, Any]:
        data = data_dict["data"]
        is_tensor = torch is not None and isinstance(data, torch.Tensor)
        arr = data.cpu().numpy() if is_tensor else np.asarray(data)
        if arr.ndim == 4:  # single sample (C, X, Y, Z)
            out, _ = self.policy.apply(arr, self.rng)
        else:
            out, _ = self.policy.apply_batch(arr, self.rng)
        data_dict["data"] = torch.from_numpy(out) if is_tensor else out
        return data_dict


if nnUNetTrainer is not None:  # pragma: no cover - requires nnunetv2 + torch

    class nnUNetTrainer_BratsUnc_250ep(nnUNetTrainer):  # noqa: N801 - nnU-Net naming
        """Arm A: 250 epochs, protocol seed, no modality dropout."""

        ARM = "A"

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            require_action("train_main")
            self.protocol_seed = _seed_from_env()
            _seed_everything(self.protocol_seed)
            super().__init__(*args, **kwargs)
            self.num_epochs = PROTOCOL_EPOCHS
            self.save_every = 5

    class nnUNetTrainer_BratsUnc_250ep_ModalityDropout(nnUNetTrainer_BratsUnc_250ep):  # noqa: N801
        """Arm B: as arm A plus the §10 modality-dropout policy after augmentation.

        VERIFY against the pinned nnU-Net version: the hook below wraps the
        training dataloader output; the exact integration point differs across
        nnU-Net releases.
        """

        ARM = "B"

        def get_dataloaders(self) -> Any:
            train_loader, val_loader = super().get_dataloaders()
            transform = DropoutTransform(self.protocol_seed)

            class _Wrapped:
                def __init__(self, inner: Any) -> None:
                    self.inner = inner

                def __iter__(self) -> Any:
                    return self

                def __next__(self) -> Any:
                    return transform(**next(self.inner))

                def __getattr__(self, name: str) -> Any:
                    return getattr(self.inner, name)

            return _Wrapped(train_loader), val_loader
