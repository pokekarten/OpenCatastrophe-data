<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-tsunami-observation-validation.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-tsunami-observation-validation.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-08-10`  
**Purpose:** Non-admission discovery registry of high-frequency tsunami sea-level observations relevant to coastal arrival-time and wave-height validation.

**Entries:** 1

## IOC Sea Level Station Monitoring Facility

**Candidate ID:** `ioc.vliz.slsmf`  
**Provider:** Intergovernmental Oceanographic Commission of UNESCO / Flanders Marine Institute (VLIZ)  
**Categories:** `tsunami`, `sea_level`, `tide_gauge`, `real_time_monitoring`, `coastal_observation`, `validation`  
**Spatial scope:** global and regional IOC sea-level networks, including GLOSS and tsunami-warning-system stations  
**Temporal scope:** near-real-time station streams with station- and operator-dependent historical continuity and availability  
**Resolution / granularity:** raw station and sensor streams; the facility states that most stations provide minute-level values updated about every five minutes, while actual sampling and transmission intervals are station and sensor specific  
**Potential roles:** `coastal_tsunami_arrival_validation`, `tsunami_wave_height_validation`, `event_cross_check`, `station_availability_and_sensor_context`  
**Access hint:** `public_monitoring_registered_api_access`  
**Authoritative source:** <https://www.ioc-sealevelmonitoring.org/>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** The facility is designed for rapid inspection of raw real-time streams from heterogeneous station operators, not as a uniformly quality-controlled tsunami archive. Sensor type, datum, sampling, gaps and operator provenance must be retained. Some SLSMF stations expose DART feeds, so any future use must resolve station/feed lineage against the repository's existing DART candidate rather than counting the same underlying measurements twice. The facility's Data Policy states that data and products available through the website may not be used for commercial purposes and directs commercial users to the relevant data originators; this discovery entry does not resolve downstream rights or redistribution permission.
