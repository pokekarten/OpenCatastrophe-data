<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-global-insurance-ils-mga-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-global-insurance-ils-mga-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission discovery of original company-, syndicate-, MGA-, reinsurance- and ILS-facing public source products needed to calibrate data-grounded synthetic risk portfolios. Existing EIOPA, OECD SDMX, GLEIF and national regulator identity registers remain canonical elsewhere; this shard does not admit source bytes or commercial extraction.

**Entries:** 10

## Artemis catastrophe bond and ILS deal directory

**Candidate ID:** `artemis.cat-bond-ils.deal-directory.2026`  
**Provider:** Artemis.bm  
**Categories:** `insurance`, `ils`, `cat_bonds`, `reinsurance`, `transaction_reference`  
**Spatial scope:** Global issuance with strong concentration in disclosed catastrophe markets; deal-specific territories  
**Temporal scope:** Historical issue list since the 1990s; dynamic transaction table checked 2026-11-03  
**Resolution / granularity:** Public deal-page issuer, sponsor/cedent, covered perils and territories, size, currency and issue date; transaction disclosure varies  
**Potential roles:** `ils_transaction_discovery`, `cedent_ils_counterparty_bridge`, `peril_region_cover_constraint`, `public_cat_bond_size_benchmark`  
**Access hint:** `public_html_research_only_no_bulk_api_or_redistribution_rights_established`  
**Authoritative source:** <https://www.artemis.bm/deal-directory/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Specialist third-party directory rather than original securities filings. Verify issued versus announced/settled status and exact as-of timestamp; a bond notional is not insured TIV, underlying event loss or an investor fund's holdings. Rights, automated extraction and re-publication remain blocked until publisher terms are checked; resolve deals against official issuer filings and sponsors.

## BMA insurance registration statistics September 2026

**Candidate ID:** `bm.bma.insurance-registration-statistics.2026m09`  
**Provider:** Bermuda Monetary Authority  
**Categories:** `insurance`, `reinsurance`, `regulatory_market_statistics`, `captives`, `ils`  
**Spatial scope:** Bermuda registered insurers, reinsurers and related market categories  
**Temporal scope:** Monthly files, September 2026 edition published 2026-10-19  
**Resolution / granularity:** Regulatory reporting-level counts and registration categories; exact file tables and historical comparability require review  
**Potential roles:** `bermuda_reinsurance_market_context`, `insurance_entity_census_crosscheck`, `ils_spv_market_structure_reference`  
**Access hint:** `public_official_document_download_asset_identity_and_terms_review_pending`  
**Authoritative source:** <https://www.bma.bm/documents-centre/statstics/documents-insurance>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Different from the already registered BMA regulated-entity directory: this is the periodic insurance registration statistics product. The landing page lists a September 2026 publication. Counts are not company-level gross exposure, total placed capacity or claims; avoid conflating special-purpose insurance entities with traditional reinsurers.

## Ontario FSRA P&amp;C insurer-MGA relationships 2023 review

**Candidate ID:** `ca.fsra.ontario.mga-pc-market-review.2023`  
**Provider:** Financial Services Regulatory Authority of Ontario (FSRA)  
**Categories:** `insurance`, `mga`, `delegated_authority`, `premiums`, `regulatory_market_research`  
**Spatial scope:** Ontario, Canada P&amp;C insurers and contracted MGAs in surveyed population  
**Temporal scope:** 2023 business reference year; official retrospective published in 2024  
**Resolution / granularity:** Survey aggregates of insurer-MGA relationships, delegated P&amp;C direct premiums and policy counts; not names of all individual contracting pairs  
**Potential roles:** `mga_market_penetration_benchmark`, `insurer_mga_delegation_rate_prior`, `synthetic_mga_premium_weight_calibration`  
**Access hint:** `public_regulator_report_download_not_original_questionnaire_or_counterparty_level`  
**Authoritative source:** <https://www.fsrao.ca/industry/property-and-casualty-and-general-insurance/publications>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Regulatory survey provides observed MGA premium/relationship scale for a bounded Ontario calibration. Insurers supplied responses and the regulator did not independently verify all survey figures. Avoid extrapolating this market share to every country or translating MGA-sourced written premium into MGA-retained CAT exposure. Publication-year/version and rights review pending.

## FINMA insurance market report 2025

**Candidate ID:** `ch.finma.insurance-market-report.2025`  
**Provider:** Swiss Financial Market Supervisory Authority (FINMA)  
**Categories:** `insurance`, `reinsurance`, `premiums`, `market_share`, `regulated_groups`  
**Spatial scope:** Swiss direct life, non-life and reinsurance market, including Swiss operations of selected branches  
**Temporal scope:** Financial year 2025; report updated 2026-08-20  
**Resolution / granularity:** Official insurer market-share tables and premiums by sector, with report-specific entity labels and CHF units  
**Potential roles:** `swiss_insurer_market_share_prior`, `company_synthetic_gwp_constraint`, `switzerland_nonlife_lob_context`  
**Access hint:** `public_regulator_pdf_report_terms_exact_file_sha_and_table_extraction_pending`  
**Authoritative source:** <https://www.finma.ch/en/documentation/finma-publications/reports/insurance-reports/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from the existing FINMA insurer-group authorisation registry. Market share and GWP refer to defined Swiss business sectors, not worldwide group exposure or building-level insured value. Match legal entities to GLEIF separately, preserve reporting sector and fiscal year; check PDF table extraction and current merger history before use.

## ECB ICO Insurance Corporations Operations statistics

**Candidate ID:** `ecb.ico.insurance-operations.sdmx`  
**Provider:** European Central Bank (ECB)  
**Categories:** `insurance`, `reinsurance`, `premiums`, `claims`, `sdmx`, `euro_area`  
**Spatial scope:** Euro area resident insurance corporations; separate euro area, country and company-type aggregations by series  
**Temporal scope:** Published time-series; exact observations and releases must be pinned at extraction  
**Resolution / granularity:** SDMX2.1 CSV dataset ICO with premiums, claims and acquisition expenses across life, non-life, reinsurance and composite company types  
**Potential roles:** `euro_area_reinsurance_premium_scale`, `nonlife_company_type_market_benchmark`, `gross_net_macro_sanity_check`  
**Access hint:** `public_ecb_sdmx21_csv_dataflow_version_and_terms_review_pending`  
**Authoritative source:** <https://data.ecb.europa.eu/methodology/insurance-corporations>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ECB ICO is a separate statistical data product from the already registered EIOPA Solvency II statistics; underlying supervisory data may overlap and must not be treated as independent observations. It is aggregate market data, not risk locations, group ownership or company-level treaty details. Keep frequency, residency basis, unit and valuation conventions.

## Lloyd's market directory: coverholders, agents and active syndicates 2026

**Candidate ID:** `lloyds.market-directory.coverholders.2026`  
**Provider:** Lloyd's of London  
**Categories:** `insurance`, `mga`, `coverholder`, `syndicate`, `delegated_authority`, `entity_registry`  
**Spatial scope:** Lloyd's international market participants; actual legal/territorial permissions differ by record  
**Temporal scope:** Live directory and active 2026 year-of-account syndicate list  
**Resolution / granularity:** Searchable coverholder/agent/broker/management records and active syndicate identifiers; classes of business vary by entity  
**Potential roles:** `mga_coverholder_entity_discovery`, `syndicate_managing_agent_crosswalk`, `delegated_underwriting_business_class_prior`  
**Access hint:** `public_interactive_directory_no_bulk_automated_reuse_rights_established`  
**Authoritative source:** <https://www.lloyds.com/market-resources/market-directory>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Lloyd's directory distinguishes coverholder, broker, managing agent, syndicate and open market correspondent; these roles must not be collapsed into insurance carriers. A coverholder's authorisation does not disclose binding authority limit, cedent allocation or actual insured risks. Match identities and effective dates; verify browser export/automation terms.

## Lloyd's Statistics Insights Hub market and syndicate dashboards

**Candidate ID:** `lloyds.statistics.insights-hub`  
**Provider:** Lloyd's of London  
**Categories:** `insurance`, `reinsurance`, `syndicate`, `market_statistics`, `capital`, `premium`  
**Spatial scope:** Lloyd's market and active syndicates by class of business  
**Temporal scope:** Historical and current data, accessed product by product  
**Resolution / granularity:** Market Profile premiums/claims, Financial Performance syndicate statements and Capital Explorer syndicate capacity; data access requires sign-up  
**Potential roles:** `syndicate_class_premium_prior`, `reinsurance_treaty_capacity_context`, `synthetic_syndicate_business_mix_benchmark`  
**Access hint:** `insights_hub_signup_access_permissions_export_rights_pending`  
**Authoritative source:** <https://www.lloyds.com/market-resources/insights-hub/statistics>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Market Profile, Financial Performance and Capital Explorer are distinct named products behind an access workflow, not an open raw data dump. Do not claim automatic API or commercial bulk rights. Capacity is not insured sum, premiums do not identify CAT geography and related public syndicate accounts may overlap.

## Lloyd's 2025 syndicate annual reports and accounts with iXBRL

**Candidate ID:** `lloyds.syndicate-annual-accounts.2025`  
**Provider:** Lloyd's of London and individual syndicate managing agents  
**Categories:** `insurance`, `reinsurance`, `syndicate`, `financial_reporting`, `ixbrl`, `premiums`  
**Spatial scope:** Individual Lloyd's syndicates, with geography/line detail only where voluntarily disclosed  
**Temporal scope:** 2025 annual year ended 2025-12-31, individual publication dates in 2026  
**Resolution / granularity:** Public syndicate-level gross and net premiums, reinsurance, claims and business/financial disclosures in HTML, PDF or iXBRL depending on record  
**Potential roles:** `syndicate_gross_net_premium_calibration`, `ceded_reinsurance_context`, `public_cat_loss_challenge`, `managing_agent_identity_join`  
**Access hint:** `public_individual_syndicate_reports_ixbrl_scope_disclaimer_and_terms_review_pending`  
**Authoritative source:** <https://www.lloyds.com/syndicatereports>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Regulator/reporting-scope data provide individual-syndicate calibration beyond country averages. The issuer notes that iXBRL tagging is not covered by the audited financial statement opinions, so numerical extracts must be reconciled to signed accounts. Business class geography, gross/net and reported CAT losses are not ground-up event loss catalogs or actual treaty towers.

## OECD Global Insurance Market Trends 2026 report

**Candidate ID:** `oecd.global-insurance-market-trends.2026`  
**Provider:** Organisation for Economic Co-operation and Development (OECD)  
**Categories:** `insurance`, `market_statistics`, `premium`, `claims`, `cross_country`, `benchmark`  
**Spatial scope:** 67 jurisdictions in 2026 edition according to full report, including OECD and selected non-OECD markets  
**Temporal scope:** Published 2026-11-02 on 2025 insurance market performance  
**Resolution / granularity:** Published country/jurisdiction analyses of premium growth, penetration, claims and business composition; derived from OECD GIS data  
**Potential roles:** `global_market_2025_vintage_benchmark`, `country_nonlife_penetration_constraint`, `market_coverage_gap_diagnostics`  
**Access hint:** `public_report_data_tables_and_reuse_scope_exact_vintage_review_pending`  
**Authoritative source:** <https://www.oecd.org/en/publications/global-insurance-market-trends-2026_c8be6585-en.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Complement to the already registered OECD DSD_INS SDMX class and underwriting dataflows, not an independent alternative source of underlying reported numbers. Preserve 2025 reference year, 2026 publication vintage, jurisdiction coverage and indicators; note that report-wide penetration includes life and non-life and cannot be converted directly into property CAT premium.

## MAS Singapore insurer-level annual insurance company returns

**Candidate ID:** `sg.mas.insurance-company-returns.2025`  
**Provider:** Monetary Authority of Singapore (MAS)  
**Categories:** `insurance`, `reinsurance`, `insurer_financials`, `legal_entity`, `premiums`, `asia`  
**Spatial scope:** Singapore incorporated insurers and licensed branches, including inward/outward reinsurance participants  
**Temporal scope:** Annual company reporting; selected 2025 filings where currently published, differing fiscal year ends and revisions  
**Resolution / granularity:** Company-code and insurer-name indexed links to annual life and general insurance returns, with insurer-specific financial line items  
**Potential roles:** `singapore_reinsurer_entity_and_branch_crosswalk`, `company_nonlife_premium_priors`, `regional_insurance_market_anchor`  
**Access hint:** `public_individual_company_returns_download_terms_as_of_and_original_asset_review_pending`  
**Authoritative source:** <https://www.mas.gov.sg/statistics/insurance-statistics/insurance-company-returns>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Company-level reporting is far more useful for a synthetic portfolio than market totals. MAS warns that insurer-attributed content may be amended and not all companies have filed by the same date. Distinguish branch vs locally incorporated entity, life vs P&amp;C vs reinsurance and Singapore vs worldwide business. Review terms and preserve original file, company code, period and currency.
