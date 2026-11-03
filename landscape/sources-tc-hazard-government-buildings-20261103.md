<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-tc-hazard-government-buildings-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-tc-hazard-government-buildings-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Research-only original-product discovery for global tropical-cyclone coastal wind exceedance validation and country-specific authoritative building-footprint provider discovery. No event-level CAT catalogue, property locations, insured TIV or source reuse/admission is inferred.

**Entries:** 2

## CHAZ 2025 global coastal tropical cyclone wind hazard maps

**Candidate ID:** `global.chaz.tc-coastal-wind-exceedance-maps.2025`  
**Provider:** Columbia tropical cyclone hazard model researchers via Dryad  
**Categories:** `tropical_cyclone`, `windstorm`, `hazard`, `return_period`, `climate_scenarios`, `model_validation`  
**Spatial scope:** Global coastal land-facing hazard map sites; not recommended for over-ocean interpolation or individual storm reconstruction  
**Temporal scope:** Dryad 2025-11-19 version; ERA5-based reference 1981-2019, 1995-2014 climate historical baseline, 2041-2060 and 2081-2100 future scenarios  
**Resolution / granularity:** 58.45 GB dataset: 44.69 GB exceedance_intensity.zip and 13.75 GB return_periods.zip plus README; point CSV and NetCDF/raster variants. Exceedance intensities rp_10 to rp_1000; threshold return periods thr_33 and thr_50 for 33 and 50 m/s; per-GCM and SSP outputs.  
**Potential roles:** `independent_tc_site_wind_exceedance_benchmark`, `coastal_wind_return_period_cross_model_challenge`, `climate_scenario_sensitivity_context`  
**Access hint:** `publisher_dataset_page_and_readme_verified_cc0_label_but_file_rights_and_byte_identity_not_admitted`  
**Authoritative source:** <https://datadryad.org/dataset/doi:10.5061/dryad.qfttdz0vz>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Published Dryad dataset page explicitly labels this dataset CC0, while associated Scientific Data article has its own publication licence; distinguish dataset rights from article rights and verify each original asset before admission. These are derived spatial exceedance/return-period maps, NOT original per-event cyclone tracks, historical wind observations, annual event frequency or loss tables. Raster.nc regular grid interpolation over oceans is explicitly cautioned against. Neither 58 GB files nor original hashes were acquired; 2025 product and scenario identities are unverified at byte level.

## NUS Open Government Building Data global authoritative source index

**Candidate ID:** `global.nus-ogbd.government-building-dataset-index.2021`  
**Provider:** National University of Singapore Urban Analytics Lab  
**Categories:** `buildings`, `exposure`, `source_discovery`, `government_geodata`, `national_footprints`, `geometry_provenance`  
**Spatial scope:** Global inventory of governmental building-footprint providers, including Europe and national or subnational datasets elsewhere; not a uniform worldwide footprint layer  
**Temporal scope:** Public beta inventory originally published 2021-07-09; project warns many outbound links were checked in Q2 2021 and can now be stale  
**Resolution / granularity:** Index links to national, regional and city governmental 2D building polygon datasets; the index refers to provider collections jointly spanning more than 100 million building footprints; geometry and semantic attributes vary by provider  
**Potential roles:** `find_national_official_building_polygon_replacements`, `overture_microsoft_google_crosswalk_validation`, `source_licence_vintage_completeness_preflight`, `exposure_building_coverage_diagnostics`  
**Access hint:** `public_index_only_individual_national_authorities_have_separate_current_licences_and_original_downloads`  
**Authoritative source:** <https://ual.sg/project/ogbd/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NUS OGBD is a source catalogue and map, NOT a redistributable global building-footprint file or permission for all listed datasets. Its source list is a preliminary 2021 snapshot and country URLs, releases and access rights require independent rechecks. Government footprints are not observed insurer TIV, policy coverage or address-level carrier allocation. For each national candidate verify source currency, semantic attributes, geometry CRS/topology, partial coverage and duplicates with Overture/OSM before any CAT exposure research.
