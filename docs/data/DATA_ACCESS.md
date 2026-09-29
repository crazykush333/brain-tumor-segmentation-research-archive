# Data access

**Status: no study data have been acquired.** Acquisition is blocked until gate **B1** (approved data route) is closed. Nothing in this repository downloads data.

## Datasets (protocol §5)

| Role | Dataset | Access | Licence / terms |
|---|---|---|---|
| Development (site ≠ 1, 740 cases) and held-out institution (site 1, 511 cases) | BraTS 2021 training set (1,251 cases) | Synapse (syn25829067 / syn25829070), authenticated account; TCIA analysis result DOI 10.7937/jc8x-9874 | CC BY 4.0 for the challenge package and ID crosswalk (per TCIA page); Synapse Terms of Use; BraTS 2021 citation/acknowledgement requirements; TCIA Data Usage Policy |
| External population (≤ 95 cases) | TCIA BraTS-Africa, Version 1 (updated 2024-09-04), processed release | TCIA collection page; DOI 10.7937/v8h6-8x67 | CC BY 4.0 (processed release) |

Metadata used for cohort definition and grouping:

- `BraTS2021_MappingToTCIA.xlsx` (TCIA crosswalk): gives the site ID per case. SHA-256 recorded at B3.
- `UCSF-PDGM-metadata_v5.csv`: verifies the same-patient follow-up groups A and B. SHA-256 recorded at B4.
- `BraTS-Africa_TCIA_datainfo_v2.xlsx`: the "95 Glioma" and "51 OtherNeoplasms" sheets.

These files are **licensed metadata** and are never committed (they are blocked by `.gitignore` and by `check-repo`).

## Route (gate B1, pending)

- The protocol makes **no legal conclusion**. Private third-party re-hosting, including a private Kaggle dataset, **requires confirmation from TCIA before use** (§5.1).
- A **public** Kaggle mirror is never used or created. Unofficial mirrors are never a source of record.
- **SR7:** if the licence or provider confirmation does not permit the planned storage route, compute halts until the owner approves a compliant workflow.

## Rules for anyone handling the data

1. Store data **outside** the repository. Point the code at it with environment variables (`BRATS2021_DATA_ROOT`, `BRATS_AFRICA_DATA_ROOT`) or CLI arguments.
2. Never commit images, labels, predictions, probability maps, arrays, licensed metadata or credentials. Only IDs, hashes, counts and metrics are committed (§24).
3. No re-identification and no facial renderings (TCIA Data Usage Policy).
4. Cite the dataset DOIs and the required BraTS papers, and include the Synapse acknowledgement sentence.
5. Trained checkpoints are not published unless the providers confirm that this is acceptable.
