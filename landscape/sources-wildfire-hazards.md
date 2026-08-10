<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-wildfire-hazards.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-wildfire-hazards.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of wildfire-hazard observation, burned-area and fire-weather sources relevant to catastrophe risk and scientific validation.

**Entries:** 1

## JRC Global Wildfire Information System Fire Danger Forecast

**Candidate ID:** `ec.jrc.gwis.fire-danger-forecast`  
**Provider:** European Commission Joint Research Centre / Global Wildfire Information System  
**Categories:** `wildfire`, `fire_weather`, `fire_danger`, `forecast`, `hazard_context`  
**Spatial scope:** global  
**Temporal scope:** operational deterministic fire-danger forecasts with FWI anomaly and ranking context derived against an approximately 40-year historical series; exact forecast cycle and archive must be pinned for reproducible use  
**Resolution / granularity:** model-dependent Fire Weather Index and component fields from deterministic ECMWF approximately 8 km, MeteoFrance approximately 10 km and NASA GEOS-5 approximately 28 km numerical weather forecasts  
**Potential roles:** `fire_weather_conditioning`, `hazard_severity_context`, `forecast_skill_research`, `event_environment_validation`  
**Access hint:** `public_gwis_maps_and_data_services`  
**Authoritative source:** <https://gwis.jrc.ec.europa.eu/about-gwis/technical-background/fire-danger-forecast>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** GWIS FWI is model-driven meteorological fire-danger information, not an observed ignition, burned-area probability or loss field. Forecast source and resolution differ by numerical weather model, and the globally harmonized danger classes plus anomaly/ranking transformations are part of the scientific contract; exact model, cycle, lead time and index definition must be preserved.
