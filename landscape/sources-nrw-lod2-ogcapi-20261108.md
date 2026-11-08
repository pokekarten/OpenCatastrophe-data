<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-nrw-lod2-ogcapi-20261108.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-nrw-lod2-ogcapi-20261108.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-08`  
**Purpose:** Non-admission source discovery for the official NRW LoD2 3D-building OGC API Features product, differentiated from restricted nationwide LoD2-DE and from NRW bulk CityGML delivery. Research-only technical access and source-vintage assessment for an explicitly fictional German exposure pilot.

**Entries:** 1

## North Rhine-Westphalia official LoD2 3D buildings OGC API Features (2026)

**Candidate ID:** `de.nrw.geobasis-lod2-ogc-features.2026`  
**Provider:** Geobasis NRW / Bezirksregierung Köln  
**Categories:** `buildings`, `building_geometry`, `roof_geometry`, `3d_city_models`, `germany`, `exposure`, `ogc_api`  
**Spatial scope:** North Rhine-Westphalia, Germany; coverage and geometry at exact API feature/query level still require a bounded source probe  
**Temporal scope:** Official OGC API Features metadata revision 2026-09-08; LoD2 source metadata references ALS and DGM1 2019-2025, ALKIS building footprints dated 2025-07-01, and ATKIS geometry dated 2025-10-01. Not a 2021 or any other historical event-year snapshot.  
**Resolution / granularity:** Individual modelled buildings and structures with standardized LoD2 roof forms; official OGC API Features delivery lists CityJSON, CityGML, glTF and 3D Tiles. Separate bulk CityGML downloads exist; format/field support and entity counts for any selected collection require live schema inspection.  
**Potential roles:** `fictional_nrwestphalia_building_geometry_pilot`, `building_roof_and_height_exposure_prior`, `source_vintage_geometry_validation`, `county_to_building_spatial_support_research`  
**Access hint:** `Publisher metadata: public OGC API Features https://ogc-api.nrw.de/3dg/v1 with no dataset access restrictions, source licence Datenlizenz Deutschland Zero 2.0; exact live API query behavior, rate/automation policy and selected asset identity not yet reviewed`  
**Authoritative source:** <https://www.govdata.de/suche/daten/3d-gebaudemodell-nw-lod28b9df>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Provider/AdV catalogue describes OGC API Features and data origin; original CityGML and SLPK are separate delivery products. See official metadata https://www.distributions.informationgrid.eu/trefferanzeige?docuuid=bde30228-a718-45a8-9518-1e17e47c0187. Before any acquisition, pin exact collection, request, response version, CRS, feature identifiers, authoritative terms and any API-service conditions, then sample a very small original feature window outside Git with SHA-256 evidence. Roof geometry or ALKIS location does not identify an R+V-insured building, construction quality, 2021 event-time exposure, replacement cost, contract terms, damage or loss. Do not equate a fictional NRW policy cohort with actual NRW insurer locations or publish data bytes merely because publisher metadata cites DL-DE/Zero-2.0.
