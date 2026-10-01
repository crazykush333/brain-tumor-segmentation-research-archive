# GitHub setup and the remote-execution loop

**Status (2026-10-01): this repository has no git remote, and the GitHub CLI (`gh`) is not installed on the owner's machine.** Nothing has been pushed. Creating the remote and pushing are owner actions: publishing code is outward-facing, and no credentials are used or stored here.

## 1. One-time: create the remote (owner)

1. On github.com, create an empty repository (private or public) with no README, licence or .gitignore, because the repository already has them.
2. From the repository root:

   ```bash
   git remote add origin https://github.com/<owner>/<repository>.git
   ```

   ```bash
   git push -u origin main infra/reproducibility-infrastructure
   ```

   ```bash
   git push origin protocol-v1.0
   ```

   The tag push publishes the frozen protocol tag unchanged; never use `--force`.
3. For a **private** repository, a remote session needs read access. Use a fine-grained, read-only token stored as a platform secret, such as a Kaggle Secret. Never put a token in a notebook cell, a config file or a URL that is printed.

## 2. The loop for every remote job

```
owner checkout (clean) ──commit──> GitHub ──clone at exact SHA/tag──> remote GPU session
        ^                                                                     │
        │                                                     gated CLI job (notebooks 00–06)
        │                                                                     │
        └── commit evidence/results <── export-artifacts <── download export/ ┘
                       │
                       └──> brats-uncertainty export-site-data ──> website build/deploy
```

1. **Before the job:** the owner's checkout is clean. Note the commit SHA (`git rev-parse HEAD`) or tag. Remote sessions always check out that exact SHA, never a branch name.
2. **Run** the notebook or VM step with `REPO_URL` and `COMMIT`. Every record stamps the commit, and real-mode records refuse dirty checkouts.
3. **Bring back** only the session's `export/` folder: records, run manifests, reports and result artifacts, never data.
4. **Import:**

   ```bash
   brats-uncertainty export-artifacts --source <downloaded export> --dest results/<EXPERIMENT>
   ```

   For gate evidence (for example the B2 record), copy the record to its evidence location, review it and stage it.
5. **Move the gate** with `brats-uncertainty gate-transition …`. Do a dry run first, then `--apply`, in the owner's checkout only.
6. **Validate and commit:**

   ```bash
   python -m pytest
   ```

   ```bash
   brats-uncertainty check-repo
   ```

   ```bash
   brats-uncertainty export-site-data
   ```

   Then `git commit`.
7. **Push and deploy:** `git push`. The website (Vercel/Netlify) builds from `website/` using the committed `website/data/*.json`.

## 3. Milestone tags (later; owner decision)

Suggested, never moved once created:
- `b6-verified` (B2–B6 complete);
- `split-v1` (B12);
- `eval-v1` (evaluation-code freeze, required by protocol SR4 / gate C6);
- `results-v1`.

`protocol-v1.0` is never moved or recreated.
