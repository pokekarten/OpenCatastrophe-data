<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-global-deep-research-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-global-deep-research-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission deep source discovery using official provider documentation, Exa and public repository source-code sweeps; 17 distinct candidate source families across hazard observation, building/infrastructure exposure, event impact, risk taxonomy and source indexing, without claiming acquisition, rights clearance or independent model validation.

**Entries:** 17

## DLR WSF Tracker 2016-2026 biannual built-up surface

**Candidate ID:** `dlr.eoc.wsf-tracker.2016-2026`  
**Provider:** German Aerospace Center DLR EOC  
**Categories:** `exposure`, `built_up`, `change_detection`  
**Spatial scope:** Global except published latitude limits; extent roughly 60 S to 78 N  
**Temporal scope:** 2016-2026 six-month composite time series, release June 2026  
**Resolution / granularity:** 10 m classified settlement presence/change, STAC collection WSF_TRACKER, COG/HTTP and WMS  
**Potential roles:** `exposure_vintage`, `building_stock_change`, `pre_post_event_settlement_context`  
**Access hint:** `public_stac_cog_and_wms_cc_by_4_0_product_review`  
**Authoritative source:** <https://geoservice.dlr.de/web/datasets/wsf_tracker>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Genuine new temporal product distinct from registered DLR WSF 2019, Evolution 1985-2015 and 3D. Licence stated CC BY 4.0 and DOI 10.15489/3fa4d2j0tk78; freeze tile time, class codes, STAC item, input Sentinel lineage. Built-up pixel is not an individual building, construction material, occupancy or insured value.

## DLR WSF 3D Material Stock global 90 m grids

**Candidate ID:** `dlr.eoc.wsf-3d-material-stock.2024`  
**Provider:** German Aerospace Center DLR EOC  
**Categories:** `exposure`, `building_materials`, `construction`, `volume`  
**Spatial scope:** Global gridded regions with product mask and resolution limits  
**Temporal scope:** Publisher release 25 October 2024, product-specific static snapshot  
**Resolution / granularity:** 90 m kg material stocks: all materials, biomass, fossil-based, metals and minerals  
**Potential roles:** `material_proxy`, `construction_type_calibration`, `replacement_cost_prior`  
**Access hint:** `public_raster_download_cc_by_4_0_product_review`  
**Authoritative source:** <https://web.geoservice.dlr.de/web/datasets/wsf_3d_matstock>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from already registered DLR WSF 3D height/volume v02. License stated CC BY 4.0; modeled kilograms per 90 m pixel are not engineering construction-type observations or insured replacement values. Record model uncertainty, units, aggregation, material category and exact version.

## JRC GDACS Global Flood Detection System version 2

**Candidate ID:** `ec.jrc.gfds.v2.passive-microwave-flood`  
**Provider:** European Commission Joint Research Centre  
**Categories:** `flood`, `satellite_observation`, `hydrology`  
**Spatial scope:** Global river/wetland water signals, coarse microwave footprint limits  
**Temporal scope:** 1997 onward daily / 4-day average, updated operationally  
**Resolution / granularity:** Merged and single-sensor daily passive-microwave satellite raster metrics TRMM AMSR-E AMSR2 GPM  
**Potential roles:** `historic_flood_signal`, `independent_radar_crosscheck`, `basin_event_matching`  
**Access hint:** `public_http_raster_archives_provider_terms_review`  
**Authoritative source:** <https://www.gdacs.org/flooddetection/data/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from registered Sentinel-1 CEMS GFM, DFO event inventories and static flood hazard return periods. Official GFDS v2 product explains merged/single sensors and half-pixel displacement artifacts; coarse daily surface water change is not building-scale inundation depth. Resolve grid, scaling, baseline, product and reuse rights before modelling.

## FAO GIEWS Agricultural Stress Index System (ASIS) vegetation/drought products

**Candidate ID:** `fao.giews.asis.global.1984-2026`  
**Provider:** Food and Agriculture Organization of the United Nations  
**Categories:** `drought`, `agriculture`, `vegetation`, `remote_sensing`  
**Spatial scope:** Global agricultural land/seasonal masks; variable-dependent areas  
**Temporal scope:** 1984 onward; near-real-time dekadal and historical frequency summaries  
**Resolution / granularity:** 1 km agricultural stress index, drought intensity, vegetation condition/health, 16000+ raster layers via FAO services  
**Potential roles:** `agricultural_drought_intensity`, `crop_exposure_context`, `historic_drought_validation`  
**Access hint:** `fao_image_services_wmts_download_terms_and_gee_request_review`  
**Authoritative source:** <https://www.fao.org/giews/earthobservation/access.jsp>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official FAO access page describes global 1 km 1984-present rasters, WMTS/ArcGIS/download and GEE assets requiring request. Vegetation stress is not observed farm revenue loss; mask seasons, LCT, legend and water balance, separate current product from historical return period.

## TerraClimate v1.1 global monthly climate and water balance

**Candidate ID:** `climatologylab.terraclimate.v1.1`  
**Provider:** University of Idaho Climatology Lab  
**Categories:** `drought`, `heat`, `precipitation`, `soil_moisture`  
**Spatial scope:** Global land excluding dataset-specific gaps  
**Temporal scope:** Monthly archives 1958 onward, v1.1 updates in 2025-2026  
**Resolution / granularity:** Approx 4 km monthly netCDF: precipitation, runoff, deficit, soil water, PDSI, temperatures, vpd and more  
**Potential roles:** `drought_weather_driver`, `antecedent_flood_conditions`, `climate_covariate_hindcast`  
**Access hint:** `public_thredds_netcdf_and_gee_detailed_rights_review`  
**Authoritative source:** <https://www.climatologylab.org/terraclimate.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** TerraClimate v1.1 now uses ERA5 anomalies with WorldClim normals; not independent of ERA5 or a daily event observation. Provider documents change in inputs, alternate 1950 vs 1958 starts and scaled netCDF variables; preserve v1.1 version, units, temporal resolution and licence per distribution.

## INGV CPTI15 version 4.0 Italian historical parametric earthquake catalogue

**Candidate ID:** `ingv.cpti15.italy.v4.0`  
**Provider:** Istituto Nazionale di Geofisica e Vulcanologia  
**Categories:** `earthquake`, `history`, `seismology`  
**Spatial scope:** Italy and neighboring earthquake sources  
**Temporal scope:** Historical earthquakes from year 1000 to 2020 per provider dataset  
**Resolution / granularity:** Earthquake parameters accessible via FDSN event and OGC WFS/WMS  
**Potential roles:** `historical_earthquake_crosswalk`, `italy_magnitude_hazard_challenge`  
**Access hint:** `provider_public_fdsn_wfs_dataset_license_per_release_review`  
**Authoritative source:** <https://data.ingv.it/en/dataset/675>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CPTI15 v4.0 is regional historical catalog with published FDSN WFS endpoints; not a substitute for ComCat and may overlap ESHM inputs. Freeze catalogue release, magnitude calibration, epicentral uncertainty, preliminary historical event definitions and terms before downstream use.

## INGV DISS v3.3.1 active seismogenic fault-source geometry

**Candidate ID:** `ingv.diss.seismogenic-sources.v3.3.1`  
**Provider:** Istituto Nazionale di Geofisica e Vulcanologia  
**Categories:** `earthquake`, `tectonics`, `fault_geometry`  
**Spatial scope:** Italy and surrounding offshore areas  
**Temporal scope:** Version 3.3.1 released March 2025, DOI 10.13127/diss3.3.1  
**Resolution / granularity:** Georeferenced faults and seismogenic source parameters as GeoJSON and WFS  
**Potential roles:** `earthquake_rupture_source_prior`, `tectonic_hazard_calibration`, `offshore_fault_context`  
**Access hint:** `public_geojson_wfs_cc_by_4_0_product_specific_review`  
**Authoritative source:** <https://diss.ingv.it/data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher states DISS releases CC BY 4.0 unless noted; distinguish individual/compound/debated sources and incompleteness. Already-registered GEM Global Active Faults and ESHM are not this original Italian DISS source; overlap in underlying studies requires lineage check.

## INGV Italian Tsunami Effects Database (ITED) version 1

**Candidate ID:** `ingv.ited.italian-tsunami-effects.v1`  
**Provider:** Istituto Nazionale di Geofisica e Vulcanologia  
**Categories:** `tsunami`, `observed_impact`, `coastal_hazard`  
**Spatial scope:** Italian coasts with four remote-source events included  
**Temporal scope:** Historical observed tsunami effects, provider version 1  
**Resolution / granularity:** 318 observed locations / 189 place names at provider description; WFS point geometry with run-up inundation and intensity metadata  
**Potential roles:** `tsunami_runup_validation`, `coastal_event_crosswalk`, `independent_damage_evidence`  
**Access hint:** `public_wfs_wms_cc_by_4_0_product_review`  
**Authoritative source:** <https://tsunamiarchive.ingv.it/tsunami-catalogues/ited-italian-tsunami-effects-database>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official INGV provides OGC WFS/WMS and CC BY 4.0. Points may be proxy place names not measurement coordinates. Cross-linked with EMTC2.0, so not an independent event source; freeze run-up datum/units, observation type, source reliability and release.

## BNPB InaRISK official Indonesia multi-hazard map services

**Candidate ID:** `id.bnpb.inarisk.hazard-mosaic.2026`  
**Provider:** Indonesia National Disaster Management Agency BNPB  
**Categories:** `multi_hazard`, `flood`, `earthquake`, `tsunami`, `volcano`, `landslide`  
**Spatial scope:** Indonesia, service-specific geographies and mapping vintages  
**Temporal scope:** Current operational map services with variable layer and map releases  
**Resolution / granularity:** ArcGIS REST MapServer and ImageServer flood, tsunami, liquefaction, volcano, landslide, wildfire, drought risk indices  
**Potential roles:** `regional_peril_baseline`, `risk_index_challenge`, `indonesia_exposure_context`  
**Access hint:** `public_arcgis_rest_catalogue_per_layer_access_and_rights_review`  
**Authoritative source:** <https://gis.bnpb.go.id/server/rest/services/inarisk>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official BNPB ArcGIS directory visibly exposes hazard, vulnerability, risk, and capacity indexes. A hazard index is not an observed event-depth or individual building damage. Each image/map layer requires source metadata, CRS, return period, vintage, feature-query availability and rights review; avoid using index as physical intensity.

## BNPB DIBI Indonesian historical hydrometeorological disaster maps

**Candidate ID:** `id.bnpb.dibi.hydromet-events.2015-2024`  
**Provider:** Indonesia National Disaster Management Agency BNPB  
**Categories:** `multi_hazard`, `event_loss`, `hydrometeorology`  
**Spatial scope:** Indonesia provinces and listed hydromet event reporting jurisdictions  
**Temporal scope:** Provider-labeled 2015-2024  
**Resolution / granularity:** Official ArcGIS REST MapServer exposes two esriGeometryPolygon feature layers, Provinsi_basah_kering and Kabupaten_basah_kering, in EPSG:4326; map has Query capability, 2000 max records; event-level features NOT established  
**Potential roles:** `regional_hydromet_aggregate_context`, `province_district_drought_wetness_comparison`, `historical_event_source_discovery_only`  
**Access hint:** `public_arcgis_rest_metadata_available_rights_and_query_fields_review`  
**Authoritative source:** <https://gis.bnpb.go.id/server/rest/services/inarisk/DIBI_Hidromet_2015_2024/MapServer>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original public MapServer ?f=pjson inspected: layers 0 Provinsi_basah_kering and 1 Kabupaten_basah_kering are provincial/district wet-dry classification polygons, not demonstrably individual event or damage records. Service name includes DIBI_Hidromet_2015_2024 but does NOT prove event-level losses; correct initial hypothesis and require layer field-level metadata and permissions. Original service supports Map/Query/Data but no historic-moment endpoint and denies export tiles.

## NOAA NCEI historical tsunami gauge runup and eyewitness observations GIS

**Candidate ID:** `noaa.ncei.tsunami-observations-arcgis`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `tsunami`, `observed_runup`, `tide_gauge`, `impact`  
**Spatial scope:** Worldwide where reports and instruments are available; severe sampling bias  
**Temporal scope:** Historical tsunami observations, layer-specific event vintage  
**Resolution / granularity:** ArcGIS REST point features: gauge/deep-ocean gauges, eyewitnes surveys, measurement type, location  
**Potential roles:** `tsunami_runup_holdout`, `coastal_event_crosswalk`, `tsunami_measurement_provenance`  
**Access hint:** `public_noaa_arcgis_feature_layers_provenance_per_observation_review`  
**Authoritative source:** <https://gis.ngdc.noaa.gov/arcgis/rest/services/web_mercator/hazards/MapServer/layers>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct observation layers 2, 3 and 4 from already registered NOAA global historical tsunami *event catalogue*. Run-up height, gauge water level, survey observation and eyewitness report are distinct measurements; coordinate uncertainty and datum need review, no inundation polygon inferred.

## Climate Risk STAC v1.0 multi-hazard exposure vulnerability metadata catalog

**Candidate ID:** `climate-risk-data.stac.catalog.v1.0`  
**Provider:** Climate Risk Data consortium / academic research team  
**Categories:** `discovery`, `metadata`, `multi_hazard`, `exposure`, `vulnerability`  
**Spatial scope:** Global and region-specific original products linked across catalog  
**Temporal scope:** Version 1.0 released February 2026; living catalog revisions  
**Resolution / granularity:** STAC metadata entries, 214 entries over hazards, exposure and vulnerability according to 2026 paper  
**Potential roles:** `candidate_discovery`, `source_coverage_audit`, `licence_and_provenance_crosswalk`  
**Access hint:** `public_mit_software_catalog_dataset_rights_individual`  
**Authoritative source:** <https://github.com/climate-risk-data/climate-risk-stac>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Metadata registry is NOT 214 newly admitted datasets; each STAC item can share upstream publisher/product with existing sources. License of open source catalog is not the same as rights to data assets. Version-pin catalog and dedupe provider, source version and raster vintage.

## UNICEF Global Child Hazard Database multi-hazard and child exposure

**Candidate ID:** `unicef.gchd.multi-hazard.2026`  
**Provider:** UNICEF Data Science Climate and Environment Data Unit  
**Categories:** `multi_hazard`, `child_exposure`, `heat`, `drought`, `flood`  
**Spatial scope:** Global assessed regions and subnational summaries with gaps  
**Temporal scope:** 2025-2026 UNICEF processed hazard and population baselines  
**Resolution / granularity:** Source-native rasters 100 m to 15 km overlaid against 100 m age-specific WorldPop estimates; multi-hazard indicators  
**Potential roles:** `multi_peril_exposure_benchmark`, `population_context`, `method_comparison`  
**Access hint:** `public_github_processing_and_gee_assets_product_specific_license_review`  
**Authoritative source:** <https://github.com/unicef/GCHD>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Source inputs reuse already registered JRC floods, GEM hazard, WorldPop, NASA FIRMS and ERA5. UNICEF's composite hazard/exposure outputs therefore are not independent ground truth. GEE assets may require separate access; retain population baseline, sex/age limitations and underlying original sources.

## UNDRR Datum public hazard information and disaster risk APIs

**Candidate ID:** `undrr.datum.global-hazard-apis.2025`  
**Provider:** United Nations Office for Disaster Risk Reduction  
**Categories:** `metadata`, `hazard_taxonomy`, `disaster_risk`, `api`  
**Spatial scope:** Global semantic hazard profiles and national disaster-risk contextual tables  
**Temporal scope:** Published API portal updated June 2025, versioned data clusters  
**Resolution / granularity:** REST JSON versioned/paginated HIP hazard classification, GAR and Sendai datasets  
**Potential roles:** `peril_taxonomy_crosswalk`, `source_registry_semantics`, `global_country_risk_context`  
**Access hint:** `public_documented_undrr_api_attribution_required_third_party_rights_preserved`  
**Authoritative source:** <https://data.undrr.org/api/json/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from already registered UNDRR DELTA/DesInventar disaster records. Hazard Information Profiles are definitions/taxonomy and GAR/Sendai national aggregates, not event hazard footprints or insured values. UNDRR permits use with attribution but excludes third-party material, per official portal.

## UNEP CDRI Global Infrastructure Risk Model and Resilience Index GIRI

**Candidate ID:** `unep.cdri.giri.global-infrastructure-risk`  
**Provider:** UN Environment Programme / Coalition for Disaster Resilient Infrastructure  
**Categories:** `multi_hazard`, `infrastructure`, `risk_model`  
**Spatial scope:** Global infrastructure sectors and geographic units, map-layer dependent  
**Temporal scope:** Current and climate-scenario risk model outputs, vintage per layer  
**Resolution / granularity:** Over 100 infrastructure risk/hazard layers in GIRI map viewer reported by GFDRR catalog  
**Potential roles:** `infrastructure_risk_comparison`, `critical_asset_vulnerability_hypotheses`, `scenario_prior`  
**Access hint:** `official_collaborative_map_viewer_data_exports_and_model_rights_unverified`  
**Authoritative source:** <https://gfdrr.github.io/CCDR-tools/docs/external-tools.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GFDRR identifies UNEP/CDRI GIRI model, earthquakes floods tsunamis landslides cyclones drought. Model-generated risk indices are not observations or independent validation against shared underlying hazard/asset sources; find true owner download/API and per-layer licence before acquisition.

## ESIP Trusted Data for Disasters cross-domain source submissions

**Candidate ID:** `esipfed.disasters-trusted-data-now.catalog`  
**Provider:** Earth Science Information Partners (ESIP)  
**Categories:** `discovery`, `metadata`, `disaster_data`  
**Spatial scope:** International source submissions with program-specific regional focus  
**Temporal scope:** Community submitted 2025-2026, freshness not guaranteed  
**Resolution / granularity:** GitHub submitted external source registry CSV and project notes  
**Potential roles:** `long_tail_source_discovery`, `source_quality_backlog`, `global_gap_finding`  
**Access hint:** `public_github_metadata_registries_community_vetting_required`  
**Authoritative source:** <https://github.com/ESIPFed/disasters-trusted-data-now>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** A community inventory of original provider links, not validated raw catastrophe measurements. Every candidate needs verification and de-duplication against 48 landscape shards and source rights before use. Watch stale and self-submitted entries.

## UNDRR PreventionWeb Global Risk Data Collection

**Candidate ID:** `undrr.preventionweb.global-risk-data-collection`  
**Provider:** UNDRR / PreventionWeb  
**Categories:** `discovery`, `metadata`, `multi_hazard`, `exposure`  
**Spatial scope:** Global and regional hazard/risks sources from national and international organizations  
**Temporal scope:** Long-lived maintained registry with per-source individual vintages  
**Resolution / granularity:** Searchable over 100 global risk dataset entries with HIP tags and original publisher links  
**Potential roles:** `source_discovery`, `peril_coverage_audit`, `existing_source_crosswalk`  
**Access hint:** `public_catalogue_individual_dataset_licenses_apply`  
**Authoritative source:** <https://www.preventionweb.net/understanding-disaster-risk/disaster-losses-and-statistics/global-risk-data-sets>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider list reports over 100 risk dataset references; it is a meta-index rather than a new event or hazard product. Audit origin, date, GIS resolution and restrictions separately; avoid double counting GEM and other upstream products already registered.
