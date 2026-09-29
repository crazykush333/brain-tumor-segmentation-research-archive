# Test fixtures: synthetic only

Everything in this directory is **synthetic**. It is generated in memory by
`synthetic.py` from fixed random seeds for software tests only.

- It is **not BraTS data**, not derived from BraTS data and not derived from any
  patient data.
- Synthetic case IDs use the prefix `SYN-` and never the BraTS naming pattern,
  except for the fixed protocol positive-control IDs where a test needs them. Those
  IDs are paired with synthetic masks and prove only that the code handles the IDs.
- No file here is an image, label volume or array dump. Volumes are created at test
  time in memory or in pytest's temporary directories.
- Synthetic numbers produced by tests are **never** results. They must not be
  written to `results/`, exported to the website or reported anywhere.
