<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-gis-cross-domain-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-gis-cross-domain-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of underused GIS and cross-domain geospatial sources for global catastrophe hazard context, infrastructure continuity and synthetic exposure research. No source bytes or model inputs admitted.

**Entries:** 6

## FABDEM v1-2 forest-and-building-removed 30 m terrain

**Candidate ID:** `uk.bristol.fabdem.v1-2`  
**Provider:** University of Bristol / Fathom  
**Categories:** `terrain`, `bare_earth_elevation`, `flood`, `landslide`, `global`  
**Spatial scope:** Near-global land within the provider distribution; check tile presence and latitude boundaries before regional use  
**Temporal scope:** FABDEM v1-2 published 2023, based on earlier Copernicus DEM source imagery rather than a current terrain survey  
**Resolution / granularity:** Approximately 1 arc-second (about 30 m at the equator) global DEM; 1-degree GeoTIFF tiles distributed through larger ZIP archives  
**Potential roles:** `river_flood_hydraulic_terrain_candidate`, `coastal_inundation_screening`, `terrain_uncertainty_comparison`  
**Access hint:** `public_research_download_noncommercial_licence_commercial_permission_required`  
**Authoritative source:** <https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Source explicitly states CC BY-NC-SA 4.0 and directs commercial licensing requests to Fathom. No permission for commercial insurer model use is inferred from a public download. Corrected forest/building effects can aid terrain representation but are not surveyed ground level, flood depth, finished-floor height or insurer exposure. Pin v1-2 tile, vertical datum, spatial coverage, corrections and independent validation before any permitted use; do not acquire data until use-specific rights decision.

## Global River Widths from Landsat (GRWL) V01.01

**Candidate ID:** `allen-pavelsky.grwl.river-widths.v01-01`  
**Provider:** George H. Allen and Tamlin M. Pavelsky / Zenodo  
**Categories:** `river_geometry`, `hydrology`, `flood`, `satellite_observation`, `global`  
**Spatial scope:** Global mapped rivers and streams sufficiently wide for Landsat-based delineation; not a census of small streams  
**Temporal scope:** Original GRWL V01.01 published 2018, derived from Landsat images sampled near mean-discharge conditions; freeze selected archive and record version  
**Resolution / granularity:** 30 m Landsat-derived river mask and centerline/width vector measurements; simplified per-segment statistics and original vector archive are different files  
**Potential roles:** `river_width_hydraulic_prior`, `hydrography_network_crosscheck`, `floodplain_geometry_challenge`  
**Access hint:** `public_zenodo_versioned_shapefile_geotiff_archives_original_licence_and_sha_review`  
**Authoritative source:** <https://zenodo.org/records/1297434>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Zenodo identifies CC BY 4.0 in published record metadata, but exact file-version terms and checksum must still be independently reviewed. Widths approximate wetted rivers under selected mean-flow conditions, not flood-stage width, flow depth, discharge, levee condition or river flood hazard. Compare geometries carefully with existing HydroSHEDS and HydroATLAS, preserving tidal/canal/lake flags and sampling lineage.

## Copernicus Land Monitoring Service Coastal Zones LCLU 2018 V1

**Candidate ID:** `eu.clms.coastal-zones.lclu-2018.v1`  
**Provider:** European Environment Agency / European Union Copernicus Land Monitoring Service  
**Categories:** `coastal_exposure_context`, `land_use`, `land_cover`, `coastal_flood`, `europe`  
**Spatial scope:** European coastal territory and mapped 10 km inland coastal buffer; provider study area excludes non-covered regions  
**Temporal scope:** Nominal 2018 land-use status with 2017-2019 observation window; distinct 2012 and 2012-2018 change products exist  
**Resolution / granularity:** EPSG:3035 vector polygons; 71 thematic classes; minimum mapping unit 0.5 ha, minimum mapping width 10 m  
**Potential roles:** `coastal_occupancy_context`, `coastal_land_use_allocation_prior`, `storm_surge_exposure_crosscheck`  
**Access hint:** `public_clms_area_or_full_dataset_download_api_terms_and_archive_identity_review`  
**Authoritative source:** <https://land.copernicus.eu/en/products/coastal-zones/coastal-zones-2018>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** CLMS public policy permits commercial use with source acknowledgement and modification disclosure; the exact dataset/vintage, access receipt and downstream obligations remain unreviewed by this repository. The 2018 LCLU class is not parcel occupancy, confirmed building geometry, insured replacement value or surge depth. Preserve area boundaries, 71-class taxonomy, vintage and overlap with registered CORINE and ESA land-cover sources.

## Intact Forest Landscapes global extent and change 2000-2025

**Candidate ID:** `intactforests.ifl.global-extent.2025`  
**Provider:** Intact Forest Landscapes Mapping Team / University of Maryland, WRI and Greenpeace collaborators  
**Categories:** `forest`, `wildfire_context`, `land_cover_change`, `ecosystem`, `global`  
**Spatial scope:** Global forest landscapes meeting IFL mapped criteria, with known regional omissions and thematic definitions  
**Temporal scope:** Reference epochs 2000, 2013, 2016, 2020 and 2025  
**Resolution / granularity:** Year-specific global GeoPackage vector extents and IFL change/degradation classes; mapping scale about 1:1,000,000  
**Potential roles:** `wildfire_landscape_fragmentation_covariate`, `forest_change_validation_context`, `ecosystem_exposure_stratification`  
**Access hint:** `public_geopackage_cc_by_4_claim_original_archive_hash_and_citation_review`  
**Authoritative source:** <https://intactforests.org/data.ifl.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider currently states CC BY 4.0 including commercial reuse with attribution, subject to exact asset-level review. Intact-forest extent is a landscape-fragmentation classification, not fuel load, burned area, ignition probability, building exposure or direct fire intensity. Correlated remote-sensing inputs can overlap with existing Global Forest Change and WorldCover; do not use as an independent truth source without lineage study.

## Gridfinder global predicted electricity distribution and transmission infrastructure

**Candidate ID:** `gridfinder.global-predicted-electricity-grid.2020`  
**Provider:** Arderne, Nicolas, Zorn and Koks / Zenodo  
**Categories:** `critical_infrastructure`, `power_grid`, `electricity`, `business_interruption`, `global`  
**Spatial scope:** Global research estimates with location-dependent predictive and OSM observation coverage, not authoritative utility asset inventories  
**Temporal scope:** Research dataset released 2020, with underlying source observation vintages predating publication  
**Resolution / granularity:** Version 1.1.1 archive with grid.gpkg predicted and tagged observed lines, targets.tif connection raster and lv.tif low-voltage infrastructure density raster  
**Potential roles:** `power_outage_network_topology_prior`, `critical_infrastructure_dependency_screening`, `synthetic_industrial_business_interruption_prior`  
**Access hint:** `public_zenodo_gpkg_geotiff_archive_upstream_osm_and_exact_licence_review`  
**Authoritative source:** <https://zenodo.org/records/3628142>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinguish model-predicted lines from incorporated OSM lines by the documented source field. OSM-derived segments may carry ODbL obligations; the exact Zenodo archive license and downstream commercial database treatment have not been approved. No inferred lines are verified grid operators' assets, electrical ratings, outage states or insured plant properties; avoid double counting with OSM and other power network products.

## Global Fishing Watch API v3 vessel presence and activity products

**Candidate ID:** `globalfishingwatch.api-v3.vessel-presence`  
**Provider:** Global Fishing Watch  
**Categories:** `maritime_exposure_context`, `vessel_presence`, `ports`, `marine`, `global`  
**Spatial scope:** Global ocean and areas with AIS and partner-data coverage; vessel detection and reporting are incomplete  
**Temporal scope:** API products vary by activity layer and release, with operational updates and potential historical summaries  
**Resolution / granularity:** Authenticated API access to AIS-derived vessel presence, activity, identity and selected event statistics; spatial and temporal aggregation depends on product  
**Potential roles:** `marine_exposure_spatial_prior`, `port_activity_business_interruption_context`, `vessel_observation_coverage_bias_study`  
**Access hint:** `noncommercial_api_registration_and_token_required_no_commercial_model_permission`  
**Authoritative source:** <https://api-doc.globalfishingwatch.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GFW terms state API data are for noncommercial use only; even private work supporting a commercial insurance product is not automatically permitted. Public documentation is not a licence to bulk-harvest or redistribute vessel records. AIS may be missing, deliberately disabled or aggregated and is not a certified insured vessel location, ownership, TIV or marine hull loss. Do not call API or ingest bytes before scope, rights and access approval.
