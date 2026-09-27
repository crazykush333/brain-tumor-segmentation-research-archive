# Structured Search Log

**Search date:** 2026-09-27
**Performed by:** Claude (AI assistant), for the project owner
**Purpose:** pre-protocol novelty audit for the candidate direction "reliability of glioma segmentation under incomplete MRI acquisition".

## Tools and their limitations

- **Web search engine** (general web index, US region), with results inspected manually.
- **Direct fetch** of arXiv abstracts and HTML full texts, MICCAI open-access pages, Frontiers, Oxford Academic, TCIA collection pages and CBICA pages.
- **Google Scholar could not be queried directly.** Scholar-indexed items were reached only through the general web index.
- **PubMed/PMC:** PMC pages returned a bot-check page and could not be read. PubMed records were found through search results.
- **Nature (Scientific Reports) and IEEE Xplore** full texts could not be fetched (login redirect or empty page).
- **Hit counts are not reported.** The general web index does not give reliable counts, so this is a documented, reproducible query list rather than a database-exact systematic search.

## Queries run

Each query was run as a web search; the relevant new records it returned are listed.

| # | Query | Relevant new records |
|---|---|---|
| 1 | "missing modality" brain tumor segmentation calibration expected calibration error | 2606.19300 (MIUA 2026), 2506.03942, MoFe-loss TMI 2025 (not retrievable), RATF-Net (Zenodo, not peer-reviewed) |
| 2 | "missing modality" segmentation failure detection risk-coverage AURC | 2603.02200 (CVPR 2026, multimodal FD, not segmentation), 2608.07183 (conformal, classification), ValUES 2401.08501 |
| 3 | missing MRI sequence glioma segmentation uncertainty quality control reliability evaluation | Pemberton 2023; UAF-AIMM |
| 4 | missing T1ce contrast-free brain tumor segmentation uncertainty calibration | UAF-AIMM; SIUM 2606.30374; 2408.13733 |
| 5 | BraTS missing modality predictive uncertainty confidence Dice correlation incomplete sequences | BMDS-Net 2601.17504; Sci Rep 2026 expert routing; pediatric npj 2026 |
| 6 | selective segmentation missing modality deferral multimodal MRI trustworthy | No Modality Left Behind (MedIA 2026) |
| 7 | UNSURE workshop MICCAI 2025 missing modality uncertainty segmentation brain | UNSURE 2025 proceedings (22 papers; titles not individually screened, see Gaps below); MICCAI 2025 missing-modality papers (MST-KDNet, IM-Fuse, DC-Seg) |
| 8 | "missing modalities" "uncertainty" "brain tumor" MICCAI 2025 calibration reliability | as above |
| 9 | AI-powered segmentation and prognosis with missing MRI in pediatric brain tumors | npj Precision Oncology 2026 |
| 10 | evidential deep learning missing modality brain tumor segmentation uncertainty | 2607.22727 (synthetic phantom); region-based EDL 2208.06038 |
| 11 | segmentation quality control missing MRI sequences volume error glioma RANO | GlioMODA (NOA 2026) |
| 12 | "missing sequences" OR "incomplete MRI" uncertainty glioma segmentation external cohort ensemble 2026 | GMENet 2605.23183 (diagnosis, not segmentation) |
| 13 | MICCAI 2026 missing modality brain tumor segmentation uncertainty calibration reliability | JBHI 2025 multi-expert; no new reliability study |
| 14 | "modality dropout" nnU-Net uncertainty ensemble calibration missing sequence glioma external validation BraTS-Africa | **BraTS-GoAT reliability 2608.13223**; Öchsner Frontiers 2026 version; De Sutter IJCARS 2024; Zhao MICCAI 2022 |
| 15 | brain tumor segmentation "missing" modality "overconfident" OR "silent failure" uncertainty incomplete MRI | nothing new |
| 16 | Named-work searches: Set-Inclusive Uncertainty Modeling, UAF-AIMM, QCResUNet, QU-BraTS, Zenk failure detection, Guarino aggregation | full texts read (see [12_PRE_PROTOCOL_AUDIT.md](12_PRE_PROTOCOL_AUDIT.md)) |

The following query strings from the owner's list were covered by queries 1–15 above (the web index does not honour Boolean operators exactly):

- "missing sequence" AND glioma AND failure detection
- "missing modality" AND segmentation AND selective prediction
- "missing modality" AND segmentation AND quality control
- "missing T1ce" AND failure detection
- "BraTS" AND failure detection AND missing modality
- "brain tumor segmentation" AND confidence AND missing modality

## Known gaps in the search (must be closed before submission)

1. The UNSURE 2025 proceedings (22 papers) and the BrainLes 2024/2025 proceedings were **not screened title-by-title**.
2. MICCAI 2026 proceedings were not screened. The conference is held around this date, so the proceedings may not be fully indexed yet.
3. MIDL 2025/2026 and MELBA 2025/2026 were not screened title-by-title.
4. MoFe-loss (IEEE TMI 2025, doi 10.1109/tmi.2025.3526818) could not be read. Its snippet mentions calibration (ECE/SCE) together with missing modalities, so it **must be read before any novelty claim**.
5. The Pemberton et al. 2023 full text could not be retrieved. Its entry relies on the abstract and secondary summaries.
6. The QCResUNet Appendix E numbers (QC performance with missing modalities) could not be retrieved.
