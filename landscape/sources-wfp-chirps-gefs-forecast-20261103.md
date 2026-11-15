<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-wfp-chirps-gefs-forecast-20261103.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-wfp-chirps-gefs-forecast-20261103.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-03`  
**Purpose:** Non-admission research of WFP CHIRPS3-GEFS daily and dekadal forecast products, distinct from CHIRPS v3 historical precipitation measurements and WFP delivery mirrors, with unresolved original-issue-vintage and rights gates.

**Entries:** 2

## WFP CHIRPS3-GEFS daily precipitation forecast rolling COG product

**Candidate ID:** `wfp.hdc.chirps3-gefs-daily-forecast.v3`  
**Provider:** World Food Programme VAM / Humanitarian Data Cube, derived from CHC CHIRPS3 and NCEP GEFSv12  
**Categories:** `precipitation`, `forecast`, `short_range_rainfall`, `flood_early_warning`, `global`  
**Spatial scope:** Land between 60S and 60N, all longitudes, subject to CHIRPS3 land mask  
**Temporal scope:** Published 2001-present; daily latest issue produces issue day plus 15 lead days. Older issues for the same valid days are overwritten and are not a historical issue archive  
**Resolution / granularity:** 0.05-degree daily Cloud Optimized GeoTIFFs. A valid date is not sufficient evidence of issue time, forecast lead, or original prediction vintage  
**Potential roles:** `precipitation_forecast_context`, `prospective_flood_alert_pilot`, `as_of_forecast_vintage_research`  
**Access hint:** `wfp_source_cooperative_public_cog_rolling_files_no_verified_immutable_issue_archive`  
**Authoritative source:** <https://source.coop/wfp/chirps-daily-forecast>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** WFP documents CHIRPS3-bias-corrected NCEP GEFSv12 forecasts, daily-disaggregated using NASA IMERGv7 Late, 16-day issue output and rolling overwrite of forecast files for identical valid dates. Older dates show lead-0 forecasts, NOT historic 1-15-day forecasts. Never use today's file for retrospective forecast-skill analysis without an immutable original issue receipt. This is a forecast, not an observed rain gauge, flood extent, insured loss, or independent product from its GEFS/CHIRPS3/IMERG parents. Provider page advertises CC BY 4.0; rights, source revision and scientific admission still require review. No source bytes or API requests committed.

## WFP CHIRPS3-GEFS dekadal precipitation forecast COG delivery

**Candidate ID:** `wfp.hdc.chirps3-gefs-dekad-forecast.v3`  
**Provider:** World Food Programme VAM / Humanitarian Data Cube, CHC and NCEP GEFSv12  
**Categories:** `precipitation`, `forecast`, `dekadal`, `flood_early_warning`, `global`  
**Spatial scope:** Land between 60S and 60N, all longitudes  
**Temporal scope:** 2001 to near present according to WFP; published roughly at beginning of a dekad; past issue-retention completeness not verified  
**Resolution / granularity:** 0.05-degree dekadal forecast Cloud Optimized GeoTIFFs. Not historical observed rainfall and not an independent forecast model relative to WFP daily GEFS  
**Potential roles:** `dekadal_rainfall_forecast_context`, `hydrological_early_warning_context`, `forecast_aggregation_consistency`  
**Access hint:** `wfp_source_cooperative_public_cog_forecast_documentation_only`  
**Authoritative source:** <https://source.coop/wfp/chirps-dekad-forecast>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** WFP describes CHIRPS3 climatology bias-corrected and downscaled NCEP GEFSv12 predictions. Daily and dekadal distributions share the same parent forecast lineage; never treat them as statistically independent observations or model ensemble members. Exact issue IDs, valid windows, model revision and historical issue retention must be verified before backtesting. CC BY 4.0 is advertised by WFP; provider terms and OpenCatastrophe rights/science reviews remain pending.
