# data/ — private research data (NOT distributed through this repository)

**No research data are present or redistributed here.** Everything under `data/`
except this README is git-ignored. The BraTS 2021 and BraTS-Africa data must be
obtained by each researcher from the official providers, through the data route
approved at gate B1, under the providers' terms (see `docs/data/DATA_ACCESS.md`).

**Status (2026-09-30): B1 is PENDING; B2-B6 are LOCKED. No data may be placed here until B1 has passed.** Synthetic test data are never generated here (the generator refuses any path inside the repository).

Local layout (create with `brats-uncertainty init-data-dirs`):

| Path | Contents | Tracked by git? |
|---|---|---|
| `data/raw/` | official files exactly as acquired (archives, NIfTI, crosswalk, metadata CSV) | **never** |
| `data/manifests/` | B2–B6 records, manifests and integrity reports produced by the code | no (IDs/hashes/counts are published separately after owner review) |
| `data/derived/` | anything computed from the images or labels | **never** |
| `data/cache/` | temporary files (nnU-Net folders live outside the repo via env vars) | **never** |

Rules:

- Never commit images, labels, predictions, arrays, licensed metadata files,
  archives, credentials (`kaggle.json`, `.env`, Synapse config) or checkpoints.
  `.gitignore` and `brats-uncertainty check-repo` enforce this.
- Never type a hash, count or ID list by hand; use the gated commands
  (`acquire` [dry run by default], `hash-metadata`, `validate-data`, `build-manifest`,
  `derive-counts`). They fail until their gates are closed.
- Public derived artifacts (hashes, counts, ID-only lists) are committed only
  after the owner reviews them, as administrative entries (see
  `docs/research/protocol-amendments/README.md`).
