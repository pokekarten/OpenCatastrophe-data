<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-gis-geocoding-foundations-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-gis-geocoding-foundations-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission discovery of geospatial address, gazetteer, temporal-building, soil and self-hosted geocoding foundations for global CAT exposure linkage and map production.

**Entries:** 7

## OpenAddresses worldwide authoritative address and parcel source index

**Candidate ID:** `openaddresses.global-source-collection.2026`  
**Provider:** OpenAddresses community and underlying national/local data providers  
**Categories:** `addresses`, `geocoding`, `cadastral_parcels`, `building_geometry`, `global`  
**Spatial scope:** Global patchwork; uneven coverage and source completeness by jurisdiction  
**Temporal scope:** Rolling weekly pipeline; each country/state/source has its own vintage  
**Resolution / granularity:** Per-source address point records with street, house number, postcode and coordinate; catalog also locates parcel, building and road-centerline products  
**Potential roles:** `address_to_coordinate_matching`, `building_address_join`, `source_discovery_by_country`, `property_geocoding_quality_challenge`  
**Access hint:** `public_source_catalogue_and_per_source_batch_data_exact_rights_review`  
**Authoritative source:** <https://github.com/openaddresses/openaddresses>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Repository source definitions are CC0, but processed records retain each upstream government's original data license; do not treat the full batch as uniformly cleared. Preserve source ID, extraction vintage, coordinate precision and address-to-structure match ambiguity. Address points are not parcel valuation, building TIV or an independently verified structure footprint.

## GeoNames global place-name gazetteer and daily country extracts

**Candidate ID:** `geonames.global-gazetteer.daily.2026`  
**Provider:** GeoNames  
**Categories:** `gazetteer`, `geocoding`, `placenames`, `postal_codes`, `global`  
**Spatial scope:** Global place-name and administrative-feature coverage, uneven by region  
**Temporal scope:** Continuously revised; provider daily dumps and separate postal-code extracts  
**Resolution / granularity:** Over 13 million named geographic features with WGS84 point coordinates, feature classes, alternate names, hierarchies and optional elevation/population  
**Potential roles:** `historical_event_place_resolution`, `place_alias_normalisation`, `geocode_fallback`, `regional_event_join`  
**Access hint:** `daily_public_text_dump_web_api_username_quota_and_attribution_review`  
**Authoritative source:** <https://www.geonames.org/export/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher advertises CC BY and commercial data use, but API service limits and exact extract/license version need documented review. This is mainly a WGS84 point gazetteer, not high-resolution polygon geometry, parcel geocoding truth or independent CAT event observations. Keep GeoNames IDs, feature codes, aliases, source date and ambiguous matches.

## Who's On First global gazetteer and administrative place hierarchies

**Candidate ID:** `whosonfirst.global-place-hierarchies.geojson`  
**Provider:** Who's On First / whosonfirst-data maintainers  
**Categories:** `gazetteer`, `administrative_boundaries`, `geocoding`, `place_hierarchies`, `global`  
**Spatial scope:** Global administrative places, neighborhoods, postal-code and venue repositories with variable completeness  
**Temporal scope:** Version and revision tracked per individual GeoJSON record; source-specific vintages  
**Resolution / granularity:** Record-level GeoJSON geometry, stable 64-bit WOF identifiers, parent hierarchies, concordances and alternate names  
**Potential roles:** `place_identity_concordance`, `administrative_region_crosswalk`, `geocode_quality_control`, `historical_locality_normalisation`  
**Access hint:** `public_geojson_and_sqlite_extracts_record_provenance_and_component_licence_review`  
**Authoritative source:** <https://github.com/whosonfirst-data>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Not independent of GeoNames/OSM or other upstream gazetteers where concordances and geometry sources overlap. Inspect per-record source attribution, geometry accuracy, disputed or superseded boundaries, placetype and licenses before any commercial reuse. No insurer exposure or event-loss labels are implied.

## Microsoft TEMPO global temporal building density and height rasters

**Candidate ID:** `microsoft.tempo.building-density-height.cog.2026`  
**Provider:** Microsoft AI for Good  
**Categories:** `building_attributes`, `building_density`, `building_height`, `urban_growth`, `remote_sensing`, `global`  
**Spatial scope:** Global approximately 100 m grids for two public periods; 40 m quarterly data for five named locations  
**Temporal scope:** Global 2020 Q4 and 2023 Q4; five regions quarterly 2020 Q2 through 2025 Q2; repository update 2026-05-19  
**Resolution / granularity:** Tile-index GeoPackage and two-band Cloud-Optimized GeoTIFF, building density fraction and height scaled to metres; ~100 m global/~40 m selected regions  
**Potential roles:** `building_stock_change_prior`, `urban_growth_exposure_backcast`, `footprint_coverage_challenge`, `height_proxy_with_uncertainty`  
**Access hint:** `public_cog_gpkg_tile_index_cdla_permissive_2_rights_asset_review`  
**Authoritative source:** <https://github.com/microsoft/buildings>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct from the already admitted/discovered Microsoft Global ML Building Footprints polygon inventory. Repository explicitly licenses its COGs and GeoPackage tile index under CDLA Permissive 2.0, while code is MIT; still review selected asset/version. Both raster bands are model-derived from Planet imagery and training priors (including Overture/Google labels); they are not observed individual building heights, claims or independent holdout truth.

## OpenLandMap-soildb gridded predicted global soil properties

**Candidate ID:** `openlandmap.soildb.global-30m.2026`  
**Provider:** OpenLandMap / OpenGeoHub  
**Categories:** `soil`, `terrain_context`, `landslide`, `flood_runoff`, `global`  
**Spatial scope:** Global excluding deserts and permanent ice for documented 30 m model  
**Temporal scope:** Target 2000 through 2022+ with modeled five-year periods; publication/asset availability varies  
**Resolution / granularity:** Approximately 30 m modelled soil texture, bulk density, carbon and pH by depth 0-30, 30-60 and 60-100 cm; predicted mean and uncertainty intervals  
**Potential roles:** `soil_hydrology_parameter_prior`, `landslide_susceptibility_context`, `infiltration_runoff_prior`, `soil_model_uncertainty_challenge`  
**Access hint:** `public_documentation_stac_or_s3_exact_layer_release_and_licence_review`  
**Authoritative source:** <https://github.com/openlandmap/soildb>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Predictions use spatiotemporal machine learning from heterogeneous soil samples. Soil properties do not directly give landslide probability, river flood depth or site-level ground truth. Some underlying soil-sample catalogs have access restrictions or degraded coordinates. Check exact STAC asset, depth, unit, vintage, uncertainty and commercial licensing per layer before downloading.

## Pelias self-hosted multi-source geocoding workflow

**Candidate ID:** `pelias.geocoder.open-source.workflow`  
**Provider:** Pelias contributors  
**Categories:** `geocoding`, `software_workflow`, `addresses`, `place_hierarchies`, `global`  
**Spatial scope:** Potentially global according to independently licensed imported source extracts  
**Temporal scope:** Continuously maintained code and versioned input-data snapshots  
**Resolution / granularity:** Forward/reverse geocoding API with importers for OpenAddresses, OpenStreetMap, GeoNames, Who's On First and custom CSV  
**Potential roles:** `reproducible_address_geocoding_pipeline`, `cross_source_geocode_concordance`, `local_batch_geocoding_without_public_api_dependence`  
**Access hint:** `self_hosted_open_source_software_imported_data_rights_separate`  
**Authoritative source:** <https://github.com/pelias/pelias>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** This is software (MIT) rather than a new location dataset. Its output depends on the imported records; each input data license, snapshot, quality profile and address privacy boundary must be reviewed separately. Record version, input-source fingerprints and candidate score; ambiguous matches must not become false building locations.

## Photon OpenStreetMap forward and reverse geocoder

**Candidate ID:** `komoot.photon.osm-geocoder.workflow`  
**Provider:** komoot / Photon contributors  
**Categories:** `geocoding`, `software_workflow`, `openstreetmap`, `search`, `global`  
**Spatial scope:** According to imported OpenStreetMap coverage; potentially planet-wide  
**Temporal scope:** Continuously maintained importer and optional OSM update feed  
**Resolution / granularity:** OpenSearch-backed multilingual search-as-you-type, bounded-area and reverse-geocoding endpoints with OSM-based data  
**Potential roles:** `osm_address_resolution_comparison`, `geocoding_candidate_generation`, `local_reverse_geocoding`  
**Access hint:** `self_hosted_apache_2_software_osm_odbl_data_demo_api_not_for_bulk_use`  
**Authoritative source:** <https://github.com/komoot/photon>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Software is Apache-2.0 but its underlying OSM database retains ODbL obligations. The public Photon demo is limited and may throttle bulk workloads; use a self-hosted, version-pinned instance if justified. This is not independent of OSM, Nominatim or Overture OSM-derived building data.
