<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-nasa-opera-dswx-s1-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-nasa-opera-dswx-s1-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery registry for NASA OPERA Sentinel-1 SAR observed surface-water extent and bounded flood-event validation research.

**Entries:** 1

## NASA OPERA Dynamic Surface Water Extent from Sentinel-1 (DSWx-S1) Version 1

**Candidate ID:** `nasa.opera.dswx-s1.v1`  
**Provider:** NASA JPL OPERA / PO.DAAC  
**Categories:** `flood`, `satellite_observations`, `surface_water_extent`, `remote_sensing`, `validation`  
**Spatial scope:** Near-global land observations from 84 degrees north to 84 degrees south, conditional on Sentinel-1 acquisition coverage and product validity.  
**Temporal scope:** PO.DAAC collection start 2023-12-01 to present; forward operational production began September 2024. Individual sensing time and collection release must be preserved.  
**Resolution / granularity:** 30 m MGRS-tiled cloud-optimized GeoTIFF Level-3 surface-water classification with associated confidence products; mapped open water detection is limited for small or narrow water bodies.  
**Potential roles:** `independent_surface_water_extent_validation`, `flood_event_footprint_comparison`, `post_event_hazard_challenge`  
**Access hint:** `nasa_earthdata_cmr_granule_discovery_and_podaac_earthdata_authenticated_data_access`  
**Authoritative source:** <https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Frozen product name OPERA_L3_DSWX-S1_V1, DOI 10.5067/OPDSWS1-L3V1, NASA CMR collection C2949811996-POCLOUD. Registry of Open Data on AWS states CC BY 4.0, but exact granule permissions, Copernicus Sentinel input attribution, Earthdata credential requirements and commercial redistribution rights need source-specific review. SAR observed surface water is not necessarily an event-specific flood, water depth, recurrence probability or loss. Document baseline-water filtering, acquisition time, confidence flags, pixel geolocation, omissions, processing version and independence from CEMS GFM before any validation use.
