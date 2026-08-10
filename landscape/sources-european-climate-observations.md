<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-european-climate-observations.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-european-climate-observations.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of European gridded climate-observation sources relevant to catastrophe-risk validation and historical context.

**Entries:** 1

## E-OBS v33.0e European gridded observations

**Candidate ID:** `copernicus.c3s.e-obs.v33.0e`  
**Provider:** Copernicus Climate Change Service / ECA&amp;D  
**Categories:** `climate_observations`, `precipitation`, `temperature`, `validation`  
**Spatial scope:** Europe, 25N-71.5N x 25W-45E  
**Temporal scope:** v33.0e full release 1950-01-01 to 2025-12-31; wind speed available from 1980 onward  
**Resolution / granularity:** daily fields on 0.1 and 0.25 degree regular grids; 20-member ensemble with best-guess and uncertainty information  
**Potential roles:** `reanalysis_validation`, `extreme_precipitation_validation`, `temperature_extremes_validation`, `historical_climate_context`  
**Access hint:** `public_download_noncommercial_terms`  
**Authoritative source:** <https://surfobs.climate.copernicus.eu/dataaccess/access_eobs.php>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Station-derived spatially interpolated observational product, not raw station truth or reanalysis; preserve ensemble/best-guess/uncertainty semantics, variable-specific coverage and known sparse-network/outlier limitations. Variable-specific upstream lineage is material: wind-speed gridding uses ERA5 800 hPa monthly averaged wind speed as a covariate, while the global-radiation product incorporates CERES satellite-derived radiation, so validation against ERA5 or CERES requires a variable-specific independence and lineage check. Provider terms state non-commercial research/education use, so public access must not be treated as commercial model-use or redistribution permission.
