<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-hazard-monitoring-services.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-hazard-monitoring-services.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-12`  
**Purpose:** Non-admission discovery registry of operational drought, landslide and severe-convective hazard monitoring services relevant to catastrophe risk.

**Entries:** 3

## Copernicus Global and European Drought Observatory WMS/WCS services

**Candidate ID:** `copernicus.cems.gdo.wms-wcs`  
**Provider:** Copernicus Emergency Management Service / European Commission Joint Research Centre  
**Categories:** `drought`, `soil_moisture`, `precipitation`, `water_storage`, `agriculture`, `web_services`  
**Spatial scope:** global and European products depending on indicator  
**Temporal scope:** operational indicators with indicator-specific archives and update cadences  
**Resolution / granularity:** WMS map layers and WCS coverages for indicators including SPI, soil-moisture anomalies, GRACE TWS anomalies, forecasts and drought-impact indicators; WCS supports GeoTIFF output  
**Potential roles:** `drought_state_monitoring`, `drought_event_definition`, `hydroclimate_validation`, `agricultural_drought_context`  
**Access hint:** `public_ogc_wms_wcs_geotiff_services`  
**Authoritative source:** <https://drought.emergency.copernicus.eu/data/wcs-service>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The current CEMS drought service documents WCS GetCoverage/DescribeCoverage and a companion WMS service for GDO/EDO indicators. Do not collapse different indicator families or versions into one variable: freeze coverage/layer ID, selected timescale, date, CRS, processing version and whether a field is observed, reanalysis-derived, forecast or composite.

## NASA Landslide Hazard Nowcast and Exposure (LHASA) 2.1

**Candidate ID:** `nasa.gsfc.lhasa.v2.1`  
**Provider:** NASA Goddard Space Flight Center / NASA Earthdata  
**Categories:** `landslide`, `near_real_time`, `hazard_nowcast`, `exposure`, `machine_learning`, `gis_services`  
**Spatial scope:** global land coverage approximately 56°S to 84°N in the current exposure service  
**Temporal scope:** April 2021-present; current overview states twice-daily updates  
**Resolution / granularity:** approximately 30 arcseconds (~1 km) hazard nowcast plus administrative exposure summaries; ArcGIS feature service supports JSON, GeoJSON and PBF  
**Potential roles:** `landslide_nowcast`, `hazard_validation`, `population_road_exposure_context`, `event_triggering`  
**Access hint:** `public_arcgis_map_and_feature_services`  
**Authoritative source:** <https://gis.earthdata.nasa.gov/portal/home/item.html?id=9e65a60a305b458bba6330baa93c0238>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** LHASA 2.1 combines GPM precipitation with SMAP antecedent soil moisture and machine learning, and the current NASA service includes exposure summaries. It is a global situational-awareness nowcast rather than local slope-stability truth; preserve model version, valid time, upstream product lineage, hazard field, administrative geometry and exposure semantics.

## NOAA Multi-Radar/Multi-Sensor System (MRMS) operational products

**Candidate ID:** `noaa.nssl.mrms`  
**Provider:** NOAA National Severe Storms Laboratory / National Weather Service  
**Categories:** `weather_radar`, `severe_convective_storm`, `hail`, `precipitation`, `flash_flood`, `near_real_time`  
**Spatial scope:** United States operational MRMS domains; product/domain dependent  
**Temporal scope:** operational real-time service plus product-specific archives  
**Resolution / granularity:** GRIB2 multi-radar/multi-sensor grids; current operational tables include 2-minute MESH and multiple hail-swath accumulations alongside precipitation and other severe-weather products  
**Potential roles:** `hail_footprint_observation`, `severe_convective_validation`, `extreme_precipitation_observation`, `flash_flood_context`  
**Access hint:** `public_operational_http_grib2_with_product_specific_archives`  
**Authoritative source:** <https://nssl.noaa.gov/projects/mrms/MRMS_data.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** NOAA documents real-time operational MRMS delivery by HTTP/LDM in GRIB2, while product tables define fields such as Maximum Estimated Size of Hail (MESH). MESH is radar/model-derived estimated hail size, not direct ground truth; preserve MRMS version, domain, product code, units, cadence, valid time, QC state and any archive/reanalysis distinction.
