# Gate B1: data-route authorization record

| Field | Value |
|---|---|
| **Status** | **PENDING** |
| Protocol version | v1.0 (frozen 2026-09-28; tag `protocol-v1.0`) |
| Protocol basis | §5.1 (licence, access and data route), SR7, lifecycle gates B1 and D2 |
| Dataset | RSNA-ASNR-MICCAI-BraTS-2021 (TCIA analysis result) |
| Dataset DOI | 10.7937/jc8x-9874 |
| Record created | 2026-09-29 |
| Inquiry | [TCIA_DATA_ROUTE_INQUIRY.md](TCIA_DATA_ROUTE_INQUIRY.md): final, ready to send manually, **not sent** |
| Evidence template | [B1_EVIDENCE_TEMPLATE.md](B1_EVIDENCE_TEMPLATE.md): template only, STATUS = PENDING |
| External written authorization | **none received** |
| B1 evidence file (`docs/data/B1_EVIDENCE_<date>.md`) | **none exists** |

**No study imaging data have been acquired under any route.**

**Provider confirmation is required before any third-party storage, re-hosting or mirroring.**

**Preparing or sending the inquiry does not complete B1.**

## 1. Intended research use

This is academic research in brain-tumour segmentation and case-level uncertainty under missing MRI sequences, as pre-registered in protocol v1.0. The data are used only to:

- train and evaluate nnU-Net models;
- compute IDs, hashes, counts and metrics.

Images, labels and licensed metadata files are never redistributed. Only IDs, hashes, counts and aggregate metrics are published.

## 2. Proposed routes (none is approved)

The inquiry separates three kinds of use:

- **Private computational storage:** an access-restricted, single-user copy on a compute platform, never shared.
- **Public redistribution:** making the files available to anyone else. This is **never done**; see protocol §5.1.
- **Runtime-only access:** download into temporary session storage, with no persistent third-party copy.

| Category | Route | What must be confirmed in writing |
|---|---|---|
| **A** | Private, access-restricted computational storage of the official BraTS 2021 files on a third-party platform, such as a **private** Kaggle dataset visible only to the project owner. | Whether TCIA permits it, and whether TCIA considers it "mirroring", "re-hosting" or another Data Analysis Center-type activity. Any conditions (attribution, access restriction, deletion). |
| **B** | Runtime-only acquisition. Each compute session downloads the official files from the official source into its temporary storage. Nothing persists after the session, and no third-party dataset copy is created. | Whether TCIA permits downloading into third-party compute such as Kaggle or Colab without persistent storage, and the supported retrieval method. The TCIA download for the challenge package lists the IBM Aspera Connect plugin as a requirement. |
| **C** | Another route that TCIA approves in writing, for example one TCIA recommends in reply to inquiry question 5. | The route itself and its conditions, as stated by TCIA. |

## 3. Official sources (verified 2026-09-29; re-verified 2026-09-30)

Only official TCIA pages were used, read in a browser on both dates. Content was unchanged on 2026-09-30. Blogs, forums, Reddit, Kaggle discussions and unofficial interpretations were not used. The statements below are short summaries, not legal conclusions. Details are in [DATA_ACCESS.md](DATA_ACCESS.md) §1.

| Source | URL | Relevant content |
|---|---|---|
| TCIA Data Usage Policies and Restrictions | https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/ | Anyone considering **mirroring** TCIA's public datasets, or providing **direct access** to them via another tool or website, is directed to the Data Analysis Centers page. Dataset (DOI) citation is required. Participants must not be identified or contacted. |
| TCIA Data Analysis Center (DAC) | https://www.cancerimagingarchive.net/tcia-data-analysis-center/ | A DAC provides TCIA data by connecting to the TCIA REST API **or by mirroring collections**. DACs must attribute each dataset, link to the usage policy and require the same downstream. Developers contact the helpdesk. |
| TCIA Support | https://www.cancerimagingarchive.net/support/ | Helpdesk **help@cancerimagingarchive.net**. Requests should include contact information and the URL of the relevant page. |
| TCIA BraTS 2021 analysis result | https://www.cancerimagingarchive.net/analysis-result/rsna-asnr-miccai-brats-2021/ | DOI 10.7937/jc8x-9874; Version 1, updated 2023/08/25; "Data Citation Required". The "Challenge data both tasks" package is **CC BY 4.0**, and its download lists the IBM Aspera Connect plugin as a requirement. The ID crosswalk (XLSX, 78.12 KB) is **CC BY 4.0**. |

The policies do **not** explicitly address a *private*, single-user copy in third-party compute storage, which is why provider confirmation is sought. **This record makes no legal conclusion and does not assume that private Kaggle storage, or any other route, is permitted.**

## 4. B1 state rule

B1 changes from **PENDING** to **AUTHORIZED** only after actual external written evidence has been supplied and recorded. In the gate state machine the "authorized" state of B1 is `PASSED`, and the website displays it as "Authorized". Acceptable evidence is exactly one of:

- a TCIA Help Desk written response;
- an explicit, official TCIA written instruction;
- another clearly authoritative written authorization from the data provider.

Authorization is **never** inferred from:

- the dataset being publicly downloadable;
- a TCIA web page, including the pages in §3;
- the CC BY 4.0 licence alone;
- Kaggle availability;
- a successful test download;
- API availability.

Protocol §5.1 also mentions "an owner-approved alternative". In this repository the owner's approval alone is **not** accepted as B1 evidence: an owner-selected alternative route (category C) still needs written provider authorization. This rule is stricter than the protocol and consistent with it. The protocol itself is unchanged.

The rule is enforced in code by `check_b1_evidence` in `src/brats_uncertainty/data/evidence.py`. The validator refuses B1 `PASSED` unless the evidence file:

- is named `docs/data/B1_EVIDENCE_<response date>.md` and is committed or staged in git;
- contains every template field exactly once, filled in, with no placeholder, `PENDING`, `TBD` or `TODO`;
- has an external `Evidence type:`;
- names the protocol version, dataset and DOI;
- has a route category of `A`, `B` or `C`;
- has a response date on or after the inquiry date;
- has an `Approved route:` equal to `data.approved_route`;
- records `Authorization status: AUTHORIZED` and `Conclusion: APPROVED`;
- quotes the provider's exact wording.

This record, the inquiry and the template are documentation and are always rejected as evidence.

## 5. How B1 can be closed (only after a written reply)

1. Send the inquiry manually, then record the send date in §7 and set `data.inquiry_sent: true`. This does not change B1.
2. When the written reply arrives, copy [B1_EVIDENCE_TEMPLATE.md](B1_EVIDENCE_TEMPLATE.md) to `docs/data/B1_EVIDENCE_<response date>.md`. Fill it in from the reply only, and stage it with `git add`.
3. If the reply authorizes a route, do a dry run first:

   ```
   brats-uncertainty gate-transition B1 PASSED --evidence docs/data/B1_EVIDENCE_<date>.md --on <date> --approved-route "<route>"
   ```

   Then add `--apply`. The command:
   - sets gate B1 to `PASSED` (shown as "Authorized") with the evidence file and date;
   - sets `data.authorization: APPROVED` and `data.approved_route`;
   - unlocks B2 (`AUTHORIZED`). B3–B12 stay `LOCKED`.
4. In the same commit:
   - add an administrative entry under `docs/research/protocol-amendments/`;
   - regenerate the website data with `brats-uncertainty export-site-data`.

If the reply refuses the route or is inconclusive, B1 does not pass. Ask a follow-up question, or record the refusal (template: `NOT AUTHORIZED` / `NOT APPROVED`) and set B1 to `FAILED` or `BLOCKED` with that file as evidence. **If TCIA declines every route**, SR7 applies: compute stays halted until a compliant workflow has written provider authorization.

## 6. Consequences while B1 is pending

- There is no data acquisition (B2), hashing (B3–B4), manifest (B5), counts (B6) or patient grouping (B7).
- EXP-001 is blocked (D2 = B1).
- B2–B12 are LOCKED.
- The real-mode commands all fail with `ResearchGateError`: `acquire --execute`, `hash-metadata`, `validate-data`, `build-manifest` and `derive-counts`.
- `acquire` fails with: "Real-data acquisition is locked because B1 data-route authorization has not been recorded."

## 7. Change log of this record

| Date | Change |
|---|---|
| 2026-09-29 | Record created; status PENDING; inquiry prepared, not sent. |
| 2026-09-30 | B2–B6 software completed (tested on synthetic data only); B2–B6 set to LOCKED under the gate state machine; B1 unchanged (PENDING). |
| 2026-09-30 | Audit: B1 evidence must be `docs/data/B1_EVIDENCE_<date>.md` (template added), committed or staged, and must name the approved route. B1 remains PENDING. |
| 2026-09-30 | B1 workflow finalized. Inquiry rewritten with six questions and the three-way distinction (private computational storage, public redistribution, runtime-only access). Evidence template rewritten with all required fields (STATUS = PENDING). The validator now accepts only recorded external written authorization; owner approval alone is no longer accepted. Official sources re-verified. Inquiry **not sent**; B1 remains **PENDING**. |
