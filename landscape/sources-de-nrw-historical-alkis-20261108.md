<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-de-nrw-historical-alkis-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-de-nrw-historical-alkis-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission research source discovery for two original NRW historic ALKIS product families (annual simplified cadastral GeoPackages and principal-building point references), with distinct footprint/point identity and CRS semantics. No external bytes or insurance-model admission.

**Entries:** 2

## NRW historic ALKIS simplified building, parcel and land-use GeoPackages 2016–2025

**Candidate ID:** `de.nrw.geobasis.historical-alkis-simplified-gpkg.2016-2025`  
**Provider:** Geobasis NRW / Bezirksregierung Koeln  
**Categories:** `buildings`, `historical_cadastre`, `building_footprints`, `land_use`, `parcels`, `exposure_history`, `germany`  
**Spatial scope:** North Rhine-Westphalia, Germany; all 53 districts and independent municipalities via official district-year ZIP packages  
**Temporal scope:** Annual January 1 snapshots for years 2016-2025; publisher latest index independently reviewed 2026-11-08  
**Resolution / granularity:** Original ALKIS-derived simplified GeoPackage; buildings and above-ground structures, parcels (without owners), actual land use, jurisdictions and cadastral units; 53 county/city GeoPackage ZIPs exposed for each year at EPSG:25832  
**Potential roles:** `historical_building_footprint_reconstruction`, `parcel_landuse_join_challenge`, `cadastral_building_identity_crosswalk`, `building_change_detection`  
**Access hint:** `official_public_directory_year_county_zips_dl_de_zero_2_0_original_assets_not_downloaded`  
**Authoritative source:** <https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_gru_vereinfacht_gpkg/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher source https://www.bezreg-koeln.nrw.de/geobasis-nrw/produkte-und-dienste/liegenschaftskataster/historisches-liegenschaftskataster/historische-grundrissdaten confirms simplified GPKG and full NAS are different schemas, each with Jan-1 historical snapshot from 2016. Do not assume NAS-only/optional construction year or construction-method fields survive simplified GPKG without inspecting exact original table schema. 2016/2025 year index pages list 53 county/district ZIP downloads each under the original licence DL-DE/Zero 2.0, at EPSG:25832; original ZIP names, hashes and real records remain unchecked. Same ALKIS upstream as separate historic house-outline shapefile candidate in PR #1429, and NRW LoD2/HU2022 inputs; duplicates and updated polygon splits must be reconciled before any year-by-year count or model use. No identifiable ownership or insurer policy data.

## NRW historic georeferenced principal building/address reference points 2016–2025

**Candidate ID:** `de.nrw.geobasis.historical-building-reference-positions.2016-2025`  
**Provider:** Geobasis NRW / Bezirksregierung Koeln  
**Categories:** `buildings`, `historical_georeferences`, `building_points`, `addressable_structures`, `cadastral`, `exposure_history`, `germany`  
**Spatial scope:** North Rhine-Westphalia, Germany; whole-state ASCII reference archives for principal/house-numbered buildings, not all detached or ancillary structures  
**Temporal scope:** Annual January 1 historical snapshots 2016-2025; 2016-2022 and 2023 onward published in separate CRS folders  
**Resolution / granularity:** Over 4 million NRW principal-building position references per year, annual ASCII ZIPs; EPSG:4647 with zone-prefixed easting for 2016-2022, EPSG:25832 without that prefix for 2023-2025; provider supplies distinct field-format guidance for 2016-2018 and from 2019  
**Potential roles:** `historical_principal_building_point_crosswalk`, `footprint_point_matching`, `historic_address_coordinate_reconciliation`, `coordinate_reference_system_guard`  
**Access hint:** `official_public_whole_state_ascii_year_archives_dl_de_zero_2_0_original_assets_not_downloaded`  
**Authoritative source:** <https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_gebref_txt/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Original publisher https://www.bezreg-koeln.nrw.de/geobasis-nrw/produkte-und-dienste/liegenschaftskataster/historisches-liegenschaftskataster/historische-gebaeudereferenzen explains principal/addressable buildings and no full postal address enrichment. Index branches hist_gebref_txt_epsg_4647 (2016-2022, zone-prefixed easting) and hist_gebref_txt_epsg_25832 (2023-2025, conventional easting) must be CRS-normalized, not relabelled, and preserve year, source IDs and quality. Distinct from &gt;10m ALKIS house outline polygons: point entries may be 1-to-many or many-to-1 with polygons and exclude ancillary structures; do not extrapolate as complete building count, insured address, construction year or TIV. Exact original archive byte hashes, per-year schema and sample-feature joins have not been audited. Shared ALKIS source lineage with existing NRW footprints and PRs #1373/#1425/#1429.
