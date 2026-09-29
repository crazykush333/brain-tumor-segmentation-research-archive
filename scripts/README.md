# scripts/

Thin command-line entry points over the `brats_uncertainty` package. Every script
that touches study data, trains, predicts or evaluates first calls
`require_action(...)`. It therefore **fails with `ResearchGateError` until the
corresponding protocol gates are closed** (with evidence) in
`docs/project_status.yaml`.

| Script | Gated action | Gates required |
|---|---|---|
| `checks/check_repository.py` | — (safe) | — |
| `reporting/export_site_data.py` | — (safe) | — |
| `data/build_manifest.py` | `build_manifest` | B1–B2 |
| `grouping/compute_t_screen.py` | `compute_t_screen` | B1–B6 |
| `grouping/run_pairwise_screen.py` | `pairwise_screen` | B1–B6 (+ T_screen record) |
| `grouping/freeze_patient_groups.py` | `freeze_patient_groups` | B1–B8 |
| `splitting/create_split.py` | `create_split` | B1–B9 |
| `experiments/train.py` | `train_main` | B1–B12, D1–D6 |
| `evaluation/analyze_primary.py` | `evaluate_internal_test` | B1–B12, D1–D6, C5, C6 + `eval-v1` checkout |

Run from the repository root, for example `python scripts/checks/check_repository.py`.
Data locations are passed as arguments or environment variables and never hard-coded.
