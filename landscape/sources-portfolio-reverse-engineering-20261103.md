<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-portfolio-reverse-engineering-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-portfolio-reverse-engineering-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission discovery of original insurer-level reporting, statutory schedules, aggregate insurance market and company-level CAT risk disclosures to constrain probabilistic synthetic portfolio reconstructions. Dataset terms, scientific suitability, original bytes and model access are separate gates.

**Entries:** 8

## Allianz 2025 group and regulated legal-entity SFCR disclosures

**Candidate ID:** `allianz.group-solo.sfcr.2025`  
**Provider:** Allianz SE / regulated operating entities  
**Categories:** `insurance`, `solvency`, `financial_reporting`, `legal_entity`, `premium`  
**Spatial scope:** Allianz group and European Solvency-II-regulated legal entities; not all countries of underlying insured locations  
**Temporal scope:** Financial year 2025; insurer-/group-specific publication dates during 2026  
**Resolution / granularity:** Group and solo SFCR annual reports containing public QRT tables S.05.01 (LoB), S.04.05 (country as defined), solvency/capital and group-perimeter information where published  
**Potential roles:** `company_lob_premium_constraint`, `individual_insurer_group_reconciliation`, `group_legal_entity_portfolio_boundary`, `published_technical_risk_context`  
**Access hint:** `public_company_report_links_individual_pdf_or_files_original_sha_and_rights_pending`  
**Authoritative source:** <https://www.allianz.com/en/investor_relations/results-reports/sfcr.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Actual provider SFCR publication pages, distinct from already registered EIOPA country aggregate statistics. Underwriting country, country-of-risk and cedant-domicile reporting may differ. Do not sum consolidated group and solo records, mix IFRS with Solvency II, or treat technical provisions/SCR as insured TIV. Exact original legal-entity report, data year, template version and rights review are required before acquisition.

## APRA quarterly general insurance industry performance statistics through June 2026

**Candidate ID:** `au.apra.general-insurance-industry-statistics.2026q2`  
**Provider:** Australian Prudential Regulation Authority (APRA)  
**Categories:** `insurance`, `market_statistics`, `premiums`, `state`, `nonlife`, `australia`  
**Spatial scope:** Australian general insurance industry; class-of-business and state dimensions where provided  
**Temporal scope:** September 2023 through June 2026 under current framework; published 2026-08-27  
**Resolution / granularity:** Industry-level XLSX database with financial performance, capital, class and state summaries  
**Potential roles:** `australia_nonlife_market_prior`, `state_lob_aggregate_benchmark`, `national_insurance_penetration_sanity_check`  
**Access hint:** `public_industry_spreadsheet_and_specification_company_institutional_level_on_hiatus_rights_review_pending`  
**Authoritative source:** <https://www.apra.gov.au/news-and-publications/quarterly-general-insurance-performance-statistics>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** APRA says current institutional-level general-insurance statistics are on hiatus pending confidentiality consultation. This current product is industry aggregate, NOT company-level 2025 rows; do not infer individual carrier portfolios or assume historical pre-2023 reporting definitions are compatible.

## Bank of England 2025 annual UK Solvency insurance aggregate statistics

**Candidate ID:** `uk.boe.solvency-insurance-annual-aggregate.2025`  
**Provider:** Bank of England / Prudential Regulation Authority  
**Categories:** `insurance`, `solvency`, `market_statistics`, `uk`, `nonlife`, `regulatory`  
**Spatial scope:** UK-authorised insurers and third-country branches in the reporting cohort  
**Temporal scope:** 2025 annual reference year; bank insurance taxonomy 2.0.1 applicable from year-end 2024  
**Resolution / granularity:** Public aggregated QRT-based yearly CSV of insurance sector financial and solvency statistics  
**Potential roles:** `uk_insurance_market_benchmark`, `nonlife_solvency_macro_prior`, `uk_regulatory_taxonomy_interoperability_check`  
**Access hint:** `public_aggregated_csv_download_taxonomy_notes_and_rights_review_pending`  
**Authoritative source:** <https://www.bankofengland.co.uk/statistics/insurance-aggregate-annual-data-report>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** BoE notes individual insurer reporting is aggregated for confidentiality; do not mislabel these industry series as firm-level QRT, and do not assume EU 2023 EIOPA template semantics remain unchanged after UK Insurance Taxonomy 2.0.1.

## Florida OIR Market Intelligence Reports residential company and county/ZIP research exports

**Candidate ID:** `us.fl.oir.mir.company-region.2025`  
**Provider:** Florida Office of Insurance Regulation  
**Categories:** `insurance`, `homeowners`, `company_market_statistics`, `zip`, `premium`, `exposure`  
**Spatial scope:** Florida personal and commercial residential property insurance by selected carrier, policy type, county and ZIP, depending on report selectors  
**Temporal scope:** Monthly from January 2025; insurer resubmissions can change extracts  
**Resolution / granularity:** Dynamic and customisable reported company/policy geography reports including policy stock, premium and selected wind-structure exposure; exact cell definitions/export must be independently checked  
**Potential roles:** `insurer_state_lob_observation`, `carrier_county_zip_reconciliation`, `regional_property_risk_prior`, `named_hurricane_covered_value_calibration`  
**Access hint:** `public_interactive_excel_export_original_query_filters_access_and_rights_review_pending`  
**Authoritative source:** <https://qsrng.floir.gov/Reports/ReportCriteriaWizard.aspx>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Existing Florida state-level data on isolated research Neon branch do not prove full original company x county x ZIP files are acquired. OIR explicitly says reports are not audited and can change after company resubmission. Record as-of, original query selectors, insurer reporting population, suppressed amounts and source SHA; no implicit portfolio admission.

## NAIC licensed individual insurance annual statement datasets and Schedules T/F/P/Y

**Candidate ID:** `us.naic.pc-statutory-individual-schedules`  
**Provider:** National Association of Insurance Commissioners (NAIC)  
**Categories:** `insurance`, `financial_statements`, `reinsurance`, `claims_development`, `state`, `legal_entity`  
**Spatial scope:** US licensed insurance legal entities and state/carrier statutory reports; varies by schedule  
**Temporal scope:** Licensed multi-year annual statement products; exact vintage, form and statement year required  
**Resolution / granularity:** Individual carrier Schedule T state premiums, Schedule F property reinsurance, Schedule P line loss development, Schedule Y organizational and affiliate transactions; supplemental policy exhibits  
**Potential roles:** `us_carrier_state_lob_crosswalk`, `ceded_reinsurance_structure_research`, `company_reserving_calibration`, `official_regulatory_group_membership`  
**Access hint:** `fee_licence_for_individual_statement_data_access_and_derivative_rights_negotiation_required`  
**Authoritative source:** <https://content.naic.org/prod_serv_idp_info_pro.htm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Different product from freely published NAIC P&amp;C market share report already listed in the register. NAIC offers individual financial statement schedules for license; no free bulk entitlement, no redistribution assumption and no sourcing of secret statutory records. Preserve gross/direct/net, return dates, group/company codes and exclusions.

## Texas DOI homeowners insured-value and policy-stock statewide market statistics 2025

**Candidate ID:** `us.tx.tdi.homeowners-market-stock.2025`  
**Provider:** Texas Department of Insurance (TDI)  
**Categories:** `insurance`, `homeowners`, `insured_value`, `policy_count`, `market_statistics`, `texas`  
**Spatial scope:** Texas homeowners policies under regulator's reported statistical plan  
**Temporal scope:** 2025 statewide preliminary observation, publication may be revised in 2026  
**Resolution / granularity:** Market snapshot includes total covered value, active policy count, average premium, direct written premium and company/group numbers  
**Potential roles:** `statewide_industry_tiv_constraint`, `homeowners_policy_penetration_prior`, `insurance_entity_group_counts_crosscheck`  
**Access hint:** `public_html_aggregate_market_snapshot_definitions_vintage_and_rights_review_pending`  
**Authoritative source:** <https://www.tdi.texas.gov/general/texas-homeowners-insurance-market-overview.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Public 2025 market snapshot shows approximately USD 2.405tn reported homeowners total insured value and 8.23m active policies. This does not split by insurer per ZIP or identify building coordinates, does not itself infer risk coverage for all perils, and must not be conflated with original Texas ZIP policy-stock research.

## Texas TDI 2025 property and casualty statutory Page 14 premium/loss report by company

**Candidate ID:** `us.tx.tdi.pc-state-page14.2025`  
**Provider:** Texas Department of Insurance (TDI)  
**Categories:** `insurance`, `regulatory_market_statistics`, `nonlife`, `company`, `line_of_business`, `direct_premium`  
**Spatial scope:** Texas licensed property/casualty carriers and state direct business  
**Temporal scope:** Financial year ended 2025-12-31; official report editions 2016-2025 listed  
**Resolution / granularity:** Carrier x statutory class direct premiums, paid/incurred losses and company type; online ZIP/Excel and PDF product options  
**Potential roles:** `texas_company_lob_direct_premium_hard_constraint`, `state_carrier_market_share`, `carrier_2025_loss_context`  
**Access hint:** `public_state_page14_spreadsheet_pdf_file_identity_and_reuse_terms_review_pending`  
**Authoritative source:** <https://www.tdi.texas.gov/reports/report4.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Different from statewide homeowners covered-value aggregate and from the Texas ZIP by policy-class market-stock research. Direct written premium is pre-reinsurance; company/LOB financial rows are not insured building positions, premium-net reinsurance, or CAT-only losses. Verify exact NAIC name/code, statement basis and downloaded report asset.

## Zurich 2025 natural catastrophe AEL and 50/100-year PML by peril-region

**Candidate ID:** `zurich.group.cat-ael-pml.2025`  
**Provider:** Zurich Insurance Group  
**Categories:** `insurance`, `risk_disclosure`, `cat_model_output`, `ael`, `pml`, `peril_region`  
**Spatial scope:** Selected top material global peril regions for Zurich group; individual countries differ per peril footprint  
**Temporal scope:** Financial year 2025 with restated 2024 comparison following model changes  
**Resolution / granularity:** Annual report iXBRL natural catastrophe figures disclosing selected net AEL and annual aggregate 50/100-year PML with scope and exclusions  
**Potential roles:** `company_cat_net_ael_holdout`, `peril_region_pml_challenge`, `risk_transfer_reconciliation`, `portfolio_uncertainty_calibration`  
**Access hint:** `public_issuer_ixbrl_disclosure_source_scope_reuse_and_model_version_review_pending`  
**Authoritative source:** <https://www.zurich.com/-/media-assets/project/zurich/dotcom/sustainability/docs/ixbrl/ixbrl-viewer.htm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Published 2025 top-five AEL figures are NET after catastrophe reinsurance and exclude Farmers Re quota-share participation; a separate Farmers Re quota-share is disclosed, and Farmers Exchanges are not owned by Zurich. Net 50/100-year annual aggregate PMLs are not GUL, physical exposure sums, or a full exceedance probability curve. Changes in model, currency and reinsurance are distinct from changes in underlying exposure.
