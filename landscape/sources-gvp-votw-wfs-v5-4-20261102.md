<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-gvp-votw-wfs-v5-4-20261102.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-gvp-votw-wfs-v5-4-20261102.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-02`  
**Purpose:** Non-admission discovery for the current Smithsonian GVP Volcanoes of the World 5.4.0 WFS product with explicit source-specific commercial-use restrictions.

**Entries:** 1

## Smithsonian Global Volcanism Program Volcanoes of the World 5.4.0 WFS

**Candidate ID:** `smithsonian.gvp.volcanoes-of-the-world.v5.4.0`  
**Provider:** Smithsonian Institution / Global Volcanism Program  
**Categories:** `volcano`, `eruption_catalogue`, `volcano_geography`, `event_context`  
**Spatial scope:** Global; curated Holocene volcanoes and eruptions, plus Pleistocene volcano information in the separately named WFS layer  
**Temporal scope:** VOTW database release v5.4.0 dated 2026-08-07; review covers eruptions through 2025 and subsequent updates require separate snapshot identity  
**Resolution / granularity:** OGC WFS feature service exposes Holocene volcano locations, Pleistocene volcano locations and Holocene eruption features; spatial records and descriptive attributes rather than ashfall or eruption-intensity rasters  
**Potential roles:** `volcano_event_identity_and_location`, `volcanic_exposure_proximity_screening`, `eruption_catalogue_crosswalk`, `historical_event_context_validation`  
**Access hint:** `public_wfs_documentation_commercial_reuse_prohibited_without_smithsonian_written_permission`  
**Authoritative source:** <https://volcano.si.edu/database/webservices.cfm>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Separate the official VOTW v5.4.0 citation (7 August 2026, DOI 10.5479/si.GVP.VOTW5-2026.5.4) from the previously registered historical v5.3.6 product. The Smithsonian GVP terms page explicitly prohibits commercial use without prior written permission, notwithstanding that the database compilation is described as a US government employee product. Do not infer that public WFS access or US government authorship permits insurer CAT product use, unrestricted reproduction, event reinsurance analysis or redistribution. No data/API request or download was made. Three WFS layer families are documented by GVP; freeze exact layer name, CRS, feature identifier, event epoch, retrieval UTC, layer version, dataset edition and source references only after provider permission. Volcano and eruption point records are not volcanic ash thickness, VEI-based intensity grids, property damage curves, frequency calibration or insured losses. Preserve observation/reporting gaps and original source-lineage.
