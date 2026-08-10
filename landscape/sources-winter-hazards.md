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

**Entries:** 3

## Global Historical Climatology Network daily (GHCNd)

**Candidate ID:** `noaa.ncei.ghcnd.daily`  
**Provider:** NOAA National Centers for Environmental Information  
**Categories:** `winter_hazard`, `snowfall`, `snow_depth`, `station_observations`, `validation`  
**Spatial scope:** global station network with strongly heterogeneous snow-variable coverage  
**Temporal scope:** station-dependent historical records through current daily updates; record lengths range from under one year to more than 175 years  
**Resolution / granularity:** daily land-station summaries; snowfall and snow-depth elements where reported, with source, measurement and quality flags  
**Potential roles:** `snowfall_validation`, `snow_depth_validation`, `winter_event_station_context`  
**Access hint:** `public_https`  
**Authoritative source:** <https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Integrated, quality-assured station archive rather than a spatially homogeneous snow network. Snow reporting is uneven by station and geography; NCEI notes that many North American stations report snowfall and snow depth, while snow-depth observations outside the United States can originate from synoptic Global Summary of the Day inputs. Preserve element-specific inventory, source/measurement/quality flags, update/version identity and archive-quality replacement timing; do not treat missing snow reports as zero snow or the station sample as spatially representative without a separate design.

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

## NOAA Storm Events Database

**Candidate ID:** `noaa.ncei.storm-events`  
**Provider:** NOAA National Centers for Environmental Information / National Weather Service  
**Categories:** `winter_hazard`, `event_catalogue`, `reported_impacts`, `snow`, `ice`, `validation`  
**Spatial scope:** United States and NOAA reporting areas  
**Temporal scope:** January 1950 to current database releases; all 48 standardized event types are digitally represented from 1996 onward  
**Resolution / granularity:** event records with county- or forecast-zone geography; winter-relevant types include Blizzard, Heavy Snow, Ice Storm, Lake-Effect Snow, Sleet, Winter Storm and Winter Weather  
**Potential roles:** `winter_event_occurrence_validation`, `event_window_definition`, `reported_impact_context`  
**Access hint:** `public_web_and_bulk_csv`  
**Authoritative source:** <https://www.ncei.noaa.gov/stormevents/index.jsp>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official Storm Data event records are valuable occurrence and impact context but collection scope and processing changed substantially over time: before 1996 the digitized historical record does not contain the full modern event-type set. Winter events are generally zone-based, and reported property damage, injuries, fatalities and narratives are administrative/event reports rather than exposure-normalized loss observations. Freeze database release/access date and event-type definitions, model reporting-process bias explicitly, and never use raw damage amounts as homogeneous insurance-loss targets without separate validation.
