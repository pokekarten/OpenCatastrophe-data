<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-critical-infrastructure.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-critical-infrastructure.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry for critical-infrastructure exposure and cascading-risk context sources.

**Entries:** 2

## Global Dam Watch database version 1.0

**Candidate ID:** `globaldamwatch.gdw.v1.0`  
**Provider:** Global Dam Watch  
**Categories:** `critical_infrastructure`, `dams`, `reservoirs`, `hydrology`  
**Spatial scope:** global  
**Temporal scope:** version 1.0 released 2024  
**Resolution / granularity:** river barrier points, reservoir polygons and linked infrastructure attributes  
**Potential roles:** `dam_failure_context`, `cascading_flood_context`, `critical_infrastructure_exposure`  
**Access hint:** `public_download`  
**Authoritative source:** <https://figshare.com/articles/dataset/Global_Dam_Watch_database_version_1_0/25988293>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Recent global dam-and-reservoir infrastructure reference with technical documentation. Treat it as exposure/context data, not as a dam-breach probability, fragility or downstream-loss model; exact rights and scientific suitability still require admission review.

## Global Power Plant Database v1.3.0

**Candidate ID:** `wri.global-power-plant-database.v1.3.0`  
**Provider:** World Resources Institute  
**Categories:** `critical_infrastructure`, `energy`, `exposure_context`  
**Spatial scope:** global  
**Temporal scope:** version 1.3.0 released June 2021  
**Resolution / granularity:** plant-level geolocations, capacity, fuel, ownership and generation attributes  
**Potential roles:** `critical_infrastructure_exposure`, `energy_asset_context`, `cascading_risk_context`  
**Access hint:** `public_download`  
**Authoritative source:** <https://datasets.wri.org/datasets/global-power-plant-database>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Useful historical power-infrastructure baseline, but WRI states the database is no longer maintained. Never treat v1.3.0 as a current plant inventory; exact rights and scientific suitability still require admission review.
