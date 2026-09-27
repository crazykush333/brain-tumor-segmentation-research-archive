# FINAL RESEARCH PROTOCOL (pre-registration)

| Field | Value |
|---|---|
| Protocol version | **v0.2 — REVISED DRAFT, awaiting owner approval** (pre-freeze revision; **not frozen**) |
| Date of this revision | 2026-09-27 |
| Previous version | v0.1 (2026-09-27), superseded |
| Reason for revision | [13_PRE_FREEZE_AUDIT.md](13_PRE_FREEZE_AUDIT.md), verdict "B. Protocol requires revision". Changes are listed in §25 and [14_PROTOCOL_REVISION_SUMMARY.md](14_PROTOCOL_REVISION_SUMMARY.md). |
| Freeze rule | Only after the owner approves **and** the pre-freeze checklist is complete: the version becomes v1.0 and is git-tagged `protocol-v1.0`. After that, changes are allowed only as logged amendments (§25). No change is allowed after any test-set evaluation. |
| Basis | [12_PRE_PROTOCOL_AUDIT.md](12_PRE_PROTOCOL_AUDIT.md), [13_PRE_FREEZE_AUDIT.md](13_PRE_FREEZE_AUDIT.md), [search_log.md](search_log.md) |

No experiment has been run and no data has been downloaded. This document contains no results. Numbers are design parameters, **[LITERATURE RESULT]**s, **[VERIFIED]** metadata facts or **[ESTIMATE]**s.

### Pre-freeze checklist

**None of these items is complete.** Each must be closed, or explicitly waived by the owner with a reason, before v1.0.

- [ ] **1. BrainLes / BraTS 2024 proceedings** remain unscreened (the volume could not be located on 2026-09-27). Screen them title by title and update §23 if anything overlaps.
- [ ] **2. PNDC** (Qiu et al., IEEE TMI 2025, doi 10.1109/TMI.2025.3526818): full text is unverified; only the abstract has been read. Read it, or record it as inaccessible.
- [ ] **3. BraTS 2021 / TCIA crosswalk.** Record the SHA-256 of `BraTS2021_MappingToTCIA.xlsx` at the data milestone. Re-derive the site-1 count (expected 511) from the file used for the splits.
- [ ] **4. BraTS-Africa file-level verification.** Confirm on the downloaded files:
  - label values (expected 1 = NETC, 2 = SNFH, 3 = ET);
  - the number of eligible glioma cases (expected ≤ 95);
  - the presence of all 4 sequences.
- [ ] **5. Licensing.** Establish whether BraTS 2021 data (TCIA Restricted License Agreement / Synapse terms) may be stored as a *private* Kaggle dataset or must be re-downloaded and re-preprocessed each session (see SR7).
- [ ] **6. EXP-001 compute pilot.** Measure the quantities in §17.2 and confirm or revise the budget under SR1/SR6. (EXP-001 is approved only after owner review of v0.2.)
- [ ] **7. Owner approval** of this protocol.

---

## 1. Research question

> When MRI sequences are missing at inference, does the case-level ensemble uncertainty of a modality-dropout nnU-Net discriminate unreliable enhancing-tumour segmentations within a given missing-sequence condition, i.e. beyond what the known identity of the missing sequence provides? How does this vary with which sequence is missing, and do the discrimination and operating thresholds transfer to a held-out institution and an external population?

**The central scientific question is:** *among cases with the same missing sequence, can ensemble disagreement identify which cases are likely to fail?*

Why the question is framed this way:

- In deployment, the identity of the missing sequence is known from the protocol or DICOM header.
- A quality-control signal is therefore only useful if it separates good from bad cases **given** that knowledge.
- Within a fixed condition, the missingness-indicator rule (I) assigns every case the same score. Any discrimination there must come from the uncertainty signal itself.

## 2. Hypotheses

### 2.1 Primary hypothesis (single; α = 0.05, two-sided 95% CI)

**H-W.** On the internal test set, for the modality-dropout (arm B) ensemble, the mean over the five primary C5 conditions (§10) of the within-condition ET ΔAURC is < 0.

Definitions:

- ΔAURC_c = AURC_c(U1) − AURC_c(I)
- U1 = ensemble pairwise-Dice confidence (§11).
- I = missingness-indicator baseline (§11).
- Within a fixed condition c, I is constant. Its expected AURC under random tie-breaking therefore equals the **mean ET risk of condition c** (random ranking). ΔAURC_c < 0 means that U1 ranks failures within condition c better than chance, i.e. better than knowing only the missing sequence.

### 2.2 Key secondary hypotheses

These are tested within the families of §14.

- **H-W(−T1c).** The −T1c component ΔAURC_−T1c < 0. It is reported separately as the key secondary result, because T1c is the sequence on which ET delineation most depends.
- **H-W-ext.** The mean within-condition ET ΔAURC < 0 on the held-out institution (UPenn, 511 cases) and on BraTS-Africa, analysed **separately** and never pooled.
- **H-T (threshold transfer).** A confidence threshold fixed on internal validation at 80% coverage does not produce *unsafe transfer* (§4, S7) on the internal test, UPenn or BraTS-Africa sets.
- **H4.** For the full-modality (arm A) ensemble under missing inputs, within-condition discrimination (ΔAURC_c for c ≠ Full) is weaker than for arm B. This tests whether a non-robust model fails silently.

### 2.3 Supporting and replication analyses (not confirmatory; no α spent)

- **Supporting / sanity (formerly H-SEG).** Compare arm B and arm A on ET Dice across the C5 conditions, to show that the modality-dropout model is usable under incomplete inputs. This replicates known findings [C6, C7, C8] and is **not** the scientific contribution. A full-input TOST (B vs A, ET Dice, margin ±1.5 Dice points following [C7]) is kept as a sanity check that dropout training does not degrade full-input performance.
- **Replication (formerly H2).** Voxel-level calibration (ECE/Brier) per condition and region. MMA-LTS (Lee et al., MICCAI 2026) has already evaluated voxel-level calibration across missing-modality combinations and tumour regions. This protocol tests only **whether that published behaviour is reproduced** in a modality-dropout nnU-Net setting. Missing-sequence-specific calibration is **not** claimed as a contribution.

## 3. Primary endpoint and justification

| Endpoint | Definition | Justification |
|---|---|---|
| **Mean within-condition ET ΔAURC** | ΔAURC = (1/5) Σ_c∈C5 [AURC_c(U1) − AURC_c(I)] on the internal test set, B ensemble. Units within condition c = patients. Risk = 1 − ET Dice. Dice convention: both masks empty → 1; exactly one empty → 0. | It isolates within-condition discrimination, the only component that cannot be supplied by knowing the missing sequence. A pooled comparison mixes between-condition difficulty ordering with within-condition discrimination (Joham et al., UNSURE 2026 [13 §3.4]), so it cannot test the research question. ET is the region most dependent on a single sequence (T1c), drives response assessment, and is the least robust region [H1, H2]. |

**AURC computation.**

- For n units ranked by descending confidence, AURC is the mean selective risk over the coverages k/n, for k = 1…n.
- Ties are handled by the expected value under random tie-breaking. For I within a condition, this gives exactly the mean risk.
- Because U1 and I score the same predictions, ΔAURC_c equals Δe-AURC_c.

## 4. Secondary endpoints

**Tested within the families of §14:**

- **S1.** ΔAURC_c for each of the five C5 conditions (ET), with −T1c highlighted (H-W(−T1c)).
- **S2.** The primary endpoint computed for TC and WT.
- **S8.** The primary endpoint and S1 on the UPenn held-out institution (511 cases) and on BraTS-Africa (≤ 95 cases), separately (H-W-ext).
- **S7.** Threshold transfer (H-T):
  - τ is fixed once on the internal **validation** set, as the U1 threshold giving 80% coverage on the validation C5 units (equal condition mixture).
  - Sensitivity analyses use 70% and 90%.
  - For each target set (internal test, UPenn, BraTS-Africa), with τ unchanged, compute:
    - **Δrisk** = target selective ET risk − validation selective ET risk;
    - **Δcoverage** = target coverage − validation coverage.
  - CIs come from **independent** patient bootstraps of the validation set and the target set (10,000 paired replicates, each resampling both sets independently).
  - **Unsafe transfer:** the 95% CI of Δrisk lies entirely > 0.
  - **Inefficient transfer:** the 95% CI of Δcoverage lies entirely < 0.
  - Neither label is applied otherwise, and **no equivalence is claimed**.
  - τ itself is not re-estimated within the bootstrap. This is a stated limitation (§22).
- **S9.** Arm A within-condition ΔAURC_c for the four missing conditions (H4).

**Secondary, descriptive only** (reported with 95% CIs, no hypothesis test):

- **S3.** WT and TC Dice; HD95 per region. HD95 uses the BraTS empty-mask convention, to be confirmed from the official evaluation code before freeze.
- **S4 (replication of MMA-LTS).** ECE and Brier score per region per condition:
  - computed on the ensemble-mean probability;
  - ROI = union of GT and predicted region, dilated by 3 voxels;
  - 15 equal-width bins; per-case values averaged over cases.
  - Interpreted only as consistency or inconsistency with published voxel-level findings.
- **S5.** Volume failure:
  - absolute ET volume error (mL);
  - **"RANO 2.0-motivated relative ET volume error ≥ 40%"** as a binary failure definition, for cases with GT ET ≥ 1 mL, with AURC computed on this risk;
  - sensitivity analysis at **65%**.
  - RANO 2.0's 40% (progression) and 65% (partial response) thresholds concern **longitudinal change in tumour burden**. They are **not** segmentation-error criteria. They are used here only as clinically motivated secondary error thresholds.
  - The ≥ 1 mL minimum is a **study-defined choice**.
- **S6.** Spearman ρ between U1 and ET Dice, per condition.
- **S10.** Fifteen-subset (C15) analysis, **internal test set and arm B only**: ET Dice, within-condition ET ΔAURC and ECE per subset. C15 is not run on external datasets unless approved later as an amendment.
- **S12. Pooled analyses (descriptive only; they must not drive the main conclusion).** The pooled C5 units are ranked by:
  1. U1;
  2. I (validation-estimated condition risk);
  3. the lexicographic **"I-then-U1"** ranker: rank first by the condition's validation-estimated ET risk, then break ties within a condition by U1.

  Comparing I, U1 and I-then-U1 separates information carried by the missingness condition from information carried by uncertainty within the condition, and shows their combination. Pooled AURC mixes **between-condition difficulty** with **within-condition discrimination**. It therefore cannot serve as the primary test of information beyond missingness identity.
- **S13. Mixture-weight sensitivity** for S12 and S7. Weights are applied by case-weighting the pooled units:
  - (a) equal weights over C5;
  - (b) 80% Full + 5% for each single-missing condition.

  Both are **hypothetical deployment mixtures**. Neither is claimed to be clinically representative. Equal weighting is arbitrary.
- **S14. Indicator transfer error.** For each condition, report the validation-estimated ET risk minus the realized target risk, on the internal test, UPenn and BraTS-Africa sets.
- **Supporting:** arm B vs arm A ET Dice over C5, and the full-input TOST (§2.3).

**Exploratory** (no inference): U3 single-model confidence (§11).

**Removed from the planned analysis** (possible future work only):

- mirroring test-time augmentation
- QU-BraTS uncertainty score
- lesion-wise Dice

## 5. Datasets

| Role | Dataset | Inclusion | n |
|---|---|---|---|
| **Development** (train / validation / internal test) | BraTS 2021 training set (Synapse / TCIA Restricted License Agreement) | All training cases **not** from site 1 (UPenn) | **740** [VERIFIED from crosswalk metadata] |
| **Held-out institution (HOI)** | UPenn-origin cases **within** BraTS 2021 training: `UPENN-GBM` (403) + `UPENN-GBM_Additional` (108), all **site 1** | All with 4 sequences and labels | **511** [VERIFIED from crosswalk metadata] |
| **External** | BraTS-Africa, TCIA **v2** release (CC BY 4.0). Metadata sheets: "95 Glioma", "51 OtherNeoplasms". | The **95** adult glioma cases with 4 sequences and labels. **51 OtherNeoplasms cases excluded.** | **≤ 95** (to confirm on files) |

Notes on the held-out institution:

- **Source:** the official TCIA crosswalk `BraTS2021_MappingToTCIA.xlsx`, which gives source collection and site ID for every BraTS 2021 case.
- The crosswalk was inspected as identifier metadata only. It is **not committed** to this repository unless its licence explicitly permits redistribution. Its SHA-256 is recorded at the data milestone (checklist item 3).
- **Why all 511 cases:** holding out the entire institution prevents same-institution leakage. Excluding only the 403 `UPENN-GBM` cases (as implied by the development n = 848 in [C7]) would leave 108 site-1 cases in development [INFERENCE from 1,251 − 403 = 848].

**Shift characteristics:**

- **HOI:** same BraTS preprocessing and curation, different institution. It is likely a mild shift; [C7] reports ~95% external Dice [LITERATURE RESULT].
- **BraTS-Africa:** population and acquisition shift. Four Nigerian centres and three scanner models (Siemens Magnetom Essenza, GE SIGNA Creator, Philips Achieva) per the v2 metadata [VERIFIED metadata]. Labels were refined from nnU-Net pre-segmentations with multi-stage expert review [A5].

**Not used:** UCSF-PDGM, EGD and standalone TCIA UPenn-GBM (possible future work).

## 6. Patient-level splits

**Not yet created.** Splits are created only after v1.0.

- Development (740) is split **70 / 10 / 20** into train / validation / internal test [ESTIMATE ≈ 518 / 74 / 148].
- Stratification: ET present vs absent, and WT-volume tertile. Both are computed from labels only.
- Split seed `20260927`. The split is performed once, before any training.
- ID lists (IDs only) are committed to `splits/`, and their hashes are recorded in the v1.0 protocol.
- One BraTS subject is treated as one patient. Any duplicate TCIA patient IDs are grouped.
- **Site 18 (UCSF, 382 training cases) stays in development.** Site composition of each split is reported.

## 7. Deduplication

- **Development vs HOI:** disjoint by site, per the crosswalk.
- **BraTS-Africa vs BraTS 2021:** different institutions; overlap is very unlikely [INFERENCE]. An identical-image-hash check is performed as a safeguard.
- The deduplication script output (IDs and counts) is committed, and the counts are reported in the paper.

## 8. Preprocessing

- Use the **BraTS-provided preprocessed** images: SRI24 space, 1 mm isotropic, skull-stripped. No re-registration.
- **nnU-Net v2**, version pinned at M1.
  - The raw dataset folder contains train + validation only, so the fingerprint and plans never see test data.
  - Default 3d_fullres plan and nnU-Net z-score normalization within the non-zero mask.
- Channel order is fixed as `[T1, T1c, T2, FLAIR]` and asserted by unit test.
- Region mapping:
  - BraTS 2021: ET = {4}, TC = {1, 4}, WT = {1, 2, 4}.
  - BraTS-Africa, **expected** labels 1 = NETC, 2 = SNFH, 3 = ET: ET = {3}, TC = {1, 3}, WT = {1, 2, 3}. **To be verified on files** (checklist item 4); the mapping is unit-tested.

## 9. Models

| | Arm A | Arm B |
|---|---|---|
| Framework | nnU-Net v2 3d_fullres, region-based (sigmoid WT/TC/ET) | same |
| Schedule | 250 epochs (`nnUNetTrainer_250epochs` semantics); `save_every` = 5 | same |
| Training data | train split | same |
| Missing-sequence dropout | none | §10 policy |
| Seeds | 0, 1, 2 | 0, 1, 2 |
| Checkpoint | `checkpoint_final` (pre-specified) | same |
| Inference | sliding window, step 0.5, **mirroring off**, threshold 0.5 | same |
| Ensemble | mean of the 3 members' sigmoid probabilities | same |

No new architecture, no MC-dropout and no attention or fusion module is used.

## 10. Missingness simulation

- A missing sequence is represented by setting its **normalized** channel to 0 (the brain-masked mean, equal to the background value). The same operation is used in training (arm B) and at inference.
- **C5 (primary):** {Full, −T1, −T1c, −T2, −FLAIR}.
- **C15 (secondary, internal test and arm B only):** all 15 non-empty subsets.
- **Arm B training policy:** per sample, with probability 0.5 the input is full. Otherwise one of the 14 non-full, non-empty subsets is chosen uniformly, after augmentation. The policy is fixed a priori and **not tuned**.
- Zero-filling is not the same as a real missing or degraded acquisition (§22).

## 11. Confidence scores

Scores are computed per case and region r.

- **U1 (primary):** mean pairwise Dice between the three members' binary masks for r. Both empty → 1.
- **U2 (secondary, descriptive):** negative mean binary entropy of the ensemble-mean probability within the ROI (union of member masks for r, dilated by 3 voxels). An empty ROI gives entropy 0.
- **U3 (exploratory):** single-model (seed 0) mean max-probability within the ROI.
- **I (baseline):** −(mean risk of that condition for r), estimated on the **validation** set for the same arm's ensemble.
  - Within a condition, I is constant (random-ranking baseline).
  - It is used across conditions only in the pooled and lexicographic analyses (S12).
  - No test or external data are used to estimate I.
- **I-then-U1 (secondary):** lexicographic, as defined in S12.
- **Not included:** temperature scaling and any missingness-conditioned calibrator. Voxel-level missingness-conditioned calibration is already addressed by MMA-LTS.

## 12. Failure definitions

- **Primary:** continuous risk = 1 − ET Dice.
- **Secondary:** the S5 binary volume failure (40%; 65% sensitivity).
- Risk–coverage curves use the tie handling of §3.
- Binary-failure AUROC may be reported as exploratory.

## 13. Statistical procedures

**Primary (H-W), 10,000 patient-level bootstrap replicates on the internal test set.** For each replicate:

1. Resample patients with replacement, keeping **all C5 conditions** of every sampled patient.
2. For each condition c, compute AURC_c(U1) and AURC_c(I) (the mean ET risk of condition c in the replicate).
3. Compute ΔAURC_c.
4. Average the five ΔAURC_c values.

**Reporting:**

- the point estimate (full sample) of the mean ΔAURC, and each ΔAURC_c, with **−T1c** highlighted;
- percentile 95% CIs, with BCa as a sensitivity analysis;
- a two-sided bootstrap p-value, 2 × min(P*(Δ ≥ 0), P*(Δ ≤ 0)), reported as approximate.

**Decision rule:** H-W is supported if the 95% CI of the mean ΔAURC lies entirely below 0.

**Other procedures:**

- **Secondary tested endpoints:** the same bootstrap scheme on the relevant set. S7 uses independent validation and target bootstraps (§4).
- **Supporting:** per-patient ET Dice differences (B − A) averaged over C5, with a Wilcoxon signed-rank test and bootstrap CI reported descriptively. The full-input TOST uses a ±1.5 Dice-point margin.
- **Seed variation:** single-member metrics are reported as mean ± SD over 3 seeds, descriptive only.
- External sets are never pooled with each other or with internal data. **No statistical equivalence is claimed** for any external result.

## 14. Multiplicity

- **Primary:** one hypothesis, α = 0.05. No multiplicity adjustment is needed.
- **Secondary families**, Holm-corrected **within each family only**:

| Family | Contents |
|---|---|
| F1 | S1: ΔAURC_c for the 5 C5 conditions, internal. −T1c is reported as the key result. |
| F2 | S8: mean within-condition ΔAURC on UPenn and on BraTS-Africa (2 tests). |
| F3 | S7: unsafe-transfer Δrisk at 80% coverage on internal test, UPenn and BraTS-Africa (3 tests). |
| F4 | S2: TC and WT mean within-condition ΔAURC (2 tests). |
| F5 | S9: arm A ΔAURC_c for the 4 missing conditions (4 tests). |

- **No global FWER control across secondary families is claimed.** Secondary results are interpreted as supporting evidence.
- Everything listed as descriptive, replication, supporting or exploratory is reported with CIs and without significance claims.

## 15. Confidence intervals

- Patient bootstrap, 10,000 replicates, percentile method (BCa as a sensitivity analysis).
- 95% throughout.
- Bootstrap seed `12345`.

## 16. Seeds

| Seed | Value |
|---|---|
| Training | 0, 1, 2 |
| Split | 20260927 |
| Bootstrap | 12345 |
| Figure-case sampling | 7 |

cuDNN / nnU-Net non-determinism is acknowledged.

## 17. Compute budget (ESTIMATES until EXP-001)

### 17.1 Budget

- **Cap:** 220 GPU-h (Kaggle free tier, about 4–8 weeks).
- **Training:** 6 runs × 250 epochs ≈ 75–150 GPU-h [ESTIMATE]. The cost does not depend on development-set size, because nnU-Net epochs are a fixed 250 iterations.
- **Primary inference:** ≈ 828 cases (val ~74, test ~148, UPenn 511, Africa ≤ 95) × 5 conditions × 6 models ≈ 21–55 GPU-h [ESTIMATE].
- **C15** (internal test, arm B): ≈ 4–10 GPU-h [ESTIMATE].
- **Total:** ≈ 100–215 GPU-h [ESTIMATE].
- Softmax maps are not stored except for ≤ 20 pre-selected figure cases. Metrics are computed on the fly.

### 17.2 EXP-001 must measure

1. Seconds per epoch on P100, on a single T4, and with two concurrent runs on 2×T4.
2. GPU utilisation (to detect a CPU/dataloader bottleneck).
3. Peak GPU memory.
4. Preprocessing time and on-disk size.
5. Checkpoint/resume correctness after a forced session kill.
6. Per-case inference time (3-member ensemble, no mirroring, including on-the-fly metrics).
7. The actual Kaggle quota, session limit and writable disk.
8. Short-run seed variability.

## 18. External validation

- The UPenn HOI set and BraTS-Africa are used **only** for final evaluation.
- No training, tuning, threshold selection, indicator-risk estimation, calibration or checkpoint choice uses them.
- Each set is evaluated once, with frozen code tagged `eval-v1`, and each is analysed separately.

## 19. Failure analysis

A rule-based categorization of (patient, condition) units per [05 §6](05_EXPERIMENTAL_DESIGN.md), plus:

- **Confident failure:** U1 above the validation 80th percentile and ET Dice < 0.5.
- **Hallucinated ET:** GT ET empty but predicted ET present, broken down by condition, especially −T1c.
- **Missed ET:** the reverse case.

Counts are reported per condition and dataset. Figure cases are selected by rule (seed 7), not by hand.

## 20. Stopping rules

- **SR1 (per-run cost).** If the pilot-measured time exceeds 25 GPU-h per run, switch all 6 runs to 150 epochs before any evaluation. If still infeasible, consult the owner.
- **SR2 (sanity, validation only).** If arm A's full-input mean ET Dice on **validation** is < 0.75, stop and debug before any test evaluation. The threshold is set a priori as clearly below typical nnU-Net BraTS 2021 performance; it is not a target.
- **SR3 (data).**
  - If the site-1 cases cannot be reproducibly identified from the crosswalk: drop the HOI set, use all 1,251 cases for development, and log the deviation.
  - If BraTS-Africa has fewer than 30 eligible labelled glioma cases: its analyses become descriptive only.
- **SR4 (integrity).** Test sets are evaluated once with tagged code. Any re-evaluation is logged, and both results are reported.
- **SR5 (bugs).** If a bug is found after evaluation: fix it, re-run everything affected, and report the deviation and both results.
- **SR6 (projected total compute).** If EXP-001 projects total compute > 220 GPU-h, apply these reductions **in order**, re-projecting after each:
  1. Arm A external inference only on Full, −T1c and −FLAIR.
  2. Drop C15.
  3. Switch all six runs to 150 epochs.
  4. Consult the owner.
- **SR7 (licensing).** If the BraTS licence does not permit the planned storage or re-hosting route (e.g. a private Kaggle dataset), halt compute until a compliant workflow is established (e.g. per-session download and preprocessing).
- **SR8 (platform change).** If Kaggle hardware or quota changes materially, recompute the project budget before continuing.

## 21. Interpretation rules

| Outcome | Interpretation |
|---|---|
| H-W: 95% CI entirely < 0 | Among internal cases with the same missing-sequence condition, ensemble disagreement ranks ET failures better than chance on average over C5. Uncertainty adds information beyond the known missingness identity. |
| H-W: CI includes 0 | No evidence that uncertainty adds within-condition information. This is **not** evidence of equivalence. |
| H-W: CI entirely > 0 | Within-condition ranking is worse than chance. This is an important negative finding. |
| −T1c component differs from the others | Reported as condition-dependent reliability. It is a supporting (F1) result, not a primary claim. |
| External (F2) | The same wording, per dataset. Conclusions about transfer are made per dataset, never pooled. |
| Transfer (F3) | "Unsafe transfer" / "inefficient transfer" only by the CI rules in S7. Otherwise "no evidence of unsafe/inefficient transfer". Never "equivalent". |
| Pooled analyses (S12–S13) | Descriptive. They must not override or substitute for the within-condition result. |
| ECE/Brier (S4) | Consistency with published voxel-level findings (MMA-LTS). No novelty claim. |

## 22. Limitations (pre-declared)

1. Missingness is **simulated by zeroing**. Real missing or degraded sequences are not studied.
2. The HOI set shares BraTS curation and preprocessing, so the institutional shift is likely mild. BraTS-Africa is small (≤ 95 cases, and fewer per condition component), which gives wide CIs.
3. The 250-epoch schedule is compute-limited. It is applied identically to both arms.
4. The 3-member ensemble comes from a single split, so the variance of ensemble-level results over retraining is not estimable. With 3 members, pairwise Dice takes coarse values.
5. Only pre-operative adult glioma is studied, with one architecture family.
6. There is no MC-dropout and no post-hoc calibration. Missingness-conditioned calibration is outside scope (see MMA-LTS).
7. Labels are expert-refined from automated pre-segmentations (BraTS, BraTS-Africa).
8. The volume-failure thresholds are RANO 2.0-motivated proxies, not validated segmentation-error criteria.
9. The threshold τ is fixed from the full validation set; its estimation variability is not propagated into the transfer CIs.
10. Within-condition AURC on the internal test set uses about 148 patients per condition. Per-condition external estimates will be imprecise.

## 23. Novelty statement (conservative; re-check before submission)

> To our knowledge, based on the search performed on 2026-09-27 (see `search_log.md`, rounds 1–3, and the unscreened sources listed in the pre-freeze checklist), prior work has established that segmentation accuracy and volumetry can be largely preserved under missing MRI sequences by per-subset or dropout-trained nnU-Nets [Ruffle et al. 2023; Öchsner et al. 2026; Pemberton et al. 2023; GlioMODA 2026]; that voxel-level calibration under missing-modality combinations is combination- and region-specific and can be improved by availability-conditioned post-hoc calibration [MMA-LTS, Lee et al., MICCAI 2026]; that region-wise calibration can be reported under missing modalities averaged over configurations [SimMLM/MoFe, Li et al. 2025]; that ensemble pairwise-Dice and related scores detect case-level segmentation failures with complete inputs [Zenk et al. 2025; BraTS-GoAT reliability study 2026]; and that pooled risk–coverage evaluation can reward between-group difficulty ordering rather than within-group detection [Joham et al., UNSURE 2026]. We did not identify a study that evaluates **case-level** reliability under missing MRI sequences, specifically whether uncertainty discriminates segmentation failures **within a fixed missing-sequence condition**, and whether that discrimination and the associated operating thresholds transfer to a held-out institution and an external population. This study is limited to that evaluation; it does not propose a new segmentation or calibration method.

## 24. Reproducibility plan

- **Every run records:**
  - an `EXP-xxx` ID
  - git commit and config hash
  - nnU-Net version and plans file
  - split file hashes and the crosswalk SHA-256
  - GPU, CUDA, PyTorch and Python versions
  - wall-clock time and peak memory
  - per-unit metric CSVs (patient, condition, region, metrics, U1/U2/U3 and I scores)
- Only IDs and metrics are committed. No images, predictions, checkpoints or licensed metadata files are committed.
- Kaggle notebooks clone a tagged commit.

## 25. Revision and amendment log

| Date | Version | Section(s) | Change | Reason | Test data seen? |
|---|---|---|---|---|---|
| 2026-09-27 | v0.1 | all | Initial draft | [12_PRE_PROTOCOL_AUDIT.md](12_PRE_PROTOCOL_AUDIT.md) | No |
| 2026-09-27 | v0.2 | §1 | Research question replaced with the within-condition, case-level, transfer formulation | The pooled question cannot isolate information beyond missingness identity (13 §8) | No |
| 2026-09-27 | v0.2 | §2–3, §13–14 | Two co-primaries (H-SEG, H-REL pooled; α = 0.025 each) replaced by a single primary H-W (mean within-condition ET ΔAURC; α = 0.05; 95% CI). Former S11 promoted. Families redefined; Holm within family only. | Joham et al. UNSURE 2026 (pooled vs within-group ranking); 13 §8 items 1, 3, 5–8 | No |
| 2026-09-27 | v0.2 | §2.3, §4 | H-SEG demoted to supporting/sanity (full-input TOST retained). Pooled U1 vs I demoted to descriptive S12, with I-then-U1 ranker and S13 mixture-weight sensitivity added. | H-SEG replicates [C6–C8]; pooled AURC depends on arbitrary weights | No |
| 2026-09-27 | v0.2 | §2.3, §4 S4 | H2 and ECE/Brier reframed as replication | MMA-LTS (MICCAI 2026) already evaluates voxel-level calibration per missing combination and region | No |
| 2026-09-27 | v0.2 | §5–7 | HOI = all **511** site-1 UPenn-origin cases (403 + 108); development = **740**; crosswalk file recorded, not committed | TCIA crosswalk; prevents same-institution leakage | No |
| 2026-09-27 | v0.2 | §5, §8 | BraTS-Africa = 95 glioma (v2 release); 51 OtherNeoplasms excluded; expected labels 1/2/3 pending file verification | TCIA v2 metadata; BraTS 2023 label documentation | No |
| 2026-09-27 | v0.2 | §4 S7, §21 | Threshold transfer redefined: Δrisk / Δcoverage with independent bootstraps; 80% primary, 70% and 90% sensitivity; unsafe/inefficient transfer rules | The v0.1 rule ignored validation sampling error and coverage drift (13 §8 item 11) | No |
| 2026-09-27 | v0.2 | §4 S5 | Volume failure renamed "RANO 2.0-motivated…"; 65% sensitivity added; 1 mL labelled a study choice | RANO 2.0 thresholds concern longitudinal change (13 §7 item 9) | No |
| 2026-09-27 | v0.2 | §4 | Removed mirroring-TTA, QU-BraTS score and lesion-wise Dice. C15 limited to internal test and arm B. | Not needed for the research question; compute | No |
| 2026-09-27 | v0.2 | §17, §20 | Compute re-estimated for the 511-case HOI; SR6–SR8 added | 13 §10 | No |
| 2026-09-27 | v0.2 | §23 | Novelty statement rewritten to acknowledge MMA-LTS, SimMLM/MoFe, Joham 2026, Zenk 2025, BraTS-GoAT and the accuracy/volumetry literature | 13 §9 | No |
| 2026-09-27 | v0.2 | checklist | Checklist replaced with the 7 open items from 13 §11 | Earlier items resolved or superseded (MoFe/PNDC correction, UPenn count, Africa count, RANO check) | No |

## Key references for revisions

- MMA-LTS: https://papers.miccai.org/miccai-2026/0659-Paper1236.html
- SimMLM / MoFe: https://arxiv.org/abs/2507.19264
- Joham et al., UNSURE 2026: https://papers.miccai.org/miccai-2026-sat/UNSURE2026_036.html
- Zenk et al. 2025: https://arxiv.org/abs/2406.03323
- BraTS-GoAT reliability study: https://arxiv.org/abs/2608.13223
- TCIA BraTS 2021 crosswalk page: https://www.cancerimagingarchive.net/analysis-result/rsna-asnr-miccai-brats-2021/
- TCIA BraTS-Africa: https://www.cancerimagingarchive.net/collection/brats-africa/
- RANO 2.0 operational summary (AJNR 2024): https://www.ajnr.org/content/45/12/1846
