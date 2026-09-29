"""[GATED: B1] B2 — hash acquired files and record their official source.

Thin wrapper over `brats-uncertainty record-acquisition`; see docs/data/DATA_PROVENANCE.md.
"""

from __future__ import annotations

import sys

from brats_uncertainty.cli import main

if __name__ == "__main__":
    sys.exit(main(["record-acquisition", *sys.argv[1:]]))
