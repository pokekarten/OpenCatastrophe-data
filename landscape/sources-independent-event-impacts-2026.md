<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-independent-event-impacts-2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-independent-event-impacts-2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-10-31`  
**Purpose:** Non-admission discovery registry of distinct source-original CAT event reports, impact estimates and product-limited validation resources; no new data admission or source-byte publication.

**Entries:** 6

## DFO Global Flood Records v0.9.0

**Candidate ID:** `dfo.floodrecords.v0.9.0`  
**Provider:** Dartmouth Flood Observatory / University of Colorado  
**Categories:** `flood`, `historical_events`, `reported_impacts`, `event_catalogue`  
**Spatial scope:** global; large reported flood events, not uniformly complete across countries  
**Temporal scope:** Publisher describes January 1985 to December 2023 for v0.9.0, but the published CSV preview contains January 2024 records; actual coverage boundary requires reconciliation  
**Resolution / granularity:** Zenodo record 19288171; downloadable Global_Flood_Records.csv and GeoPackage; catalogue lists event date intervals, affected area approximations, causes, fatalities, displaced people and source labels  
**Potential roles:** `historical_flood_event_reconciliation`, `country_date_event_holdout`, `reported_human_impact_quality_review`  
**Access hint:** `public_versioned_zenodo_catalogue_cc0_claim_separate_from_legacy_maps`  
**Authoritative source:** <https://zenodo.org/records/19288171>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher FloodRecords wiki states CC0 for this event-record product and points to the v0.9.0 Zenodo release; independently inspect its bundled LICENSE.txt and pin exact downloaded bytes before any admission. Legacy Flood Observatory archive and event inundation raster/maps may have different noncommercial terms; CC0 must never be carried over to those separate files. Catalogue area affected is not measured flood-depth raster or insured loss; repeated, fragmented and cross-border events need manual identity review. Observed source inconsistency: v0.9.0 CSV starts with January 2024-dated rows despite its stated December 2023 endpoint; the source release is not yet date-range validated. Original CSV uses M/D/YY dates, not ISO YYYY-MM-DD; any importer must parse them unambiguously and preserve the raw receipt.

## NOAA Storm Prediction Center Severe Weather GIS through 2025

**Candidate ID:** `noaa.spc.svrgis.2025`  
**Provider:** NOAA National Weather Service Storm Prediction Center  
**Categories:** `severe_convective_weather`, `tornado`, `hail`, `windstorm`, `historical_reports`  
**Spatial scope:** United States  
**Temporal scope:** tornado reports 1950-2025; hail and damaging wind 1955-2025; site updated April 2026  
**Resolution / granularity:** CSV-derived downloadable event point and path ESRI Shapefiles; report attributes and coordinates, with a provider changelog of historical corrections and changing identifiers  
**Potential roles:** `reported_severe_weather_event_holdout`, `tornado_hail_wind_location_validation`, `observation_bias_study`  
**Access hint:** `public_us_government_reports_gis_product_and_terms_review_required`  
**Authoritative source:** <https://www.spc.noaa.gov/gis/svrgis/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** SPC states the GIS derives from official Storm Data CSV, so it is not independent of NOAA NCEI Storm Events. For tornadoes missing end points, the provider makes artificial short LineStrings using 0.0001 degree offsets: do not read them as physical swaths. The 24 April 2026 changelog also changes newer om_number identifiers. Version and SHA-pin releases, preserve original report IDs, report types, dates and source bias. Reports are not insured claims or complete event footprints.

## USGS ComCat Did You Feel It event products

**Candidate ID:** `usgs.comcat.dyfi`  
**Provider:** United States Geological Survey Earthquake Hazards Program  
**Categories:** `earthquake`, `felt_intensity`, `crowdsourced_observations`, `historical_event_validation`  
**Spatial scope:** United States and selected global earthquakes with voluntary responses  
**Temporal scope:** event-dependent historical and ongoing responses; no continuous complete global coverage asserted  
**Resolution / granularity:** Per-event versioned ComCat dyfi products including city or ZIP aggregates, geocoded 1 km and 10 km GeoJSON intensity files, response counts and product update timestamps  
**Potential roles:** `independent_felt_intensity_challenge`, `earthquake_event_spatial_holdout`, `crowd_response_bias_review`  
**Access hint:** `public_usgs_event_product_exact_version_and_response_privacy_review_required`  
**Authoritative source:** <https://ghsc.code-pages.usgs.gov/hazdev/pdl/userguide/products/known-types/dyfi.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DYFI combines volunteered macroseismic experiences into aggregated intensity, not instrument-measured PGA, building damage, insurance claims or unbiased exposure sampling. Freeze ComCat event ID plus source/type/code/update-time to avoid silently comparing revised preferred versions. A missing response must never become zero shaking; exclude individual raw responses absent explicit release and privacy review.

## USGS ComCat PAGER earthquake impact estimates

**Candidate ID:** `usgs.comcat.losspager`  
**Provider:** United States Geological Survey Earthquake Hazards Program  
**Categories:** `earthquake`, `modelled_impacts`, `economic_loss_estimate`, `benchmark`  
**Spatial scope:** significant earthquakes worldwide for which a losspager product exists  
**Temporal scope:** event-dependent historical and current ComCat products; coverage and updates vary by event  
**Resolution / granularity:** Versioned losspager event product; pager.xml plus json/losses.json, json/exposures.json, alerts, population exposure and alert-level summaries  
**Potential roles:** `earthquake_impact_sanity_check`, `model_output_comparison_only`, `event_product_version_reconciliation`  
**Access hint:** `public_usgs_modelled_product_data_dependencies_and_terms_review_required`  
**Authoritative source:** <https://ghsc.code-pages.usgs.gov/hazdev/pdl/userguide/products/known-types/losspager.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** PAGER fatalities and economic losses are MODELLED estimates informed by ShakeMap, LandScan exposure and regional historical-impact relationships, not observed losses or insured claims. Never train against PAGER and then declare independent loss validation against it, and do not infer treaty losses. Pin product version and all upstream assumptions; protect against changes to preferred ComCat products.

## Copernicus Emergency Management Service Rapid Mapping

**Candidate ID:** `ec.jrc.cems.rapid-mapping`  
**Provider:** European Commission Joint Research Centre / Copernicus CEMS  
**Categories:** `flood`, `wildfire`, `earthquake`, `multi_hazard`, `satellite_mapping`  
**Spatial scope:** global emergency activations; coverage limited to specific requested areas of interest  
**Temporal scope:** activation-triggered archive and near-event response; no global regular event-frequency series  
**Resolution / granularity:** Activation and product level geospatial delineation, grading and reference maps; selected vector Shapefiles, KMZ, georeferenced TIFF and map products  
**Potential roles:** `event_footprint_spatial_holdout`, `damage_grading_comparison`, `satellite_detection_uncertainty_review`  
**Access hint:** `mostly_open_public_activation_products_with_product_specific_exceptions`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/collection/id-0072>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** JRC says data are open access with exceptions: this statement is NOT a blanket redistribution approval for each activation/product. Preserve activation ID, mapping area, production time, satellite date, mapping type, licence and byte receipts. Delineation or damage grading from emergency mapping is a constrained observation, not a sampled catalogue of all events, exact flood depths or insurer losses; avoid extrapolating unmapped areas as zero.

## UNDRR DesInventar Sendai national disaster loss databases

**Candidate ID:** `undrr.desinventar.sendai.country-loss-records`  
**Provider:** United Nations Office for Disaster Risk Reduction and contributing national institutions  
**Categories:** `multi_hazard`, `reported_impacts`, `disaster_loss_records`, `country_statistics`  
**Spatial scope:** many country and regional databases, with highly variable geographic and historical coverage  
**Temporal scope:** country-specific historical intervals and periodic updates; not one uniform global time series  
**Resolution / granularity:** Country-hosted event and subnational disaster impact records with possible CSV or Excel exports, hazard categories, human impacts, affected housing and reported economic indicators  
**Potential roles:** `historical_disaster_event_reconciliation`, `reported_country_loss_holdout`, `source_coverage_gap_analysis`  
**Access hint:** `public_country_specific_disaster_records_with_separate_data_rights_review`  
**Authoritative source:** <https://www.desinventar.net/DesInventar/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The Apache-style licence described by the publisher applies to DesInventar SOFTWARE, not automatically to separately contributed national DATABASES. Dataset rights, provenance and export availability must be checked by country. Differences in event definitions, reporting thresholds, spatial units, nominal-currency values and completeness prohibit automatic pooling or translation into insured CAT loss.
