<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-nasa-gfwed-fwi-v2-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-nasa-gfwed-fwi-v2-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery for NASA GFWED versioned GEOS-5 experimental daily fire-weather NetCDF data; precise HTTP access and commercial rights unapproved.

**Entries:** 1

## NASA GISS GFWED GEOS-5 daily fire-weather indices v2.0

**Candidate ID:** `nasa.giss.gfwed.geos5.daily-fwi.v2.0`  
**Provider:** NASA Goddard Institute for Space Studies / Global Fire WEather Database  
**Categories:** `wildfire`, `fire_weather`, `meteorological_hazard`, `derived_index`, `global`  
**Spatial scope:** Global, with coverage of each original GEOS-5 daily fire-weather product dependent on its model and precipitation inputs  
**Temporal scope:** GEOS-5 experimental near-real-time analysis family begins in 2014; the provider documents an exact v2.0 example for sensing date 2014-05-01; do not infer a complete daily record without file-level inventory  
**Resolution / granularity:** Daily modeled fire-weather indices in provider NetCDF files; GEOS-5 analysis meteorological fields are described at 0.25 x 0.25 degree, but exact NetCDF grid, variables, fill codes and units must be checked independently  
**Potential roles:** `wildfire_fire_weather_hazard_covariate`, `seasonal_and_regional_fire_weather_context`, `independent_firms_fire_observation_crosscheck`, `wildfire_climate_driver_research`  
**Access hint:** `public_provider_documented_netcdf_http_archive_exact_terms_and_file_sample_not_reviewed`  
**Authoritative source:** <https://data.giss.nasa.gov/impacts/gfwed/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Fixed example product path: v2.0/fwiCalcs.GEOS-5/Default/GEOS-5/2014/FWI.GEOS-5.Daily.Default.20140501.nc, as published by NASA GISS. GFWED provides FWI-system derived danger and moisture/behavior indices, NOT observed wildfires, fire ignition event footprints, burned area, building damage, annual insured losses or an insurance vulnerability curve. NASA describes multiple forcing/precipitation variants including MERRA-2 and experimental GEOS-5 products: preserve exact variant, data vintage, local-noon convention, precipitation input, CRS, date, nodata and units, and avoid treating other MERRA-2/NASA products as independent meteorological truth. Public HTTP documentation is not proof of currently available exact bytes or commercial redistribution rights. No remote NetCDF, file range or archive download was performed.
