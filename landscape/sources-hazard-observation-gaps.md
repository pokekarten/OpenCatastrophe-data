<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-hazard-observation-gaps.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-hazard-observation-gaps.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of additional hazard-observation and physical-context sources relevant to catastrophe risk.

**Entries:** 8

## Copernicus CEMS Global Flood Monitoring v4.1.1

**Candidate ID:** `copernicus.cems.gfm.v4.1.1`  
**Provider:** Copernicus Emergency Management Service / Global Flood Awareness System  
**Categories:** `flood`, `satellite_observations`, `event_footprint`, `validation`  
**Spatial scope:** global Sentinel-1 coverage  
**Temporal scope:** Sentinel-1 archive from 2015 plus near-real-time monitoring; operational v4.1.1 from June 2026  
**Resolution / granularity:** Sentinel-1 SAR-derived flood and water products with 10 m input pixel sampling and multiple uncertainty/advisory layers  
**Potential roles:** `flood_extent_validation`, `event_footprint_observation`, `inundation_model_benchmark`  
**Access hint:** `public_web_services_api_and_download`  
**Authoritative source:** <https://global-flood.emergency.copernicus.eu/react/technical-information/glofas-gfm/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GFM is an automated Sentinel-1 ensemble flood-mapping system, not a direct water-depth observation; preserve product version, acquisition footprint, exclusion/advisory flags and uncertainty layers.

## MODIS Terra+Aqua MCD64A1 Burned Area v6.1

**Candidate ID:** `nasa.modis.mcd64a1.v6.1`  
**Provider:** NASA LP DAAC / MODIS  
**Categories:** `wildfire`, `burned_area`, `remote_sensing`, `validation`  
**Spatial scope:** global  
**Temporal scope:** November 2000-present  
**Resolution / granularity:** monthly 500 m burned-area grids with burn-date and quality information  
**Potential roles:** `wildfire_footprint_validation`, `burned_area_baseline`, `fire_event_extent_benchmark`  
**Access hint:** `public_earthdata_dataset`  
**Authoritative source:** <https://doi.org/10.5067/MODIS/MCD64A1.061>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** MCD64A1 maps approximate burn date from MODIS reflectance and active-fire observations; preserve Collection 6.1, QA/uncertainty fields and the distinction between burned area and active-fire detections.

## ETOPO 2022 15 Arc-Second Global Relief Model

**Candidate ID:** `noaa.ncei.etopo.2022`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `terrain`, `bathymetry`, `global_relief`, `baseline_geography`  
**Spatial scope:** global  
**Temporal scope:** 2022 release  
**Resolution / granularity:** 15 arc-second global grids with Ice Surface and Bedrock variants plus source-ID and geoid products  
**Potential roles:** `tsunami_modelling_context`, `coastal_hazard_context`, `global_relief_baseline`  
**Access hint:** `public_download_and_grid_extract`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/etopo-global-relief-model>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ETOPO 2022 integrates heterogeneous topographic and bathymetric inputs and provides distinct ice-surface/bedrock products; source-ID, vertical reference and navigation limitations must remain explicit.

## EMODnet Bathymetry Digital Terrain Model 2024

**Candidate ID:** `emodnet.bathymetry.dtm.2024`  
**Provider:** European Marine Observation and Data Network / European Commission  
**Categories:** `bathymetry`, `coastal_hazard`, `marine_context`, `baseline_geography`  
**Spatial scope:** European seas plus the EMODnet 2024 Caribbean DTM region  
**Temporal scope:** 2024 release  
**Resolution / granularity:** 1/16 x 1/16 arc-minute grid, approximately 115 m, with source-reference and quality-index layers  
**Potential roles:** `storm_surge_context`, `tsunami_modelling_context`, `coastal_bathymetry_baseline`  
**Access hint:** `public_view_download_and_web_services`  
**Authoritative source:** <https://emodnet.ec.europa.eu/en/emodnet-bathymetry-dtm-2024-release>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The DTM combines many surveys and composite products and exposes provenance/quality layers; freeze release, region, LAT/MSL vertical reference and source-reference semantics before use.

## Meteosat Third Generation Lightning Imager Level 2

**Candidate ID:** `eumetsat.mtg-li.l2`  
**Provider:** EUMETSAT  
**Categories:** `lightning`, `convective_storm`, `satellite_observations`, `validation`  
**Spatial scope:** MTG Lightning Imager field of view from geostationary orbit near 0 degrees longitude  
**Temporal scope:** current MTG-I mission products  
**Resolution / granularity:** continuous optical total-lightning detections grouped into events, groups and flashes  
**Potential roles:** `convective_hazard_validation`, `lightning_event_catalogue`, `storm_tracking_context`  
**Access hint:** `eumetsat_data_store_and_eumetcast`  
**Authoritative source:** <https://user.eumetsat.int/resources/user-guides/mtg-li-level-2-data-guide>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** LI detects optical total-lightning activity rather than surface damage or precipitation; freeze product processing version and preserve event/group/flash definitions and detection-efficiency limitations.

## World Stress Map Database Release 2025

**Candidate ID:** `gfz.world-stress-map.2025`  
**Provider:** GFZ Helmholtz Centre for Geosciences / World Stress Map Project  
**Categories:** `tectonics`, `crustal_stress`, `earthquake_context`, `geomechanics`  
**Spatial scope:** global  
**Temporal scope:** database release 2025  
**Resolution / granularity:** quality-ranked point records of present-day crustal stress indicators  
**Potential roles:** `tectonic_context`, `fault_mechanics_context`, `geophysical_model_benchmark`  
**Access hint:** `public_open_access_download`  
**Authoritative source:** <https://www.world-stress-map.org/download/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The 2025 database is a heterogeneous quality-ranked stress compilation, not a probabilistic earthquake-hazard model; preserve indicator type, quality class and release identity.

## GFZ Geomagnetic Kp Index

**Candidate ID:** `gfz.geomagnetic-kp`  
**Provider:** GFZ Helmholtz Centre for Geosciences  
**Categories:** `space_weather`, `geomagnetic_activity`, `time_series`, `validation`  
**Spatial scope:** planetary geomagnetic index derived from contributing observatories  
**Temporal scope:** historical definitive series plus continuously updated nowcast products  
**Resolution / granularity:** 3-hour Kp index with derived ap, Ap, Cp and C9 products  
**Potential roles:** `geomagnetic_hazard_baseline`, `space_weather_event_definition`, `infrastructure_risk_context`  
**Access hint:** `public_gfz_data_service`  
**Authoritative source:** <https://doi.org/10.5880/Kp.0001>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Definitive and nowcast Kp are distinct maturity states; preserve DOI/versioning, contributing-observatory provenance and the distinction between Kp and derived indices.

## NOAA SWPC Real-Time Solar Wind

**Candidate ID:** `noaa.swpc.real-time-solar-wind`  
**Provider:** NOAA Space Weather Prediction Center  
**Categories:** `space_weather`, `solar_wind`, `magnetometer`, `plasma_observations`  
**Spatial scope:** upstream solar-wind observations near the Sun-Earth L1 point  
**Temporal scope:** archive from 1998 plus continuously updated operational data  
**Resolution / granularity:** spacecraft-dependent magnetometer and thermal-plasma time series with resolution up to seconds  
**Potential roles:** `geomagnetic_storm_driver`, `space_weather_event_context`, `infrastructure_hazard_forcing`  
**Access hint:** `public_web_and_json_services`  
**Authoritative source:** <https://www.swpc.noaa.gov/products/real-time-solar-wind>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The operational source spacecraft can switch between DSCOVR and ACE during outages; source spacecraft, data-quality flags, cadence and processing state must be explicit in any reproducible use.
