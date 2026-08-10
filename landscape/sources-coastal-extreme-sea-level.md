<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-coastal-extreme-sea-level.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-coastal-extreme-sea-level.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of high-frequency coastal sea-level observation sources relevant to storm-surge and extreme-water-level validation.

**Entries:** 1

## GESLA Version 3 higher-frequency sea-level dataset

**Candidate ID:** `gesla.global-extreme-sea-level.v3`  
**Provider:** GESLA collaboration / British Oceanographic Data Centre  
**Categories:** `sea_level`, `tide_gauges`, `storm_surge`, `coastal_flood`, `validation`, `in_situ_observations`  
**Spatial scope:** quasi-global tide-gauge network assembled from 36 contributing sources  
**Temporal scope:** historical records with the oldest record starting in 1805; Version 3 released in 2021  
**Resolution / granularity:** 5,119 tide-gauge records at least hourly, totaling 91,021 station-years, with per-record metadata and quality/use flags  
**Potential roles:** `extreme_sea_level_validation`, `storm_surge_observation_benchmark`, `tide_gauge_benchmark`, `coastal_flood_context`  
**Access hint:** `public_dataset_split_by_reuse_terms`  
**Authoritative source:** <https://doi.org/10.1002/gdj3.174>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The peer-reviewed Version 3 description and BODC archives split the release into Part 1 (4,527 records, CC BY 4.0) and Part 2 (592 records, CC BY-NC 4.0 and research-only use); keep rights unresolved until the exact archive and intended use are reviewed. Tide-gauge water level is a point observation, not surge-only or flood-depth truth: preserve datum, gauge type, cadence, quality/use flags, gaps and contributor provenance, and do not assume independence from other tide-gauge networks such as PSMSL.
