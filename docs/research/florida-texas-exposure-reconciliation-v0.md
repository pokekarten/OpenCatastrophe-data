<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Florida/Texas insurance exposure research: real staged-data QA v0

**Date:** 2026-11-01. **Database:** CAT-only Neon `insurance-risk-core`, database `insurance`, **branch** `validation-schema-20261031` (NOT `main`). No credentials, source rows, insurer portfolio secrets or original provider bytes are committed to this repository.

## Problem solved

Previously, source-exposed Florida company/policy-type totals and Texas ZIP/policy-type market stock were present only as unrelated staged observations. The work adds **read-only derived views** that let an analyst check reporting scope and exact arithmetic, aggregate the Florida source at its **observed** granularity and monitor which crucial CAT inputs are still absent. No cross-state allocation, company-ZIP inference, sampled buildings, new insured portfolio or CAT simulation is created.

Run the two SQL files against the isolated validation branch:

- `research_runners/sql/fl_oir_company_exposure_readiness_v0.sql` creates `research.fl_oir_company_exposure_readiness_v0`.
- `research_runners/sql/tx_market_policy_stock_quality_v0.sql` creates `research.tx_market_policy_stock_quality_v0`.
- `research_runners/sql/exposure_research_invariants_v0.sql` evaluates 11 **read-only** data integrity assertions.

These SQL files are additive to the validation branch. The corresponding source tables do **not** exist in main; never run the definitions there without deliberately migrating, validating and approving their dependencies.

## Real Neon read-back (2026-11-01)

| Source/study input | Source rows | Derived QA result | Known limitations |
| --- | ---: | --- | --- |
| Florida OIR statewide 2025-12-31 MIR company x policy type | 442 | 160 unique NAIC company keys; 25 reported policy-type categories; **0** malformed rows, **0** count/exposure/premium split mismatches | Original XLSX SHA stored, workbook extract complete, **not** proof that all regulated carriers filed; source data unaudited; rights not reviewed; not geographic company-ZIP exposures |
| FL–NC same-NAIC research crosswalk | 101 | All 101 exact NAIC identifiers present in the 160 Florida keys | Same code is not ownership, treaty, branch or complete portfolio proof |
| Texas 2025-12-31 ZIP5 x policy-type stock | 9,194 | 2,069 unique ZIP5; six policy types; 9,190 positive research rows; four negative values quarantined; **0** duplicate ZIP-policy pairs; **0** malformed rows | **No** legal carrier per ZIP, actual insured TIV, or recorded provider-original HTTP SHA |
| Invariant query | 11 checks | **11 passed** | Checks source arithmetic and false promotion; not full independent source audit or CAT calibration |

Texas non-negative *policy counts* across 9,190 research rows sum to 11,530,061; this is **not** 11.5 million unique insured buildings and must never be used as a carrier exposure estimate without additional evidence. Four negative signed counts sum to -79 and stay quarantined. Florida company totals must be labelled source-reported, by policy type, as of 2025-12-31; they are **not** geocoded building TIV, and aggregating product lines can double-count physical assets.

Florida company coverage view keeps separately reported including-wind and excluding-wind exposures and direct premiums. The observations are company-statewide x source policy type. The view **always sets `model_input_approved=false`** and reports evidence gates. All 160 groups currently have `BLOCKED_REPORTING_UNIVERSE_UNKNOWN` as their first outstanding gate; independently, all source rows have `commercial_rights_reviewed=false`, no parcel-TIV, no per-carrier-ZIP observations, and `cat_loss_calibration_admissible=false`.

The Texas view likewise fixes `model_input_approved=false`; its current first blocker is `BLOCKED_ORIGINAL_SOURCE_PROVENANCE` (no original HTTP hashes). **Never** join this Texas ZIP market distribution to Florida statewide company exposures. These are different geographies, carriers and policy universes.

## Official source semantics and limitations

- Florida OIR [MIR reports](https://qsrng.floir.gov/Reports/ReportCriteriaWizard.aspx): monthly company-reported data, subject to resubmission, **not audited by OIR**. Record query parameters and original retrieval timestamp before extraction.
- Florida OIR [Tools and Data](https://floir.gov/tools-and-data): beginning January 2025, filings have county/ZIP reporting support. A company-statewide summary is **not** a company x ZIP source table.
- Florida [MIR FAQ](https://floir.gov/docs-sf/default-source/data-call-instructions/mir---faqs.pdf): the primary form's lines and coverage definitions, independent from a CAT policy-level risk count.
- Texas [TDI open data](https://data.texas.gov/): distinguish policies in force, actions, rates, line of business and units; negative provider values are not negative insured assets.

## Next scientifically meaningful steps

1. Acquire an **exact original** Florida MIR company x ZIP x policy type export, with period/selection criteria and retrieval timestamp. Keep bytes outside Git pending product-specific licensing/privacy review. Verify it against the statewide source for same month/companies/policy scopes, then derive geocoded *reported* source values, not invented individual buildings.
2. Acquire the Texas TDI original HTTP bytes/headers and hash, confirm documented suppression/negative-code meaning and ZIP/policy aggregation semantics. Keep quarantined signed values separate.
3. Complete company NAIC identity verification with official regulator sources; do not transform FL–NC same-NAIC overlap into parent relationship or reinsurance link.
4. Independently admit building stock (taxonomies, occupancy, height, age, value), hazard intensity footprints, vulnerability functions and **insured penetration** for a specified peril/geography/window, all with licence/source/version/CRS and holdout evidence.
5. Only then build an explicitly **synthetic** carrier portfolio scenario preserving marginal totals, with uncertainty, gross-to-net contracts and 10,000-year joint simulations. Never label synthetic allocations as observed insurer buildings.

These scripts deliberately complement (not overlap files in) open source/building PRs #900–#904 and NFIP preflight #898.
