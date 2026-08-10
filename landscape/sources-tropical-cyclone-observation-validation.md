<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-tropical-cyclone-observation-validation.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-tropical-cyclone-observation-validation.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of tropical-cyclone observational and satellite-derived validation sources relevant to catastrophe risk.

**Entries:** 3

## NOAA NCEI Advanced Dvorak Technique Hurricane Satellite (ADT-HURSAT) v1

**Candidate ID:** `noaa.ncei.adt-hursat.v1`  
**Provider:** NOAA National Centers for Environmental Information / University of Wisconsin-Madison CIMSS  
**Categories:** `tropical_cyclone`, `intensity`, `satellite_derived`, `climate_validation`  
**Spatial scope:** global tropical-cyclone record  
**Temporal scope:** 1978-2024; static first release published February 2026  
**Resolution / granularity:** storm-centred tropical-cyclone intensity estimates derived by applying ADT v9.0 to homogenized HURSAT B1 infrared imagery  
**Potential roles:** `intensity_climatology_validation`, `long_term_trend_context`, `synthetic_catalogue_intensity_benchmark`  
**Access hint:** `public_ncei_and_noaa_open_data`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/advanced-dvorak-technique-hurricane-satellite>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NOAA identifies v1 as a consistently derived 1978-2024 intensity record and explicitly warns that reduced HURSAT sampling does not preserve individual-storm intensity peaks and valleys; use it for climatology/trend-oriented comparison rather than authoritative event peak intensity, and preserve its HURSAT/IBTrACS lineage.

## NOAA NCEI Hurricane Satellite HURSAT-B1 v06

**Candidate ID:** `noaa.ncei.hursat-b1.v06`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `tropical_cyclone`, `satellite_imagery`, `storm_structure`, `historical_observations`  
**Spatial scope:** global tropical cyclones visible from the geostationary satellite constellation, with documented early Indian Ocean coverage limitations  
**Temporal scope:** 1978-2015 for current HURSAT-B1 v06  
**Resolution / granularity:** approximately 8 km, 3-hourly storm-centred geostationary imagery on a 301 x 301 grid  
**Potential roles:** `storm_structure_validation`, `satellite_imagery_benchmark`, `intensity_algorithm_input`  
**Access hint:** `public_ncei_https_download`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/hurricane-satellite-data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** HURSAT-B1 v06 is derived from ISCCP B1 geostationary observations, but its storm-centred grids use temporally interpolated IBTrACS locations; it is therefore valuable satellite-image evidence but not independent track-validation truth. Preserve version, channel/satellite availability, calibration and centering lineage.

## NOAA NCEI Blended Sea Winds (NBS) v2.0

**Candidate ID:** `noaa.ncei.blended-seawinds.v2.0`  
**Provider:** NOAA CoastWatch / NOAA National Centers for Environmental Information  
**Categories:** `tropical_cyclone`, `ocean_wind`, `satellite_observations`, `hazard_footprint`, `validation`  
**Spatial scope:** global ocean  
**Temporal scope:** retrospective science record since July 1987 plus near-real-time production with approximately one-day latency  
**Resolution / granularity:** Level-4 10 m neutral sea-surface winds on a 0.25 degree global grid, with 6-hourly, daily and monthly products  
**Potential roles:** `ocean_wind_footprint_validation`, `tropical_cyclone_wind_context`, `marine_hazard_benchmark`  
**Access hint:** `public_coastwatch_https_thredds_and_erddap`  
**Authoritative source:** <https://coastwatch.noaa.gov/cwn/products/noaa-ncei-blended-seawinds-nbs-v2.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NBS v2.0 is a multi-sensor Level-4 blend rather than a direct point observation. Wind-speed/magnitude information is multi-sensor satellite-derived, including SMAP and AMSR2 inputs that improve retrieval of very high hurricane winds, while vector direction is supplied from ERA5 for the retrospective Science Quality stream and from GFS for NRT. Preserve exact science-versus-NRT stream, direction-model lineage, source-sensor availability, blending assumptions and ocean-only semantics before any footprint validation; do not treat the complete vector field as independent satellite evidence against ERA5 or GFS.
