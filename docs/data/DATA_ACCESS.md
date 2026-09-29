# Data access

**Status (2026-09-29): gate B1 is PENDING. No study data have been acquired.** Acquisition is blocked until B1 (approved data route) is closed; see [B1_DATA_ROUTE_AUTHORIZATION.md](B1_DATA_ROUTE_AUTHORIZATION.md). Nothing in this repository downloads data.

Labels used below:

- **VERIFIED FACT** — read on an official source on the stated date.
- **PLANNED WORKFLOW** — what this project intends to do; not yet done.
- **PENDING PROVIDER CONFIRMATION** — must not be assumed until TCIA confirms in writing.

## 1. Datasets (protocol §5)

| Role | Dataset | Planned size (protocol design parameters) |
|---|---|---|
| Development (site ≠ 1) and held-out institution (site 1) | RSNA-ASNR-MICCAI-BraTS-2021, training cases | 1,251 total, 511 site 1, 740 development. **Verification targets for gate B6**, not yet re-derived from the hashed crosswalk |
| External population | TCIA BraTS-Africa (processed release), DOI 10.7937/v8h6-8x67 | ≤ 95 glioma cases (gates C1–C3) |

## 2. Official-source verification (performed 2026-09-29)

All sources are official TCIA pages, read in a browser on **2026-09-29**. The statements are short summaries, not legal interpretation.

| Source | URL | VERIFIED FACT (2026-09-29) |
|---|---|---|
| TCIA BraTS 2021 analysis result | https://www.cancerimagingarchive.net/analysis-result/rsna-asnr-miccai-brats-2021/ | DOI 10.7937/jc8x-9874. "Data Citation Required". Version 1, updated 2023/08/25. The page lists 1,480 subjects and 142 GB. The "Challenge data both tasks" package (DICOM and NIfTI) is licensed **CC BY 4.0**, and its download lists the **IBM Aspera Connect** plugin as a requirement. The "ID Crosswalk map between BraTS ID and TCIA ID" (XLSX, 78.12 KB) is **CC BY 4.0**. Some linked *original* source DICOM falls under the NIH Controlled Data Access Policy; it is not needed. The page acknowledges Synapse ID syn25829067. It carries an April 2026 note that source-data manifest updates do not affect the Challenge downloads. |
| TCIA Data Usage Policies and Restrictions | https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/ | Users must not identify or contact participants, nor generate representations such as facial images that could identify them. Users must acknowledge the datasets (DOI data citation) in every presentation and publication. Anyone considering **mirroring** TCIA's public datasets, or **providing direct access via another tool or website**, is directed to the Data Analysis Centers (DACs) page. DACs must attribute each dataset, link to the policy and require downstream users to do the same. Each dataset's licence is shown in its Data Access table. Since April 2025, datasets requiring data use agreements are hosted by the NCI CRDC, with access via dbGaP. |
| TCIA Data Analysis Center (DAC) | https://www.cancerimagingarchive.net/tcia-data-analysis-center/ (the legacy wiki page https://wiki.cancerimagingarchive.net/pages/viewpage.action?pageId=22515655 redirects here; wiki page last modified 2026-06-02) | A DAC is a tool or website that offers downloading, visualization or analysis of TCIA data through the TCIA REST API **or by mirroring collections**. Developers of such resources are asked to contact the helpdesk to be listed and to ensure attribution. Kaggle does not appear in the DAC listing reviewed (legacy wiki list). Not being listed is neither a permission nor a prohibition. |
| TCIA Support | https://www.cancerimagingarchive.net/support/ | Helpdesk email **help@cancerimagingarchive.net**, phone +1 385-275-8242. Requests should include contact information, the relevant page URL and a description. |
| UCSF-PDGM collection (source of the gate-B4 metadata file) | https://www.cancerimagingarchive.net/collection/ucsf-pdgm/ | The page links `UCSF-PDGM-metadata_v5.csv` at https://www.cancerimagingarchive.net/wp-content/uploads/UCSF-PDGM-metadata_v5.csv. |

Carried over from protocol §5.1 (verified 2026-09-27/28; **not re-verified in this pass**): Synapse access (syn25829067 / syn25829070) requires an authenticated account and is subject to the Synapse Terms of Use and the BraTS 2021 citation/acknowledgement requirements. Kaggle's own terms of service were **not** reviewed as part of this verification.

## 3. What is and is not established

| Statement | Status |
|---|---|
| The challenge package and crosswalk are CC BY 4.0, and a DOI citation is required | VERIFIED FACT |
| TCIA's policies direct mirroring and third-party direct access to the DAC process | VERIFIED FACT |
| A **private**, single-user copy on Kaggle is permitted, or is not "mirroring" | **PENDING PROVIDER CONFIRMATION** (not addressed explicitly by the policies) |
| Runtime-only download into Kaggle/Colab without persistence is permitted and technically supported | **PENDING PROVIDER CONFIRMATION** |
| Use Route A or Route B (see B1 record) | PLANNED WORKFLOW; neither approved |
| A public mirror | **Never** (protocol §5.1) |

**Nothing in this repository states or implies that Kaggle storage is permitted.**

## 4. Planned workflow after B1 closes (PLANNED WORKFLOW)

1. **B2:** acquire the official files via the approved route only, into `data/raw/` locally or the approved compute storage. Then run `brats-uncertainty record-acquisition` to hash the acquired files and record source, version, DOI, URL, route, date and code commit.
2. **B3:** `brats-uncertainty hash-metadata --gate B3 --file .../BraTS2021_MappingToTCIA.xlsx ...`
3. **B4:** `brats-uncertainty hash-metadata --gate B4 --file .../UCSF-PDGM-metadata_v5.csv ...`
4. **B5:** `brats-uncertainty validate-data ...`, then `brats-uncertainty build-manifest ...`
5. **B6:** `brats-uncertainty derive-counts --crosswalk ... --b3-record ...`. This re-hashes the crosswalk, checks the hash against B3, and derives the counts. A mismatch is recorded as FAILED_SR3 and stops.

Each command fails until the preceding gate is CLOSED. Full reproduction steps: [DATA_PROVENANCE.md](DATA_PROVENANCE.md).

## 5. Rules for anyone handling the data

1. Keep data outside git: under the git-ignored `data/` tree ([data/README.md](../../data/README.md)) or in the approved compute storage. Point the code at it with `BRATS2021_DATA_ROOT` or CLI arguments.
2. Never commit or upload images, labels, predictions, arrays, archives, licensed metadata files, credentials (`kaggle.json`, `.env`, Synapse config) or checkpoints. Never put a credential in a `NEXT_PUBLIC_*` variable.
3. No re-identification and no facial renderings (TCIA Data Usage Policies).
4. Cite the dataset DOIs and the required BraTS papers; include the Synapse acknowledgement.
5. Trained checkpoints are not published unless the providers confirm that is acceptable (protocol §5.1).
