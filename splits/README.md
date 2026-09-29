# splits/

**No split exists.** The final patient-group split (protocol §6.3) is created exactly
once, at gate B10, after the patient grouping is frozen (B7-B9). It will contain case
IDs, patient-group IDs and partition names only, and its SHA-256 hashes are recorded
at B12. Do not create or commit any file here before those gates are closed.
