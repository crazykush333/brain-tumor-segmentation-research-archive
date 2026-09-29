# results/

No scientific results are available because experimental execution has not yet occurred.

This directory will hold small, provenance-stamped result artifacts (IDs and metrics
only; never images, predictions or checkpoints) written by
`brats_uncertainty.results.artifacts.write_artifact`. Every artifact records the
experiment ID, git commit, config hash, protocol hash and input hashes. Synthetic
(test) artifacts are refused here. `results/index.json` will list published
artifacts once results exist; the website reads only that index.
