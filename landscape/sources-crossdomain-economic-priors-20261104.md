<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-crossdomain-economic-priors-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-crossdomain-economic-priors-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of complementary economic, trade, labour, property-price and agricultural data for data-grounded synthetic insurance exposure and indirect-loss research; source rights, scientific fitness and model-input approval remain unreviewed.

**Entries:** 5

## CEPII BACI bilateral product-level trade flows, release 202601

**Candidate ID:** `cepii.baci.hs6-trade.v202601`  
**Provider:** CEPII (Centre d'Etudes Prospectives et d'Informations Internationales)  
**Categories:** `trade`, `economic_dependencies`, `supply_chains`, `business_interruption`  
**Spatial scope:** Worldwide bilateral merchandise trade for approximately 200 reporting economies; individual insured facilities are not identified  
**Temporal scope:** Release 202601 updated 2026-01-30; coverage year varies by HS revision and reaches 2024  
**Resolution / granularity:** Annual exporter-importer-HS6 product flows, trade values and quantities, code lists; distinct HS92, HS96, HS02, HS07, HS12, HS17 and HS22 families  
**Potential roles:** `bilateral_product_dependency_prior`, `sector_supply_chain_calibration`, `trade_exposure_macro_challenge`  
**Access hint:** `public_large_hs_csv_etalab2_attribution_scope_review`  
**Authoritative source:** <https://www.international-economics.eu/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original CEPII page identifies version 202601 and Etalab 2.0. Exact files, derived disclosure scope and attribution still need admission review. Pin HS vintage and dictionaries. Verify trade-value units, currency, mirror-flow reconciliation, missing flows and revision semantics. Annual national trade does not identify physical suppliers, cargo routes, insured contracts, risk locations, TIV or contingent-business-interruption losses.

## OECD 2025 Inter-Country Input-Output tables, regular edition

**Candidate ID:** `oecd.icio.2025-regular`  
**Provider:** Organisation for Economic Co-operation and Development  
**Categories:** `economic_dependencies`, `input_output`, `supply_chains`, `industry_statistics`  
**Spatial scope:** Multiple economies and aggregate rest of world, with country and industry coverage defined by the regular release  
**Temporal scope:** 2025 release covers annual observations 1995-2022; historical methods and accounts can be revised  
**Resolution / granularity:** Country-industry intermediate-use, production, final-demand and cross-border monetary flows, distributed as period-specific CSV and method notes  
**Potential roles:** `sector_interdependency_matrix`, `indirect_business_interruption_prior`, `counterfactual_supply_chain_shock_challenge`  
**Access hint:** `public_publisher_csv_archives_exact_edition_and_reuse_review`  
**Authoritative source:** <https://www.oecd.org/en/data/datasets/inter-country-input-output-tables.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official portal distinguishes regular and extended ICIO, with different handling of firm heterogeneity. Pin release, country and industry codes, row orientation, valuation and price year, source archive and licence. Crosswalk of HS6 BACI to economic industries is many-to-many and must be validated. Monetary industry relationships are not observed plant-level supply contracts or insured contingent-business-interruption claims.

## ILOSTAT labour and sector employment bulk statistics

**Candidate ID:** `ilo.ilostat.bulk-sector-employment`  
**Provider:** International Labour Organization, Department of Statistics  
**Categories:** `employment`, `economy`, `industry_statistics`, `exposure_priors`  
**Spatial scope:** Global national and regional estimates; country, sector and population coverage differs across indicators  
**Temporal scope:** Historical annual and subannual series of varying vintages; exact indicator, reference year and download snapshot must be fixed  
**Resolution / granularity:** Bulk tables grouped by indicator or reference area, including employment by economic activity and official code lists, observations and missing-data flags  
**Potential roles:** `commercial_occupancy_prior`, `industry_workforce_weight_prior`, `business_interruption_sector_benchmark`  
**Access hint:** `public_bulk_indicator_and_refarea_download_exact_series_rights_review`  
**Authoritative source:** <https://ilostat.ilo.org/data/bulk/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Workforce counts are not factories, business locations, insured payroll or building occupancy observations. Preserve source, survey versus estimates, methodology flags, sex, age, unit, numerator and industry classification. Align ISIC revisions with selected OECD ICIO release. Commercial use and source-specific redistribution remain unreviewed.

## BIS residential and commercial property price statistical series

**Candidate ID:** `bis.property-prices.residential-commercial`  
**Provider:** Bank for International Settlements and national statistical source authorities  
**Categories:** `property_prices`, `valuation_proxies`, `macroeconomic_series`, `economic_stress`  
**Spatial scope:** Numerous jurisdictions with selected national and subnational coverage, different for each residential or commercial product  
**Temporal scope:** Quarterly and other frequencies across heterogeneous ranges; series-level vintage and country source must be pinned  
**Resolution / granularity:** Property price indices, changes and some level series in BIS Data Portal with CSV and SDMX bulk download options  
**Potential roles:** `property_price_trend_challenge`, `geographic_macro_valuation_stress`, `insured_value_inflation_context`  
**Access hint:** `public_bis_csv_sdmx_national_upstream_licence_and_series_review`  
**Authoritative source:** <https://data.bis.org/topics/RPP/data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Sale-price and appraisal indices are not construction-cost indices, replacement values or total insurable values. Preserve property subtype, index base, nominal versus real, region, national source, observation date and revisions. BIS and contributing national source rights require exact-source review before commercial redistribution or model use.

## FAOSTAT agriculture, production, livestock and trade statistical series

**Candidate ID:** `fao.faostat.agriculture-production`  
**Provider:** Food and Agriculture Organization of the United Nations  
**Categories:** `agriculture`, `crop_production`, `livestock`, `food_supply_chain`, `economic_exposure`  
**Spatial scope:** FAOSTAT covers more than 245 countries and territories; each domain varies by geography and reporting granularity  
**Temporal scope:** Historical observations extend back to 1961 in some domains; not all products or countries have all years and updated series  
**Resolution / granularity:** National and regional series for crop area, production, harvested volume, livestock, food supply and agricultural trade, via download and developer API portal  
**Potential roles:** `crop_production_allocation_prior`, `livestock_exposure_context`, `agricultural_supply_chain_challenge`  
**Access hint:** `public_statistical_download_api_some_auth_rights_exact_domain_review`  
**Authoritative source:** <https://www.fao.org/faostat/en/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Data are national or larger-area statistical aggregates, not geocoded farms or insured crop schedules. Record domain, commodity item, indicator element, unit, reporting quality flag, geographical code, exact observation and download date. Some new API endpoints require authentication. Do not infer insured sums or physical loss at a farm from harvested area, livestock or production tonnage.
