<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Worldwide insurer identities and market shares: executable admission gap (2026-11-05)

**Status: read-only research evidence; no provider row acquisition, rights clearance, company-share import, portfolio or CAT-model admission.** This supplements (does not replace) `worldwide-insurer-group-source-coverage-20261102.md`, `insurance-two-branch-join-gates-20261104.md`, and the existing `landscape/sources-insurance-market-calibration.json`. The California and North Carolina source identities are **already in that canonical catalog**; they are not new database imports or newly discovered unique sources.

## Reproducible live core-database receipt

Executed 2026-11-05 against the **independent** Neon project `insurance-risk-core`, database `insurance`, explicit **main** branch `br-late-recipe-ba1cr8hc`, read-only, using:
[`research_runners/sql/worldwide_insurer_market_share_readiness_main_v0.sql`](../../research_runners/sql/worldwide_insurer_market_share_readiness_main_v0.sql).

| Measured object / schema | Live rows/count |
| --- | ---: |
| Secondary `research.insurer_directory_candidate_v0` discovery rows | 18,180 |
| Distinct directory `country_slug` values (NOT a validated sovereign-country count) | 181 |
| Distinct casefold name × market-slug pairs (NOT unique legal persons) | 18,176 |
| Original provider SHA-256 rows in this secondary directory | 0 |
| `model_input_approved=true` directory rows | 0 |
| Verified legal organizations (`entity.organization`) | 22 |
| Verified US-domiciled legal organizations in this core table | 0 |
| `entity.organization_candidate` rows | 161 |
| Still unresolved organization candidates | 156 |
| Verified GLEIF LEI identifier rows | 18 |
| Verified NAIC identifier rows in core | 0 |
| `entity.organization_relationship` rows | 0 |
| `entity.published_metric` rows | 0 |
| `entity.licence_observation` rows | 58 |

**Counting-semantics guard (review update):** The SQL output `organization_relationship_rows_total` is a raw count of `entity.organization_relationship` rows, **not** a count of independently verified, effective-dated insurer group memberships. Likewise, a nonzero `entity.published_metric` row count alone would not prove that its values are licensed, relevant P&C premium numerators or share-ready. Source rights, metric type, entity identity, year, LoB and denominators remain mandatory before any market-share calculation.

**Result:** `BLOCKED_NO_COMPANY_PREMIUM_METRICS`. There is no supported basis in **core main** today to calculate a named legal insurer's country × line-of-business premium market share. The zero NAIC counts are about **this core table**, not the external universe or the separate validation branch. The 18,180 secondary names may duplicate legal companies, groups, historical names, branches and other establishments; no coverage percentage against a regulator-complete all-insurers universe is justified.

The earlier 2026-11-04 receipt on **validation** branch `br-summer-sky-bawujqu8` reported 442 Florida company × statewide policy-type rows (160 reported NAIC codes), plus 9,194 Texas ZIP × policy-type observations (no issuer in the Texas ZIP population). Those records are **not on core main** and must not be represented as a single materialized company-market-share join. Both branches and rights gates remain separate.

## Verified official/public source-product observations — 2026-11-05

| Source | Observation verified on the publisher page | What a future authorised row can establish | Current limit |
| --- | --- | --- | --- |
| [California DOI 2025 P&C Market Share](https://www.insurance.ca.gov/01-consumers/120-company/04-mrktshare/2025/index.cfm) | 2025 state statutory Page 14 direct insurance; group and company NAIC IDs; Excel detail linked. Published 2025 all-lines DWP **USD 115.4bn**, homeowners **USD 16.4bn**, fire **USD 2.8bn**, private passenger auto **USD 48.4bn**; leading 25 groups' combined P&C market concentration **78.3%**. | State × legal insurer × LoB **direct written premiums** and source-defined shares, plus earned premium and incurred losses, after original workbook validation. | Figures are publisher-rounded web facts; the original XLSX bytes were **not obtained or parsed** in this review. CA-licensed, active and DWP > 0 reporting universe only; 25-group concentration is not total all-group exposure. Rights, worksheet/denominator/grain review pending. |
| [North Carolina DOI 2025 Market Share](https://www.ncdoi.gov/insurance-industry/financial-analysis/insurance-company-market-share-and-premium-information) | Official 2025 P&C sections include fire, allied, private flood, federal flood, homeowners, both portions of commercial multiple peril and non-proportional assumed reinsurance; [homeowners 2025 page](https://www.ncdoi.gov/documents/financial-analysis/statistical-data/2025p3s04homeowners-multiple-peril) identifies June 4, 2026 file publication. | State × company × statutory line benchmark, potentially a second-state consistency check. | The section landing pages were inspected, **not** original PDF numeric rows. Rights and publisher-byte checks needed; reinsurance assumed premium is a different population from direct insurance. |
| [NAIC official Research/Actuarial page](https://content.naic.org/es/node/596) | Describes 2025 top-25 direct P&C group/company line statistics and more detailed top-125 countrywide / top-10 state P&C reports. | Official group or company US direct premium shares within precisely published NAIC scope. | Published summaries and paid / rights-restricted underlying data are not interchangeable. NAIC *group* codes are not NAIC *company* codes; membership requires an independently checked dated crosswalk. |
| [EIOPA European Insurance Overview 2026](https://www.eiopa.europa.eu/assets/insurance-overview-report/European_Insurance_Overview_2026.html) | **2025 annual** EEA reporting; concentration charts defined as top-3, top-5 and top-10 premium writer shares **by country**, and downloadable associated Excel. | Country × segment **market concentration denominators**, independent benchmark for inferred distributions. | Concentration measures do not reveal names / premiums for all legal insurers. Original workbook not checked in this review; no company-specific join yet. |
| [EIOPA insurance statistics](https://www.eiopa.europa.eu/tools-and-data/insurance-statistics_en) | Solo annual premiums / claims through 2025; published totals by country and selected Solvency II lines, current updates dated 2026-10-12. | A **country × year × business/LoB** sector premium denominator, subject to precise QRT, geographic, gross/net and reporting-universe definitions. | Country aggregate is not a legal-entity company numerator or geographic CAT location; provisional / revised periods differ. |
| [OECD Global Insurance Market Trends 2026](https://www.oecd.org/en/publications/global-insurance-market-trends-2026_c8be6585-en.html) | **Published 2026-11-02**; 2025 market analysis over 50 reporting jurisdictions. | Cross-country premium/penetration benchmarking and denominator plausibility checks. | Not a list of every licensed insurer or every company-level share. National definitions and exact reporting populations must be reconciled. |

**Scope-sensitive examples:** CA's published 2025 top-25 group concentration of 78.3% answers a particular **group × California × all P&C lines** concentration question, **not** worldwide coverage, an individual company's share, or the proportion of buildings insured by those groups. EIOPA's top-3/top-5/top-10 concentration is a different EEA national/sector definition. Never turn sector concentration into named insurer allocations.

## Market-share calculation contract (not yet admitted)

Accept a percentage only if numerator and denominator have matching **(reporting year, geography-role, market / line-of-business, direct-vs-assumed, gross-vs-net, written-vs-earned, statutory accounting basis, currency / scale, reporting scope and original-source vintage)**:

```text
carrier_share_pct =
  100 * (verified carrier direct written premium for c,s,t) /
        (verified complete market direct written premium for c,s,t)
```

A source may publish a share directly; retain it as a **source-reported share** with its own denominator scope instead of pretending it is independently recomputed. Different types of insurer and reporting population (licensed/admitted, surplus lines, self-insurance, state funds, residual market, mutual, public pools, multi-country FOS) need explicit inclusion flags. Published missing values, source negatives, adjustments and zeroes must not be forced into attractive 100% totals. Rounding tolerances and discrepancies are first-class audit outputs.

Identity resolution order: dated national regulator legal licence / local insurer number -> official NAIC **company** code or EIOPA undertaking ID/LEI -> verified legal `organization_id` -> separately evidenced group membership, valid for the source date. Public company/insurance marketing brand and accounting consolidation are neither unique regulatory licence nor definitive group-membership evidence. Never add a group aggregate on top of its member-company rows.

A computed premium market share is a **financial benchmark**, not insured building market share, replacement TIV, policy distribution by ZIP, loss ratio conditioned on peril, treaty share, inward assumed exposure, or reinsured retained CAT risk. Any such allocation requires a clearly labelled **synthetic scenario** with assumption uncertainty and independent geographic / policy / CAT calibration.

## Ordered executable next steps and gates

1. **US state pilot / original bytes:** Acquire 2025 California detail Excel from the exact publisher hyperlink; record HTTP source URL, retrieval time, SHA-256, file format, sheets, header cells, duplicate codes, published denominator and usage rights. Work *outside Git* until legal reuse is cleared. Start with California homeowners, fire and all-lines; cross-check official published rounded 2025 state totals. Separately acquire the 2025 North Carolina homeowners and private flood original files; retain different PDF/Excel schemas. No unsupported programmatic scraping or bulk reposting.
2. **Country/LoB denominator:** Acquire 2025 EIOPA Solo Annual PCE exact CSV + accompanying note under existing `EIOPA_SOLO_ANNUAL_MARKET_PILOT_V0` path; validate unit scale, dates and coverage. Register 2026 EIOPA concentration overview and 2026 OECD report as **research source-product evidence**; do not ingest into a production company table until rights and numerical semantics pass.
3. **Group/company crosswalk:** Confirm regulator original 2025 NAIC member-company mapping under separate copyright/permissions gate; resolve NAIC company code to legal organizations **without** using a group name as identifier. Check branch-specific Florida research codes against regulator/verified identity; do not auto-promote source rows.
4. **Bounded research staging:** Design source-versioned `market_denominator`, `insurer_market_premium`, `source_reported_share` and `coverage_exception` projections on an isolated reviewed migration. Key by source, period, geography role, LoB, entity grain, basis and financial unit. Keep source files external, protect origin/reuse licence, and avoid writes to `main` until explicitly reviewed.
5. **Acceptance:** Require original-source provenance, permitted rights, numeric and statutory semantic reconciliation, verified legal entity, matched numerator/denominator, zero group/member double counts, and holdout validation against published regulator shares. Run an explicit status matrix: `SOURCE_OBSERVED`, `SOURCE_BYTES_VERIFIED`, `RIGHTS_REVIEWED`, `IDENTITY_VERIFIED`, `DENOMINATOR_MATCHED`, `SHARE_RECONCILED`, `MODEL_NOT_ADMITTED`.

**Outcome of this PR:** adds one rerunnable **read-only** SQL readiness check and this source-linked research handoff. No insurer market shares, financial reports or legal identities were inserted, no source was promoted and no CAT portfolio was fabricated.

## Independently repeated exact-query live receipt (2026-11-05)

The **current GitHub-branch SQL blob** `cf45a654d48d10cfed3684e8a663586d505650a9`, including the corrected `organization_relationship_rows_total` alias, was fetched directly from this PR and executed unchanged as a **single read-only SELECT** against the explicitly selected `insurance-risk-core / insurance / main` Neon branch `br-late-recipe-ba1cr8hc`. No source data, schema objects or production rows were written.

Observed output: `candidate_rows=18180`, `country_slugs=181`, `distinct_name_market_pairs=18176`, `verified_legal_entities=22`, `verified_us_entities=0`, `verified_lei_rows=18`, `verified_naic_identifier_rows=0`, `organization_relationship_rows_total=0`, `published_company_metric_rows=0`, `admitted_directory_rows=0`, `original_sha_rows=0`, `licence_observation_rows=58`. The gate remains **`BLOCKED_NO_COMPANY_PREMIUM_METRICS`**.

The live database schema was separately inspected via read-only `information_schema.columns`: `entity.organization_relationship` has parent/child IDs, relationship type, effective dates and source key, but **no verified boolean**. Even when rows exist, a verified and effective-dated relationship cannot be inferred by row count alone. `entity.published_metric` has `metric_name`, `business_scope`, `gross_net_basis`, `measurement_kind`, `year`, `country_code`, `currency_code` and `source_key`; counting rows alone is therefore not enough to establish a direct-written-premium insurer numerator or an admissible market share.

This is a current database-readiness check, **not** an original regulatory premium data import or a verified worldwide insurer census. Source-specific rights, official market denominator and dated legal identity must pass independently before market-share calculations or location allocation.
