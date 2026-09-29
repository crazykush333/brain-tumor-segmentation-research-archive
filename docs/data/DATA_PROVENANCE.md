# Data provenance and the B2–B6 reproducibility chain

**Status (2026-09-30): no real provenance records exist, because no data have been acquired (B1 PENDING; B2–B6 LOCKED).** Every hash, count and ID list is computed by code from the actual files at the stated gate. None is typed by hand.

## 1. Four zones

| Zone | What lives there | Leaves the zone? |
|---|---|---|
| **PUBLIC REPOSITORY** | code, configs, JSON Schemas, frozen protocol, documentation, status file, website; after each gate passes, the owner-reviewed derived public artifacts | public |
| **PRIVATE RESEARCH DATA** | official files as acquired (`data/raw/` or the approved compute storage), licensed metadata files, full manifests, integrity reports (`data/manifests/`) | never enters git or an unapproved location |
| **COMPUTE ENVIRONMENT** | the machine that runs the gated commands from a **clean, committed** checkout (records refuse dirty or uncommitted trees); credentials only from the platform's secret store; data only via the approved route | only records (JSON: names, sizes, hashes, counts, provenance) |
| **DERIVED PUBLIC ARTIFACTS** | the B2–B6 records and the manifest hash and summary, committed as gate evidence and administrative entries | public |

## 2. The chain

Every B2–B6 record is traceable to **protocol version + git commit + source + file hash + configuration + environment**, through a deterministic structure (records schema v3 and manifest schema v2, `brats_uncertainty.data.records` and `manifest_doc`). Every record and manifest carries an explicit `data_class`: `REAL_RESEARCH_DATA` or `SYNTHETIC_TEST_DATA`.

```
B1 evidence (committed; route approved)             data.approved_route
   │
B2 AcquisitionRecord ── source{dataset, version, DOI, URL, route} · adapter · acquired_at
   │                     storage_location (logical) · inventory[relpath, size, SHA-256]
   │                     stamp · record_fingerprint
   ├── B3 MetadataFileRecord (BraTS2021_MappingToTCIA.xlsx: name, size, SHA-256, source, DOI)
   ├── B4 MetadataFileRecord (UCSF-PDGM-metadata_v5.csv: name, size, SHA-256, source, DOI)
   │
B5 RAW DATA MANIFEST ── acquisition.record_fingerprint (B2) · metadata_records{B3, B4:
   │                     file, SHA-256, fingerprint} · files[case, type, modality,
   │                     relpath, size, SHA-256] · summary · duplicates · manifest_sha256 · stamp
   │
B6 CountsRecord ─────── crosswalk SHA-256 == B3 · b3_record_fingerprint · counts · targets
                         checks · diagnostics · site_counts · ID-list hashes
                         status VERIFIED_FROM_SOURCE (real) | SYNTHETIC_TEST_ONLY | FAILED_VERIFICATION · stamp

stamp = {created_at, code_commit, code_dirty, package_version, protocol_version,
         protocol_sha256, config_sha256{path: hash}, environment}
record_fingerprint = SHA-256 of canonical JSON without volatile fields
                     (created_at, environment, acquired_at)
```

Properties:

- The same inputs, code and configuration always give the same fingerprint.
- Editing a record breaks its fingerprint; readers refuse it.
- A B2–B6 gate can only PASS on its own execution record that meets all of these conditions:
  - the fingerprint is intact;
  - `data_class` is `REAL_RESEARCH_DATA`;
  - it was produced from a clean checkout whose commit exists;
  - it was produced against the frozen protocol hash;
  - it is committed (staged or committed, never a git-ignored file);
  - it is linked to the earlier gates' evidence: B5 to B2, B3 and B4; B6 to B3, including the crosswalk hash.

  B6 can only pass on `VERIFIED_FROM_SOURCE`. The status validator enforces all of this on every load.
- FAILED never returns to execution directly. FAILED goes to BLOCKED (with evidence), and BLOCKED goes to AUTHORIZED only with an owner-decision document.
- Software never advances a gate. The owner runs `gate-transition` (dry run by default, `--apply` to write) after reviewing the record.

## 3. Reproducing B2–B6 (future researcher)

You do **not** receive patient data from GitHub.

1. Get the code at the recorded commit:
   - `git checkout <code_commit from the published records>`
   - `pip install -e ".[dev,io]"`
   - `brats-uncertainty verify-protocol`
2. Obtain access under the providers' terms and the route in the closed B1 evidence. Run `brats-uncertainty init-data-dirs`.
3. **B2.** Dry run first, then execute:

   ```
   brats-uncertainty acquire --adapter local-import --delivered <operator download> \
     --dataset RSNA-ASNR-MICCAI-BraTS-2021 --dataset-version "<as on the official page>" \
     --doi 10.7937/jc8x-9874 --route "<B1-approved route>" \
     --storage-root data/raw/brats2021 --acquired-by "<name>" --out data/manifests/B2.json
   # then the same with --execute
   ```

4. **B3 and B4.**
   - `brats-uncertainty hash-metadata --gate B3 --file data/raw/brats2021/<...>/BraTS2021_MappingToTCIA.xlsx --source-url https://www.cancerimagingarchive.net/analysis-result/rsna-asnr-miccai-brats-2021/ --doi 10.7937/jc8x-9874 --out data/manifests/B3.json`
   - the same with `--gate B4` for `UCSF-PDGM-metadata_v5.csv`, using the UCSF-PDGM collection page.
5. **B5.**
   - `brats-uncertainty validate-data --dataset-config configs/dataset/brats2021.yaml --data-root <training folder>`
   - `brats-uncertainty build-manifest --dataset-config configs/dataset/brats2021.yaml --data-root <training folder> --acquisition-record data/manifests/B2.json --metadata-file <crosswalk> --metadata-record data/manifests/B3.json --metadata-file <ucsf csv> --metadata-record data/manifests/B4.json --out data/manifests/B5_manifest.json --out-csv data/manifests/B5_manifest.csv`
6. **B6.** `brats-uncertainty derive-counts --crosswalk <crosswalk> --b3-record data/manifests/B3.json --out data/manifests/B6.json`
7. **Compare** SHA-256 values, `manifest_sha256`, counts and record fingerprints with the published records. Equal values mean byte-identical inputs and identical results.

Each real-mode command runs only while its gate is AUTHORIZED or RUNNING, after its prerequisites have PASSED.

## 4. Synthetic test data

Any command with `--synthetic` (and `acquire --adapter synthetic-fixture`) runs on SYNTHETIC_TEST_DATA only:

- trees are generated outside the repository, with a marker listing each file's SHA-256;
- any file not generated by the generator, or modified after generation, is refused;
- outputs are written outside the repository, and records carry `synthetic: true`.

Synthetic data are never BraTS, never results and can never close a gate.

## 5. Current state

| Gate | State | Record |
|---|---|---|
| B1 | PENDING | [B1_DATA_ROUTE_AUTHORIZATION.md](B1_DATA_ROUTE_AUTHORIZATION.md) |
| B2–B6 | LOCKED | none |
| B6 counts | EXPECTED_BY_PROTOCOL (targets only) | none |
| B7–B12 | LOCKED | none |
