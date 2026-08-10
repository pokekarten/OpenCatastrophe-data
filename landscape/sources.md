<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of potentially useful catastrophe-risk data sources.

**Entries:** 31

## GEBCO_2026 Grid

**Candidate ID:** `gebco.global-terrain-grid.2026`  
**Provider:** GEBCO  
**Categories:** `terrain`, `bathymetry`, `baseline_geography`  
**Spatial scope:** global  
**Temporal scope:** 2026 release  
**Resolution / granularity:** 15 arc-second grid  
**Potential roles:** `coastal_hazard_context`, `terrain_baseline`, `bathymetric_context`  
**Access hint:** `public_download`  
**Authoritative source:** <https://www.gebco.net/data-products-gridded-bathymetry-data/gebco2026-grid>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Global ocean-and-land terrain model; evaluate vertical-datum caveats and coastal suitability before model use.

## ERA5-Land hourly data from 1950 to present

**Candidate ID:** `copernicus.c3s.era5-land`  
**Provider:** Copernicus Climate Change Service / ECMWF  
**Categories:** `climate`, `reanalysis`, `hydrometeorology`  
**Spatial scope:** global land  
**Temporal scope:** 1950-present  
**Resolution / granularity:** hourly land reanalysis  
**Potential roles:** `meteorological_forcing`, `climate_baseline`, `hazard_covariates`  
**Access hint:** `public_catalog`  
**Authoritative source:** <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** High-value general land reanalysis candidate; exact variables, aggregation windows and use-specific validation must be frozen before admission.

## ESA WorldCover 10 m 2021 v200

**Candidate ID:** `esa.worldcover.2021.v200`  
**Provider:** European Space Agency WorldCover consortium  
**Categories:** `land_cover`, `exposure_context`, `remote_sensing`  
**Spatial scope:** global  
**Temporal scope:** 2021  
**Resolution / granularity:** 10 m land-cover map  
**Potential roles:** `land_cover_covariate`, `exposure_context`, `vulnerability_covariate`  
**Access hint:** `public_download`  
**Authoritative source:** <https://esa-worldcover.org/en/data-access>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Useful stable historical baseline; WorldCover is completed and has an operational Copernicus LCFM successor.

## Copernicus LCFM Global Land Cover 10 m

**Candidate ID:** `copernicus.clms.lcfm.global-land-cover-10m`  
**Provider:** Copernicus Land Monitoring Service  
**Categories:** `land_cover`, `remote_sensing`, `exposure_context`  
**Spatial scope:** global  
**Temporal scope:** annual products from 2020 onward  
**Resolution / granularity:** 10 m annual land-cover mapping  
**Potential roles:** `operational_land_cover`, `change_detection`, `exposure_context`  
**Access hint:** `public_catalog`  
**Authoritative source:** <https://land.copernicus.eu/en/news/lcfm-a-new-chapter-in-global-land-cover-monitoring>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Operational successor direction for WorldCover-style use cases; exact product/version should be selected before admission.

## HydroATLAS

**Candidate ID:** `hydrosheds.hydroatlas.v1`  
**Provider:** HydroSHEDS  
**Categories:** `hydrology`, `river_network`, `catchments`  
**Spatial scope:** global  
**Temporal scope:** static compiled attributes  
**Resolution / granularity:** basin, river-reach and lake attributes  
**Potential roles:** `catchment_context`, `flood_covariates`, `river_network_interoperability`  
**Access hint:** `public_download`  
**Authoritative source:** <https://www.hydrosheds.org/hydroatlas>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Strong general hydro-environmental reference candidate spanning BasinATLAS, RiverATLAS and LakeATLAS.

## SoilGrids250m version 2.0

**Candidate ID:** `isric.soilgrids250m.v2.0`  
**Provider:** ISRIC — World Soil Information  
**Categories:** `soil`, `hydrology`, `environmental_covariates`  
**Spatial scope:** global  
**Temporal scope:** modelled global soil properties  
**Resolution / granularity:** 250 m; six standard depth intervals  
**Potential roles:** `infiltration_covariates`, `landslide_covariates`, `drought_and_flood_context`  
**Access hint:** `public_service`  
**Authoritative source:** <https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Modelled soil-property maps with quantified spatial uncertainty; use should preserve modelled-versus-observed semantics.

## GEM Global Active Faults Database v2020

**Candidate ID:** `gem.global-active-faults.v2020`  
**Provider:** Global Earthquake Model Foundation  
**Categories:** `earthquake`, `faults`, `tectonics`  
**Spatial scope:** global with documented coverage gaps  
**Temporal scope:** v2020 open release  
**Resolution / granularity:** fault traces and attributes  
**Potential roles:** `seismic_source_context`, `fault_proximity_features`, `hazard_model_reference`  
**Access hint:** `public_repository`  
**Authoritative source:** <https://www.globalquakemodel.org/product/active-faults-database>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Global homogenised active-fault reference; regional completeness and ShareAlike implications require explicit review before use.

## ISC-GEM Global Instrumental Earthquake Catalogue v12.1

**Candidate ID:** `isc-gem.global-instrumental-earthquake-catalogue.v12.1`  
**Provider:** International Seismological Centre  
**Categories:** `earthquake`, `event_catalogue`, `validation`  
**Spatial scope:** global  
**Temporal scope:** 1904-2021 catalogue; v12.1 released 2025  
**Resolution / granularity:** reviewed earthquake event catalogue  
**Potential roles:** `historical_seismicity`, `hazard_calibration`, `catalogue_validation`  
**Access hint:** `public_download`  
**Authoritative source:** <https://ftp.isc.ac.uk/iscgem/download.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Purpose-built for seismic hazard and risk work; distinguish from real-time or lower-magnitude operational catalogues.

## ANSS Comprehensive Earthquake Catalog (ComCat)

**Candidate ID:** `usgs.anss.comcat`  
**Provider:** U.S. Geological Survey  
**Categories:** `earthquake`, `event_catalogue`, `event_products`  
**Spatial scope:** global contributions with network-dependent coverage  
**Temporal scope:** historical and current events  
**Resolution / granularity:** event parameters plus associated products  
**Potential roles:** `near_real_time_seismicity`, `event_enrichment`, `shakemap_and_pager_linkage`  
**Access hint:** `public_api`  
**Authoritative source:** <https://earthquake.usgs.gov/data/comcat/index.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** API-accessible operational catalogue with products such as ShakeMap, moment tensors and PAGER; contributor/preferred-origin semantics need explicit handling.

## NASA GPM IMERG V07B

**Candidate ID:** `nasa.gpm.imerg.v07b`  
**Provider:** NASA Global Precipitation Measurement Mission  
**Categories:** `precipitation`, `flood`, `climate`, `remote_sensing`  
**Spatial scope:** near-global  
**Temporal scope:** 1998-present  
**Resolution / granularity:** 0.1 degree; half-hourly and aggregated products  
**Potential roles:** `extreme_precipitation`, `flood_forcing`, `validation_covariate`  
**Access hint:** `registration_or_public_services`  
**Authoritative source:** <https://gpm.nasa.gov/data/imerg>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Multiple Early, Late and Final runs have different latency/quality; an admission must select one exact run and version.

## NASA FIRMS Active Fire Data

**Candidate ID:** `nasa.lance.firms.active-fire`  
**Provider:** NASA LANCE / FIRMS  
**Categories:** `wildfire`, `thermal_anomalies`, `remote_sensing`  
**Spatial scope:** global  
**Temporal scope:** near-real-time plus archive  
**Resolution / granularity:** sensor-dependent MODIS, VIIRS and Landsat detections  
**Potential roles:** `wildfire_event_detection`, `hazard_validation`, `event_monitoring`  
**Access hint:** `registration_required_for_downloads`  
**Authoritative source:** <https://firms.modaps.eosdis.nasa.gov/active_fire/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Near-real-time detections are later replaced by standard science-quality products; do not mix product maturity levels silently.

## Global Human Settlement Layer Data Package R2023A

**Candidate ID:** `ec-jrc.ghsl.r2023a`  
**Provider:** European Commission Joint Research Centre / Copernicus Emergency Management Service  
**Categories:** `population`, `built_environment`, `exposure_context`  
**Spatial scope:** global  
**Temporal scope:** multitemporal 1975-2030 products  
**Resolution / granularity:** product-dependent population, built-up and settlement grids  
**Potential roles:** `population_exposure`, `built_up_proxy`, `urbanisation_context`  
**Access hint:** `public_download`  
**Authoritative source:** <https://human-settlement.emergency.copernicus.eu/dataToolsOverview.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Family contains GHS-POP, GHS-BUILT and settlement products; an admission should select an exact product rather than the whole package.

## WorldPop Global 2 population R2024B

**Candidate ID:** `worldpop.global2.r2024b`  
**Provider:** WorldPop  
**Categories:** `population`, `exposure_context`, `demography`  
**Spatial scope:** global  
**Temporal scope:** 2015-2030 annual population estimates  
**Resolution / granularity:** 100 m and 1 km variants  
**Potential roles:** `population_exposure`, `human_impact_denominator`, `exposure_validation`  
**Access hint:** `public_download`  
**Authoritative source:** <https://data.worldpop.org/repo/prj/Global_2015_2030/R2024B/doc/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** High-resolution demographic surface candidate; constrained/unconstrained variants and census-model assumptions must remain explicit.

## Copernicus DEM GLO-30

**Candidate ID:** `copernicus.dem.glo-30`  
**Provider:** Copernicus Data Space Ecosystem / ESA / European Union  
**Categories:** `terrain`, `surface_model`, `baseline_geography`  
**Spatial scope:** global  
**Temporal scope:** TanDEM-X acquisition basis 2011-2015 with maintained releases  
**Resolution / granularity:** 30 m digital surface model  
**Potential roles:** `terrain_features`, `flood_and_landslide_covariates`, `elevation_baseline`  
**Access hint:** `registered_public_access`  
**Authoritative source:** <https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Digital surface model includes buildings, infrastructure and vegetation; do not treat it as bare-earth terrain without review.

## JRC Global Surface Water 1984-2024

**Candidate ID:** `ec-jrc.global-surface-water.1984-2024`  
**Provider:** European Commission Joint Research Centre  
**Categories:** `surface_water`, `flood_context`, `remote_sensing`  
**Spatial scope:** global  
**Temporal scope:** 1984-2024  
**Resolution / granularity:** Landsat-derived water occurrence and change layers  
**Potential roles:** `historical_water_extent`, `floodplain_context`, `water_change_validation`  
**Access hint:** `public_download`  
**Authoritative source:** <https://global-surface-water.appspot.com/download>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Current download surface reports a 1984-2024 dataset; separate persistent water from episodic flood interpretation.

## NOAA NCEI Storm Events Database

**Candidate ID:** `noaa.ncei.storm-events`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `severe_weather`, `historical_events`, `impact_observations`  
**Spatial scope:** United States and associated areas  
**Temporal scope:** 1950-present with event-type dependent record periods  
**Resolution / granularity:** event records with narratives, injuries, fatalities and damage fields  
**Potential roles:** `event_validation`, `impact_validation`, `historical_hazard_catalogue`  
**Access hint:** `public_search_and_bulk_download`  
**Authoritative source:** <https://www.ncei.noaa.gov/stormevents/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Collection methods and event coverage changed materially over time; loss fields require careful interpretation.

## Global Historical Climatology Network Daily (GHCN-Daily)

**Candidate ID:** `noaa.ncei.ghcn-daily`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `weather_observations`, `climate`, `validation`  
**Spatial scope:** global station network  
**Temporal scope:** historical to current updates  
**Resolution / granularity:** daily station observations  
**Potential roles:** `temperature_validation`, `precipitation_validation`, `extreme_weather_baseline`  
**Access hint:** `public_download`  
**Authoritative source:** <https://www.ncei.noaa.gov/pub/data/ghcn/daily/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Large station archive with changing station availability; quality flags, element definitions and station histories need explicit handling.

## International Best Track Archive for Climate Stewardship v04r01

**Candidate ID:** `noaa.ncei.ibtracs.v04r01`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `tropical_cyclone`, `event_catalogue`, `validation`  
**Spatial scope:** global tropical-cyclone basins  
**Temporal scope:** historical record with weekly current-version updates  
**Resolution / granularity:** storm-track points and provider parameters in netCDF, CSV and shapefile forms  
**Potential roles:** `observed_tropical_cyclone_catalogue`, `synthetic_catalogue_validation`, `track_statistics`  
**Access hint:** `public_download`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/international-best-track-archive>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Current v04r01 is updated weekly and mixes provisional/best-track availability; known pre-1950 matching issues and provider harmonisation must be handled explicitly.

## Volcanoes of the World v5.3.6

**Candidate ID:** `smithsonian.gvp.volcanoes-of-the-world.v5.3.6`  
**Provider:** Smithsonian Institution Global Volcanism Program  
**Categories:** `volcano`, `eruption_catalogue`, `geophysical_hazard`  
**Spatial scope:** global  
**Temporal scope:** Holocene and Pleistocene volcano records with current eruption updates  
**Resolution / granularity:** volcano and eruption records; downloadable lists and geospatial web services  
**Potential roles:** `volcanic_hazard_context`, `eruption_catalogue`, `volcano_exposure_screening`  
**Access hint:** `public_web_and_services`  
**Authoritative source:** <https://volcano.si.edu/gvp_votw.cfm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Version 5.3.6 is dated 26 May 2026; preserve the database version because the site is actively updated and previous versions are not generally served.

## Cooperative Open Online Landslide Repository (COOLR)

**Candidate ID:** `nasa.coolr.landslides`  
**Provider:** NASA Goddard Space Flight Center  
**Categories:** `landslide`, `event_catalogue`, `validation`  
**Spatial scope:** global with reporting bias  
**Temporal scope:** historical reports plus continuing citizen-science submissions  
**Resolution / granularity:** event reports including NASA Global Landslide Catalog and Landslide Reporter contributions  
**Potential roles:** `landslide_event_validation`, `rainfall_trigger_analysis`, `hazard_model_evaluation`  
**Access hint:** `public_platform`  
**Authoritative source:** <https://science.nasa.gov/citizen-science/landslide-reporter/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Open global landslide inventory with known reporting and language bias; event credibility and heterogeneous source provenance require explicit treatment.

## NCEI/WDS Global Historical Tsunami Database

**Candidate ID:** `noaa.ncei.global-historical-tsunami`  
**Provider:** NOAA National Centers for Environmental Information / World Data Service for Geophysics  
**Categories:** `tsunami`, `historical_events`, `runup_observations`  
**Spatial scope:** global ocean basins and affected coasts  
**Temporal scope:** 2100 BC-present  
**Resolution / granularity:** tsunami source-event and runup-location records  
**Potential roles:** `tsunami_hazard_validation`, `runup_validation`, `historical_impact_context`  
**Access hint:** `public_search_and_download`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/natural-hazards/tsunamis-earthquakes-volcanoes/tsunamis/global-historical-data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Long historical catalogue with source/runup uncertainty, changing place names and reference-level ambiguity; use validity and measurement fields explicitly.

## GRDC Global River Discharge Data Portal

**Candidate ID:** `grdc.global-river-discharge`  
**Provider:** Global Runoff Data Centre / WMO  
**Categories:** `river_discharge`, `hydrology`, `in_situ_observations`  
**Spatial scope:** global station network  
**Temporal scope:** station-dependent historical to current holdings  
**Resolution / granularity:** daily/monthly time series, metadata, statistics and catchment boundaries  
**Potential roles:** `hydrological_model_validation`, `flood_validation`, `river_discharge_baseline`  
**Access hint:** `request_form_noncommercial_research`  
**Authoritative source:** <https://grdc.bafg.de/data/data_portal/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Scientifically valuable global in-situ discharge source, but the standard portal states original data are non-commercial research use and redistribution is restricted; keep separate from freely reusable GRDC project datasets.

## WMO State of Global Water Resources 2024 underlying river-discharge dataset

**Candidate ID:** `grdc.wmo-global-water-resources-2024`  
**Provider:** Global Runoff Data Centre / World Meteorological Organization  
**Categories:** `river_discharge`, `hydrology`, `validation`  
**Spatial scope:** 1833 stations in 41 countries  
**Temporal scope:** 1991-2024  
**Resolution / granularity:** quality-controlled daily and monthly in-situ discharge observations  
**Potential roles:** `hydrological_validation`, `global_water_resources_benchmark`, `flood_context`  
**Access hint:** `public_reuse_dataset`  
**Authoritative source:** <https://grdc.bafg.de/news/2026/wmo_report_data/index.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Published by GRDC in March 2026 as the WMO 2024 report dataset and described by GRDC as freely accessible and reusable; exact Zenodo licence and file identity still require admission review.

## Global Ocean Waves Reanalysis (GLOBAL_MULTIYEAR_WAV_001_032)

**Candidate ID:** `copernicus.marine.global-waves-reanalysis`  
**Provider:** Copernicus Marine Service  
**Categories:** `ocean_waves`, `storm_surge_context`, `marine_hazard`  
**Spatial scope:** global ocean  
**Temporal scope:** 1980-present multi-year reanalysis  
**Resolution / granularity:** 1/5 degree regular-grid wave parameters at 3-hour intervals  
**Potential roles:** `wave_hazard_baseline`, `coastal_storm_context`, `marine_hazard_validation`  
**Access hint:** `public_catalog_and_api`  
**Authoritative source:** <https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_WAV_001_032/description>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** WAVERYS model/reanalysis product assimilates historical altimetry and Sentinel-1 wave spectra; preserve modelled/reanalysis semantics and exact product ID.

## Permanent Service for Mean Sea Level tide-gauge data

**Candidate ID:** `psmsl.global-tide-gauge-sea-level`  
**Provider:** Permanent Service for Mean Sea Level / UK National Oceanography Centre  
**Categories:** `sea_level`, `tide_gauges`, `coastal_hazard`  
**Spatial scope:** global tide-gauge network  
**Temporal scope:** long-term historical records with continuing updates  
**Resolution / granularity:** station sea-level records and derived products  
**Potential roles:** `sea_level_baseline`, `coastal_validation`, `long_term_trend_context`  
**Access hint:** `public_data_service`  
**Authoritative source:** <https://psmsl.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Global long-term sea-level data bank; datum, vertical-reference, station-quality and non-oceanographic signal semantics must be preserved.

## EM-DAT Public Data

**Candidate ID:** `cred.em-dat.public-data`  
**Provider:** UCLouvain Centre for Research on the Epidemiology of Disasters  
**Categories:** `disaster_impacts`, `historical_events`, `human_losses`, `economic_losses`  
**Spatial scope:** global  
**Temporal scope:** historical living database with weekly updates  
**Resolution / granularity:** event-country disaster-impact records  
**Potential roles:** `impact_validation`, `loss_context`, `disaster_event_benchmark`  
**Access hint:** `free_registered_noncommercial_paid_commercial`  
**Authoritative source:** <https://doc.emdat.be/docs/data-accessibility/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Public data are free after registration for non-commercial use, while commercial use requires a paid licence; redistribution and derived-use limits require dedicated rights review before any OpenCatastrophe admission.

## CMIP6 climate projections

**Candidate ID:** `copernicus.c3s.cmip6-projections`  
**Provider:** Copernicus Climate Change Service / ECMWF / CMIP6 contributing institutes  
**Categories:** `climate_projections`, `climate_change`, `scenario_data`  
**Spatial scope:** global  
**Temporal scope:** historical experiments and future SSP experiments, typically 1850-2100  
**Resolution / granularity:** model-dependent global grids with daily and monthly variables  
**Potential roles:** `future_hazard_scenarios`, `climate_change_stress_testing`, `scenario_conditioning`  
**Access hint:** `public_catalog_with_source_terms`  
**Authoritative source:** <https://cds.climate.copernicus.eu/datasets/projections-cmip6>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Multi-model projections require explicit experiment, model, member, grid, variable and scenario identity; do not collapse ensemble uncertainty into a single deterministic future.

## ERA5-Drought global drought indices

**Candidate ID:** `ecmwf.era5-drought`  
**Provider:** European Centre for Medium-Range Weather Forecasts  
**Categories:** `drought`, `climate_indices`, `hydrometeorology`  
**Spatial scope:** global  
**Temporal scope:** 1940-near-real-time  
**Resolution / granularity:** 0.25 degree monthly SPI and SPEI at 1-48 month accumulation windows  
**Potential roles:** `drought_hazard_baseline`, `drought_event_detection`, `water_stress_covariates`  
**Access hint:** `public_data_store`  
**Authoritative source:** <https://www.ecmwf.int/en/forecasts/datasets/monthly-drought-indices-1940-present-derived-era5-reanalysis>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** SPI and SPEI are derived from ERA5 and available with multiple accumulation windows and ensemble-based uncertainty information; freeze index, window, version and reference period before use.

## ESA WorldCereal global maps 2021

**Candidate ID:** `esa.worldcereal.2021`  
**Provider:** European Space Agency WorldCereal consortium  
**Categories:** `agriculture`, `crop_exposure`, `irrigation`, `remote_sensing`  
**Spatial scope:** global  
**Temporal scope:** 2021 product collection with future products planned  
**Resolution / granularity:** 10 m temporary-crop, crop-type and irrigation maps  
**Potential roles:** `agricultural_exposure`, `crop_vulnerability_context`, `drought_and_flood_exposure`  
**Access hint:** `public_viewer_and_download`  
**Authoritative source:** <https://esa-worldcereal.org/en/products/global-maps>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Season definitions vary by agro-ecological zone and neighbouring regional maps are not automatically comparable; preserve product, season and crop-class semantics.

## OpenStreetMap data

**Candidate ID:** `openstreetmap.planet`  
**Provider:** OpenStreetMap contributors / OpenStreetMap Foundation  
**Categories:** `infrastructure`, `transport`, `points_of_interest`, `exposure_context`  
**Spatial scope:** global community-mapped coverage  
**Temporal scope:** continuously updated  
**Resolution / granularity:** vector nodes, ways, relations and tags  
**Potential roles:** `infrastructure_exposure`, `road_and_network_context`, `critical_facility_discovery`  
**Access hint:** `open_odbl_database`  
**Authoritative source:** <https://www.openstreetmap.org/copyright>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Open global mapping database under ODbL; completeness, tagging heterogeneity, attribution and share-alike/database obligations require explicit downstream design.

## geoBoundaries gbOpen administrative boundaries

**Candidate ID:** `geoboundaries.gbopen`  
**Provider:** William &amp; Mary geoLab / geoBoundaries community  
**Categories:** `administrative_boundaries`, `baseline_geography`, `aggregation`  
**Spatial scope:** global country and subnational administrative levels  
**Temporal scope:** versioned boundary releases  
**Resolution / granularity:** ADM0-ADM5 country files plus global composite and simplified products  
**Potential roles:** `administrative_aggregation`, `exposure_reporting`, `regional_model_packaging`  
**Access hint:** `open_cc_by_4_0_gbopen`  
**Authoritative source:** <https://www.geoboundaries.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Use the gbOpen/CC BY 4.0 line rather than less-open mirrored variants; disputed-area treatment and boundary vintage must be explicit for reproducible aggregation.
