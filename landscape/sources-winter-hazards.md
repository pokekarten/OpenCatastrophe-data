<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-winter-hazards.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-winter-hazards.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-11`  
**Purpose:** Non-admission discovery registry of potentially useful catastrophe-risk data sources.

**Entries:** 1

## MODIS/Terra CGF Snow Cover Daily L3 Global 500m SIN Grid, Version 61

**Candidate ID:** `nasa.nsidc.mod10a1f.v61`  
**Provider:** NASA National Snow and Ice Data Center Distributed Active Archive Center  
**Categories:** `winter_hazard`, `snow_cover`, `remote_sensing`, `cryosphere`, `validation`  
**Spatial scope:** global land surface  
**Temporal scope:** 24 February 2000 to present  
**Resolution / granularity:** daily cloud-gap-filled snow cover on a 500 m sinusoidal grid; 10 degree by 10 degree tiles  
**Potential roles:** `snow_cover_extent_validation`, `winter_hazard_spatial_context`, `station_satellite_cross_validation`  
**Access hint:** `earthdata_login_required`  
**Authoritative source:** <https://nsidc.org/data/mod10a1f/versions/61>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Cloud-gap-filled Level-3 snow cover derived from MOD10A1 by retaining prior clear-sky surface classifications for cloudy cells; the companion days-since-clear observation layer is scientifically material. This persistence can miss snowfall that appears and melts before clouds clear, and thin or ephemeral snow and polar darkness remain limitations. Freeze Version 61, tile/subset, observation-age handling and NDSI-to-binary/fractional interpretation before validation; do not treat gap-filled pixels as same-day direct observations.
