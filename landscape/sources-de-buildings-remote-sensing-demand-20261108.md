<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-de-buildings-remote-sensing-demand-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-de-buildings-remote-sensing-demand-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission discovery of five German geospatial building-related scientific source products including three remote-sensing rasters, population disaggregation and synthetic residential energy profiles. Source existence is not model-input admission or permission for commercial reuse.

**Entries:** 5

## Germany satellite-modelled building height map 10 m (Frantz et al. 2020)

**Candidate ID:** `de.hu-berlin.building-height-map.2020`  
**Provider:** Humboldt University of Berlin / David Frantz et al.  
**Categories:** `buildings`, `building_height`, `satellite`, `raster`, `germany`  
**Spatial scope:** All of Germany; urban built-up pixels, not individual cadastral building objects  
**Temporal scope:** Map published 2020, representativeness approximately 2015; Sentinel-1 2017, Sentinel-2 2018, official reference LoD2 2012-2020  
**Resolution / granularity:** 10 m gridded predicted building heights, GeoTIFF 30 x 30 km tiles EPSG:3035; ZIP 532.1 MB; storage value scaled by 10 (69 means 6.9 metres)  
**Potential roles:** `national_height_proxy`, `raster_to_footprint_height_comparison`, `vintage_shift_sensitivity`  
**Access hint:** `public_zenodo_zip_download_data_licence_and_per_file_derivative_use_unreviewed`  
**Authoritative source:** <https://zenodo.org/records/4066295>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Predicted *average building height in a 50 m radius* at a 10 m cell, not a directly measured roof height of an individual structure. A model date around 2015 cannot verify 2026 existence. Training uses official state LoD2; agreement with contemporary IOER 3D metrics is not independent confirmation. DOI 10.5281/zenodo.4066295. Separate code GPL-3.0, Sentinel inputs and data file licensing/attribution. Never substitute height for exact floor count or insured rebuild value.

## Germany satellite-derived building types map 10 m (Schug et al. 2021)

**Candidate ID:** `de.hu-berlin.building-types-map.2021`  
**Provider:** Humboldt University of Berlin / Franz Schug et al.  
**Categories:** `buildings`, `building_typology`, `satellite`, `raster`, `germany`  
**Spatial scope:** All of Germany only in cells with sufficient detected building density  
**Temporal scope:** 2021 publication; remote sensing from Sentinel-1 2017 and Sentinel-2 2018  
**Resolution / granularity:** GeoTIFF 30 x 30 km tiles EPSG:3035, 10 m; 120.6 MB ZIP; code 0=no building, 1=commercial/industrial, 2=single-family, 3=lightweight, 4=multi-family  
**Potential roles:** `national_occupancy_class_prior`, `residential_commercial_mix_challenge`, `holdout_study_for_source_typology`  
**Access hint:** `public_zenodo_zip_download_exact_raster_licence_and_training_lineage_review`  
**Authoritative source:** <https://zenodo.org/records/4601219>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Random forest raster prediction in cells with building density above 25 percent, not observed occupancy or individual-building structure taxonomy. Same Sentinel and density upstream as Germany 10 m building fraction and height layers; not independent count/ground truth. DOI 10.5281/zenodo.4601219. Verify per-asset rights and map pixels/classes against original source dictionary before any modelling.

## Germany building fraction 10 m and 100 m remote sensing maps (Schug et al. 2022)

**Candidate ID:** `de.hu-berlin.building-fraction-map.2022`  
**Provider:** Humboldt University of Berlin / Franz Schug et al.  
**Categories:** `buildings`, `building_density`, `satellite`, `raster`, `germany`  
**Spatial scope:** All of Germany; satellite modelled fractions rather than cadastral building polygons  
**Temporal scope:** Published 2022; underlying Sentinel images 2017-2018  
**Resolution / granularity:** Building-footprint share of grid cell at nominal 10 m and 100 m, source ZIP 1.5 GB; model recommends aggregating to 20, 50 or 100 m and thresholding noisy 10 m fractional values near 20 percent  
**Potential roles:** `polygon_coverage_completeness_prior`, `building_area_vs_sealed_area_comparison`, `urban_rural_coverage_audit`  
**Access hint:** `public_zenodo_zip_download_data_rights_model_training_and_version_review`  
**Authoritative source:** <https://zenodo.org/records/6632584>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Building fraction is not general impervious surface fraction and does not enumerate structures. Dataset trained and validated against existing footprint source families, so model agreement with cadastral house outlines can be correlated. Preserve pixel scale, no-data, grid CRS and fractional value meaning; one pixel does not equal one building. DOI 10.5281/zenodo.6632584.

## Germany 10 m gridded population from building volume and census (Schug et al. 2021)

**Candidate ID:** `de.hu-berlin.gridded-population-building-covariates.2021`  
**Provider:** Humboldt University of Berlin / Franz Schug et al.  
**Categories:** `population`, `built_environment`, `exposure_context`, `raster`, `germany`  
**Spatial scope:** All of Germany; population allocated to gridded cells, not resident identity nor insured buildings  
**Temporal scope:** 2021 dataset, built from older official census, building height approximately 2015 and Sentinel 2017-2018  
**Resolution / granularity:** Three 10 m people-per-cell GeoTIFF population-disaggregation estimates, including building-volume adjusted and bottom-up resident floor-area proxies, EPSG:3035  
**Potential roles:** `residential_population_exposure_weight`, `regional_floor_area_sensitivity`, `population_vs_building_coverage_check`  
**Access hint:** `public_zenodo_dataset_release_original_methods_licence_and_census_terms_review`  
**Authoritative source:** <https://zenodo.org/records/4601292>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Derived from the same German building fraction/height/type remote-sensing layers and demographic census, thus not independent for footprint validation. 10 m values are statistical disaggregation not observed occupancy of houses or policy holders; do not infer precise residents, insurer property identities or TIV from cells. DOI 10.5281/zenodo.4601292; original data rights and vintage-specific demographic definitions require review.

## Germany eGon-data residential building electricity and heat profiles v2 (2022)

**Candidate ID:** `de.egon.residential-building-load-profiles.v2.2022`  
**Provider:** Reiner Lemoine Institut / Europa-Universitaet Flensburg / project eGon  
**Categories:** `buildings`, `residential_energy`, `building_demand`, `synthetic_buildings`, `germany`  
**Spatial scope:** Germany; residential buildings represented by matched OpenStreetMap objects and synthetic stand-ins where coverage is missing  
**Temporal scope:** Published 2022-09-14, explicit v2.0 superseding obsolete v1; input census 2011, OSM and modelled 2035 / 2050 scenarios  
**Resolution / granularity:** Open Zenodo 31.3 GB PostgreSQL backup and schema/documentation; building IDs map OSM residential polygons plus synthetic building locations to electricity and heat demand profiles  
**Potential roles:** `building_energy_model_research`, `osm_source_completeness_sensitivity`, `synthetic_residential_footprint_comparison`  
**Access hint:** `public_large_postgresql_backup_original_licence_odbl_upstream_rights_and_exact_data_release_review`  
**Authoritative source:** <https://zenodo.org/records/7071795>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is not an observed complete inventory of current residential buildings, actual power readings or real insurer portfolios. Some locations explicitly **synthetic**; mixed OSM ODbL/census/energy-method inputs need per-table lineage and privacy/redistribution review. Earlier v1 https://zenodo.org/records/6771218 is explicitly marked outdated; do not double count versions or claim independent structure identities. Do not confuse modelled heating/electricity profiles with claims, contents or business interruption values.
