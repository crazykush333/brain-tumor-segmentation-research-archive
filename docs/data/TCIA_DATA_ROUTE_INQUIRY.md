# TCIA data-route inquiry (READY TO SEND — NOT SENT)

| Field | Value |
|---|---|
| Status | **Draft, not sent.** The project owner sends it manually. |
| To | help@cancerimagingarchive.net (the TCIA Helpdesk address on the official Support page, verified 2026-09-29) |
| Purpose | Gate B1 of protocol v1.0: written confirmation of the data route |
| After sending | Record the send date in `docs/data/B1_DATA_ROUTE_AUTHORIZATION.md` §6 and set `data.inquiry_sent: true` in `docs/project_status.yaml` |

Fill in the bracketed fields before sending. Do not add personal data beyond what you want TCIA to have.

---

**Subject:** Permitted data route for RSNA-ASNR-MICCAI-BraTS-2021 (DOI 10.7937/jc8x-9874): private cloud compute storage vs runtime download

Dear TCIA Helpdesk,

I am planning an academic research study on brain-tumor segmentation and case-level uncertainty under missing MRI modalities. It will use the RSNA-ASNR-MICCAI-BraTS-2021 analysis result (DOI 10.7937/jc8x-9874): the "Challenge data both tasks" package and the "ID Crosswalk map between BraTS ID and TCIA ID". The study protocol is pre-registered. Only identifiers, file hashes, counts and aggregate metrics will be published. No images, labels or metadata files will be redistributed, and no re-identification or facial rendering will be attempted.

Our compute will run on a third-party cloud notebook platform (Kaggle, possibly Google Colab). Before acquiring any data, I would be grateful for your written guidance on the following:

1. **Private storage.** Is it permitted to store a private, access-restricted copy of the official BraTS 2021 files as a private dataset in a third-party computational environment such as Kaggle? The copy would be visible only to me and not shared or published.
2. **Mirroring/re-hosting.** Would TCIA consider such private storage to be "mirroring" or "re-hosting" under the TCIA Data Usage Policies and the Data Analysis Center guidance? If so, what would be required?
3. **Runtime-only download.** Is it permitted instead to download the files from TCIA directly into the temporary storage of a Kaggle or Colab session at runtime, with no persistent copy kept after the session ends? The challenge-data download lists the IBM Aspera Connect plugin as a requirement. Is there a supported programmatic or command-line method suitable for such environments?
4. **Conditions.** Do any additional attribution, access-restriction, retention or deletion requirements apply beyond the dataset's CC BY 4.0 licence, the required data citation and the TCIA Data Usage Policies?
5. **Recommended route.** If neither option is appropriate, does TCIA recommend an approved alternative route for using this dataset with cloud GPU compute?

Thank you for your help.

Kind regards,
[Full name]
[Affiliation / institution]
[Contact email]
Reference pages:
- https://www.cancerimagingarchive.net/analysis-result/rsna-asnr-miccai-brats-2021/
- https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/
- https://www.cancerimagingarchive.net/tcia-data-analysis-center/

---

## Notes for the owner

- The Support page asks requests to include your contact information and the URL of the relevant page (already included above).
- Keep the full reply privately. Only the redacted evidence summary described in the B1 record is committed.
- Receiving a reply does not close B1 by itself. B1 closes only when the evidence file is committed and the owner sets the gate to CLOSED.
