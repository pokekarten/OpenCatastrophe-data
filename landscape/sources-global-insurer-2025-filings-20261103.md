<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-global-insurer-2025-filings-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-global-insurer-2025-filings-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission discovery of named global insurer and reinsurer FY2025 source filing product families that can constrain company-level synthetic portfolio calibration without assuming any confidential treaty, TIV or customer-level insured exposure.

**Entries:** 12

## American International Group 2025 Form 10-K

**Candidate ID:** `aig.annual-10k.2025`  
**Provider:** American International Group / U.S. Securities and Exchange Commission  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** AIG North American, international commercial and personal segments  
**Temporal scope:** Year ended 2025-12-31; filed 2026  
**Resolution / granularity:** Public U.S. annual report with commercial property, casualty, financial lines and specialty underwriting segment disclosures  
**Potential roles:** `north_america_and_international_company_prior`, `financial_line_not_cat_property_guard`, `company_segment_geography_constraints`  
**Access hint:** `public_sec_html_fair_access_terms_and_filing_exhibit_rights_review_pending`  
**Authoritative source:** <https://www.sec.gov/Archives/edgar/data/5272/000000527226000023/aig-20251231.htm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Separate held/sold business, property and business interruption, casualty, cyber and gross vs net. Operating across 200+ countries through network partners cannot be equated to 200+ separately insured risk location portfolios.

## AXA 2025 Universal Registration Document and annual report

**Candidate ID:** `axa.annual-universal-registration.2025`  
**Provider:** AXA Group  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Global group segments and legal entities; risk location only where disclosed  
**Temporal scope:** Financial year 2025; published 2026-03-20  
**Resolution / granularity:** Public group annual financial statements, segment/geographic reporting, reinsurance and CAT risk narratives; source figures by applicable reporting basis  
**Potential roles:** `global_company_segment_prior`, `property_casualty_financial_reconciliation`, `insurer_group_portfolio_constraint`  
**Access hint:** `public_official_issuer_report_pdf_source_bytes_and_reuse_terms_review_pending`  
**Authoritative source:** <https://www.axa.com/en/press/publications/2025-annual-report>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** AXA consolidated IFRS disclosures are not each licensed carrier book and not property TIV. Distinguish Life/Health from P&amp;C, entity and management segment, rate effects, and reinsurance assumptions.

## Chubb Limited 2025 Form 10-K

**Candidate ID:** `chubb.annual-10k.2025`  
**Provider:** Chubb Limited / U.S. Securities and Exchange Commission  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** North America, Overseas General and Global Reinsurance and other reportable segments  
**Temporal scope:** Year ended 2025-12-31; SEC filing 2026-02-27  
**Resolution / granularity:** Official SEC annual filing with P&amp;C, agricultural, overseas, and global reinsurance segment disclosures and risk factors  
**Potential roles:** `underwriting_segment_gwp`, `reinsurance_inward_vs_direct_role`, `regional_specialty_company_prior`  
**Access hint:** `public_sec_html_fair_access_terms_and_filing_exhibit_rights_review_pending`  
**Authoritative source:** <https://www.sec.gov/Archives/edgar/data/896159/000089615926000005/cb-20251231.htm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** P&amp;C written or earned premiums by business segment are not subnational physical risk locations. Reinsurance catastrophe XL only attaches after cedant deductible/attachment; a property-cat treaty notional is not assumed property TIV.

## Generali Germany 2025 solo company annual and SFCR reports

**Candidate ID:** `generali.germany.solo-reports.2025`  
**Provider:** Generali Deutschland AG / subsidiaries  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Germany domestic licensed insurance entities and their disclosed operations  
**Temporal scope:** Year ended 2025; reports available in 2026  
**Resolution / granularity:** Company-level P&amp;C and life annual accounts plus Solvency II solo risk/financial condition reports by German regulated entity  
**Potential roles:** `germany_single_carrier_lob_calibration`, `solo_vs_parent_group_reconciliation`, `solvency_legal_entity_constraint`  
**Access hint:** `public_legal_company_reports_pdf_rights_template_and_original_bytes_review_pending`  
**Authoritative source:** <https://www.generali.de/ueber-uns/zahlen-daten-fakten>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Do not aggregate different legally licensed carriers' premium, administrative entities and investment income as one property book. The 2025 Germany reports are separate from Generali Group global consolidated business.

## Hannover Re 2025 annual report and supplementary financial XLSX

**Candidate ID:** `hannoverre.annual-report-financial-supplement.2025`  
**Provider:** Hannover Rück SE  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Global assumed property/casualty and life/health reinsurance; operational territory where disclosed  
**Temporal scope:** Financial year ended 2025-12-31; published in 2026  
**Resolution / granularity:** Official annual report and financial supplement with global P&amp;C/L&amp;H reinsurance revenue and line/region financial breakdowns  
**Potential roles:** `reinsurer_worldwide_assumed_premium_prior`, `treaty_category_prior`, `retro_and_inward_risk_reconciliation`  
**Access hint:** `public_company_annual_report_financial_supplement_exact_asset_version_and_terms_review_pending`  
**Authoritative source:** <https://www.hannover-re.com/en/investors/results-and-reports/annual-report/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** IFRS 17 reinsurance revenue is not automatically gross written premium or sum insured. Distinguish direct specialty insurer business, assumed treaty business, related E+S legal entity accounting links and outward retrocession.

## Munich Re Group 2025 SFCR and published catastrophe accumulation model disclosure

**Candidate ID:** `munichre.group-sfcr.2025`  
**Provider:** Münchener Rückversicherungs-Gesellschaft AG  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Global reinsurance, Global Specialty Insurance and ERGO direct insurance; peril-region and legal-entity scopes differ  
**Temporal scope:** 2025 year-end; SFCR published 2026  
**Resolution / granularity:** Public group SFCR QRT, risk profile, country/nonlife group insurance and retained peril-region return-period information  
**Potential roles:** `reinsurer_inward_gross_net_constraint`, `cat_event_pml_holdout`, `ergo_primary_vs_reinsurance_split`, `group_counterparty_retro_context`  
**Access hint:** `public_original_group_sfcr_pdf_exact_release_license_and_table_review_pending`  
**Authoritative source:** <https://www.munichre.com/content/dam/munichre/contentlounge/website-pieces/documents/SFCR-Munich-Re-Group-2025.pdf/_jcr_content/renditions/original./SFCR-Munich-Re-Group-2025.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A 200-year Atlantic hurricane retained catastrophe risk metric is not underlying physical insured TIV, gross ground-up loss, or a revealed contract graph. ERGO is a primary insurance business whereas reinsurance assumes cedants' portfolios; prevent duplicate contributions in group aggregation.

## QBE Insurance Group Annual Report 2025

**Candidate ID:** `qbe.group-annual-report.2025`  
**Provider:** QBE Insurance Group Limited  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Australia Pacific, North America and International incl QBE Re and Lloyd's  
**Temporal scope:** Calendar year ended 2025-12-31; published 2026  
**Resolution / granularity:** Official signed report including segment GWP, net insurance revenue, product and disaster loss disclosures, and statutory vs management basis reconciliation  
**Potential roles:** `australia_us_international_company_prior`, `crop_specialty_reinsurance_scope`, `group_segment_bridge`  
**Access hint:** `public_signed_pdf_original_sha_and_issuer_data_use_rights_pending`  
**Authoritative source:** <https://www.qbe.com/media/qbe/group/document-listing/2026/02/19/21/01/2025-qbe-annual-report---with-signatures(11277941).pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** QBE reporting warns management financial measures need reconciliation to statutory figures. North American crop, International reinsurance, direct P&amp;C, financial lines and non-CAT business must not be counted as a single CAT insured asset class.

## RenaissanceRe Holdings Limited 2025 Form 10-K

**Candidate ID:** `renaissancere.form10k.2025`  
**Provider:** RenaissanceRe Holdings Limited / SEC  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Global property catastrophe and other property reinsurance, casualty and specialty  
**Temporal scope:** Year ended 2025-12-31; filed 2026-02-11  
**Resolution / granularity:** Public 10-K segment gross premiums and reinsurance business structure; separate property vs casualty/specialty disclosures  
**Potential roles:** `global_reinsurer_property_cat_premium_prior`, `treaty_excess_of_loss_model_prior`, `risk_transfer_layering_context`  
**Access hint:** `public_issuer_10k_html_access_rights_original_version_review_pending`  
**Authoritative source:** <https://investor.renre.com/reports-filings/sec-filings/content/0000913144-26-000012/rnr-20251231.htm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** 2025 property business includes cat and other property reinsurance; property segment gross premium is NOT pure CAT premium. The disclosed company business is assumed risk from cedants, not a direct asset inventory.

## SCOR SE 2025 Universal Registration Document

**Candidate ID:** `scor.2025-universal-registration-document`  
**Provider:** SCOR SE  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Global group reinsurance business including P&amp;C and life/health  
**Temporal scope:** Financial year 2025; ESEF universal registration document filed 2026-03-13  
**Resolution / granularity:** ESEF consolidated financial annual statements and segment/risk/reinsurance disclosures  
**Potential roles:** `scor_property_casualty_reinsurance_prior`, `group_annual_financial_constraints`, `cat_risk_development_research`  
**Access hint:** `public_issuer_esef_filing_announcement_original_assets_and_licensing_review_pending`  
**Authoritative source:** <https://www.scor.com/en/press-release/scor-se-announces-availability-its-2025-universal-registration-document>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Filing announcement is an original pointer; requires fetching actual ESEF report and identifying exact tables and taxonomy. Group annual report does not reveal individual treaties, cedant assets, or insured CAT exposure.

## Suncorp Group FY2025 annual report

**Candidate ID:** `suncorp.group-fy2025-annual-report`  
**Provider:** Suncorp Group Limited  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Australian general insurance group with AAMI/GIO/Shannons and other brands; entity carrier mapping requires official records  
**Temporal scope:** Fiscal year ended 2025-06-30, not 2025-12-31  
**Resolution / granularity:** Official general insurer annual performance, personal and commercial portfolio GWP and gross/net weather-event cost reporting  
**Potential roles:** `australia_home_motor_lob_market_prior`, `carrier_brand_group_reconciliation`, `weather_cat_loss_holdout_candidate`  
**Access hint:** `public_original_issuer_pdf_fy_label_scope_and_rights_review_pending`  
**Authoritative source:** <https://www.suncorpgroup.com.au/assets/documents/suncorpgroup/fy25-suncorp-annual-report-final-public.pdf>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** FY25 ends June 2025 and is not commensurate with calendar-year 2025 company reports without a period bridge. Brand vs legal carrier and prior sales of bank/life businesses must be reconciled.

## Swiss Re Annual Report 2025

**Candidate ID:** `swissre.annual-report.2025`  
**Provider:** Swiss Re Ltd  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Worldwide P&amp;C Re, Corporate Solutions and Life &amp; Health Re with distinct legal and capital perimeters  
**Temporal scope:** Year ended 2025-12-31; report published 2026  
**Resolution / granularity:** Official group annual financial and risk reporting by P&amp;C Re, Corporate Solutions, L&amp;H Re; contains NATCAT burden and solvency disclosures  
**Potential roles:** `reinsurer_primary_vs_assumed_separation`, `global_cat_loss_holdout`, `company_segment_and_sst_context`  
**Access hint:** `public_issuer_annual_report_original_file_version_attribution_and_rights_review_pending`  
**Authoritative source:** <https://www.swissre.com/investors/annual-report-2025.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Swiss Re P&amp;C Re and Corporate Solutions contain different risk-bearing contracts; 2025 net catastrophe claims are not loss catalogues or source-specific event footprints. Swiss Solvency Test and IFRS 17 bases are distinct.

## Tokio Marine Holdings FY2025 group and major-subsidiary financial supplements

**Candidate ID:** `tokiomarine.fy2025-ir-supplement`  
**Provider:** Tokio Marine Holdings, Inc.  
**Categories:** `insurance`, `company_report`, `underwriting`, `financial_reporting`, `risk_profile`  
**Spatial scope:** Japan, North America, International operating subsidiaries; fiscal-year and segment convention differ  
**Temporal scope:** Fiscal year 2025 ends March 2026; IR call 2026-05-20 with Jun/Aug 2026 restatements  
**Resolution / granularity:** Official FY2025 results presentation and group IFRS/major subsidiary supplemental Excel/financial summaries  
**Potential roles:** `japan_group_subsidiary_underwriting_prior`, `north_america_japan_business_mix`, `restated_financial_vintage_check`  
**Access hint:** `public_investor_results_xlsx_pdf_restated_version_exact_asset_rights_pending`  
**Authoritative source:** <https://www.tokiomarinehd.com/en/ir/event/presentation/2025/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher explicitly identifies subsequent June and August 2026 restatements to some IFRS performance metrics. Preserve each vintage and distinguish asset allocation/AUM from insurance exposure or TIV; FY2025 is not calendar 2025.
