<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Official GLEIF Level 2: 11-source current original audit vs CAT-only Neon research

**Review date:** 2026-11-03. **Public research and reference evidence only:** no customer data, insurer exposures, materialised ownership graph or CAT model admission.

## Actual work executed

Fetched and inspected **11 separate exact original GLEIF JSON:API HTTP response bodies** on 2026-11-03, all pointing to **Golden Copy `2026-11-03T08:00:00Z`** (official GLEIF publication time in the returned original JSON). Verified the response relationship and registration status of all nine published consolidation records as `ACTIVE`/`PUBLISHED`, their source child and parent LEIs and the explicit reasons of two reporting exceptions. Locally calculated SHA-256 of each original response body and validated the hashing algorithm against the standard `abc` test vector before producing the pinned receipt list.

The eleven original HTTP bytes are **not stored in Git**. The exact URLs, original-body byte lengths, SHA-256, expected source relationship kind and source `RELATIONSHIP_PERIOD` start timestamp live in the bounded [read-only Neon SQL](../../research_runners/sql/gleif11_original_http_neon_branch_readonly_20261103.sql). This is a **source-versioned research snapshot**, not a standing claim that the online API cannot change.

Executed that exact SQL against independent **`insurance-risk-core` / `insurance` / `main`**. For all 11 receipts, precisely **one** previous `entity.relationship_observation` row had matching child LEI, exact official source endpoint, source-reported parent, relationship category, source-reported status (or explicit exception), and `RELATIONSHIP_PERIOD.startDate`. The observations were originally staged on 2026-10-31 from **two source-scoped research assets**, not ingested from the present GLEIF API snapshot.

| Distinct current evidence category | Observations | Independent Neon identity status |
| --- | ---: | --- |
| Direct accounting consolidation | 5 | Source fields verified; not a regulator group licence |
| Ultimate accounting consolidation | 4 | Source fields verified; not beneficial ownership |
| Direct-parent reporting exceptions | 2 | No parent edge is permitted |
| **All official source observations** | **11** | All 11 old research keys/period starts match fresh original GLEIF records |
| Consolidation observations with exactly one verified legal child **and** parent LEI | **7** | Research-ready legal endpoints, still no authorised graph insertion |
| Consolidation observations with a separately recorded French regulatory passport/foreign registration instead of a new verified legal-entity row | **2** | Distinct foreign regulatory identity; do not double-count as another insurer |
| Reporting-exception observations | **2** | Explicit `NO_KNOWN_PERSON` / `NON_CONSOLIDATING`; no relation inserted |

The first three rows are a disjoint partition of 11. The last three rows separately classify the **nine consolidation plus two exception observations** by identity/edge resolution.

## Critical discovery: foreign-registration LEI versus German head office

Two observations under `969500VV8Y4PQ7XJWE02` are associated with France, but the exact official [French ACPR insurer listing](https://acpr.banque-france.fr/fr/fiche-detaillee/allianz-global-corporate-specialty-se-5) identifies:

- Legal registration **SIREN 487424608**, French supervisory activity `Entrant`, EU inward passport, and **BaFin** as home-state regulator.
- Its GLEIF LEI **`969500VV8Y4PQ7XJWE02`** points to the German-registered `F240A7PWJB2BLKELB442` as **direct accounting consolidating parent**, and to Allianz SE's LEI `529900K9B0N5BT694847` as ultimate parent.
- An independent [French government company register](https://annuaire-entreprises.data.gouv.fr/entreprise/487424608) describes the SIREN registration as an **international/foreign commercial entity** with registered parent headquarters in Germany, and shows distinct French establishments.

GLEIF's **foreign-registry LEI** and a regulator's **passporting registration** are not automatically an additional legally independent insurance risk carrier. Nor should the two LEIs be collapsed solely because the names match. This must be a separately typed, dated and source-scoped `foreign_branch_observation`. **Neon already has the appropriate French passport observation** for this LEI, referencing the verified German head-office LEI. It also holds a separate Singapore branch observation (registration-status `LAPSED`), which is outside the eleven GLEIF accounting records and must not be counted as another current licensed legal insurance company without separate regulator verification.

This is a **source-backed identity ambiguity / cross-border-entity duplication guard**, not a decision to merge two LEIs or override GLEIF's published relationship semantics. For legal consolidation or solvency calculations, a foreign EU passport cannot automatically be a new underwriting portfolio.

## Provenance and admission gates

The two stored `registry.repository_asset` references for the pre-existing eleven Neon relationships have `evidence_status=research_only`, `rights_status=source_scoped`, `raw_import_allowed=false`. Additionally, `registry.entity_feed` has `gleif_global.rights_status=cc0_verified` but **`automated_import_allowed=false`**. This source access distinction is an intentional safety gate: even where a source provides data with permissive terms, *permission for this downstream automated ingestion workflow* has not been granted.

The current `entity.organization_relationship` table still contains **zero** rows. It has only parent UUID, child UUID, relation type, date-only effective period and optional source key; it cannot by itself store the full GLEIF original-response SHA, publication time, RR-CDF relationship type, reporting status and accounting/document/relationship periods. The richer `entity.relationship_observation` should remain the source-evidence layer. Do not recode `IS_ULTIMATELY_CONSOLIDATED_BY` as a direct parent or use the official Golden Copy time as a relationship start.

This audit leaves **`authorized_to_materialize=false`**, **`neon_written=false`**, **`model_input_approved=false`** for all eleven rows and hard-blocks missing/duplicate observations, changed keys, changed source period starts, invalid legal LEI matches and unsupported branch classifications. The related offline regression checks verify the fixed source cohort and graph consistency using only synthetic mutation tests.

## Next causal engineering step

Only after rights/workflow authorization, legal-entity-versus-branch decisions and review of exact GLEIF consolidation semantics, design the **versioned evidence-to-relationship materialisation** with immutable original-source hash, source `as of` time, relationship and accounting dates and explicit legal identity keys. Keep regulatory group membership separate from GLEIF's accounting relationships. GLEIF [RR-CDF 2.1](https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-2-data-relationship-record-rr-cdf-2-1-format) and [Reporting Exceptions 2.1](https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-2-data-reporting-exceptions-2-1-format) define distinct relationship/period/exception meanings.

The newly found **eleven current original receipts** close the immediate origin-verification gap at research level but do *not* change the access or model-input policy.
