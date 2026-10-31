<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-observed-event-validation-2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-observed-event-validation-2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-10-31`  
**Purpose:** Non-admission discovery registry of source-original event footprints, cross-peril hazard proxies and empirical damage benchmarks for OpenCatastrophe scientific validation.

**Entries:** 9

## Global Flood Database MODIS Events v1

**Candidate ID:** `cloudtostreet.global-flood-database.v1`  
**Provider:** Cloud to Street / Dartmouth Flood Observatory  
**Categories:** `flood`, `observed_inundation`, `event_footprint`, `validation`  
**Spatial scope:** global; 169 countries represented by selected mapped flood events  
**Temporal scope:** 2000-2018  
**Resolution / granularity:** 913 quality-controlled flood events; MODIS-based maximum extent, inundation duration and cloud-quality bands; Earth Engine image collection and georeferenced data exports  
**Potential roles:** `flood_extent_holdout`, `event_footprint_comparison`, `observation_quality_challenge`  
**Access hint:** `earth_engine_and_external_geotiff_download_rights_restricted`  
**Authoritative source:** <https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The official Earth Engine catalogue states CC BY-NC 4.0 for flood-map data; MIT licensing of the associated analysis code must NOT be interpreted as licensing the raster data. Satellite-derived mapping is not flood depth, insured loss or a representative probability sample; preserve event IDs, cloud flags, temporal composites and commercial-use restrictions.

## COMPASS D1.4 Tropical Cyclone-Affected Areas v1.0

**Candidate ID:** `compass.tc.affected-areas.d1p4.v1`  
**Provider:** COMPASS project / Potsdam Institute for Climate Impact Research (PIK)  
**Categories:** `tropical_cyclone`, `windstorm`, `rainfall`, `storm_surge`, `compound_hazard`  
**Spatial scope:** global historical IBTrACS tropical-cyclone footprint coverage  
**Temporal scope:** 1950-2023; provisional 2024 subset; five named hourly example cyclones  
**Resolution / granularity:** NetCDF gridded 300 arc-second (~10 km) storm-lifetime maximum wind, maximum 24 h rain and modelled coastal surge depth; selected hourly wind/rain cases  
**Potential roles:** `multiperil_footprint_research`, `historical_storm_replay`, `joint_event_identity_challenge`, `parametric_hazard_comparison`  
**Access hint:** `public_zenodo_download_rights_review_required`  
**Authoritative source:** <https://zenodo.org/records/14547984>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Use the final v1.0 record, not the superseded v0.1 Zenodo version. Wind fields use H08/ER11 methods, rainfall uses TCR, surge uses GeoClaw; these are MODELLED fields partly derived from IBTrACS/ERA5, not independent observed footprints. Do not add wind/rain/surge damage, infer event frequency or reuse an IBTrACS identifier as proof of independently validated event correlation.

## Global Earthquake Impact Database (GEID)

**Candidate ID:** `gem.geid.2026`  
**Provider:** GEM Foundation / Global Earthquake Model  
**Categories:** `earthquake`, `historical_impacts`, `shaking`, `vulnerability_validation`  
**Spatial scope:** global; historical damaging earthquake case studies across multiple regions  
**Temporal scope:** historical earthquake archive; 2026 GEM release described by publisher  
**Resolution / granularity:** More than 100 event case studies with observed/reported damage, fatalities, economic impacts, station/rupture information and OpenQuake-compatible scenario resources  
**Potential roles:** `independent_earthquake_loss_validation`, `event_impact_benchmark`, `openquake_scenario_fixture_research`  
**Access hint:** `public_git_repository_case_data_separate_license_review`  
**Authoritative source:** <https://github.com/gem/geid>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinguish field observations and reported impacts from reconstructed/modelled shaking and scenario assumptions. Case-specific completeness, coverage and damage-class conventions vary; freeze an immutable release/commit and each input's provenance before quantitative comparison. No claim of historical ESRM20/Kosovo equivalence.

## ImpactMesh-Fire v1

**Candidate ID:** `ibm.impactmesh.fire.v1`  
**Provider:** IBM Research / DLR / ESA Phi-lab  
**Categories:** `wildfire`, `remote_sensing`, `burn_scar`, `machine_learning_validation`  
**Spatial scope:** global benchmark sample; 229 mapped wildfire events  
**Temporal scope:** event-based multisensor collection; version 1 documented in current publisher card  
**Resolution / granularity:** 16,512 labelled image samples, four time steps and Sentinel-1 SAR, Sentinel-2 optical, Copernicus DEM and burn-scar masks; event-separated test holdout  
**Potential roles:** `wildfire_burn_extent_segmentation`, `independent_holdout_design`, `multimodal_event_footprint_benchmark`  
**Access hint:** `public_huggingface_dataset_download_underlying_rights_review_required`  
**Authoritative source:** <https://huggingface.co/datasets/ibm-esa-geospatial/ImpactMesh-Fire>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher card labels benchmark CC BY 4.0, but underlying Sentinel/Copernicus DEM and source annotation terms require separate review. Do not treat burn-scar masks as fire heat intensity, loss or calibrated vulnerability. Retain v1 event holdout and avoid leakage across multiple temporal images of one event.

## ImpactMesh-Flood v1

**Candidate ID:** `ibm.impactmesh.flood.v1`  
**Provider:** IBM Research / DLR / ESA Phi-lab  
**Categories:** `flood`, `remote_sensing`, `observed_inundation`, `machine_learning_validation`  
**Spatial scope:** global benchmark sample; 206 mapped flood events  
**Temporal scope:** event-based multisensor collection; version 1 documented in current publisher card  
**Resolution / granularity:** 24,578 labelled samples using multi-temporal Sentinel-1 SAR, Sentinel-2 optical, Copernicus DEM and annotated flood masks; distinct event-level test holdout  
**Potential roles:** `flood_extent_segmentation`, `independent_holdout_design`, `cross_sensor_footprint_validation`  
**Access hint:** `public_huggingface_dataset_download_underlying_rights_review_required`  
**Authoritative source:** <https://huggingface.co/datasets/ibm-esa-geospatial/ImpactMesh-Flood>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher card labels benchmark CC BY 4.0; separately verify underlying satellite/DEM and original Copernicus EMS mapping rights. A flood mask is neither water depth nor insurer claim. Preserve source-event splits and avoid test leakage from multiple dates of one physical event.

## GEOID-Flood v1

**Candidate ID:** `links.geoid-flood.v1`  
**Provider:** Fondazione LINKS / Politecnico di Torino  
**Categories:** `flood`, `remote_sensing`, `sar`, `event_extent_validation`  
**Spatial scope:** 65 countries with 219 Copernicus EMS Rapid Mapping flood events  
**Temporal scope:** 2016-2026 event archive described in 2026 dataset publication  
**Resolution / granularity:** 14,282 1024x1024 image tiles at 10 m with Sentinel-1 GRD/RTC, Sentinel-2, Copernicus DEM and three-class hand-checked inundation labels; approximately 588 GB complete dataset  
**Potential roles:** `flood_segmentation_holdout`, `sar_footprint_benchmark`, `cross_sensor_quality_challenge`  
**Access hint:** `public_huggingface_large_scale_download_underlying_dem_rights_review_required`  
**Authoritative source:** <https://huggingface.co/datasets/links-ads/geoid-flood>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Compilation labels and splits are CC BY 4.0; code MIT, but the DEM has separate upstream conditions. Source authors document event-separated splits; preserve those and validity masks. Dataset size makes single bounded tile/event acquisition preferable to full bulk import. Labels distinguish flooded water from permanent water, not flood depth or insured loss.

## 2016 Tropical Cyclone Winston empirical building wind-damage dataset

**Candidate ID:** `niwa.fiji-winston-building-wind-damage.v1`  
**Provider:** NIWA / Fiji Meteorological Service / Paulik et al.  
**Categories:** `tropical_cyclone`, `windstorm`, `building_damage`, `empirical_vulnerability`  
**Spatial scope:** Fiji; selected post-event surveyed locations on Viti Levu  
**Temporal scope:** 20 February 2016 storm; March 2016 field survey; dataset released 2024  
**Resolution / granularity:** Approximately 700 building-level field-survey records as CSV, with building attributes, roof/wall damage states, water ingress, disruption and geolocated sampled sites  
**Potential roles:** `wind_vulnerability_curve_validation`, `building_damage_observation`, `empirical_hazard_to_damage_challenge`  
**Access hint:** `public_zenodo_csv_download_with_data_and_location_rights_review`  
**Authoritative source:** <https://zenodo.org/records/14353428>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The companion 2025 Data in Brief article is CC BY; verify Zenodo DATA rights separately, especially precise site coordinates and reuse scope. Survey sample is not an exhaustive census nor an insurer claims portfolio; wind-speed/source-intensity matching, construction taxonomy and selection bias require separate work.

## WFIGS Interagency Fire Perimeters

**Candidate ID:** `us.nifc.wfigs.interagency-perimeters`  
**Provider:** US National Interagency Fire Center (NIFC)  
**Categories:** `wildfire`, `observed_fire_perimeter`, `historical_events`, `spatial_validation`  
**Spatial scope:** United States  
**Temporal scope:** historical events and ongoing year-to-date/current incident layers; mutable operational updates  
**Resolution / granularity:** Per-fire polygons and IRWIN/FODR-linked event attribution through hosted ArcGIS feature services, GIS exports and public map views  
**Potential roles:** `wildfire_footprint_validation`, `event_identity_lineage`, `observational_holdout`  
**Access hint:** `public_arcgis_service_per_layer_access_and_rights_review`  
**Authoritative source:** <https://data-nifc.opendata.arcgis.com/pages/wfigs-page>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The provider warns that consolidated perimeters may be incomplete, updated late or replaced as attribution improves. Preserve retrieval time, service/layer identifiers, IRWIN/FODR IDs, geometry revision and quality flags; do not infer flame intensity, every historical fire, exposed assets or paid insurance damage from the polygon.

## 2024 Noto Peninsula earthquake building damage assessment dataset

**Candidate ID:** `vescovo.noto.earthquake-building-damage.2024`  
**Provider:** Vescovo et al. / Japanese research collaborators  
**Categories:** `earthquake`, `building_damage`, `geospatial_validation`, `empirical_impact`  
**Spatial scope:** Japan; Noto Peninsula, Ishikawa Prefecture  
**Temporal scope:** 1 January 2024 earthquake; research publication 2025  
**Resolution / granularity:** 140,208 building-footprint polygons with visually assessed damage labels assembled from multiple imagery and voluntary ground-truth sources; source deposit DOI described by authors  
**Potential roles:** `earthquake_damage_validation`, `damage_class_confusion_analysis`, `spatial_holdout_benchmark`  
**Access hint:** `public_research_data_deposit_rights_and_label_review_required`  
**Authoritative source:** <https://essd.copernicus.org/articles/17/5259/2025/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Authors point to Zenodo 10.5281/zenodo.11055711; exact dataset version and redistribution terms need separate receipt. Visual assessments and reported event effects include uncertainty and are not contract loss or directly comparable to Kosovo residential ESRM20 without harmonizing damage/exposure/ground-motion definitions.
