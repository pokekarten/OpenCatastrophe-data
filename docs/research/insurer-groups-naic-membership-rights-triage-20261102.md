<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Insurer groups: identity-reconciliation triage and official NAIC 2025 crosswalk scope

**Evidence as of 2026-11-02, read-only on `insurance-risk-core/main`, database `insurance`.** Research only; not an approved insurer-group-to-company data import, verified legal ownership graph, licence adjudication, insurer catastrophe exposure, or CAT model approval.

## Actual current identity gap

The executed query `research_runners/sql/worldwide_insurer_group_hint_review_readonly_v0.sql` on the explicitly selected independent CAT-only Neon main yields:

| Metric | Live result |
| --- | ---: |
| Organization candidates in `entity.organization_candidate` | 161 |
| Unmatched organization candidates | 156 |
| Candidates with nonblank `group_hint` | 154 |
| Unmatched candidates with `group_hint` | 149 |
| Distinct textual group hints | 118 |
| Repeated hints (at least two candidate rows) | 10 |
| Candidate rows under repeated hints | 46 |
| Hints with both an unmatched candidate and an already resolved organization candidate | 3 |
| Asserted rows in `entity.organization_relationship` | **0** |
| Verified NAIC group code identifiers in `entity.organization_identifier` | **0** |

These are **research text labels**. A shared group_hint does not prove that those businesses share a legal parent, are distinct legal insurers, hold a licence in that country, or are currently under the same group in an official snapshot. The already-resolved candidate count indicates legal-entity identification only; it is **not** group membership certification.

### Current bounded manual review queue

| Priority | Examples from live read-only query | Reason for manual work |
| --- | --- | --- |
| P1 — manual identity reconciliation | Hannover Re, Munich Re, SCOR | At least one unmatched and one previously resolved entity candidate share a text hint; use **independent, unique regulator identifiers** and GLEIF relationship evidence, never the hint alone |
| P2 — regulator research | RenaissanceRe, Arch Capital, Everest, PartnerRe, Fairfax, Swiss Re | Multiple unresolved candidate legal entities; collect their legal-company numbers, jurisdiction, dated name changes and branch/granularity evidence |
| P3 — other hints | One or two unresolved rows | Check official source before entity registration, not before entire hierarchy can be verified |

The executed SQL limits output to the top 30 sorted review clusters; it includes no source-row payload, unverified ownership assertion, or database write. For P1 the output names are **prioritisation labels**, not a verified relation. The query intentionally returns three hard-coded `false` audit flags for regulator group-code verification, parent-child verification and model admission.

## Newly identified authoritative US member-company source — rights gate

The [NAIC Listing of Companies Summary](https://content.naic.org/sites/default/files/publication-loc-zu-listing-companies-summary.pdf) is a **December 2025** NAIC publication whose introduction specifies `Group Listing Numeric` and explains the **group-code → individual member insurer company code** lookup, together with statement type, company status and domicile fields. This is **more actionable for a group-to-carrier bridge** than the NAIC [2026-Q2 Insurance Group Lead State Report](https://isiteplus.naic.org/lead-state/publeadstate/pubLSHtml), which lists group name, group code and regulatory lead state, not member-company membership.

**Publication rights are a hard blocker**: the 2025 NAIC PDF expressly states *all rights reserved* and forbids reprinting or distributing material without written permission. It is accessible to read, but **accessibility is not a blanket licence to republish, commit, bulk copy or automatically ingest all rows**. Only bibliographic description, column semantics and a permission hold were added to the 19-entry source register. No NAIC member-company rows or source PDF bytes were stored in Git or Neon.

**Cross-year data risk:** group membership for data year 2025 need not match a 2026 Q2 group-lead-state report; do not join these as if they share a single snapshot. Record group-code namespace, company-code namespace, licence/entity status, separate source period and any name/merger changes.

## Exactly what makes the identity linkage valid

For the group/company lane, request authorised reuse or find a genuinely open regulator-issued group-to-member table; acquire the exact original dated file and receipt, and review its rights. Where company codes are available, independently corroborate the company code's legal entity and country and (when relevant) its LEI. A regulator *group membership* record should remain distinct from corporate accounting-consolidating parentage in [GLEIF Level-2](https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-2-data-who-owns-whom/roc-policy-on-level-2-data); a multinational insurance group's operating entities can be licensed under different legal frameworks.

A branch, captive, managing general agent or broker is not automatically an additional insurance company. Likewise a group's market share, property TIV, catastrophe losses or contractual treaty terms cannot be determined from a company listing.

The existing 18,180 entries across 181 market-slugs remain secondary-source research observations under [PR #899](https://github.com/pokekarten/OpenCatastrophe-data/pull/899), not a legally deduplicated worldwide group/corporate tree. This research does not modify those records.

## Execution and safe result

Run the SQL as a **read-only query** against the project/branch/database explicitly selected by the operator. This was executed successfully on 2026-11-02: the top 30 contained 3 P1 clusters, 6 P2 clusters and 21 P3 research clusters, with **all ownership / group code / model-approval result flags false**. The dataset scope must always be recorded with a future run; do not interpret unchanged class labels as verification.
