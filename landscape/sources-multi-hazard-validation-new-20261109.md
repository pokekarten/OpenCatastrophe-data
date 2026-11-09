<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-multi-hazard-validation-new-20261109.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-multi-hazard-validation-new-20261109.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-09`  
**Purpose:** Non-admission original-provider discovery of five distinct 2026 critical-infrastructure, DOI wildfire, hydrodynamic, UK urban flood monitoring and USDA community wildfire benchmark products. No source admission, data retrieval or permission inferred.

**Entries:** 5

## Global Exposure and Risk Database: multi-hazard critical infrastructure v1.0.0

**Candidate ID:** `nirandjan.global-infra-exposure-risk.v1-0-0`  
**Provider:** Nirandjan and Koks / Vrije Universiteit Amsterdam, University of Oxford / Zenodo  
**Categories:** `critical_infrastructure`, `exposure`, `risk_benchmark`, `flood`, `earthquake`, `tropical_cyclone`, `landslide`  
**Spatial scope:** Global GADM Admin-2 region summaries across energy, transport, telecom, waste, water, education and healthcare; geography follows source GADM boundaries  
**Temporal scope:** Zenodo version 1.0.0, released 2026-09-14; hazard and exposure input vintages differ and must be recovered from methodology before comparisons  
**Resolution / granularity:** Eight main XLSX workbooks: global_infra_risk plus seven sector exposure summaries; additional design-standard sensitivity ZIP; admin-2 risk quantiles min/Q1/Q2/Q3/max and return-period suffixes for lengths (km), areas (m2), and counts  
**Potential roles:** `regional_infrastructure_risk_benchmark`, `synthetic_infrastructure_portfolio_prior`, `hazard_defence_sensitivity_comparison`  
**Access hint:** `public_zenodo_doi_metadata_and_large_xlsx_workbooks_rights_review_required_metadata_only`  
**Authoritative source:** <https://zenodo.org/records/22750653>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider states modeled multi-hazard risk estimates and exposure summaries; NOT observed insured losses, building-level geocoordinates, independent event footprints or insurer TIV. Treat design standards, return periods, risk quantiles and multi-hazard summed outputs with their own semantics. Trace original vulnerability curves and asset layers to Nirandjan's already registered physical vulnerability and infrastructure products before claiming independent validation. Freeze source GADM version and publication files. Published MD5 labels are provider metadata, not our SHA-256 byte receipts. Exact dataset license and all upstream reuse rights unreviewed; no file bytes acquired.

## DOI Wildland Fire Service wildfire risk map 2026

**Candidate ID:** `usgs.doi-uswfs-wildfire-risk.2026`  
**Provider:** US Geological Survey / US Department of the Interior / US Wildland Fire Service  
**Categories:** `wildfire`, `hazard_context`, `critical_infrastructure`, `buildings`, `geospatial_raster`, `united_states`  
**Spatial scope:** Conterminous United States, Alaska and Hawaii in separate, regionally projected raster products  
**Temporal scope:** USGS data release published 2026-11-04; source Wildfire Hazard Potential references 2023 WHP, 2020 LANDFIRE-based fuels and earlier upstream data  
**Resolution / granularity:** Regional risk and risk-classification raster layers plus life, property and infrastructure valuation proxies, 2400-m buffered combinations, wilderness mask, separate metadata and data_dictionary.csv  
**Potential roles:** `doi_wildfire_risk_relative_benchmark`, `infrastructure_exposure_context`, `wildfire_hazard_lineage_reconciliation`  
**Access hint:** `public_usgs_data_release_cc0_page_and_metadata_download_script_data_specific_rights_check`  
**Authoritative source:** <https://www.usgs.gov/data/us-department-interior-wildfire-risk-map-us-wildland-fire-service>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** USGS DOI release DOI 10.5066/P14VT8QI labels the work CC0 1.0, but maintain rights not_reviewed until checking exact asset metadata and source-derived layers. Source explicitly limits intended interpretation to DOI responsibilities; not a comprehensive wildfire risk assessment for all non-DOI properties, not annual burn probability, not asset replacement cost and not insured loss. WHP uses existing LANDFIRE and FSIM inputs; not independent of other US wildfire hazard layers. Do not turn categorical WHP into an event set or treat 2400-m buffers as actual fire perimeters.

## Observed inundation and hydrodynamic simulation data

**Candidate ID:** `si.donevska-inundation-hydrodynamic.zenodo-22275184`  
**Provider:** Donevska and Mikos / University of Ljubljana / Zenodo  
**Categories:** `flood`, `observed_inundation`, `hydrodynamic_simulation`, `uncertainty`, `validation`, `slovenia`  
**Spatial scope:** Slovenia study catchment; exact reach, CRS and flood-event location must be established from original GIS metadata  
**Temporal scope:** Zenodo record 22275184 published 2026-09-03; observed extent date and modeled design-storm return period are separate temporal semantics  
**Resolution / granularity:** Observed inundation extent archive plus GeoTIFF hydrodynamic simulations for Q10, Q100, Q500 and multiple channel/floodplain/uncertainty configurations  
**Potential roles:** `observed_vs_modelled_flood_extent_challenge`, `hydraulic_sensitivity_benchmark`, `flood_depth_and_uncertainty_test_cases`  
**Access hint:** `public_zenodo_cc_by4_record_zipped_geotiff_and_observation_metadata_only_until_exact_asset_gate`  
**Authoritative source:** <https://zenodo.org/records/22275184>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Zenodo displays CC BY 4.0 for this record, but exact source reuse, raster contents and dependencies still need source review. Distinguish surveyed/remote observed inundation from modeled Q10/Q100/Q500 depth outputs and 10/90 confidence scenarios. Return period labels do not imply real historical event frequency for the measured extent. Must inspect TIFF band units, CRS, NoData, vertical datum, observed event timestamp, uncertainties and overlap with existing Copernicus/EEA flood products. No bytes acquired or damage/claims inferred.

## Blue Heart high-density urban hydrometric and sewer monitoring dataset

**Candidate ID:** `uk.exeter-blueheart-hydrometric.zenodo-20699635`  
**Provider:** Sweetapple, Illingworth and Melville-Shreeve / University of Exeter / East Sussex County Council / Zenodo  
**Categories:** `flood`, `pluvial`, `urban_drainage`, `observations`, `rainfall`, `water_levels`, `united_kingdom`  
**Spatial scope:** 78 km2 urban catchment in East Sussex, UK, including rainfall, rivers, groundwater, road gullies and in-sewer gauges  
**Temporal scope:** Zenodo record 20699635, project release v1.0 in 2026; individual instrument sampling dates and completeness must be verified from index/README  
**Resolution / granularity:** 497 sensor locations with multiple telemetry datasets, catchment and network shapefiles; index_telemetry_data.csv and original README are metadata-first review targets  
**Potential roles:** `urban_pluvial_time_series_calibration`, `storm_sewer_response_validation`, `observational_hydrologic_uncertainty_benchmark`  
**Access hint:** `public_zenodo_download_listing_licence_field_not_resolved_terms_and_telemetry_privacy_check`  
**Authoritative source:** <https://zenodo.org/records/20699635>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider dataset lists 497 gauges over 78 km2 and separate archives including 331-MB catchment geometry, 231-MB sewer telemetry and small index file. Publication page exposed no readable license designation at this review; commercial use, derivative publication and exact observation rights remain unknown. First inspect versioned metadata and README, then timestamps/timezones, rainfall units and gauge quality flags. A rain or water-level observation is not a flood polygon, sewer loss, insured claim, or independent exposure inventory. Do not ingest sensor or infrastructure locations into public Git.

## Wildfire Risk to Communities all-lands and populated-area GIS layers

**Candidate ID:** `usda.fs.wildfire-risk-to-communities.rds-2020-0016-2`  
**Provider:** US Department of Agriculture / US Forest Service  
**Categories:** `wildfire`, `hazard_context`, `burn_probability`, `flame_length`, `buildings`, `community_risk`, `united_states`  
**Spatial scope:** United States nationally consistent, downloadable state GIS rasters and community/county/tribal summaries; check coverage and edition by jurisdiction  
**Temporal scope:** USDA Forest Service Research Data Archive all-lands 2nd edition reference RDS-2020-0016-2 (2024); website dashboard updated through April 2026 independently of GIS release  
**Resolution / granularity:** GIS rasters including annual burn probability, conditional flame length, risk to potential structures and building/housing summaries; several building grids described as 30-meter pixels  
**Potential roles:** `us_wildfire_burn_probability_cross_model_comparison`, `population_and_building_risk_context`, `wildfire_intensity_component_sensitivity`  
**Access hint:** `public_usda_gis_state_downloads_and_research_data_archive_exact_release_terms_review`  
**Authoritative source:** <https://wildfirerisk.org/download/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Annual burn probability is a distinct probability variable; conditional flame length and risk-to-home indices are not interchangeable and none is an insurer payout. Published risk is generalized and not parcel-level/home-specific. Underlying LANDFIRE/FSIM, FEMA USA Structures, Census and related sources may overlap DOI USWFS and existing OpenCatastrophe wildfire candidates; do not use the two products as independent holdouts by default. Separate 2024 versioned GIS from 2026 website content, check raster dates, projection, NoData, license and training inputs before use. No source bytes acquired.
