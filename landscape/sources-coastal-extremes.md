<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-coastal-extremes.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-coastal-extremes.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of potentially useful catastrophe-risk data sources.

**Entries:** 2

## GESLA Version 3 Part 1

**Candidate ID:** `bodc.gesla.v3.part1`  
**Provider:** NERC EDS British Oceanographic Data Centre / GESLA  
**Categories:** `sea_level`, `tide_gauges`, `coastal_hazard`, `validation`  
**Spatial scope:** quasi-global tide-gauge network  
**Temporal scope:** records from 1805 to 2021; most begin in the 1950s  
**Resolution / granularity:** 4,527 high-frequency station records; at least hourly  
**Potential roles:** `extreme_sea_level_validation`, `storm_surge_benchmark`, `coastal_flood_validation`  
**Access hint:** `public_archived_download`  
**Authoritative source:** <https://www.bodc.ac.uk/data/published_data_library/catalogue/10.5285/d21a496a-a48e-1f21-e053-6c86abc08512>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Fixed GESLA-3 Part 1 archive assembled from many upstream providers; preserve station-specific datum, timing, quality and coverage semantics, and do not combine it silently with the separately archived Part 2 rights scope.

## NOAA CO-OPS Water Level Data

**Candidate ID:** `noaa.co-ops.water-levels`  
**Provider:** NOAA Center for Operational Oceanographic Products and Services  
**Categories:** `sea_level`, `tide_gauges`, `coastal_hazard`, `observations`  
**Spatial scope:** United States and associated coastal and Great Lakes station network  
**Temporal scope:** station- and product-dependent historical observations to current updates  
**Resolution / granularity:** product-dependent; 6-minute water_level and verified hourly_height among supported products  
**Potential roles:** `event_scale_water_level_validation`, `storm_surge_validation`, `coastal_flood_benchmark`  
**Access hint:** `public_api`  
**Authoritative source:** <https://api.tidesandcurrents.noaa.gov/api/prod/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Water-level retrieval semantics depend on station, product, datum, time zone, units and time window; water_level may be preliminary or verified while hourly_height is verified. Gauge height is not a pure storm-surge residual.
