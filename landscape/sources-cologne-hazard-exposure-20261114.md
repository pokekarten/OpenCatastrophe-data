<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-cologne-hazard-exposure-20261114.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-cologne-hazard-exposure-20261114.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-14`  
**Purpose:** Non-admission source discovery for Cologne flood, municipal geographies and urban trees; distinguishes official reusable NRW dataset listings from viewing-only StEB 3D maps, with no data/model admission.

**Entries:** 4

## Cologne municipal statistical geography GeoPackage and KGG WFS (2026)

**Candidate ID:** `de.koeln.statistik.rbs-geopackage.2026`  
**Provider:** Stadt Köln, Amt für Stadtentwicklung und Statistik  
**Categories:** `germany`, `cologne`, `administrative_boundaries`, `address_context`, `exposure_geometry`, `wfs`  
**Spatial scope:** Stadt Köln, North Rhine-Westphalia, Germany; municipal statistical geographies, districts and street/block units, not a national building inventory  
**Temporal scope:** Continuously maintained publisher collection; public dataset page updated 2026-09-24; exact ZIP and WFS feature revision not yet captured  
**Resolution / granularity:** Published GeoPackage ZIP plus WFS collection service with city, district, neighbourhood, statistical-quarter, block and other municipal planning divisions; address data provided via separate district-scoped service  
**Potential roles:** `cologne_pilot_spatial_join_key`, `neighbourhood_aggregation_geometry`, `synthetic_exposure_geographical_support`, `regional_hazard_overlay_context`  
**Access hint:** `official_public_zip_plus_wfs_catalogue_only_original_endpoint_and_licence_per_asset_pending`  
**Authoritative source:** <https://www.offenedaten-koeln.de/dataset/geopackage-raumbezugssystem-koeln>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official Stadt Köln dataset updated 2026-09-24 lists ZIP GeoPackage RBS and KGG Sammeldienst WFS/WMS; attributes include municipal geographies and separately described address relations to ALKIS building IDs and building functions. Some address layers are published through another district-scoped service. No ZIP bytes or live WFS GetFeature receipt acquired in this review. Verify exact distribution URLs, per-asset reuse rights and WFS schema, CRS, update timestamp and identifiers before any data/model acquisition. Statistical geography is not owner, insurer, insured address or property TIV.

## Stadt Köln continuously updated managed-tree register, WFS and WMS (2026)

**Candidate ID:** `de.koeln.city-tree-register.2026`  
**Provider:** Stadt Köln, Amt für Landschaftspflege und Grünflächen  
**Categories:** `germany`, `cologne`, `urban_trees`, `windstorm`, `exposure_context`, `wfs`  
**Spatial scope:** Köln municipal street trees and city-managed trees on municipal objects only; not the complete urban tree stock  
**Temporal scope:** Publisher dataset metadata updated 2025-11-27, source describes daily updates; exact live WFS vintage not pinned  
**Resolution / granularity:** Individual managed trees with tree identifier, species, planting year, stem size, height, crown diameter and neighbourhood where recorded; WFS and WMS distributions  
**Potential roles:** `urban_tree_wind_fall_exposure_context`, `cologne_road_and_building_proximity_screening`, `municipal_tree_inventory_validation`  
**Access hint:** `official_public_wfs_and_wms_described_rights_and_technical_getfeature_not_verified`  
**Authoritative source:** <https://www.offenedaten-koeln.de/dataset/baumkataster-koeln-fortlaufend-aktualisiert>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The city explicitly limits the register to municipally managed trees and warns that location/crown coordinates are not an official site survey; the data may contain gaps after a system migration. It is not a probability of tree failure or measured wind vulnerability. Verify individual WFS endpoint, licence, exact attributes, absent values and geometry before bounded source receipts. Do not ingest ownership-like fields or infer private-tree presence or insured claims.

## NRW HWRM high-probability flood hazard depths, boundaries and velocities

**Candidate ID:** `de.nrw.lanuk.hwrm-hqhaeufig-flood.2026`  
**Provider:** LANUK Nordrhein-Westfalen / Bezirksregierungen NRW / Open.NRW  
**Categories:** `germany`, `north_rhine_westphalia`, `cologne`, `flood`, `river_flood`, `hazard_depth`, `gis`  
**Spatial scope:** North Rhine-Westphalia, Germany; to be clipped to Cologne only after geospatial and rights review  
**Temporal scope:** Original publisher HWRM folder lists original high-probability Shape ZIP updates on 2026-01-29 and GeoTIFF ZIP updates on 2026-01-30; exact archive content digest and underlying model-vintage semantics pending source acquisition  
**Resolution / granularity:** EPSG:25832 state-wide depth GeoTIFF ZIP (publisher-listed 2.4 GB), depth-in-risk-area GeoTIFF ZIP (1.1 GB), flood boundaries (142.9 MB) and velocities (5.2 MB) as Shapefile ZIP; WMS for display; no download performed  
**Potential roles:** `cologne_fluvial_hazard_overlay_candidate`, `flood_depth_damage_function_research`, `official_flood_extent_validation`  
**Access hint:** `official_nrw_hwrm_archives_datenlizenz_deutschland_zero_2_0_but_live_wms_capabilities_name_attribution_2_0_per_service_original_file_bytes_not_acquired`  
**Authoritative source:** <https://open.nrw/dataset/053549cf-b9c4-4633-80f9-680888ae5a04>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original Open.NRW resource provides specific high-probability depth TIFF ZIP https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/hochwasser/hwrm/HQhaeufig-Tiefen-UeberschwemmungsGebiete_EPSG25832_TIFF.zip and WMS https://www.wms.nrw.de/umwelt/wasser/HW_Gefahrenkarte?REQUEST=GetCapabilities&amp;SERVICE=WMS ; catalogue shows Datenlizenz Deutschland Zero 2.0 for named distributions. High probability HQ10-HQ50 is a regulatory scenario grouping, not a stochastic single-event loss frequency or building-level measured water height. Must pin original ZIP bytes, depth units, NoData, flood defence assumptions and version before admitted hazard raster or commercial use. Capabilities probe code is metadata-only. Exact original publisher index: https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/hochwasser/hwrm/ ; direct release filenames and sizes were cross-checked there on 2026-11-14. Official WMS GetCapabilities Service/AccessConstraints inspected 2026-11-14 through a third-party public XML view and states Datenlizenz Deutschland Namensnennung 2.0 with required attribution 'Land NRW'; this is different from the official downloadable HWRM archive directory, which displays DL-DE Zero 2.0. These per-distribution terms must not be conflated. The XML view showed WMS name, Service/Title, GetCapabilities and GetMap, but no original response-byte SHA-256 or executable verified_live receipt. Do not mistake external XML-to-Markdown conversion for original WMS bytes.

## StEB Köln interactive 3D pluvial and flood hazard viewer (2025)

**Candidate ID:** `de.koeln.steb-3d-pluvial-hazard.2025`  
**Provider:** Stadtentwässerungsbetriebe Köln AöR (StEB Köln)  
**Categories:** `germany`, `cologne`, `pluvial_flood`, `groundwater_flood`, `urban_flood`, `hazard_map`  
**Spatial scope:** Stadt Köln, Germany; public interactive view for heavy rainfall and Rhine/tributary or groundwater flood scenarios  
**Temporal scope:** New 3D heavy-rainfall visualisation published June 2025; future updates and scenario versions need provider confirmation  
**Resolution / granularity:** Interactive scenario visualisation with water levels at buildings, flow indicators and evolving storm snapshots; no confirmed machine download of original numerical model grids  
**Potential roles:** `cologne_flood_visual_plausibility_check`, `municipal_hazard_model_comparison_after_permission`  
**Access hint:** `public_browser_view_only_raw_machine_endpoint_and_reuse_rights_unverified_do_not_scrape`  
**Authoritative source:** <https://steb-koeln.de/service/karten-und-anwendungen/ueberflutungsgefahrenkarten>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** StEB describes its city-wide maps and visual rainfall simulations, but publication of an interactive free viewer is not a data-download or redistribution grant. Treat numerical tiles, depths, temporal sequences and any embedded application calls as unavailable for automated source acquisition unless the provider explicitly documents a machine endpoint and its licensing. Do not reverse-engineer or scrape viewer payloads. A scenario display alone is neither empirical event hazard nor a calibrated stochastic model.
