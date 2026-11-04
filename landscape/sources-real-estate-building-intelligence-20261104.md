<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-real-estate-building-intelligence-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-real-estate-building-intelligence-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of unusual building intelligence from commercial property portfolios, judicial appraisals, rooftop analytics, LoD2 derivatives and EU stock statistics. Rights, individual-building identity, privacy, source-lineage and replacement-value safeguards remain explicit; no data bytes or insured-policy assertions are admitted.

**Entries:** 7

## IÖR 3D Building Metrics Germany 2025

**Candidate ID:** `de.ioer.3d-building-metrics.2025`  
**Provider:** Leibniz-Institut für ökologische Raumentwicklung / ioerDATA  
**Categories:** `building_3d`, `footprints`, `structural_metrics`, `geometry`, `germany`  
**Spatial scope:** Germany; all 16 federal states; publication says 57,735,634 modelled buildings and structures  
**Temporal scope:** 2025 building-model reference; dataset published 2026-10-14; version 1.0  
**Resolution / granularity:** State-partitioned GeoParquet from official German LoD2 3D models; includes structures such as bridges and silos, not only ordinary buildings  
**Potential roles:** `independent_schema_coverage_check`, `roof_and_building_geometry_enrichment`, `building_structure_type_validation`  
**Access hint:** `portal_metadata_public_underlying_files_access_restricted_request_access_and_licence_review`  
**Authoritative source:** <https://data.fdz.ioer.de/dataset.xhtml?persistentId=doi%3A10.71830%2FAY8CRK>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original ioerDATA page advertises a nationwide ~5 GB ZIP and state GeoParquet files, but individual file pages show Restricted / Request Access. A CC BY 4.0 dataset notice does not guarantee current anonymous file download or override underlying GeoBasis-DE/BKG conditions. Derived from official LoD2; not independent validation of the same underlying cadastre or BKG LoD2. Freeze schema, file access, version, geometry CRS, building-part semantics and source rights before pilot. No actual file bytes acquired.

## DLR EO Solar Germany roof solar potential and installation context

**Candidate ID:** `de.dlr.eo-solar.rooftops`  
**Provider:** Deutsches Zentrum für Luft- und Raumfahrt (DLR), EOC  
**Categories:** `rooftop_geometry`, `solar_potential`, `building_equipment`, `energy`, `germany`  
**Spatial scope:** Germany, method applied to approximately 20 million buildings; public presentation across administrative levels  
**Temporal scope:** Current service described in 2026; source model vintages and release snapshots require inspection  
**Resolution / granularity:** Rooftop solar potential and PV deployment indicators calculated from BKG surface/geospatial models, ML, and MaStR; per-building bulk dataset/API NOT confirmed  
**Potential roles:** `regional_roof_form_prior`, `pv_equipment_penetration_context`, `rooftop_hazard_modifier_research`  
**Access hint:** `public_information_portal_no_verified_bulk_building_file_or_reuse_rights`  
**Authoritative source:** <https://eodata.dlr.de/en/applications/eo-solar>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher describes ~20 million building methodology and DGM/DSM, roof aspect and shade; this is NOT evidence of 20 million freely downloadable per-building records. Shared BKG and MaStR lineage means observations may correlate with existing public cadastre and PV candidates. Small PV addresses in MaStR can be masked. Verify licence, spatial resolution, download route and equipment semantics before any join.

## Vonovia group-owned housing portfolio 2025 regional and country disclosures

**Candidate ID:** `de.vonovia.owned-housing-portfolio.2025`  
**Provider:** Vonovia SE  
**Categories:** `corporate_real_estate`, `residential_portfolio`, `company_disclosures`, `valuation_proxy`, `germany`  
**Spatial scope:** Germany, Sweden and Austria; city/country segment geography, not a public address-level roster  
**Temporal scope:** As of 2025-12-31; annual report released during 2026; sales and purchases during 2025  
**Resolution / granularity:** Group-owned 530,979 residential units across 608 towns/cities; Germany-owned 471,153 residential units across 459 towns/cities; aggregate areas, values, vacancies and location breakdowns; third-party management is separate  
**Potential roles:** `synthetic_landlord_residential_portfolio_geographic_weights`, `housing_unit_area_benchmark`, `temporal_ownership_scope_challenge`  
**Access hint:** `public_company_html_annual_report_aggregate_extract_rights_review`  
**Authoritative source:** <https://report.vonovia.com/2025/q4/de/portfolio-im-bewirtschaftungsgeschaeft>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Annual report separately discloses 76,255 managed third-party units; do not merge these with owned holdings. The property portfolio is NOT a schedule of insured buildings, a complete building identity roster or an insurance contract, and assets may share multiple dwellings. Accounting fair value, rent and market value are not replacement-cost TIV. Reconcile geography, year, sales/acquisitions, IFRS group boundary and method before fitting synthetic exposure.

## TAG Immobilien 2025 multi-year residential portfolio geographic and valuation data

**Candidate ID:** `de.tag-immobilien.owned-housing-portfolio.2025`  
**Provider:** TAG Immobilien AG  
**Categories:** `corporate_real_estate`, `residential_portfolio`, `property_valuation`, `germany`, `poland`  
**Spatial scope:** Germany and Poland, different ownership and rental/development measures; most German holdings in north/east and NRW  
**Temporal scope:** As of 2025-12-31, website table includes 2022-2025 historical comparatives  
**Resolution / granularity:** 83,504 German residential units, 3,526 completed rental apartments in Poland at year-end 2025, aggregate property volume by country and historical vacancy information  
**Potential roles:** `independent_second_landlord_portfolio_pilot`, `regional_rental_exposure_weights`, `time_series_sales_acquisitions_validation`  
**Access hint:** `public_company_website_aggregate_disclosures_rights_review`  
**Authoritative source:** <https://www.tag-ag.com/ueber-die-tag/portfolio-gesamt>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider gives public owned portfolio and valuation totals, not building IDs, policy locations or individual construction material. Poland rental, delivered and sales metrics overlap in distinct ways; avoid double count. Disclosed real estate volume is market/accounting value, not building replacement value or sum insured. Freeze reporting year and legal entities.

## German judicial forced-sale notices and property valuation appraisals

**Candidate ID:** `de.justiz.zvg-public-valuations`  
**Provider:** Gemeinsames Justizportal der Länder / Amtsgerichte  
**Categories:** `property_appraisals`, `building_condition`, `floor_area`, `construction_quality`, `sample_validation`  
**Spatial scope:** Germany, only properties subject to announced judicial sale; nonrepresentative and privacy-sensitive sample  
**Temporal scope:** Notice and appraisal dates differ; court-specific availability and publication duration vary  
**Resolution / granularity:** Individual cases may provide appraiser-described condition, layout, shortcomings and valuation method, with no universal structured bulk export or durable reuse right  
**Potential roles:** `anonymised_repair_and_condition_feature_dictionary`, `independent_valuation_method_review`, `residential_structural_attribute_sample`  
**Access hint:** `public_notices_court_appraisal_case_by_case_no_bulk_reuse_clearance`  
**Authoritative source:** <https://www.justiz.bayern.de/gerichte-und-behoerden/amtsgerichte/muenchen/verfahren_30.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official Bavarian court page points to zvg-portal.de and says reports/exposes usually available; legal/privacy/retention/copyright issues demand case review. Not representative of building stock: foreclosed properties are selection-biased. Never publish owner/tenant/occupant details or infer insurance coverage. Appraisal market value is not rebuild cost, official release does not imply blanket machine redistribution.

## EU Building Stock Observatory 2026 national energy and renovation statistics

**Candidate ID:** `eu.ec.building-stock-observatory.2026`  
**Provider:** European Commission Directorate-General for Energy  
**Categories:** `energy_efficiency`, `building_stock`, `energy_certificates`, `renovation`, `europe`  
**Spatial scope:** EU Member States, selected country indicators, not individual geocoded building records  
**Temporal scope:** Official database updated June 2026, with indicator-specific historical reference years  
**Resolution / granularity:** Country/year/topic downloadable XLSX and factsheets with stock, consumption, building elements, energy certificates, renovation and financing indicators  
**Potential roles:** `national_energy_class_prior`, `renovation_stock_scenario_prior`, `country_level_building_stock_consistency_check`  
**Access hint:** `public_aggregated_workbook_licence_individual_indicator_upstream_review`  
**Authoritative source:** <https://energy.ec.europa.eu/topics/energy-efficiency/energy-performance-buildings/eu-building-stock-observatory_en>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EU Commission states full BSO dataset may be downloaded as XLSX. This is an aggregate source only; energy certificate counts do not locate individual certified buildings, and country totals must not be copied to polygons as observations. Inspect year, units, indicators and upstream country sources; licence and redistribution remain to be reviewed.

## ImmoScout24 API listing-data licensing boundary and property attributes

**Candidate ID:** `de.immobilienscout24.api.terms.2022`  
**Provider:** Immobilien Scout GmbH  
**Categories:** `real_estate_listings`, `property_descriptions`, `restricted_commercial_data`, `source_rights_negative_control`  
**Spatial scope:** Germany, advertisement-specific selection rather than exhaustive building stock  
**Temporal scope:** Published API terms dated 2022-08-15; verify current contract before any use  
**Resolution / granularity:** Listings may contain year built, floor area, modernization and energy attributes; API use is contract-based and restricted  
**Potential roles:** `forbidden_ingestion_guardrail`, `possible_negotiated_licensed_data_evaluation`, `attribute_taxonomy_only_without_copying_data`  
**Access hint:** `do_not_crawl_or_build_internal_database_without_separately_expressly_agreed_licence`  
**Authoritative source:** <https://api.immobilienscout24.de/terms-of-use/en/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official API terms section 6 prohibits crawling/robots to obtain portal data; section 7 prohibits use to create licensee databases or evaluations for other purposes and limits standard API storage to 24 hours. Therefore do NOT scrape, bulk-copy, persist or train from listings under ordinary terms. Candidate documents a licensing barrier, not an available source. Seek direct written commercial permission before ingestion.
