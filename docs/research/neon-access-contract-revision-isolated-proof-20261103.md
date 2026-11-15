<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Append-only source-access contract version proof — isolated Neon, 2026-11-03

**Purpose:** protect two significant rights/operation transitions from being
silently applied to production source records. This is a *research evidence
table*, not the operational authorization store and not an approved migration.

## Actual isolated run

- Connected project: CAT-only `insurance-risk-core`, database `insurance`.
- Neon branch **`access-contract-revision-proof-20261103`**,
  `br-steep-lab-baeo8bmc`, cloned from the already isolated
  `access-contract-metadata-stage-20261103` branch.
- Created **only** `research.access_contract_revision_evidence_v0`,
  its append-only reject-update/delete trigger and the associated function
  on this isolated branch.
- Recorded the **two original** versions using the existing verified
  `registry.source_record` rows and the **two proposed new versions**
  using exact original GitHub JSON source bytes pinned to
  `pokekarten/OpenCatastrophe-data` commit
  `e37fee4467079a5685423856659b2998d1db1f64`.
- Deliberately **did not update** `registry.source_record` or the
  operational access contracts and did not grant API or CAT access.

| Access contract | Historical blob, state | Proposed blob, unapproved state |
| --- | --- | --- |
| ESA WorldCover 2021 v200 | `830fff1705d6b29d8c88dc423a27c7254608ca50`; `documented_only`, probe `none` | `2884e2f50b495eee3b399f55c08d43cfa100b602`; `probe_ready`, probe `head` |
| NOAA CO-OPS Water Levels | `53aa5e6e9f23dc0ddd153fae1c57a4752f31b0aa`; `documented_only`, probe `none` | `f617e0a1915e84d0dbe51f08532793c7fb8accb4`; `probe_ready`, probe `provider_specific` |

The new JSON revisions are **research proposals**, not operational authorizations.
The old rows remain the operative historical observations on this branch.
In addition, `rights_status=verified` at *dataset* level is not a model
scientific review or open-ended API/data acquisition license.

## Executed negative mutation test

An actual isolated PostgreSQL
`UPDATE research.access_contract_revision_evidence_v0 SET review_status=review_status`
on the historical WorldCover row **failed** as expected with:

```text
access revision evidence is append-only; corrections need a separate reviewed lineage table
```

This attempted no-op mutation was rejected by the database trigger.
No update or deletion succeeded. A subsequent readback showed two
revisions per contract, one `historical_observed` and one
`proposed_unapproved`, all permission/admission fields false.

The unchanged `research_runners/sql/access_contract_revision_evidence_v0_verify_readonly.sql`
was executed against the isolated branch, returning:

| Verification | Actual value |
| --- | ---: |
| Total revision rows | **4** |
| Distinct contracts | **2** |
| Historical `documented_only` / probe none | **2** |
| Proposed `probe_ready` / bounded probes | **2** |
| Source rights/contract mismatches | **0** |
| Previously registered contract rows mutated | **0** |
| Production, download or model authorization flags | **0** |

Independently compared the existing **147**
`registry.source_record` rows on the parent staging branch and new
revision-proof branch by stable ordered full-row metadata digest:
both **`3b1defa8b55dee9cd1accdd2807b35ee`**. The digest is a
controlled database parity receipt, **not** an external provider
authenticity or licence proof.

## Promotion explicitly blocked

No SQL from this proposal may be executed on the default Neon branch
without a separately reviewed production migration, fresh immutable source
version capture, independent original-provider rights and endpoint review,
an explicit rule for which version controls the live probe, and
post-transaction verification. In particular do not merge entire
Neon branches; use a bounded, append-only, source-ID checked process.
The original production database still contains **114 source records**,
with no admitted raw data. The staged production candidate currently has
147 records, but is **not** production.

This PR includes SQL DDL **for isolated testing only**. Do not run it as
part of automated database migrations, CI setup, or product workflows.
