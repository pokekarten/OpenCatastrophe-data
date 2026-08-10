<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-severe-convective-weather.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-severe-convective-weather.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of potentially useful severe-convective and hail data sources.

**Entries:** 2

## MeteoSwiss National Hail Climatology Switzerland

**Candidate ID:** `meteoswiss.national-hail-climatology`  
**Provider:** Federal Office of Meteorology and Climatology MeteoSwiss  
**Categories:** `hail`, `radar`, `climatology`, `severe_weather`  
**Spatial scope:** Switzerland and nearby radar-covered regions  
**Temporal scope:** radar hail observations from 2002 onward with operational climatology updates  
**Resolution / granularity:** 1 km² radar-derived POH/MESHS fields at 5-minute resolution; climatologies and HailStoRe return-period products  
**Potential roles:** `regional_hail_climatology`, `hail_hazard_validation`, `extreme_value_method_reference`  
**Access hint:** `public_climate_service`  
**Authoritative source:** <https://www.meteoswiss.admin.ch/climate/the-climate-of-switzerland/hail-climatology.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Radar-generation and model changes limit temporal homogeneity; distinguish radar-derived POH/MESHS fields from HailStoRe resampled synthetic-event products and do not infer trends from the short record.

## NOAA MRMS Maximum Estimated Size of Hail (MESH)

**Candidate ID:** `noaa.mrms.mesh`  
**Provider:** NOAA National Weather Service / National Severe Storms Laboratory  
**Categories:** `hail`, `radar`, `severe_weather`, `derived_product`  
**Spatial scope:** MRMS operational domains, including CONUS and other supported U.S. domains  
**Temporal scope:** operational product with versioned MRMS processing  
**Resolution / granularity:** 0.01 degree gridded MESH at 2-minute resolution; swath maxima available for multiple windows  
**Potential roles:** `hail_footprint_validation`, `hail_intensity_proxy`, `severe_storm_nowcast_context`  
**Access hint:** `public_operational_product`  
**Authoritative source:** <https://vlab.noaa.gov/web/wdtd/-/maximum-estimated-size-of-hail-mes-2>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Radar/model-derived hail-size estimate in millimetres, not direct ground truth; preserve known storm-structure and temperature-profile biases plus exact MRMS version/product identity.
