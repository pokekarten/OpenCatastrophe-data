<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-underused-property-valuation-market-20261105.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-underused-property-valuation-market-20261105.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-05`  
**Purpose:** Non-admission discovery of ten product-specific public property valuation, cadastral building crosswalk, construction-cost, insurer-distribution, historical exposure and post-disaster recovery data sources; original data bytes and actual insured exposures remain excluded.

**Entries:** 10

## New Zealand LINZ public National District Valuation Roll subset

**Candidate ID:** `nz.linz.dvr-public-subset.2026`  
**Provider:** Toitu Te Whenua Land Information New Zealand (LINZ)  
**Categories:** `property_valuation`, `cadastral_reference`, `residential_property`, `exposure_value_proxy`  
**Spatial scope:** New Zealand; only territorial authorities permitting public publication; not a complete national valuation roll  
**Temporal scope:** Public table updated weekly; official page last updated 2026-07-23 at source inspection  
**Resolution / granularity:** Non-spatial property valuation table with unit_of_property_id, valuation and property descriptors; approximately 287,243 publicly listed rows on inspected source page, dependent on current version and related LINZ tables  
**Potential roles:** `assessed_value_and_property_type_prior`, `property_spine_identifier_join_research`, `replacement_cost_vs_tax_valuation_challenge`  
**Access hint:** `public_partial_dvr_table_cc_by_4_claimed_by_provider_exact_field_terms_and_spatial_join_review_pending`  
**Authoritative source:** <https://data.linz.govt.nz/table/114085-nz-properties-national-district-valuation-roll/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher explicitly differentiates this public partial CC BY 4.0 table from government-only full National DVR. Owner/ratepayer information is excluded. The table itself has null/empty geometries, so a verified unit_of_property_id to separately licensed spatial table join is required before asset geolocation. Tax/rating value is not insured replacement cost, TIV, market value or actual carrier exposure; preserve authority participation/selection bias and valuation date. No raw records acquired or committed. Official NZ Property Boundaries layer 122657 contains unit_of_property_id; Property-Building Reference table 119620 joins unit_of_property_id to building_id; NZ Building Outlines layer 101290 contains that building_id. Each must be pinned to compatible vintages and checked for selection, null keys and one-to-many relations. The provider category listing was updated in late October 2026 with approximately 288K public DVR rows, while the detailed earlier source page listed 287,243 rows in July; the differing dates are not a real joined coverage estimate.

## Manitoba ROLL ENTRY assessed-property GIS layer

**Candidate ID:** `ca.mb.roll-entry.assessment.2026`  
**Provider:** Government of Manitoba / Manitoba Maps  
**Categories:** `cadastral_parcels`, `property_assessment`, `dwelling_units`, `geospatial_exposure_proxy`  
**Spatial scope:** Province of Manitoba, Canada; jurisdictional assessment coverage, not all Canada or a verified footprint inventory  
**Temporal scope:** Official Canada open-data record updated 2026-03-11; individual ASMT_ROLL valuation tax year and version vary by record  
**Resolution / granularity:** Parcel/roll boundaries and summary assessment fields, including municipality, civic/short legal address, DWELLING_UNITS, TOTAL_VALUE and assessment version; listed CSV, GeoJSON, GeoPackage and ArcGIS FeatureServer access  
**Potential roles:** `spatial_assessed_value_prior`, `dwelling_unit_density_and_parcel_join`, `parcel_to_building_cardinality_challenge`  
**Access hint:** `public_arcgis_geopackage_csv_openmb_license_named_by_provider_data_exemptions_and_privacy_review_pending`  
**Authoritative source:** <https://open.canada.ca/data/dataset/1cf8672a-2258-2917-0c8e-4cb8eb6401d9>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A ROLL ENTRY is an assessed-property or parcel unit, not one building, insured location or loss. TOTAL_VALUE is a tax-assessment measure, not replacement cost/TIV. The publisher describes a civic or legal-location field and parcel-like geometry: assess personal-data risk and record-level exclusions before any acquisition; no property-owner or policy inference. Verify the current ArcGIS service schema, geometry quality, rate-year versions and the dataset-specific rights statement. No third-party bytes stored. Canada open-data catalogue expressly names OpenMB Information and Data Use License. Government's official terms allow commercial reuse, adaptation and redistribution with attribution, but exempt personal information and unlicensed third-party rights. This is a source-rights ceiling, not project admission; civic address exposure and record-level PII need a separate documented review. Original FeatureServer identifies MG_ROLL_ENTRY_POLY geometry and EPSG:26914; metadata access is observed, but no live row/count query success was verified in this research.

## Eurostat quarterly construction producer price/cost index for new residential buildings

**Candidate ID:** `eu.eurostat.sts-copi-q.2026`  
**Provider:** Eurostat / European Commission  
**Categories:** `construction_cost`, `price_indices`, `replacement_cost_inflation_proxy`, `europe`  
**Spatial scope:** Reporting European countries with available Eurostat quarterly series; country-level, not city/building-level rates  
**Temporal scope:** Official quarterly series sts_copi_q, with source catalogue showing updates in October 2026 and historical coverage varying by country  
**Resolution / granularity:** Eurostat SDMX/CSV quarterly national index series for construction producer prices or costs of new residential buildings; associated view teiis510  
**Potential roles:** `residential_building_replacement_cost_escalation`, `cross_country_inflation_sensitivity`, `tiv_vintage_normalization_challenge`  
**Access hint:** `public_eurostat_sdmx_csv_country_frequency_unit_base_year_rights_review_pending`  
**Authoritative source:** <https://ec.europa.eu/eurostat/databrowser/view/sts_copi_q/default/table?lang=en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** An index of cost change is not an absolute EUR/m2 reconstruction price, per-building insured sum, actual claims inflation or non-residential cost series. Preserve units, base-year rebasings, seasonal adjustment, country gaps, residential NACE code and vintage when applying to separate independently justified replacement value priors. Source data are not copied here.

## IVASS geographic distribution of Italian insurance premiums, reference year 2024

**Candidate ID:** `it.ivass.geographic-premiums.2024`  
**Provider:** IVASS - Istituto per la Vigilanza sulle Assicurazioni  
**Categories:** `insurance_market`, `regional_premiums`, `market_statistics`, `portfolio_geography`  
**Spatial scope:** Italy; geography published by the Italian insurance supervisor, not verified individual insurer risk-site geocodes  
**Temporal scope:** 2024 reference-year geographic-premium analysis published 2026-02-19  
**Resolution / granularity:** Regulator statistical publication and downloadable XLSX tables on geographic premium distribution; exact regional/class and entity dimensions require workbook inspection  
**Potential roles:** `regional_insurance_market_allocation_prior`, `premium_geographic_concentration_crosscheck`, `country_specific_insurer_portfolio_constraints`  
**Access hint:** `public_ivass_pdf_xlsx_exact_table_dimensions_and_reuse_rights_review_pending`  
**Authoritative source:** <https://www.ivass.it/pubblicazioni-e-statistiche/statistiche/comunicazioni-statistiche/2026/cs-n-2-2026/index.html?com.dotmarketing.htmlpage.language=1>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Only the published report topic, 2024 reference year, 2026 date and XLSX availability were checked. Per-carrier, per-peril, regional granularity and workbook values were not independently verified. Premium collection geography does not identify insured asset coordinates, building counts, TIV, claims or ceded reinsurance share. Do not infer insurer-specific geographic allocation without confirmed table dimensions.

## OpenFEMA Public Assistance Funded Projects Details v2

**Candidate ID:** `us.fema.public-assistance-projects.v2`  
**Provider:** Federal Emergency Management Agency (FEMA), United States  
**Categories:** `disaster_recovery`, `observed_damage_proxy`, `public_infrastructure`, `financial_assistance`  
**Spatial scope:** United States federally supported public-assistance disaster recipients and eligible facilities; excludes most private insurance claims  
**Temporal scope:** Continuously updated OpenFEMA v2 public data; obligated projects only, with ongoing historic migration and revisions  
**Resolution / granularity:** Project worksheet and applicant-linked obligations; public OpenFEMA v2 REST API and published data dictionary, not directly site-level validated insured losses  
**Potential roles:** `disaster_recovery_cost_observation`, `public_facility_impact_validation`, `hazard_event_to_aid_scope_challenge`  
**Access hint:** `public_openfema_v2_api_daily_revision_terms_and_record_join_review_pending`  
**Authoritative source:** <https://www.fema.gov/openfema-data-page/public-assistance-funded-projects-details-v2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** FEMA explicitly warns that these grant obligations are from grant-management systems, not official federal financial reporting or complete economic damages. Project worksheets are only funded/obligated work and may cover debris or mitigation, not physical replacement. Data migration changed record counts; do not treat v1 and v2 as independent observations or sum with actual insured claims. Candidate is not an insured loss calibration dataset without selection/inflation and project-class controls.

## APRA intermediated general insurance statistical series through June 2026

**Candidate ID:** `au.apra.intermediated-general-insurance.2026h1`  
**Provider:** Australian Prudential Regulation Authority (APRA)  
**Categories:** `insurance_distribution`, `broker_channels`, `market_statistics`, `insurance_market`  
**Spatial scope:** Australia, APRA-authorised general insurance, Lloyd's and reported unauthorised foreign insurance intermediated channel; some reported regional categories for foreign risks  
**Temporal scope:** December 2010 to June 2026 series, official 2026-09-29 release; semiannual  
**Resolution / granularity:** Public APRA XLSX database and explanatory notes, industry aggregate intermediated placements; foreign insurer segments may be shown by region, exemption, atypical risk and reason  
**Potential roles:** `distribution_channel_market_prior`, `broker_placement_trend_crosscheck`, `insurer_portfolio_non_identifiability_constraint`  
**Access hint:** `public_apra_xlsx_data_definitions_confidentiality_and_rights_review_pending`  
**Authoritative source:** <https://www.apra.gov.au/news-and-publications/intermediated-general-insurance-statistics>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This official intermediated-business publication is distinct from APRA's older insurer institution-level series. It is industry-level, not a geolocated named insurer portfolio or customer-level policy file; its regional breakdown for unauthorised foreign insurers must not be conflated with all Australian property risks. Do not assume 2024-2026 institution-level disclosure remains available: APRA notes the quarterly institution-level general-insurance series is on hiatus. Inspect workbook and licence before numerical reuse.

## LINZ NZ Property Boundaries rated property / title / parcel polygon composite

**Candidate ID:** `nz.linz.property-boundaries.2026`  
**Provider:** Toitu Te Whenua Land Information New Zealand (LINZ)  
**Categories:** `property_boundaries`, `cadastral_parcels`, `geospatial_exposure`, `property_identity`  
**Spatial scope:** New Zealand; coverage built from rating units, supplemented with property titles then parcels; it is not an all-building footprint layer  
**Temporal scope:** Continuously revised weekly; inspected layer shows 2026-10-22 update, and publisher category shows 2026-10-29; freeze one exact snapshot for joins  
**Resolution / granularity:** Layer 122657 ~2,718,135 polygon features at inspected vintage; attributes include geom, source, source_id, unit_of_property_id, title_no, parcel_id, area; NZGD2000 EPSG:4167  
**Potential roles:** `geolocate_public_valuation_subset`, `source_stratified_property_identity_join`, `parcel_vs_building_crosswalk_quality`  
**Access hint:** `public_linz_cc_by_4_claimed_by_provider_api_and_spatial_join_rights_review_pending`  
**Authoritative source:** <https://data.linz.govt.nz/layer/122657-nz-property-boundaries/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official layer composes rating units, titles and fallback parcels. Some rows have null unit_of_property_id (title/parcel fallback), so a DVR equality join has unknown selective coverage. Property polygon is not roof footprint, single building or insured asset. Keep source category, unit ID, geometry validity, CRS transformation and source-vintage; exact count changes weekly. Source page advertises CC BY 4.0 but rights/scientific review for intended data pipeline is still pending; no rows published in Git.

## LINZ NZ Properties Property-Building Reference

**Candidate ID:** `nz.linz.property-building-reference.2026`  
**Provider:** Toitu Te Whenua Land Information New Zealand (LINZ)  
**Categories:** `building_identity`, `property_identity`, `relational_crosswalk`, `geospatial_exposure`  
**Spatial scope:** New Zealand buildings with an official reference to a unit of property; linked stock is not complete for every building  
**Temporal scope:** Official table 119620 updated 2026-09-24 at inspected source, with weekly update schedule  
**Resolution / granularity:** Non-spatial PDMF property-to-building relationship table 119620 with id, unit_of_property_id and building_id; 5,029,306 rows at inspected snapshot  
**Potential roles:** `property_to_building_reference_join`, `building_counts_and_cardinality_challenge`, `coverage_deduplication_research`  
**Access hint:** `public_linz_cc_by_4_claimed_by_provider_nonspatial_relation_access_and_rights_review_pending`  
**Authoritative source:** <https://data.linz.govt.nz/table/119620-nz-properties-property-building-reference/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official publisher states unit_of_property_id -&gt; building_id from NZ Building Outlines, not one-to-one: one property can relate to multiple buildings and physical relationships change through time. This product contains no geometry; join building_id to an exact-vintage NZ Building Outlines layer. Do not multiply or evenly spread full rating/insured value across bridge rows or label each row an insured structure. Freeze weekly releases and test missing/duplicate keys and join cardinality before use.

## LINZ NZ Building Outlines current mainland roof-footprint polygons

**Candidate ID:** `nz.linz.building-outlines.current.2026`  
**Provider:** Toitu Te Whenua Land Information New Zealand (LINZ)  
**Categories:** `building_footprints`, `aerial_imagery`, `exposure_geometry`, `building_inventory`  
**Spatial scope:** Mainland New Zealand, close to nationwide except high mountain/Fiordland/Stewart and Chatham gaps; aerial-vintage dependent  
**Temporal scope:** Current published layer 101290 last updated 2026-05-18 at inspected source; capture_source_from/to dates can be years older  
**Resolution / granularity:** ~3,236,141 vector polygons in NZGD2000 / NZTM2000 EPSG:2193; building_id, type/use and source capture dates; roof outlines &gt;=10 square metres, may include garages and sheds  
**Potential roles:** `building_level_exposure_geometry`, `building_id_link_from_linz_property_reference`, `aerial_vintage_and_missingness_validation`  
**Access hint:** `public_linz_cc_by_4_claimed_by_provider_exact_layer_vintage_license_and_raw_data_review_pending`  
**Authoritative source:** <https://data.linz.govt.nz/layer/101290-nz-building-outlines/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Polygon represents imagery-derived roof outline, not assured wall or insurable building count; garages/sheds included and boundaries may lag real construction years. For property-value link use table 119620 at compatible revision and record building_id, imagery capture dates, coverage gaps, topology, duplicates and current-version mismatch. This is an exposure geometry candidate only, not insured TIV or policy holder evidence.

## LINZ NZ Building Outlines All Sources historical imagery cohorts

**Candidate ID:** `nz.linz.building-outlines.all-sources.2026`  
**Provider:** Toitu Te Whenua Land Information New Zealand (LINZ)  
**Categories:** `historical_building_footprints`, `exposure_vintage`, `aerial_imagery`, `change_detection`  
**Spatial scope:** Mainland New Zealand historical imagery coverage and gaps, not complete nationally for every year  
**Temporal scope:** Layer 101292 last updated 2026-05-18 at inspected source; includes multiple image-year states per location  
**Resolution / granularity:** ~6,634,223 historical/current vector outlines with building_outline_id, building_id, capture window and begin/end lifespan or lifecycle; EPSG:2193  
**Potential roles:** `historical_cat_event_exposure_validation`, `building_appearance_disappearance_timing`, `avoid_future_exposure_backtest_leakage`  
**Access hint:** `public_linz_cc_by_4_claimed_by_provider_time_validity_and_licensed_derivation_review_pending`  
**Authoritative source:** <https://data.linz.govt.nz/layer/101292-nz-building-outlines-all-sources/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is explicitly multi-vintage, not 6.6M concurrent buildings; using all rows as a single exposure portfolio would double-count replaced/removed buildings. Datasource reports chronology of image capture and evolving outline IDs; lifecycle table stopped updates after January 2025. A pre-event CAT validation must exclude later-observed footprints, handle splits/merges and uncertain capture dates. No model input permitted from this candidate by catalogue alone.
