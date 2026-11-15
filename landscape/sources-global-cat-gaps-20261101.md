<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-global-cat-gaps-20261101.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-global-cat-gaps-20261101.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of independently identified global catastrophe hazard, building exposure, drought context and historical flood-depth products missing from the existing source registry; access, data rights and scientific fitness remain unapproved.

**Entries:** 6

## JRC satellite-derived flood depth maps for Europe

**Candidate ID:** `ec.jrc.satellite-flood-depth-europe.2015-2024`  
**Provider:** European Commission Joint Research Centre / CEMS  
**Categories:** `flood`, `observed_flood`, `satellite`, `flood_depth`, `event_validation`, `europe`  
**Spatial scope:** Europe; satellite-observed flood events where acquisitions exist  
**Temporal scope:** 2015-2024 in the currently catalogued JRC dataset; archive may subsequently expand  
**Resolution / granularity:** 20 m flood-depth GeoTIFFs; event-start and event-end in filename; centimetres; 9999 denotes permanent or seasonal water bodies  
**Potential roles:** `observed_flood_depth_challenge`, `historical_event_reconciliation`, `flood_extent_and_depth_validation`  
**Access hint:** `public_anonymous_catalogue_yearly_archive_exact_asset_and_terms_review`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/0bc96690-b89c-4909-9166-c2c322a20130>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Separate JRC depth reconstruction product from the already registered CEMS GFM v4.1.1 flood-extent monitoring. Depth is model-assisted reconstruction from Sentinel-1 extent and topography, not a gauge-measured depth or insured loss. Preserve event ID/date, acquisition coverage, raster CRS, cm units, dummy 9999 water-body mask and spatial validity. The third-party EuroFlood index advertises an extended 2015-2025 range: independently verify its exact catalogue vintage and lineage before joining. Never count GFM and these derived depths as independent observations.

## OpenBuildingMap global footprints and estimated building attributes

**Candidate ID:** `gfz.openbuildingmap.global.2025`  
**Provider:** GFZ / Oostwegel, Schorlemmer and collaborators  
**Categories:** `exposure`, `buildings`, `building_footprints`, `building_attributes`, `global`  
**Spatial scope:** Global, according to coverage of its three input footprint families  
**Temporal scope:** 2025 publication; source snapshots include OSM July 2024, Google Open Buildings and Microsoft building footprints  
**Resolution / granularity:** About 2.7 billion footprint polygons with inferred occupancy, height and floorspace, distributed as tiled building records  
**Potential roles:** `building_geometry_coverage_comparison`, `building_height_and_use_proxy`, `global_exposure_enrichment`, `source_lineage_challenge`  
**Access hint:** `public_download_tile_by_tile_original_odbl_and_upstream_lineage_review`  
**Authoritative source:** <https://www.openbuildingmap.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original providers include OSM, Google Open Buildings and Microsoft, which are already known separately; this derived product does not add an independent building population or measured attributes. Height uses GHSL; occupancy draws on OSM land use/POI, and floorspace is derived. Preserve original footprint family, dedup/conflation, tile and release identity. Dataset states ODbL 1.0; assess share-alike and commercial redistribution obligations for exact use; no insured values or vulnerability functions.

## WRI Aqueduct Floods Hazard Maps Version 2

**Candidate ID:** `wri.aqueduct-flood-hazard.v2.2020`  
**Provider:** World Resources Institute (WRI)  
**Categories:** `flood`, `river_flood`, `coastal_flood`, `climate_scenarios`, `global`  
**Spatial scope:** Global coverage subject to flood-model spatial limits  
**Temporal scope:** Historical/baseline and projections for 2030, 2050 and 2080; version 2 corrected 2020-10-20  
**Resolution / granularity:** Single-band GeoTIFF inundation depth in metres; riverine/coastal, return period, climate scenario and coastal subsidence options vary by file  
**Potential roles:** `global_flood_hazard_challenge`, `scenario_risk_sensitivity`, `coastal_vs_riverine_comparison`  
**Access hint:** `public_download_exact_v2_tif_and_data_dictionary_rights_review`  
**Authoritative source:** <https://datasets.wri.org/datasets/aqueduct-floods-hazard-maps>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is Aqueduct Floods v2, not the separate Aqueduct 4.0 Water Risk Atlas. Provider warns the 2020 model omits flood protections; historical and future scenarios are modelled not observed. A 2020-10-20 river-map bias correction requires exact corrected asset identity, return-period/scenario/subsidence flag, datum, grid and hash. Do not treat a return-period surface as an event catalogue, or sum it with JRC floods as independent losses.

## WRI Aqueduct 4.0 global water-risk indicators

**Candidate ID:** `wri.aqueduct.water-risk-atlas.v4.0`  
**Provider:** World Resources Institute (WRI)  
**Categories:** `drought`, `water_stress`, `hydrology`, `climate_scenarios`, `global`  
**Spatial scope:** Global basins and reported country/provincial aggregates  
**Temporal scope:** Current baseline and projections to 2030, 2050 and 2080; Aqueduct 4.0 documentation  
**Resolution / granularity:** Basin-level baseline annual/monthly and future water-risk indicators; aggregated rankings and multiple component metrics  
**Potential roles:** `drought_context_proxy`, `basin_water_stress_stratification`, `regional_exposure_validation_context`  
**Access hint:** `public_download_wri_terms_and_individual_indicator_dictionary_review`  
**Authoritative source:** <https://datasets.wri.org/datasets/aqueduct-global-maps-40-data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Not the Aqueduct Floods v2 depth maps and not an annual stochastic drought loss event set. Indicators combine heterogeneous inputs; aggregate rankings are lossy and not measured site-level hazard or insurer exposure. Preserve basin-level identifiers, indicator meaning, epoch, climate model, raw component and uncertainty; original WRI CC BY attribution and provider registration/usage instructions require an exact scope review.

## GEM Global Seismic Hazard Map v2026.1

**Candidate ID:** `gem.global-seismic-hazard-map.v2026.1`  
**Provider:** Global Earthquake Model Foundation  
**Categories:** `earthquake`, `seismic_hazard`, `probabilistic_hazard`, `global`  
**Spatial scope:** Global including offshore areas  
**Temporal scope:** Version v2026.1 issued June 2026; supersedes v2023.1  
**Resolution / granularity:** Base map of PGA in g on reference rock Vs30 800 m/s at 10% exceedance probability in 50 years; vector/raster map products  
**Potential roles:** `earthquake_hazard_crosscheck`, `regional_seismic_model_validation`, `seismic_hazard_prior`  
**Access hint:** `public_open_noncommercial_layer_only_other_layer_and_commercial_license_request`  
**Authoritative source:** <https://www.globalquakemodel.org/product/global-seismic-hazard-map>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The base map is a composite of regional/national PSHA models and is not an event catalogue or loss model. Exact layer/format licensing differs: public hazard map is CC BY-NC-SA 4.0 and commercial use requires separate agreement. Preserve PGA units, return/exceedance definition, soil reference, version, composite regional boundaries and model dependencies. Do not assert spatial independence from ESHM20 or translate PGA directly into property claims.

## Imperial College Storm Model IRIS 10000-year synthetic tropical cyclones

**Candidate ID:** `imperial.iris.synthetic-tropical-cyclones.2024`  
**Provider:** Imperial College London / Sparks and Toumi  
**Categories:** `tropical_cyclone`, `stochastic_events`, `synthetic_tracks`, `wind`, `global`  
**Spatial scope:** Global tropical cyclone basins represented by input observation period  
**Temporal scope:** 2024 data publication, fixed present-climate representation based on 1980-2021 observations  
**Resolution / granularity:** 10000-year global synthetic tropical cyclone track/time-step data, distributed by basin in text archives; 3-hour time steps  
**Potential roles:** `tropical_cyclone_catalogue_challenge`, `stochastic_frequency_intensity_comparison`, `shared_event_year_design_research`  
**Access hint:** `public_paper_figshare_data_and_github_code_separate_exact_rights_review`  
**Authoritative source:** <https://doi.org/10.1038/s41597-024-03250-y>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** IRIS uses IBTrACS v04r00 and ERA5 fields, both upstream-dependent, so do not treat IRIS versus STORM or IBTrACS as wholly independent evidence. Simulates the post-lifetime-maximum-intensity stage, excludes pre-peak track evolution and extra/post-tropical storms, and years are independent without interannual correlation. Preserve basin/year/event identity and wind averaging definitions before comparing with STORM v4; a synthetic track is not an observed insured loss. Code is GPL-3.0; exact Figshare dataset rights require separate review.
