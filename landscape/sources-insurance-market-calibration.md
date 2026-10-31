<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-insurance-market-calibration.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-insurance-market-calibration.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-10-31`  
**Purpose:** Non-admission discovery registry of official insurance legal-entity identifiers and national/regional market benchmark data needed to calibrate synthetic insurer and reinsurer CAT portfolios.

**Entries:** 7

## EIOPA Register of Insurance Undertakings

**Candidate ID:** `eiopa.register.insurance-undertakings`  
**Provider:** European Insurance and Occupational Pensions Authority (EIOPA)  
**Categories:** `insurance`, `insurer_entity_registry`, `regulation`, `legal_entity`, `lei`, `cross_border`  
**Spatial scope:** EU/EEA insurance undertakings and notified cross-border operations; national registers have authoritative precedence  
**Temporal scope:** EIOPA states updates weekly on Fridays; extract must pin capture timestamp and actual registration dates  
**Resolution / granularity:** public CSV/Excel table of insurer name, NCA, home country, identifiers, LEI if supplied, cross-border country, authorisation, start/end dates and status  
**Potential roles:** `insurer_entity_discovery`, `lei_entity_crosswalk`, `country_operating_presence`, `synthetic_insurer_portfolio_universe`  
**Access hint:** `public_export_csv_excel_browser_workflow_terms_review_pending`  
**Authoritative source:** <https://register.eiopa.europa.eu/registers/register-of-insurance-undertakings>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is a register of authorised legal entities and cross-border operations, not property risk locations or market shares; subsidiaries and cross-border rows must not be counted as independent groups. The EIOPA page says national NCA records prevail on discrepancies; preserve identification-code namespace, LEI missingness, home versus host country, registration validity and extraction date. Public CSV access does not itself clear automated harvesting or redistribution.

## GLEIF Global LEI Index Level 1 and Level 2 corporate relationships

**Candidate ID:** `gleif.global-lei-index.level1-level2`  
**Provider:** Global Legal Entity Identifier Foundation (GLEIF)  
**Categories:** `insurance`, `legal_entity`, `lei`, `corporate_hierarchy`, `global_registry`, `entity_resolution`  
**Spatial scope:** global cross-sector LEI holders, not limited to insurers  
**Temporal scope:** continuously updated; Golden Copy and delta files published up to three times daily  
**Resolution / granularity:** LEI Level 1 identity records and Level 2 direct/ultimate accounting-consolidating parent relationships with reporting exceptions; API, full-file and delta access  
**Potential roles:** `insurer_group_deduplication`, `reinsurer_entity_resolution`, `parent_subsidiary_hierarchy`, `multi_source_company_join`  
**Access hint:** `public_api_golden_copy_delta_download_rights_review_pending`  
**Authoritative source:** <https://www.gleif.org/en/lei-data/access-and-use-lei-data/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** LEI identifies legal entities, not insured assets. The Level 2 parent link is accounting-consolidation based and can be absent or exception-reported; do not infer missing links or beneficial ownership. Preserve LEI, record status, effective dates, relationship type, exception, source vintage, mapping confidence and original identifiers. Review official data licensing and file/API terms before ingestion.

## EIOPA Solvency II aggregated insurance statistics to 2026 Q2

**Candidate ID:** `eiopa.solvency2.aggregate-insurance-statistics.2026q2`  
**Provider:** European Insurance and Occupational Pensions Authority (EIOPA)  
**Categories:** `insurance`, `market_statistics`, `premiums`, `claims`, `capital`, `solvency`, `europe`  
**Spatial scope:** European Economic Area with country-level aggregates for solo/group insurance undertakings  
**Temporal scope:** quarterly solo 2016 Q3 through 2026 Q2 and annual through 2025; group series follow their own publication schedule  
**Resolution / granularity:** CSV/XLSX aggregates for premiums, claims and expenses (S.05.01), own funds/SCR (S.23.01), balance sheet (S.02.01), investment asset exposures (S.06.02); solo/group, quarter/year, country, measure  
**Potential roles:** `nonlife_market_premium_benchmark`, `country_lob_calibration`, `portfolio_size_constraints`, `reinsurance_capital_context`  
**Access hint:** `public_csv_xlsx_country_aggregates_terms_review_pending`  
**Authoritative source:** <https://www.eiopa.europa.eu/tools-and-data/insurance-statistics_en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Latest page update observed 2026-10-12; quarterly values can be provisional and revised. These are aggregated reporting data, NOT individual insurer premium, geographic CAT exposure, claim triangles, or catastrophe insured loss. Never sum solo and group observations or mix provisional and final series; retain currency, measure code, reporting basis, frequency, country, year, publication vintage and Solvency II QRT definitions.

## EIOPA Solvency II cross-border insurance premiums 2023-2025

**Candidate ID:** `eiopa.solvency2.cross-border-premiums.2025`  
**Provider:** European Insurance and Occupational Pensions Authority (EIOPA)  
**Categories:** `insurance`, `cross_border`, `nonlife`, `premiums`, `market_statistics`, `europe`  
**Spatial scope:** EEA with cross-border reporting jurisdiction and country breakdown; contract-signing vs risk-location semantics depend on business class  
**Temporal scope:** annual series 2023 through 2025; earlier series provided separately  
**Resolution / granularity:** XLSX aggregated annual Solvency II solo cross-border premiums by country with publication metadata  
**Potential roles:** `home_host_market_crosswalk`, `country_portfolio_allocation_constraint`, `nonlife_cross_border_premium_benchmark`  
**Access hint:** `public_xlsx_aggregates_separate_series_and_rights_review_pending`  
**Authoritative source:** <https://www.eiopa.europa.eu/tools-and-data/insurance-statistics_en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Do not equate insurance premium booking jurisdiction, insurer domicile and physical location of the CAT risk. Preserve country role, branch/FOS reporting basis, business class, period, value, currency and coverage, and avoid double counting underlying domestic/group totals. Public annual series is not per-risk geocoded insurance exposure.

## OECD Insurance business written by class of insurance (DSD_INS@DF_CLASSES)

**Candidate ID:** `oecd.insurance.dsd-ins-df-classes.v1`  
**Provider:** Organisation for Economic Co-operation and Development (OECD)  
**Categories:** `insurance`, `insurance_class`, `premium`, `market_statistics`, `international`, `sdmx`  
**Spatial scope:** OECD and participating non-OECD reporting jurisdictions; country coverage varies by series  
**Temporal scope:** annual historical country series, latest available year varies; OECD Data Explorer page updated 2025-12-08 at source review  
**Resolution / granularity:** OECD SDMX 1.0 dataflow DSD_INS@DF_CLASSES: insurance class, gross written premium metrics, country, accounting basis, currency, year  
**Potential roles:** `country_peril_lob_premium_constraint`, `nonlife_insurance_class_benchmark`, `cross_country_synthetic_portfolio_weights`  
**Access hint:** `public_oecd_sdmx_rest_series_export_terms_and_api_limits_review_pending`  
**Authoritative source:** <https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.DAF.CM&df%5Bds%5D=dsDisseminateFinalDMZ&df%5Bid%5D=DSD_INS%40DF_CLASSES&df%5Bvs%5D=1.0&lc=en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Exact SDMX flow: OECD.DAF.CM,DSD_INS@DF_CLASSES,1.0; query structure metadata before selecting dimensions, then pin request, response format, release and date. Class-of-business premiums are not individual insurer exposure and cannot be disaggregated into peril- or building-specific insured values without explicit modelling assumptions. Preserve missing observations and reporting changes.

## OECD Premiums claims and expenses (DSD_INS@DF_UNDERWRITING)

**Candidate ID:** `oecd.insurance.dsd-ins-df-underwriting.v1`  
**Provider:** Organisation for Economic Co-operation and Development (OECD)  
**Categories:** `insurance`, `reinsurance`, `premium`, `claims`, `underwriting`, `market_statistics`, `sdmx`  
**Spatial scope:** OECD and reporting non-OECD jurisdictions with different historical coverage  
**Temporal scope:** annual historical series; latest year country/measure specific and dataflow page updated 2025-12-08 at source review  
**Resolution / granularity:** OECD SDMX dataflow DSD_INS@DF_UNDERWRITING covering direct and reinsurance-accepted premiums, ceded premiums, net premiums, gross claims, costs, ownership and location dimensions  
**Potential roles:** `country_reinsurance_cession_benchmark`, `insurance_market_loss_ratio_context`, `gross_net_premium_reconciliation`, `synthetic_reinsurer_market_size`  
**Access hint:** `public_sdmx_rest_statistics_with_versioned_dimensional_dictionary`  
**Authoritative source:** <https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.DAF.CM&df%5Bds%5D=dsDisseminateFinalDMZ&df%5Bid%5D=DSD_INS%40DF_UNDERWRITING&df%5Bvs%5D=1.0&lc=en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Exact SDMX flow OECD.DAF.CM,DSD_INS@DF_UNDERWRITING,1.0. Gross premiums, ceded premiums, accepted reinsurance and paid claims are distinct accounting measures; paid claims are NOT event-level CAT incurred insured losses and do not reveal contract attachment points. Pin denominator, reporting scope, units and revision dates before country comparisons. Check OECD service licence/API policy before storing source bytes.

## IAIS Global Insurance Market Report 2025 (public aggregate)

**Candidate ID:** `iais.global-insurance-market-report.2025`  
**Provider:** International Association of Insurance Supervisors (IAIS)  
**Categories:** `insurance`, `reinsurance`, `market_statistics`, `capital`, `retrocession`, `global`  
**Spatial scope:** globally pooled supervisory monitoring and selected markets; 58 jurisdictions participated in at least one sector-wide 2025 component  
**Temporal scope:** December 2025 report with sector and reinsurance metrics largely through year-end 2024  
**Resolution / granularity:** public PDF charts and aggregated tables covering reinsurance premiums, capital, retention, retrocession and industry-wide indicators; individual insurer submissions are confidential  
**Potential roles:** `global_reinsurance_market_scale_benchmark`, `retrocession_aggregate_context`, `industry_capital_stress_context`  
**Access hint:** `public_report_only_underlying_gme_individual_insurer_data_confidential`  
**Authoritative source:** <https://www.iais.org/uploads/2025/12/Global-Insurance-Market-Report-2025.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** IAIS 2025 public report uses confidential Individual Insurer Monitoring and Sector-Wide Monitoring submissions. Only publicly released aggregates may be researched after copyright review; do not infer the 57 insurer-level observations from report totals or fabricate group-specific treaty/retro placements. Distinguish 2024 observation period from 2025 publication and do not call the 2026 report released before its official publication.
