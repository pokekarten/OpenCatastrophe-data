<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-open-geospatial-toolchain-20261104.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-open-geospatial-toolchain-20261104.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-04`  
**Purpose:** Non-admission research index of ten free/open-source geocoding, spatial SQL, raster, grid and web-map tools complementary to active GIS source PR #1239; tools are NOT original CAT data, production geocoding authorization or model inputs.

**Entries:** 10

## Nominatim self-hosted OpenStreetMap geocoder

**Candidate ID:** `osm.nominatim.selfhosted-geocoder.workflow`  
**Provider:** osm-search / OpenStreetMap contributors  
**Categories:** `geocoding`, `open_source_software`, `address_matching`, `reverse_geocoding`  
**Spatial scope:** Worldwide to the extent of an explicitly acquired and version-pinned OpenStreetMap extract  
**Temporal scope:** Software release and imported OSM data snapshot are separately versioned; reviewed 2026-11-04  
**Resolution / granularity:** Address and place forward/reverse search returning candidate coordinates and OSM objects, not surveyed building-level truth  
**Potential roles:** `self_hosted_address_lookup`, `reverse_geocode_diagnostic`, `pelias_photon_benchmark`  
**Access hint:** `self_hosted_only_for_repeated_or_bulk_use_public_osmf_api_restricted`  
**Authoritative source:** <https://github.com/osm-search/Nominatim>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Software licensing differs by component: current repository README lists Python GPL-3.0-or-later, Lua Apache-2.0 and other files GPLv2. OSM data are ODbL; licensed source snapshot and attribution are separate. OSMF's public nominatim.openstreetmap.org service disallows systematic reverse-grid queries and autocomplete, caps requests at 1/s and restricts longer bulk work; do NOT use it as a background world-geocoding worker. This is a software/workflow discovery, not a new independent address dataset, measured building footprint, approved exposure asset, or permission to export customer locations.

## libpostal international address parsing and normalization

**Candidate ID:** `openvenues.libpostal.address-parser.workflow`  
**Provider:** openvenues / libpostal contributors  
**Categories:** `address_normalization`, `open_source_software`, `geocoding_preprocessing`  
**Spatial scope:** Global, language and address-format performance dependent on training data and country  
**Temporal scope:** Software and model-data releases separately pinned; reviewed 2026-11-04  
**Resolution / granularity:** Tokens and normalized address variants; it does not geocode to surveyed coordinates  
**Potential roles:** `multilingual_address_parsing`, `geocoder_candidate_preprocessing`, `normalization_error_audit`  
**Access hint:** `local_software_and_model_download_required_no_public_address_api`  
**Authoritative source:** <https://github.com/openvenues/libpostal>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** MIT-licensed software per upstream LICENSE. Statistical model artifacts and source/training-data lineage need an exact-version and terms review; parsing errors can reorder units, house numbers or street names. Preserve untouched input, parser/model version, country and language hints, and per-field alternatives. Do not publish sensitive/customer address text or infer an exact building match from a successfully parsed string.

## DuckDB Spatial extension for local and external geospatial analysis

**Candidate ID:** `duckdb.spatial.local-geoparquet-analysis.workflow`  
**Provider:** DuckDB Foundation / DuckDB Spatial  
**Categories:** `spatial_sql`, `geoparquet`, `open_source_software`, `vector_processing`  
**Spatial scope:** Worldwide, conditional on separately lawfully acquired spatial datasets  
**Temporal scope:** Version-pinned DuckDB core and spatial extension required; reviewed 2026-11-04  
**Resolution / granularity:** Geometry SQL and GDAL-backed vector reads; preserves source geometry but does not provide observations  
**Potential roles:** `bounded_overture_parquet_screening`, `source_vintage_tile_comparison`, `offline_spatial_join_quality_control`  
**Access hint:** `local_spatial_extension_execution_pin_core_extension_and_driver_versions`  
**Authoritative source:** <https://duckdb.org/docs/stable/core_extensions/spatial/overview>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** DuckDB core is MIT licensed; verify spatial extension/bundled GDAL dependency and exact binary licenses for deployment. Extension is useful for versioned Overture GeoParquet partitions and bounded joins, not a canonical insurer database or primary record of building identity. Pin CRS, EPSG axis order, geometry validity, polygon-area units, input asset hash, data licence and output count/hash. Do not move provider bytes into public Git.

## PostGIS spatial joins and persistent geometry storage

**Candidate ID:** `postgis.postgresql.spatial-joins.workflow`  
**Provider:** PostGIS / OSGeo  
**Categories:** `spatial_sql`, `geodatabase`, `open_source_software`, `geometry_matching`  
**Spatial scope:** Worldwide, dependent on independently admitted and versioned source features  
**Temporal scope:** Use exact PostgreSQL/PostGIS extension versions on the selected isolated insurance database branch  
**Resolution / granularity:** OGC geometry/geography types and spatial predicates; no bundled global asset inventory  
**Potential roles:** `persistent_building_crosswalk`, `hazard_polygon_exposure_overlay`, `spatial_index_and_reconciliation`  
**Access hint:** `existing_isolated_insurance_neon_postgis_branch_not_a_new_database`  
**Authoritative source:** <https://postgis.net/documentation/faq/gpl-license/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** PostGIS is GPLv2 and its official FAQ distinguishes database use from distributing modified PostGIS source code. Existing synthetic-only PostGIS/Neon joins in OpenCatastrophe-data are not real insurer exposure admissions. Require exact geometry SRID and source identity, ST_Covers/ST_Intersects semantics, distance buffer CRS, split/merge ambiguity, and rights before ever promoting spatial matches. This is tool discovery, not authorization to write production Neon.

## H3 hierarchical hexagonal geospatial index

**Candidate ID:** `uber.h3.hexagonal-index.workflow`  
**Provider:** Uber / H3 contributors  
**Categories:** `spatial_indexing`, `aggregation`, `open_source_software`, `grid`  
**Spatial scope:** Global grid on the Earth's surface  
**Temporal scope:** Library/API version and chosen resolution fixed per run; reviewed 2026-11-04  
**Resolution / granularity:** Discrete hierarchical hexagonal cells, not building parcel boundaries or geocoded evidence  
**Potential roles:** `global_hazard_exposure_screening`, `cat_accumulation_aggregation`, `shared_world_grid_index`  
**Access hint:** `local_library_versioned_resolution_declared`  
**Authoritative source:** <https://github.com/uber/h3>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Apache-2.0 software. H3 cell IDs are computational bins, not official postcode/admin boundaries or stable physical building IDs. Boundary crossings, polar distortion, partial-cell and spatial-resolution effects require tests, especially for flood/coastal exposure and multi-peril correlations. A cell intersection is not proof that a specific building is damaged or insured.

## QGIS desktop GIS quality-control and reproducible cartography

**Candidate ID:** `qgis.desktop-gis-quality-control.workflow`  
**Provider:** QGIS project / OSGeo  
**Categories:** `gis_desktop`, `map_visualization`, `open_source_software`, `manual_review`  
**Spatial scope:** Global, contingent on input datasets, plugins and raster/vector service access  
**Temporal scope:** Pin QGIS and plugin versions, saved processing parameters and input data vintages  
**Resolution / granularity:** Interactive vector/raster viewing, overlay and processing; presentation/diagnostics rather than data creation  
**Potential roles:** `manual_building_match_adjudication`, `flood_raster_crs_review`, `research_visual_qc`  
**Access hint:** `local_desktop_tool_not_public_geocoding_endpoint`  
**Authoritative source:** <https://github.com/qgis/QGIS>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** QGIS upstream describes GPL-2.0-or-later licensing. Interactive map inspection is useful for disputed polygons, NoData, elevation and split/merge cases but is not reproducible evidence by itself; export command or processing history, layer CRS, styling, project version and numerical tests. Basemap tiles or third-party plugins may have separate licenses and terms.

## GDAL/OGR raster and vector geospatial conversion toolkit

**Candidate ID:** `osgeo.gdal.ogr.raster-vector-toolchain.workflow`  
**Provider:** GDAL/OSGeo  
**Categories:** `raster_processing`, `vector_processing`, `open_source_software`, `crs_transform`  
**Spatial scope:** Global spatial formats with supported drivers  
**Temporal scope:** Exact GDAL binary, drivers, PROJ and dependent library versions; reviewed 2026-11-04  
**Resolution / granularity:** Raster/vector read, warp, reproject, cutline, translation and format conversion; not a source of hazard measurements  
**Potential roles:** `reproducible_geotiff_processing`, `geopackage_to_geoparquet_conversion`, `crs_and_nodata_validation`  
**Access hint:** `local_command_line_library_pin_driver_and_dependency_versions`  
**Authoritative source:** <https://gdal.org/en/stable/license.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GDAL/OGR source is generally MIT licensed, but official documentation warns binary dependencies and drivers can impose different terms. Reprojection must preserve CRS, axis order, coordinate epoch and vertical datum; raster alignment, pixel-as-area conventions, NoData, resampling and depth units need explicit receipts. GDAL cannot confer reuse rights on transformed upstream data.

## MapLibre GL JS interactive web map rendering

**Candidate ID:** `maplibre.gljs.open-map-visualization.workflow`  
**Provider:** MapLibre community  
**Categories:** `web_mapping`, `open_source_software`, `visualization`  
**Spatial scope:** Global map display where authorized vector/raster tile data exist  
**Temporal scope:** Versioned JS renderer, style and tileset snapshots; reviewed 2026-11-04  
**Resolution / granularity:** Browser vector tile rendering, layer styling and user interaction; no address geocoder or risk hazard dataset included  
**Potential roles:** `nextgen_risk_map_frontend`, `exposure_hazard_layers`, `inspection_of_geocoding_uncertainty`  
**Access hint:** `client_library_requires_separately_licensed_tiles_styles_and_attribution`  
**Authoritative source:** <https://github.com/maplibre/maplibre-gl-js>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** BSD-3-Clause software; renderer and map styles do not grant map tile, basemap or provider-data rights. Reserve public OpenCatastrophe-data for references and reproducibility metadata, and display only legally permitted spatial layers; never expose confidential insurer positions or loss records in public map tiles. Map visualization alone is not evidence of a model-ready building match.

## PMTiles versioned static geospatial tile archive

**Candidate ID:** `protomaps.pmtiles.static-tile-archive.workflow`  
**Provider:** Protomaps / PMTiles  
**Categories:** `web_mapping`, `geospatial_tiling`, `open_source_software`, `data_distribution`  
**Spatial scope:** Global or regionally bounded tilesets, based entirely on chosen inputs  
**Temporal scope:** Pin PMTiles specification/implementation, generated tileset hash and all source vintages  
**Resolution / granularity:** Single-file tile archive for range-request retrieval and offline/remote static publication  
**Potential roles:** `bounded_public_risk_map_tiles`, `hazard_layer_visualization_delivery`, `reproducible_map_release_artifact`  
**Access hint:** `local_tile_packaging_and_object_store_publication_only_after_asset_rights`  
**Authoritative source:** <https://github.com/protomaps/PMTiles>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Reference implementations use BSD-3-Clause; format specification public domain/CC0. The license of the PMTiles container is not the license of any tileset or underlying OSM/Overture layers. Tile generalization, dropped attributes, scale thresholds and caching can alter visual detail; risk and loss computations must use original version-pinned numerical geometry or raster, not map-display tiles.

## GeoServer OGC map and feature serving

**Candidate ID:** `geoserver.ogc-spatial-services.workflow`  
**Provider:** GeoServer / OSGeo  
**Categories:** `ogc_services`, `web_mapping`, `open_source_software`, `spatial_data_publication`  
**Spatial scope:** Global or regional services backed by authorized datasets  
**Temporal scope:** Pin GeoServer/OGC extension and layer configuration versions; reviewed 2026-11-04  
**Resolution / granularity:** Server publishes OGC-facing WMS/WFS/related services, not underlying observed data  
**Potential roles:** `internal_hazard_layer_services`, `bounded_catalogue_interoperability`, `nextgen_gis_layer_api`  
**Access hint:** `self_hosted_service_optional_not_needed_for_initial_offline_pilot`  
**Authoritative source:** <https://github.com/geoserver/geoserver>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GeoServer is GPL-licensed (official source and notices describe GPLv2 or later). Hosting and publishing separate spatial services entail network security, authorization, cache, service and layer-level rights reviews. WMS imagery is not necessarily suitable as analytical numeric hazard input; prefer exact original raster/vector bytes and declared coordinate systems for loss calculations. Start with static PMTiles for approved visualization and add GeoServer only when OGC operations are needed.
