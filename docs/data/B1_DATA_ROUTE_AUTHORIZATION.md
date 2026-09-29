# Gate B1: data-route authorization record

| Field | Value |
|---|---|
| **Status** | **PENDING** |
| Protocol version | v1.0 (frozen 2026-09-28; tag `protocol-v1.0`) |
| Protocol basis | §5.1 (licence, access and data route), SR7, lifecycle gates B1 and D2 |
| Dataset | RSNA-ASNR-MICCAI-BraTS-2021 (TCIA analysis result) |
| Dataset DOI | 10.7937/jc8x-9874 |
| Record created | 2026-09-29 |
| Inquiry | [TCIA_DATA_ROUTE_INQUIRY.md](TCIA_DATA_ROUTE_INQUIRY.md): prepared, **not sent** |
| Written provider confirmation | **none received** |
| Owner-approved alternative | **none recorded** |

**No study imaging data have been acquired under this route yet.**

**Provider confirmation is required before third-party re-hosting/mirroring.**

## 1. Intended research use

Academic research in brain-tumor segmentation and case-level uncertainty under missing MRI modalities, as pre-registered in protocol v1.0. The data are used only to:

- train and evaluate nnU-Net models;
- compute IDs, hashes, counts and metrics.

Images, labels and licensed metadata files are never redistributed. Only IDs, hashes, counts and aggregate metrics are published.

## 2. Proposed routes (neither is approved)

| Route | Description | What must be confirmed |
|---|---|---|
| **A** | Private, access-restricted computational storage of the official BraTS 2021 files on a third-party platform (e.g. a **private** Kaggle dataset visible only to the project owner) | Whether TCIA permits it, and whether TCIA considers it "mirroring/re-hosting" under the Data Usage Policies (which point mirroring to the Data Analysis Center process). Any conditions (attribution, access restriction, deletion). |
| **B** | Runtime-only acquisition: each compute session downloads the official files from the official source into the session's temporary storage. Nothing persists after the session, and no third-party dataset copy is created. | Whether TCIA permits downloading into third-party compute (Kaggle/Colab) without persistent storage, and the recommended programmatic retrieval method. The TCIA download for the challenge package lists the IBM Aspera Connect plugin as a requirement. |

A **public** mirror is never used or created (protocol §5.1).

## 3. Verified policy context (official sources, verified 2026-09-29)

These are summaries, not legal conclusions. Sources and details are in [DATA_ACCESS.md](DATA_ACCESS.md) §2.

- The BraTS 2021 challenge-data package and the ID crosswalk are listed as **CC BY 4.0**, and data citation (DOI) is required.
- The TCIA Data Usage Policies ask anyone considering **mirroring** TCIA's public datasets, or **providing direct access** to them via another tool or website, to review the **Data Analysis Centers (DACs)** page. DACs must attribute each dataset, link to the usage policy, and require the same of downstream users.
- The policies do **not** explicitly address a *private*, single-user copy in third-party compute storage. That is why provider confirmation is sought. **This record makes no legal conclusion and does not assume private Kaggle storage is permitted.** Public downloadability of the data does not imply permission to re-host it.

## 4. How B1 may be closed (either path; both require a written record)

1. **Provider confirmation.** TCIA replies in writing about the chosen route. Record the reply as `docs/data/B1_EVIDENCE_<YYYY-MM-DD>.md`, containing:
   - the date received;
   - the TCIA ticket or reference number, if any;
   - the exact relevant sentences of the reply, with personal contact details redacted;
   - the route it covers;
   - any conditions stated.
2. **Owner-approved alternative** (protocol §5.1: "or an owner-approved alternative"). The owner signs a dated decision record naming the exact route, the rationale and the residual uncertainty, and stating that the route does not create a public or private persistent third-party copy unless TCIA has confirmed that is acceptable.

Then, in the same commit:

- set gate B1 to `CLOSED` in `docs/project_status.yaml`, with the evidence file and date;
- set `data.authorization: APPROVED` and `data.approved_route: "<route>"` (the status validator rejects APPROVED without B1 CLOSED, and vice versa);
- add an administrative entry under `docs/research/protocol-amendments/`;
- regenerate website data: `brats-uncertainty export-site-data`.

**If TCIA declines both routes**, SR7 applies: compute stays halted until the owner approves a compliant workflow.

## 5. Consequences while B1 is pending

- No data acquisition (B2), hashing (B3–B4), manifest (B5) or counts (B6).
- EXP-001 is blocked (D2 = B1).
- The gated commands `record-acquisition`, `hash-metadata`, `validate-data`, `build-manifest` and `derive-counts` all fail with `ResearchGateError`.

## 6. Change log of this record

| Date | Change |
|---|---|
| 2026-09-29 | Record created; status PENDING; inquiry prepared, not sent. |
