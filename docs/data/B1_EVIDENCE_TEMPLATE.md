# B1 evidence — TEMPLATE (not evidence)

This file is a **template**. It is not authorization and cannot close gate B1: the status validator accepts B1 evidence only from a file named `docs/data/B1_EVIDENCE_<YYYY-MM-DD>.md`.

To record real B1 evidence:

1. Copy this template to `docs/data/B1_EVIDENCE_<date the reply/decision was received>.md`.
2. Fill in the fields below from the actual written reply or owner decision.
3. Stage it (`git add`).
4. Run `brats-uncertainty gate-transition B1 PASSED --evidence docs/data/B1_EVIDENCE_<date>.md --on <date> --approved-route "<route>"`. This is a dry run; add `--apply` to write.

The two machine-checked lines must appear exactly once each, at the start of a line:

- `Evidence type:` followed by exactly one of `TCIA written confirmation` or `Owner-approved alternative`;
- `Approved route:` followed by the route text, identical to the `--approved-route` value.

---

Evidence type: <TCIA written confirmation | Owner-approved alternative>
Approved route: <exact route text>

- Date received / decided:
- TCIA ticket or reference (if any):
- Route covered:
- Conditions stated by the provider (attribution, access restriction, retention, deletion):
- Relevant sentences of the written reply, verbatim, with personal contact details redacted:
- For an owner-approved alternative: the decision, rationale and residual uncertainty, signed and dated by the owner:
