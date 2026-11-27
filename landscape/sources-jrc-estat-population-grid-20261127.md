<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-jrc-estat-population-grid-20261127.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-jrc-estat-population-grid-20261127.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-27`  
**Purpose:** Discover the revised JRC-ESTAT 100 m population exposure proxy without conflating modelled cells with observed census or insured exposure.

**Entries:** 1

## JRC-ESTAT Census Population Grid 2021, 100 m, revision 2026.07

**Candidate ID:** `ec.jrc.census2021-population-grid-100m.r2026.07`  
**Provider:** European Commission Joint Research Centre / Eurostat  
**Categories:** `population`, `exposure`, `demography`, `europe`  
**Spatial scope:** Europe; exact country and raster extent require original asset inspection  
**Temporal scope:** 2021 resident population, revision 2026.07 (catalogue modified 2026-07-24)  
**Resolution / granularity:** 100 m modelled resident population count per cell; 1 km census V2-0 of 2024-06-16 disaggregated using residential built-up volume  
**Potential roles:** `population_exposure_prior`, `bounded_flood_population_overlay`, `aggregate_population_conservation_challenge`  
**Access hint:** `public_anonymous_jrc_zip_ec_reuse_notice_upstream_rights_review`  
**Authoritative source:** <https://data.jrc.ec.europa.eu/dataset/98336641-fd1c-4992-8c7b-c470dd5eb81e>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Publisher identifies DOI 10.2905/JRC.VP18KXG and revision 2026.07 with updated LUISA residential areas. Uses Census V2-0, not V3 of May 2026; no independent V3 CSV-TIFF parity or independent building-footprint validation. Shared EUBUCCO, Overture, GHSL and TomTom inputs require lineage and third-party rights review. Fine-scale counts are estimated, not enumerated residents, insured locations, TIV or exact dwellings. Catalogue links a ZIP and declares anonymous access and EU reuse subject to attribution and third-party rights. Original ZIP member inventory, byte identity, CRS, NoData, units and aggregate conservation remain unverified.
