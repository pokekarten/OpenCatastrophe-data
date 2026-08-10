<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-observation-context.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-observation-context.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of observation and physical-context sources relevant to catastrophe risk.

**Entries:** 17

## RADKLIM gauge-adjusted one-hour precipitation sums v2017.002

**Candidate ID:** `dwd.radklim.rw.v2017.002`  
**Provider:** Deutscher Wetterdienst  
**Categories:** `precipitation`, `weather_radar`, `extreme_rainfall`, `validation`  
**Spatial scope:** Germany  
**Temporal scope:** 2001-2025 available through the core release and later extensions as of 2026-08  
**Resolution / granularity:** 1 km grid; hourly gauge-adjusted radar precipitation sums  
**Potential roles:** `extreme_precipitation_validation`, `flood_forcing`, `convective_hazard_context`  
**Access hint:** `public_download`  
**Authoritative source:** <https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_RADKLIM_RW_V2017.002-en.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Extensions and supplements sit outside the original DOI core; freeze the exact time span and corrected/supplement files, including the documented 2021 NetCDF correction, before use.

## CatRaRE W3 Eta heavy-rainfall event catalogue v2025.01

**Candidate ID:** `dwd.catrare.w3-eta.v2025.01`  
**Provider:** Deutscher Wetterdienst  
**Categories:** `extreme_rainfall`, `event_catalogue`, `weather_radar`, `validation`  
**Spatial scope:** Germany  
**Temporal scope:** 2001-2024  
**Resolution / granularity:** independent radar-based heavy-rainfall events derived from 1 km RADKLIM-RW across 11 accumulation durations  
**Potential roles:** `pluvial_flood_event_validation`, `extreme_rainfall_catalogue`, `event_severity_benchmark`  
**Access hint:** `public_download`  
**Authoritative source:** <https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_CatRaRE_W3_Eta_v2025.01-en.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Event objects are derived using a specific W3 threshold and Eta selection method; preserve catalogue version, event-definition semantics and the distinction from raw precipitation fields.

## HYRAS-DE hydrometeorological gridded data

**Candidate ID:** `dwd.hyras-de`  
**Provider:** Deutscher Wetterdienst  
**Categories:** `hydrometeorology`, `precipitation`, `temperature`, `humidity`, `climate_baseline`  
**Spatial scope:** Germany, with related HYRAS products extending into adjacent river basins  
**Temporal scope:** long-term daily products including 1951-2020 reference data; product-dependent updates  
**Resolution / granularity:** product-dependent daily grids; HYRAS-DE precipitation includes 1 km products and broader HYRAS variables include 5 km grids  
**Potential roles:** `regional_climate_baseline`, `hydrological_forcing`, `bias_adjustment_reference`  
**Access hint:** `public_hyras_de_with_product_specific_scope`  
**Authoritative source:** <https://www.dwd.de/DE/leistungen/hyras/hyras.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Do not treat the HYRAS family as one homogeneous asset: geography, variable, grid, version and access conditions differ between HYRAS-DE and broader project products.

## SMAP L4 Global Surface and Root Zone Soil Moisture Geophysical Data v8

**Candidate ID:** `nasa.smap.spl4smgp.v8`  
**Provider:** NASA NSIDC DAAC  
**Categories:** `soil_moisture`, `hydrology`, `drought`, `landslide_context`  
**Spatial scope:** global land  
**Temporal scope:** 2015-present  
**Resolution / granularity:** 3-hourly 9 km EASE-Grid 2.0 land-surface fields  
**Potential roles:** `antecedent_soil_moisture`, `flood_and_landslide_covariates`, `drought_state_validation`  
**Access hint:** `earthdata_access`  
**Authoritative source:** <https://nsidc.org/data/spl4smgp/versions/8>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is a model-and-assimilation Level-4 product rather than direct soil-moisture observations at every grid cell; preserve version, assimilation inputs and quality fields.

## JPL GRACE/GRACE-FO Mascon CRI RL06.3Mv04

**Candidate ID:** `nasa.jpl.grace-gracefo.mascon-cri.rl06.3mv04`  
**Provider:** NASA JPL PO.DAAC  
**Categories:** `terrestrial_water_storage`, `groundwater_context`, `drought`, `hydrology`  
**Spatial scope:** global  
**Temporal scope:** 2002-present  
**Resolution / granularity:** monthly gridded equivalent-water-height anomalies with Coastal Resolution Improvement filtering  
**Potential roles:** `water_storage_anomaly`, `drought_and_groundwater_context`, `large_scale_hydrology_validation`  
**Access hint:** `earthdata_access`  
**Authoritative source:** <https://podaac.jpl.nasa.gov/dataset/TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Monthly mass anomalies are spatially smoothed geophysical estimates, not local groundwater measurements; preserve release, filtering, scaling and leakage semantics.

## USGS ShakeMap

**Candidate ID:** `usgs.shakemap`  
**Provider:** U.S. Geological Survey Earthquake Hazards Program  
**Categories:** `earthquake`, `ground_motion`, `event_footprint`, `validation`  
**Spatial scope:** event-dependent global and regional coverage  
**Temporal scope:** historical event products plus near-real-time significant earthquakes  
**Resolution / granularity:** event-specific ground-motion and shaking-intensity maps  
**Potential roles:** `earthquake_footprint_validation`, `ground_motion_benchmark`, `event_impact_context`  
**Access hint:** `public_event_products`  
**Authoritative source:** <https://earthquake.usgs.gov/data/shakemap/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ShakeMap combines observations and modelling and can be revised after an event; pin the exact event/product revision and distinguish measured from interpolated/modelled fields.

## Global Earthquake-Triggered Ground-Failure Inventory Database

**Candidate ID:** `usgs.earthquake-ground-failure-inventories`  
**Provider:** U.S. Geological Survey Landslide Hazards Program  
**Categories:** `earthquake`, `landslide`, `liquefaction`, `secondary_peril`, `validation`  
**Spatial scope:** global collection of event inventories  
**Temporal scope:** historical earthquake-triggered inventories  
**Resolution / granularity:** original digital inventories plus integrated records with mapping-method and completeness metadata  
**Potential roles:** `secondary_peril_validation`, `landslide_susceptibility_validation`, `liquefaction_validation`  
**Access hint:** `public_sciencebase_repository`  
**Authoritative source:** <https://www.usgs.gov/programs/landslide-hazards/science/global-earthquake-triggered-ground-failure-inventory-database>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The repository mixes USGS and non-USGS inventory authorship and heterogeneous mapping completeness; exact inventory-level provenance and rights must be preserved.

## European Ground Motion Service Basic

**Candidate ID:** `copernicus.clms.egms.basic.v1`  
**Provider:** Copernicus Land Monitoring Service  
**Categories:** `ground_motion`, `insar`, `subsidence`, `landslide_context`, `infrastructure_context`  
**Spatial scope:** Europe  
**Temporal scope:** 2016-present with annual releases  
**Resolution / granularity:** Sentinel-1 InSAR vector measurement points at approximately 5 x 20 m source resolution  
**Potential roles:** `subsidence_monitoring`, `landslide_motion_context`, `infrastructure_ground_motion`  
**Access hint:** `public_explorer_and_api`  
**Authoritative source:** <https://land.copernicus.eu/en/products/european-ground-motion-service/egms-basic>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Basic measurements are satellite line-of-sight displacement products with quality/localisation limitations; Basic, Calibrated and Ortho products must not be conflated.

## CEMS historical fire danger indices

**Candidate ID:** `copernicus.cems.fire-danger-historical.v1`  
**Provider:** Copernicus Emergency Management Service / ECMWF / JRC  
**Categories:** `wildfire`, `fire_weather`, `reanalysis`, `climate`  
**Spatial scope:** global land  
**Temporal scope:** 1940-present  
**Resolution / granularity:** daily fire-danger indices; 0.25 degree reanalysis grid and 0.5 degree ensemble grid  
**Potential roles:** `fire_weather_baseline`, `wildfire_hazard_covariates`, `historical_fire_danger_validation`  
**Access hint:** `registered_public_data_store`  
**Authoritative source:** <https://ewds.climate.copernicus.eu/datasets/cems-fire-historical-v1>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Indices reconstruct meteorological fire danger from ERA5 forcing and are not burned-area or ignition observations; select the exact fire-danger model and variable before use.

## CAMS global atmospheric-composition reanalysis EAC4

**Candidate ID:** `copernicus.cams.eac4`  
**Provider:** Copernicus Atmosphere Monitoring Service / ECMWF  
**Categories:** `atmospheric_composition`, `smoke`, `dust`, `air_quality`, `reanalysis`  
**Spatial scope:** global  
**Temporal scope:** 2003-2025 in the current reanalysis release  
**Resolution / granularity:** 3-hourly 0.75 degree gridded atmospheric-composition fields  
**Potential roles:** `wildfire_smoke_context`, `dust_hazard_context`, `air_quality_validation`  
**Access hint:** `registered_public_data_store`  
**Authoritative source:** <https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EAC4 is an assimilated atmospheric-composition reanalysis, not direct pollutant observations everywhere; exact species, level, units and temporal aggregation must be frozen.

## NOAA CO-OPS water-level observations and derived products

**Candidate ID:** `noaa.coops.water-levels`  
**Provider:** NOAA Center for Operational Oceanographic Products and Services  
**Categories:** `coastal_water_level`, `storm_surge`, `tide_gauges`, `validation`  
**Spatial scope:** United States coasts and Great Lakes station network  
**Temporal scope:** station-dependent historical records through near-real-time observations  
**Resolution / granularity:** station observations including 1-minute, 6-minute, hourly and verified aggregate water-level products  
**Potential roles:** `storm_surge_validation`, `coastal_water_level_validation`, `extreme_water_level_benchmark`  
**Access hint:** `public_api_and_download`  
**Authoritative source:** <https://tidesandcurrents.noaa.gov/products.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Preliminary and verified products differ, and datum/time-zone selection is scientifically material; freeze station, product, datum, interval and verification state.

## NOAA DART deep-ocean tsunami measurements

**Candidate ID:** `noaa.ndbc.dart`  
**Provider:** NOAA National Data Buoy Center / Tsunami Program  
**Categories:** `tsunami`, `ocean_observations`, `bottom_pressure`, `validation`  
**Spatial scope:** operational deep-ocean DART station network  
**Temporal scope:** station-dependent real-time and historical records  
**Resolution / granularity:** bottom-pressure-derived water-column-height measurements with event-dependent reporting intervals  
**Potential roles:** `tsunami_propagation_validation`, `deep_ocean_event_detection`, `tsunami_model_benchmark`  
**Access hint:** `public_realtime_and_archive`  
**Authoritative source:** <https://www.ndbc.noaa.gov/dart/dart.shtml>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Operational, test and historical station states must be distinguished; pressure-to-height conversion, station relocation and measurement-type cadence are material semantics.

## Integrated Global Radiosonde Archive v2.2

**Candidate ID:** `noaa.ncei.igra.v2.2`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `upper_air`, `weather_observations`, `wind`, `humidity`, `validation`  
**Spatial scope:** global network of more than 2,800 stations  
**Temporal scope:** 1905-present with near-real-time data from a subset of stations  
**Resolution / granularity:** radiosonde and pilot-balloon soundings at pressure and height levels plus derived parameters  
**Potential roles:** `upper_air_validation`, `wind_profile_validation`, `convective_environment_context`  
**Access hint:** `public_https_download`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/weather-balloon/integrated-global-radiosonde-archive>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Station history, source streams, pressure/height level types and sounding-derived parameters must remain distinct; network coverage changes substantially over time.

## Randolph Glacier Inventory v7

**Candidate ID:** `nsidc.rgi.v7`  
**Provider:** IACS / GLIMS community via NASA NSIDC DAAC  
**Categories:** `cryosphere`, `glacier_geometry`, `climate_context`, `exposure_context`  
**Spatial scope:** global glaciers outside ice sheets  
**Temporal scope:** inventory snapshot centred approximately on year 2000  
**Resolution / granularity:** glacier outlines, complexes, centerlines, hypsometry and attributes  
**Potential roles:** `glacier_exposure_context`, `glacial_hazard_context`, `cryosphere_baseline`  
**Access hint:** `nsidc_data_access`  
**Authoritative source:** <https://nsidc.org/data/nsidc-0770/versions/7>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** RGI v7 is a glacier-outline inventory snapshot and is explicitly not suitable as a glacier-by-glacier area-change-rate time series.

## ICESat-2 ATL06 Land Ice Height v7

**Candidate ID:** `nasa.icesat2.atl06.v7`  
**Provider:** NASA NSIDC DAAC  
**Categories:** `cryosphere`, `elevation`, `land_ice`, `validation`  
**Spatial scope:** global land-ice observation tracks  
**Temporal scope:** ICESat-2 mission period  
**Resolution / granularity:** geolocated land-ice surface-height estimates with quality and ancillary parameters  
**Potential roles:** `land_ice_elevation_validation`, `glacier_change_context`, `cryosphere_hazard_research`  
**Access hint:** `earthdata_access`  
**Authoritative source:** <https://nsidc.org/data/atl06/versions/7>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** ATL06 heights are referenced to the WGS84 ellipsoid and include quality parameters; track sampling must not be treated as a wall-to-wall gridded elevation surface.

## Copernicus HRL Impervious Built-Up 2024

**Candidate ID:** `copernicus.clms.impervious-built-up.2024`  
**Provider:** Copernicus Land Monitoring Service  
**Categories:** `built_environment`, `imperviousness`, `exposure_context`, `remote_sensing`  
**Spatial scope:** Europe  
**Temporal scope:** 2024 reference year  
**Resolution / granularity:** 10 m binary built-up grid plus 100 m share-of-built-up layer and confidence information  
**Potential roles:** `built_environment_proxy`, `urban_exposure_context`, `runoff_and_pluvial_flood_covariates`  
**Access hint:** `public_download_via_wekeo`  
**Authoritative source:** <https://land.copernicus.eu/en/products/high-resolution-layer-imperviousness/impervious-built-up-2024>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The current 2024 product is marked validation pending; built-up presence and imperviousness are exposure proxies rather than individual insured-building records.

## EUBUCCO v0.2 European building stock database

**Candidate ID:** `eubucco.buildings.v0.2`  
**Provider:** EUBUCCO / Potsdam Institute for Climate Impact Research / Technical University Berlin  
**Categories:** `buildings`, `exposure_context`, `building_attributes`, `vulnerability_context`  
**Spatial scope:** EU-27, United Kingdom, Norway and Switzerland  
**Temporal scope:** v0.2 harmonised release with source-dependent building vintages  
**Resolution / granularity:** individual building footprints and harmonised attributes for more than 322 million buildings  
**Potential roles:** `building_exposure_context`, `vulnerability_covariates`, `high_resolution_exposure_benchmark`  
**Access hint:** `public_download_with_source_specific_licensing`  
**Authoritative source:** <https://docs.eubucco.com/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** EUBUCCO harmonises many government, OSM and Microsoft sources and mixes ground-truth, merged and ML-estimated attributes; downstream use must preserve per-source provenance, uncertainty and licence compatibility.
