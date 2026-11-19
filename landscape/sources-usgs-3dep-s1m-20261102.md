<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-usgs-3dep-s1m-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-usgs-3dep-s1m-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery registry of USGS 3DEP newer seamless 1-meter S1M bare-earth terrain elevation for bounded flood and exposure modelling validation.

**Entries:** 1

## USGS 3DEP Seamless 1-Meter (S1M) Bare-Earth Digital Elevation Models

**Candidate ID:** `usgs.3dep.seamless-1m.s1m`  
**Provider:** U.S. Geological Survey (USGS) 3D Elevation Program / The National Map  
**Categories:** `terrain`, `elevation`, `flood`, `coastal_hazard`, `geospatial_validation`  
**Spatial scope:** United States and territories, with progressively expanding S1M source coverage; not a claim of complete U.S. 1-meter coverage.  
**Temporal scope:** S1M production began in mid-2025; 10 km S1M tiles are added as they become available. Underlying lidar survey years and updates vary by source work unit.  
**Resolution / granularity:** Seamless 1-meter bare-earth DEM cloud-optimized GeoTIFFs in 10 km by 10 km tiles; source-quality/vertical datum, horizontal CRS and project survey dates must be read per tile.  
**Potential roles:** `flood_depth_topographic_support`, `pluvial_and_riverine_flowpath_context`, `building_ground_elevation_validation`, `terrain_source_crosscheck`  
**Access hint:** `public_national_map_api_and_seamless_dem_http_download`  
**Authoritative source:** <https://www.usgs.gov/3d-elevation-program/about-3dep-products-services>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** USGS reports 3DEP products free of charge without use restrictions and public domain, but admission and exact source/asset rights remain separately reviewed. The S1M programme is new, 1-meter and 10 km tiled: do not conflate with legacy project-seamless 1-meter DEM, 1/3 arc-second nationwide DEM, source-resolution OPR DEM, digital surface models or LAZ point clouds. Bare-earth heights are terrain, not roofs or true building finished-floor heights. Preserve tile ID, horizontal/vertical CRS and epoch, lidar acquisition/vintage, interpolation, uncertainty, no-data, tile edges, source lineage and relation to USACE NSI or FEMA building coordinates before any model calculation.
