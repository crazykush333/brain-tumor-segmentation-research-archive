# FINAL RESEARCH PROTOCOL (pre-registration)

| Field | Value |
|---|---|
| Protocol version | **v0.1 — DRAFT, awaiting owner approval** |
| Date drafted | 2026-09-27 |
| Freeze rule | On owner approval, the version becomes v1.0 and is git-tagged `protocol-v1.0`. After that, changes are allowed only as logged amendments (§24). No change is allowed after any test-set evaluation. |
| Basis | [12_PRE_PROTOCOL_AUDIT.md](12_PRE_PROTOCOL_AUDIT.md), [search_log.md](search_log.md) |

No experiment has been run. This document contains no results. Numbers are design parameters, **[LITERATURE RESULT]**s or **[ESTIMATE]**s.

### Pre-freeze checklist

These items must be completed before v1.0.

- [ ] Read MoFe-loss (IEEE TMI 2025, doi 10.1109/tmi.2025.3526818) in full. Screen UNSURE 2025, BrainLes 2024/2025, MICCAI 2026, MIDL 2025/2026 and MELBA 2025/2026 titles. Update §23 if any of them overlaps.
- [ ] Confirm the BraTS 2021 ↔ source-institution mapping file identifies UPenn cases. Record the count; Öchsner et al. report 403.
- [ ] Confirm the number of BraTS-Africa **glioma** cases with public labels. Sources conflict: 60, 75 or 95.
- [ ] Verify the RANO 2.0 volumetric progression threshold used in §4 (S5).
- [ ] Measure pilot cost (EXP-001) and confirm the budget in §17.
- [ ] Owner decides the code licence and approves this protocol.

---

## 1. Research question

When MRI sequences are missing at inference, does the ensemble uncertainty of a modality-dropout nnU-Net identify unreliable **enhancing-tumour (ET)** segmentations:

- (a) better than a rule based only on *which* sequence is missing;
- (b) consistently across missing-sequence conditions and tumour regions;
- (c) with operating thresholds that transfer from internal data to held-out-institution and external cohorts?

## 2. Hypotheses

**Primary hypotheses** (two co-primary, α = 0.025 each, two-sided):

- **H-SEG.** On the internal test set, pooled over the five primary conditions C5 (§10), the per-patient mean ET Dice of the **B ensemble** (modality-dropout) differs from that of the **A ensemble** (full-modality training). Expected direction: B > A.
  - This is a *replication* of established findings [C6, C7]. It is included because the reliability analysis is only meaningful for a model that is actually usable under missingness.
- **H-REL.** On the internal test set, for the B ensemble, pooled over C5, the ET AURC of the **ensemble pairwise-Dice confidence (U1)** differs from the ET AURC of the **missingness-indicator baseline (I)**. Expected direction: AURC(U1) < AURC(I).

**Secondary hypotheses** (Holm-corrected within family, §14):

- **H2.** For the B ensemble, ET e-AURC is higher (worse) when T1c is missing than with full input. This is the missing-sequence-specific degradation.
- **H3.** The H-REL difference has the same sign on the held-out-institution (UPenn) and external (BraTS-Africa) sets. A confidence threshold fixed on validation data yields selective ET risk on those sets that does not exceed the validation selective risk (threshold transfer, S7).
- **H4.** For the A ensemble, confidence (U1) under missing inputs is poorly aligned with failure. This is the "silent failure of a non-robust model" test.

## 3. Primary endpoints and justification

| Endpoint | Definition | Why this and not another |
|---|---|---|
| **Primary segmentation: ET Dice** | Region ET = label 4 (BraTS 2021) or 3 (newer conventions). Dice per (patient, condition). Both empty → 1; exactly one empty → 0. Per-patient mean over C5, B ensemble vs A ensemble. | ET is the region that depends most on a single sequence (T1c). It drives clinical response assessment and is the least robust region [H1, H2, C9]. |
| **Primary reliability: ET AURC** | Units = (patient, condition) pairs, pooled over C5. Risk = 1 − ET Dice. Confidence = U1 or I. AURC is computed with expected tie handling (average over random tie-breaking). | The two rankers score **the same predictions**, so ΔAURC = Δe-AURC. The optimal AURC cancels. AURC is the established case-level failure-detection metric [D2]. |

## 4. Secondary endpoints

- **S1.** ET e-AURC (U1) per condition in C5, and each condition's difference vs Full (tests H2).
- **S2.** TC and WT AURC: U1 vs I.
- **S3.** WT and TC Dice; HD95 per region. HD95 uses the BraTS convention when one mask is empty (value to be confirmed from BraTS evaluation code before freeze).
- **S4.** ECE and Brier score per region per condition:
  - computed on the ensemble-mean sigmoid probability;
  - over the ROI = union of GT and predicted region, dilated by 3 voxels;
  - 15 equal-width bins, voxels pooled per case and then averaged over cases.
- **S5.** Volume:
  - absolute ET volume error in mL;
  - clinically relevant ET failure = relative ET volume error ≥ 40% for cases with GT ET ≥ 1 mL (threshold tied to RANO 2.0 volumetric progression; **verify before freeze**);
  - AURC with this binary failure as risk.
- **S6.** Spearman ρ between U1 and ET Dice, per condition.
- **S7.** Threshold transfer:
  - τ is chosen on the **validation** set to give 80% coverage in the pooled C5 units;
  - τ is applied unchanged to the internal test, UPenn and BraTS-Africa sets;
  - report realized coverage and selective ET risk, each with bootstrap 95% CIs.
- **S8.** All primary and secondary endpoints repeated on UPenn and BraTS-Africa (tests H3).
- **S9.** A-ensemble reliability endpoints S1, S4 and S6 (tests H4).
- **S10.** Fifteen-subset analysis for the B ensemble on validation, internal test and BraTS-Africa: ET Dice, ET e-AURC and ECE per subset.
- **S11.** Within-condition discrimination: ET AURC(U1) vs the expected AURC of random ranking, per condition. Does uncertainty rank cases *within* a fixed missingness condition?

**Exploratory** (reported as such, no multiplicity control):

- QU-BraTS score
- lesion-wise Dice
- mirroring-TTA uncertainty
- per-seed single-model reliability (U3)
- 40% vs 25% volume thresholds

## 5. Datasets

| Role | Dataset | Inclusion | n |
|---|---|---|---|
| Development (train / val / internal test) | BraTS 2021 training set (Synapse / TCIA restricted licence) | All cases **not** originating from UPenn, per the BraTS 2021 mapping file | **ESTIMATE 848** (per Öchsner et al.) |
| Held-out institution (HOI) | UPenn-origin cases **within** BraTS 2021 | All with 4 sequences and labels | **ESTIMATE 403** |
| External | BraTS-Africa (TCIA, CC BY 4.0), processed release | Adult glioma cases with public labels. The 51 non-glioma cases are excluded. | **60–95, to verify** |

Design rationale:

- The HOI set uses BraTS preprocessing and BraTS label conventions, so its shift is **institutional only**. The literature suggests it is a mild shift (external Dice ~95% in [C7], [LITERATURE RESULT]).
- BraTS-Africa is a genuine population and acquisition shift (1.5T, Nigeria). It uses a BraTS-style preprocessing protocol, and its labels were refined from nnU-Net pre-segmentations with a three-stage expert review.
- UCSF-PDGM, EGD and standalone UPenn-GBM (TCIA) are **not** used, to keep the study focused and avoid preprocessing mismatch. They are possible future work.

## 6. Patient-level splits

- The development set is split **70/10/20** into train, val and internal test (ESTIMATE ≈ 594 / 85 / 169).
- Stratification uses ET-present vs ET-absent and WT-volume tertile. Both are computed from labels only and involve no model output.
- The random seed is `20260927`.
- The split is performed **once**, before any training. ID lists are committed to `splits/` (IDs only). A hash of the split files is recorded in this protocol at freeze.
- One BraTS subject is treated as one patient. Any detected duplicate subject IDs are grouped into the same split.

## 7. Deduplication

- **Development vs HOI:** disjoint by construction (mapping file).
- **BraTS-Africa vs BraTS 2021:** different source institutions. Check for identical image hashes as a safeguard.
- The deduplication script output (IDs and counts) is committed. The counts are reported in the paper.

## 8. Preprocessing

- Use the **BraTS-provided preprocessed** images: co-registered to SRI24, 1 mm isotropic, skull-stripped. No re-registration.
- **nnU-Net v2**, version pinned at M1.
  - The raw dataset folder contains **train + val only**, so the fingerprint and plans never see test data.
  - Default 3d_fullres plan with nnU-Net's z-score normalization per channel within the non-zero mask.
- Channel order is fixed as `[T1, T1c, T2, FLAIR]` and asserted by unit test.
- Label conversion to regions:
  - BraTS 2021: ET = {4}, TC = {1, 4}, WT = {1, 2, 4}.
  - BraTS-Africa: mapped after reading its label values (expected ET = {3}); the mapping is unit-tested.

## 9. Models (baselines)

Arms A and B are identical except for the dropout policy.

| | Arm A | Arm B |
|---|---|---|
| Framework | nnU-Net v2 3d_fullres, **region-based** (sigmoid WT/TC/ET) | same |
| Schedule | 250 epochs (`nnUNetTrainer_250epochs` semantics); `save_every` = 5 | same |
| Training data | train split | same |
| Missing-sequence dropout | none | §10 policy |
| Seeds | 0, 1, 2 | 0, 1, 2 |
| Checkpoint | `checkpoint_final` (pre-specified; no selection on val) | same |
| Inference | sliding window, default step 0.5, **mirroring off**, threshold 0.5 | same |
| Ensemble | mean of the 3 members' sigmoid probabilities | same |

No new architecture, no MC-dropout and no attention module is used.

## 10. Missingness simulation

- A missing sequence is represented by setting its **normalized** channel to 0. That equals the brain-masked mean and the background value, so the channel carries no information.
- The same operation is used in training (arm B) and at inference.
- **C5 (primary conditions):** {Full, −T1, −T1c, −T2, −FLAIR}. These are single-sequence absences, the most plausible clinical scenario; the real-world frequency is unknown.
- **C15 (secondary):** all 15 non-empty subsets.
- **Arm B training policy:** per training sample, with probability 0.5 the input is full. Otherwise one of the 14 non-full, non-empty subsets is chosen uniformly and applied after augmentation. The policy is fixed a priori and **not tuned**.
- **Limitation:** zeroing is not the same as a real missing or degraded acquisition. This is acknowledged in §22.

## 11. Uncertainty methods

Case-level confidence per region r:

- **U1 (primary):** mean pairwise Dice between the three members' binary masks for r. Both empty → 1.
- **U2:** negative mean binary entropy of the ensemble-mean probability within the ROI (the union of member masks for r, dilated by 3 voxels). If the ROI is empty, entropy is defined as 0, i.e. maximal confidence.
- **U3 (exploratory):** single-model (seed 0) mean max-probability within the ROI.
- **I (baseline):** missingness indicator. Confidence = −(mean risk for r of that condition, estimated on the **validation** set for the same arm's ensemble).
- **TTA:** exploratory only.
- **Temperature scaling:** not in the primary analysis (sigmoid outputs are evaluated as produced). This is noted as a limitation.

## 12. Failure-detection methods and evaluation

- Rankers are U1 (primary), U2, U3 and I.
- Risk–coverage curves are computed over pooled units.
- AURC uses expected tie handling. e-AURC = AURC − optimal AURC.
- Binary-failure AUROC is an exploratory metric.
- Failure definitions: 1 − Dice (continuous, primary) and the S5 volume failure (binary, secondary).

## 13. Statistical tests

- **Unit of resampling:** patient. All conditions of a patient are resampled together.
- **H-REL:**
  - ΔAURC = AURC(U1) − AURC(I).
  - Paired patient bootstrap, 10,000 resamples, percentile **97.5%** CI.
  - Reject H0 if the CI excludes 0.
- **H-SEG:**
  - per-patient Δ = mean over C5 of Dice_B − Dice_A (ET);
  - two-sided Wilcoxon signed-rank at α = 0.025;
  - Hodges–Lehmann estimate and bootstrap 97.5% CI reported.
- **Full-condition non-inferiority** (key secondary): TOST for B vs A, ET Dice, margin ±1.5 Dice points, following [C7]'s pre-specified margin.
- **Secondary families:** bootstrap CIs; p-values from bootstrap or Wilcoxon, as appropriate to the endpoint.
- **Seed variation:** single-member metrics are reported as mean ± SD over 3 seeds, descriptive only.
- No t-tests. No pooling of the internal, HOI and external sets.

## 14. Multiplicity correction

- **Co-primary:** Bonferroni, α = 0.025 each.
- **Secondary families**, each Holm-corrected at α = 0.05:
  - F1 = {S1 per-condition vs Full, 4 tests}
  - F2 = {S2: TC, WT}
  - F3 = {H3: UPenn ΔAURC, Africa ΔAURC}
  - F4 = {S7 transfer: internal, UPenn, Africa}
  - F5 = {H4}
- Everything else is descriptive or exploratory. It is reported with CIs and no significance claims.

## 15. Confidence intervals

- Patient bootstrap, 10,000 resamples, percentile method (BCa as a sensitivity analysis).
- Primary endpoints use 97.5% CIs; all others use 95%.
- The bootstrap seed is fixed (`12345`) and recorded.

## 16. Seeds

| Seed | Value |
|---|---|
| Training | 0, 1, 2 (both arms) |
| Split | 20260927 |
| Bootstrap | 12345 |
| Figure case sampling | 7 |

nnU-Net/cuDNN non-determinism is acknowledged. Exact bitwise reproducibility is not claimed.

## 17. Compute budget (ESTIMATE until EXP-001)

- **Cap:** 220 GPU-h (Kaggle free tier, about 4–8 weeks).
- **Allocation:**
  - pilot: ≤ 10 GPU-h
  - training: ≤ 150 GPU-h (6 runs × ≤ 25 h)
  - primary inference: ≤ 50 GPU-h
  - C15 inference: ≤ 23 GPU-h
  - TTA: only from any remainder
- Softmax maps are not stored except for ≤ 20 pre-selected figure cases. Metrics are computed on the fly.
- See [12 §Phase 5](12_PRE_PROTOCOL_AUDIT.md).

## 18. External validation

- The HOI and BraTS-Africa sets are used **only** for final evaluation.
- No training, tuning, threshold selection, indicator-risk estimation, calibration or checkpoint choice uses them.
- Each is evaluated once with the frozen code tagged `eval-v1`.

## 19. Failure analysis

A rule-based, automated categorization of units (in [05 §6](05_EXPERIMENTAL_DESIGN.md)), plus:

- **Confident failure:** U1 above the validation 80th percentile and ET Dice < 0.5.
- **Hallucinated ET:** GT ET empty but predicted ET present, broken down by condition, especially −T1c.
- **Missed ET:** the reverse case.

Counts are reported per condition and dataset. Figure cases are drawn by rule with seed 7 (worst-k per category), not hand-picked.

## 20. Stopping rules

- **SR1 (cost).**
  - If pilot-measured time exceeds 25 GPU-h per run, switch **all 6 runs** to a 150-epoch schedule before any evaluation.
  - If that is still infeasible, stop and consult the owner.
- **SR2 (sanity, validation set only).** If arm A's full-input mean ET Dice on **validation** is < 0.75, stop and debug before any test evaluation. The threshold is set a priori as clearly below typical nnU-Net BraTS 2021 performance; it is not a target.
- **SR3 (data).**
  - If UPenn cases cannot be identified: drop the HOI set, use all 1,251 cases for development, and log the deviation.
  - If BraTS-Africa has fewer than 30 labelled glioma cases: its analyses become descriptive only.
- **SR4 (integrity).** Test sets are evaluated once with tagged code. Any re-evaluation is logged as a deviation, and **both** results are reported.
- **SR5 (bugs).** If a bug is found after evaluation: fix it, re-run everything affected, and report the deviation and both results.

## 21. Interpretation rules

| Outcome | Interpretation |
|---|---|
| H-REL CI entirely < 0 | Ensemble uncertainty adds failure-ranking information beyond knowing the missing sequence (internal data). |
| H-REL CI includes 0 | No evidence that uncertainty beats the indicator. This is **not** evidence of equivalence. Report as such. |
| H-REL CI entirely > 0 | The indicator rule ranks failures better than uncertainty. This is an important negative finding for uncertainty-based QC under missingness. |
| H3 sign differs externally | Reliability conclusions do not transfer. This is reported as a primary limitation of uncertainty-based QC. |
| Threshold transfer | Coverage or risk is "not transferred" if the realized selective risk on a target set exceeds the validation selective risk and the 95% CI excludes the validation value. |

Wording on small external sets uses CIs and avoids "significant" unless the test is in a pre-specified family.

## 22. Limitations (pre-declared)

1. Missingness is **simulated by zeroing**. Real missing, degraded or partially covered sequences are not studied.
2. The HOI set comes from the same BraTS curation pipeline, so the institutional shift is likely mild. BraTS-Africa is small, which gives wide CIs.
3. The 250-epoch schedule (compute-limited) is not the nnU-Net default. It is applied identically to both arms.
4. Only a 3-member ensemble from a single split is used. The variance of ensemble-level results over retraining is not estimable.
5. Only pre-operative adult glioma is studied, with a single architecture family. Generalization to other models is untested.
6. There is no MC-dropout and no post-hoc calibration in the primary analysis.
7. Label quality: BraTS and BraTS-Africa labels are expert-refined from automated pre-segmentations.
8. The volume-failure threshold is a proxy for clinical impact and has not been validated clinically.

## 23. Novelty statement (cautious; to be re-checked before submission)

> To our knowledge, based on a structured search performed on 2026-09-27 (see `search_log.md`, including its stated gaps), prior studies have evaluated segmentation *accuracy* and *volumetry* under missing MRI sequences [C6, C7, C8, H4], and have evaluated case-level failure detection and region-specific calibration of nnU-Net ensembles under *complete* inputs [D2, H1, H2]. We did not identify a study that evaluates whether a segmentation model's own uncertainty identifies failures **conditional on the identity of the missing sequence**, compares it against the trivially available missingness-indicator rule, and tests transfer of reliability thresholds to held-out-institution and external cohorts. This study addresses that specific question; it does not propose a new segmentation architecture.

"First", "novel method" and "state-of-the-art" will not be used.

## 24. Reproducibility plan and amendments

- **Every run records:**
  - an `EXP-xxx` ID
  - the git commit and config hash
  - the nnU-Net version and plans file
  - split file hashes
  - GPU, CUDA, PyTorch and Python versions
  - wall-clock time and peak memory
  - per-unit metric CSVs (patient, condition, region, metrics, confidences)
- Only IDs and metrics are committed. No images, predictions or checkpoints are committed.
- Kaggle notebooks clone a tagged commit.
- **Amendment log:** date, section, change, reason, and whether any test data had been seen. The log is empty at v0.1.

| Date | Section | Change | Reason | Test data seen? |
|---|---|---|---|---|
| — | — | — | — | — |
