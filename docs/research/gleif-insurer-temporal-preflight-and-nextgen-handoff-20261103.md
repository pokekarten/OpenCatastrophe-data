<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Insurer legal-entity group preflight: temporal evidence, rights, NextGen handoff

**Executed research, 2026-11-03.** OpenCatastrophe-data is the public source/evidence register; this note does **not** import third-party data, create insurer ownership links, simulate portfolios, admit insured exposure or alter a consumer database.

## What changed in live evidence

Read-only SQL `research_runners/sql/gleif_relationship_temporal_preflight_readonly_v0.sql` was **successfully executed on the selected separate CAT-only Neon insurance main**. It inspects eleven existing GLEIF Level-2 research observations (pre-existing research asset IDs 21 and 28), their original typed `periods` JSON, independently verified legal-entity LEIs, existing branch/passport observations, and existing internal importer policy.

| Observed live audit bucket | Rows | Why this is not a production graph edge |
| --- | ---: | --- |
| Legal-entity LEI endpoints verified; one each of relationship, accounting and filing periods | **5** | Original staged source asset `raw_import_allowed=false` and GLEIF ingestion feed `automated_import_allowed=false`; no semantic approval |
| Legal-entity LEI endpoints verified but `ACCOUNTING_PERIOD` and `DOCUMENT_FILING_PERIOD` absent | **2** | Incomplete documentation chronology; **no fabricated accounting end date or inferred 2026 accounting year** |
| French `eu_inward_passport` / foreign registration with verified German head office | **2** | Separate regulatory/branch identity, **not a second independently licensed legal insurer** |
| GLEIF reporting exceptions with no parent | **2** | `NO_KNOWN_PERSON` or `NON_CONSOLIDATING`: **never invent a parent edge** |
| **Total** | **11** | **0** authorised materialisations; **0** writes to Neon; **0** model admissions |

The first two buckets are **seven** source-reported accounting relationships with distinct exact verified child/parent legal-entity LEIs. The 2 foreign-registration observations are the other two accounting records. The last two are explicit no-edge exceptions.

In the current eleven-record cohort, **9** are source-reported `ACTIVE` consolidation records. All 9 include exactly one `RELATIONSHIP_PERIOD`; only **5** include exactly one `ACCOUNTING_PERIOD` and `DOCUMENT_FILING_PERIOD`. Four lack the latter two period types, including the two foreign-registration records and the two legal-entity Allianz corporate specialty records. Absence is recorded as missing evidence, **not as null accounting loss, automatic legal-entity rejection, or an assumption of present-day contract duration**.

## Why three different times matter

The [official GLEIF RR-CDF v2.1](https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-2-data-relationship-record-rr-cdf-2-1-format) distinguishes:

- **`RELATIONSHIP_PERIOD`**: validity of the recorded accounting-consolidation relationship itself;
- **`ACCOUNTING_PERIOD`**: accounting dates covered by documents used to validate the relationship;
- **`DOCUMENT_FILING_PERIOD`**: filing/publication document chronology.

They are not synonyms. `relation.status=ACTIVE`, current GLEIF Golden Copy publication, old research `ingested_at` and source relationship start date are each different information.

The destination table `entity.organization_relationship` currently exposes only `effective_from date`, `effective_to date`, parent/child UUIDs, a relationship-type text label and a source-key reference. A simple `::date` of a GLEIF timezone-aware relationship timestamp discards the exact instant; interpreting accounting-period end or Golden Copy publication as `effective_from` would be incorrect. The query therefore preserves timestamp-with-timezone data separately, and emits `safe_to_coerce_source_timestamp_into_date_only_effective_from=false` for **every** observation. It proposes **no date-only production values**.

## Separate current licensing and ingestion policy

The [official GLEIF LEI Data Terms of Use](https://www.gleif.org/en/meta/lei-data-terms-of-use) state that LEI/LE reference data is available under **CC0**. That public licence does not itself alter the independent internal application controls. The existing insurance database reports:

- `registry.entity_feed('gleif_global').rights_status='cc0_verified'`, but `automated_import_allowed=false`;
- the original staged source assets have `evidence_status='research_only'`, `rights_status='source_scoped'`, and `raw_import_allowed=false`;
- `entity.organization_relationship` contains **zero** approved, asserted legal-entity relationship rows (as of this live run).

The appropriate next step is a specific rights/access governance decision and provenance-preserving consumer design, **not changing those flags to green or bypassing them with a SQL insertion**. Provider access terms may evolve; review the exact source/API usage profile prior to scaling to the full worldwide feed.

## Machine-contract implication for a future NextGen consumer

Keep three distinct semantic data paths, each carrying source URL/identity, source snapshot, explicit admission state and later validation outcomes:

1. **Legal-entity identity:** distinct exact verified LEIs / jurisdiction / status. Do not collapse a foreign regulator's branch/passport LEI into a legal company solely based on names. Link it through a separately typed *branch-or-passport registration* observation and verified head office.
2. **Accounting consolidation evidence:** direct parent, ultimate parent, explicit reporting exception, `RELATIONSHIP_PERIOD`, `ACCOUNTING_PERIOD`, `DOCUMENT_FILING_PERIOD`, original-source SHA/byte size/Golden Copy timestamp and publication/validation status. This is **not proof of shareholding or solvency group perimeter**. Check date-range overlaps and cycles for any proposed group tree.
3. **Regulatory group and insurance portfolio/underwriting exposure:** require a **separate** regulator-grade membership/licence and separately sourced actual or clearly labelled synthetic insurance portfolio. The corporate LEI graph alone cannot supply exposure coordinates, hazard, vulnerability, event losses, treaties, DLT/ELT/ILT/YLT or model input approval.

In particular, an inward/outward treaty or catastrophe aggregation must not replicate an insurer's exposure because it has an additional international registration. A model must carry both the **group evaluation as-of** and the **source evidence as-of**, and explicitly distinguish simulated/synthetic from observed exposure.

## Next engineering gate

Implement a *reviewed, versioned consumer schema* with immutable provider receipt identity (SHA-256 of actual original body), source semantic category, separate periods in `timestamptz`, exact verified endpoints, distinct branch evidence, source-governance decision, provenance of any approved materialisation, and false-by-default CAT model admission. It must be capable of rejecting an exception, unlicensed input, missing corporate identity, branch duplication, cyclic consolidation and conflicting dated parent edges. The existing query is a **read-only input preflight**, not the write procedure or materialized view.

The prior 11-source original-response pinning remains in `research_runners/sql/gleif11_original_http_neon_branch_readonly_20261103.sql`; this change adds the *temporal-readiness* analysis without duplicating or editing its original-source hashes.
