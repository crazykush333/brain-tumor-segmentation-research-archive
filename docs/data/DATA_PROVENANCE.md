# Data provenance and reproduction of gates B2–B6

**Status (2026-09-29): no provenance records exist, because no data have been acquired (B1 PENDING).** Nothing below may be filled in by hand. Every hash, count and ID list is produced by the code from the actual files at the stated gate.

## 1. Four zones

| Zone | What lives there | Leaves the zone? |
|---|---|---|
| **PUBLIC REPOSITORY** (this git repo) | code, configs, frozen protocol, documentation, status, the website, and (after each gate closes) owner-reviewed derived public artifacts | public |
| **PRIVATE RESEARCH DATA** | official BraTS 2021 / BraTS-Africa files (NIfTI, labels), the crosswalk XLSX, the UCSF-PDGM metadata CSV, full manifests, integrity reports. Stored under the git-ignored `data/` tree or in the B1-approved compute storage | **never** enters git or any unapproved location |
| **COMPUTE ENVIRONMENT** | the machine or notebook where gated commands run. It clones a **tagged or committed** revision of this repository; credentials come from the platform's secret store; data arrive only via the approved route | only records (JSON: IDs, hashes, counts) are copied back for owner review |
| **DERIVED PUBLIC ARTIFACTS** | per gate, after owner review: file names, sizes and SHA-256 (B2–B4); the manifest hash and summary (B5); counts and ID-list hashes (B6); later the ID-only groups and split files (B9–B12) | committed as administrative entries (`docs/research/protocol-amendments/`) |

Licensed metadata files and images are never derived public artifacts. Whether per-file manifests (case IDs plus hashes) may be published is decided at B5 under the data licence. The default is to publish only the manifest hash and summary.

## 2. What each record contains

Every record carries a **provenance stamp** (`brats_uncertainty.data.records.ProvenanceStamp`):

- creation time (UTC);
- the exact **code commit**, and whether the tree was clean (commands refuse to run from a dirty or uncommitted tree);
- package version;
- **protocol version** and protocol SHA-256;
- the captured **environment**: Python, platform, package versions, GPU if any.

| Gate | Command | Record fields (in addition to the stamp) |
|---|---|---|
| B2 | `record-acquisition` | exact source: dataset, **dataset version** as shown on the official page, **DOI**, **source URL**, **route** (must equal the B1-approved route); **acquisition date**; acquirer; for each acquired file its **file name**, size and **SHA-256** |
| B3 | `hash-metadata --gate B3` | file name must be exactly `BraTS2021_MappingToTCIA.xlsx`; size; SHA-256; source URL; DOI |
| B4 | `hash-metadata --gate B4` | file name must be exactly `UCSF-PDGM-metadata_v5.csv`; size; SHA-256; source URL; DOI |
| B5 | `validate-data`, then `build-manifest` | **manifest version** (schema 1); manifest SHA-256; case count; integrity report (errors and warnings); per case: relative paths, sizes, SHA-256 of 4 modalities and the label |
| B6 | `derive-counts` | crosswalk SHA-256 recomputed and compared with the B3 record; derived counts and protocol targets (1,251 / 511 / 740); site-1 rule; SHA-256 of the sorted development and held-out-institution ID lists; status `PASSED` or `FAILED_SR3` |

Record classes validate themselves: malformed hashes, empty fields, wrong file names, non-https sources, a route not approved at B1, and inconsistent B6 status all raise errors. There is no API for entering a hash by hand.

## 3. How to reproduce B2–B6 (future researcher)

You do **not** receive patient data from GitHub. You obtain it yourself from the official provider.

1. Clone the repository at the commit named in the published records:
   - `git checkout <code_commit>`
   - `pip install -e ".[dev,io]"`
   - `brats-uncertainty verify-protocol`
2. Obtain access under the providers' terms and the route documented in the closed B1 record. Acquire the files into `data/raw/` (run `brats-uncertainty init-data-dirs` first).
3. **B2.** Record what was acquired:

   ```
   brats-uncertainty record-acquisition \
     --dataset RSNA-ASNR-MICCAI-BraTS-2021 --dataset-version "<as on the official page>" \
     --doi 10.7937/jc8x-9874 \
     --source-url https://www.cancerimagingarchive.net/analysis-result/rsna-asnr-miccai-brats-2021/ \
     --route "<B1-approved route>" --acquisition-date YYYY-MM-DD --acquired-by "<name>" \
     --out data/manifests/B2_acquisition.json data/raw/<acquired files...>
   ```

4. **B3 and B4.** Hash the metadata files:
   - `brats-uncertainty hash-metadata --gate B3 --file data/raw/BraTS2021_MappingToTCIA.xlsx --source-url <page> --doi 10.7937/jc8x-9874 --out data/manifests/B3_crosswalk.json`
   - the same with `--gate B4` for `UCSF-PDGM-metadata_v5.csv`, using the UCSF-PDGM collection page and its DOI.
5. **B5.**
   - `brats-uncertainty validate-data --dataset-config configs/dataset/brats2021.yaml --data-root <extracted training folder> --out data/manifests/B5_integrity.json`
   - `brats-uncertainty build-manifest --dataset-config configs/dataset/brats2021.yaml --data-root <same> --out data/manifests/B5_manifest.json`
6. **B6.** `brats-uncertainty derive-counts --crosswalk data/raw/BraTS2021_MappingToTCIA.xlsx --b3-record data/manifests/B3_crosswalk.json --out data/manifests/B6_counts.json`
7. **Compare** your hashes and counts with the published derived artifacts. Identical SHA-256 values mean you hold byte-identical inputs.

Each command runs only when the preceding gates are CLOSED in `docs/project_status.yaml`. In a reproduction, the published status already shows them CLOSED with evidence.

Configuration that must be confirmed on the real files (recorded, never assumed):

- the dataset file naming and `expected_shape` in `configs/dataset/brats2021.yaml`;
- the crosswalk column headers (from report 15; re-checked at B3/B6).

## 4. Integrity checks (`brats_uncertainty.data.integrity`)

The integrity audit checks:

- expected files exist, and file names follow the dataset schema;
- all four modalities are present, and label files are available;
- there are no duplicate or colliding case IDs, and the found case IDs match the expected ones;
- there are no unexpected files;
- no file is corrupt (full gzip CRC read plus a NIfTI-1/2 header check, without loading voxels);
- each case's modalities and label have the same dimensions, and they are 3-D;
- file hashes match an existing manifest.

It returns a report of all issues. `build-manifest` refuses to write a manifest while the report has errors.

## 5. Current state

| Gate | State | Record |
|---|---|---|
| B1 | PENDING | [B1_DATA_ROUTE_AUTHORIZATION.md](B1_DATA_ROUTE_AUTHORIZATION.md) |
| B2–B6 | NOT STARTED | none |
| B7–B12 | LOCKED (pending B1–B6) | none |
