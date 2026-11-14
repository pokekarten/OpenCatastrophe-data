<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-cross-sector-risk-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-cross-sector-risk-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of high-value cross-sector public data and open analytical workflow references for agriculture, insurer reporting, infrastructure logistics and business interruption; no external source-data bytes, admission or model-use rights are granted.

**Entries:** 5

## IFPRI MapSPAM 2020 v2r2 spatial crop production

**Candidate ID:** `ifpri.mapspam2020.v2r2`  
**Provider:** International Food Policy Research Institute (IFPRI)  
**Categories:** `agriculture`, `crop_exposure`, `production`, `yield`, `irrigation`, `geospatial`  
**Spatial scope:** Global gridded agricultural production; output cell estimates do not identify individual farms or insured parcels  
**Temporal scope:** Reference agricultural production year 2020; IFPRI SPAM 2020 version 2 release 2 published in 2026  
**Resolution / granularity:** 5 arc-minute (~10 km) cell statistics by 46 crop groups, rainfed/irrigated farming, physical and harvested area, production and yield; CSV and GeoTIFF  
**Potential roles:** `crop_value_exposure_prior`, `agriculture_peril_region_calibration`, `flood_drought_wind_crop_loss_denominator`, `crop_portfolio_synthetic_allocation`  
**Access hint:** `public_csv_geotiff_and_harvard_dataverse_exact_asset_rights_and_vintage_review_pending`  
**Authoritative source:** <https://www.mapspam.info/data/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The provider offers MapSPAM 2020 v2r2 files with original product/version DOI 10.7910/DVN/SWPENT. Modelled spatial disaggregation from agricultural statistics is not a plot-verified crop map, farm ownership or insured sums. Preserve crop and production-system semantics, reference year, source revisions and usage terms; do not use gridded production directly as agricultural policy TIV.

## Central Bank of Ireland 2025 public SFCR quantitative template repository

**Candidate ID:** `ie.centralbank.sfcr-qrt-repository.2025`  
**Provider:** Central Bank of Ireland  
**Categories:** `insurance`, `reinsurance`, `solvency`, `legal_entity`, `financial_reporting`, `regulatory`  
**Spatial scope:** Insurers and reinsurers reporting in Ireland; domicile, underwriting country and insured-risk geography are not interchangeable  
**Temporal scope:** Annual public SFCR repository; published source page includes 2016-2025 reporting years with separately dated files  
**Resolution / granularity:** Undertaking-level Solvency II public quantitative template data in downloadable year-specific CSV (2025 and earlier); coverage/columns depend on reporting year  
**Potential roles:** `irish_insurer_lob_premium_constraint`, `company_solvency_reinsurance_prior`, `solo_group_reporting_crosscheck`, `public_qrt_template_parser_benchmark`  
**Access hint:** `public_regulator_csv_and_pdf_exact_reporting_year_template_and_reuse_review_pending`  
**Authoritative source:** <https://www.centralbank.ie/regulation/industry-market-sectors/insurance-reinsurance/solvency-and-financial-condition-report-repository>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The regulator publishes annual undertakings' SFCR template repositories; year 2025 appears on its official page. These are public quantitative regulatory disclosures, not proprietary exposure data or complete geocoded insurer portfolios. Check S.05/S.19 and template years, solo/group duplication, gross/net distinctions, entity identities, disclosure suppression and source-specific reuse before modelling.

## WFP ArcGIS global logistics infrastructure and supply-route services

**Candidate ID:** `wfp.gis.global-logistics-feature-services.2026`  
**Provider:** United Nations World Food Programme (WFP)  
**Categories:** `critical_infrastructure`, `logistics`, `ports`, `airports`, `warehouses`, `supply_chain`  
**Spatial scope:** Global service collections with country-by-country source coverage and uneven update dates  
**Temporal scope:** Live and periodically updated ArcGIS service inventory observed 2026-11-04; no frozen asset vintage yet  
**Resolution / granularity:** ArcGIS REST feature services for GlobalPorts, GlobalAirports, GlobalBridges, Warehouses, border crossings, WFP facilities and supply routes  
**Potential roles:** `port_warehouse_airport_geospatial_exposure`, `multi_modal_disruption_network`, `business_interruption_context`, `cross_source_infrastructure_geometry_challenge`  
**Access hint:** `public_arcgis_service_listing_only_license_and_individual_layer_query_scope_pending`  
**Authoritative source:** <https://gis.wfp.org/arcgis/rest/services/GLOBAL>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The first-party WFP ArcGIS directory exposes multiple distinct facility/transport layers. It may aggregate OpenStreetMap and partner data, so do not assume independent facility observations relative to NGA World Port Index, OSM or other sources. A visible REST service does not establish permission to bulk download, redistribute, commercialise or rely on its points. Capture per-layer description, licence, source vintage, query response and identity before acquisition.

## Eurostat FIGARO 2026 inter-country input-output and supply-use tables

**Candidate ID:** `eu.eurostat.figaro.2026`  
**Provider:** Eurostat / European Commission  
**Categories:** `economy`, `trade`, `supply_chain`, `business_interruption`, `input_output`, `industry`  
**Spatial scope:** EU inter-country and international partner economic flows under the exact FIGARO regional coverage; not physical company or plant locations  
**Temporal scope:** FIGARO 2026 edition: annual 2010-2024 series  
**Resolution / granularity:** International supply, use and input-output matrices by up to 64 NACE industries and 64 CPA products; CSV/Excel data, related indicators supplied as Parquet  
**Potential roles:** `industry_dependency_matrix`, `economic_business_interruption_multiplier_research`, `sector_supply_chain_prior`, `cross_border_activity_proxy`  
**Access hint:** `official_eurostat_csv_excel_parquet_catalogue_individual_table_rights_version_review_pending`  
**Authoritative source:** <https://ec.europa.eu/eurostat/en/web/esa-supply-use-input-tables/database>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** FIGARO is a national-accounts industry flow product, not observed firms' logistics contracts or insurance time-element claims. Inter-country input-output linkages need declared price basis, table version, classification, reference year, treatment of imports and economic propagation assumptions. Do not treat aggregate monetary flows as geocoded exposure or insurer-specific contingent BI limits.

## Open-GIRA reproducible global infrastructure risk analysis workflow

**Candidate ID:** `nismod.open-gira.workflow.2026`  
**Provider:** University of Oxford / NISMOD and collaborators  
**Categories:** `open_source_workflow`, `infrastructure`, `network_risk`, `business_interruption`, `hazard_overlay`  
**Spatial scope:** Country-to-global workflows subject to each chosen OSM, infrastructure and hazard input's coverage  
**Temporal scope:** Actively maintained open-source workflow; results have user-selected input/snapshot dates rather than one global observation vintage  
**Resolution / granularity:** Snakemake and Python pipeline for roads, rail, electricity network overlays with flood, storm surge and tropical-cyclone hazard, direct damages and indirect interruption  
**Potential roles:** `infrastructure_hazard_overlay_reference`, `network_disruption_methodology`, `reproducible_pipeline_comparison`, `direct_indirect_loss_model_research`  
**Access hint:** `open_github_source_repository_separate_software_license_and_underlying_data_rights_review`  
**Authoritative source:** <https://github.com/nismod/open-gira>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is software and methodology, NOT a new independent source dataset or measured insurer loss. Referenced OSM and hazard outputs retain their original providers and rights. Its Snakemake topology/CI samples can inform reproducible network-loss experiments, but must not be counted as independent infrastructure observations or as validated loss-severity curves.
