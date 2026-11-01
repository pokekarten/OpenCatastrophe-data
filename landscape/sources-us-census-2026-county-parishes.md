<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-us-census-2026-county-parishes.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-us-census-2026-county-parishes.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-01`  
**Purpose:** Non-admission discovery of an original official US administrative boundary release for county-equivalents including Louisiana parishes; no insurer exposure, hazard or model use is admitted.

**Entries:** 1

## US Census TIGER/Line 2026 county and parish-equivalent administrative boundaries

**Candidate ID:** `us.census.tigerline.county-parish-equivalent.v2026`  
**Provider:** United States Census Bureau, Geography Division  
**Categories:** `administrative_boundaries`, `baseline_geography`, `county_equivalents`, `parishes`, `united_states`  
**Spatial scope:** United States, Puerto Rico and US island areas covered by Census county and equivalent layers; Louisiana parishes are county-equivalent administrative units  
**Temporal scope:** Boundaries and names as of 2026-01-01, released 2026-10-14; historical catastrophe years require time-specific source versions  
**Resolution / granularity:** National county-and-equivalent polygon Shapefile ZIP, Census GEOID / state and county FIPS; original ZIP advertised at roughly 80 MB  
**Potential roles:** `administrative_boundary_locator`, `county_parish_reporting_crosswalk`, `region_peril_exposure_aggregation_context`  
**Access hint:** `anonymous_official_archive_exact_original_bytes_and_dataset_rights_review_required`  
**Authoritative source:** <https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.2026.html>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official public 2026 national COUNTY directory lists tl_2026_us_county.zip at https://www2.census.gov/geo/tiger/TIGER2026/COUNTY/ . This catalogue verification is not a downloaded, SHA-256-verified archive, a polygon validation, a model-ready boundary or an insured property portfolio. Preserve GEOID/STATEFP/COUNTYFP, boundary as-of date, exact original ZIP/hash/CRS and source usage terms. Do not join by county/parish name alone or silently carry 2026 boundaries into historical disaster losses. County-equivalent terms differ by jurisdiction, and these geometries contain no catastrophe hazard, asset values, insurance terms or claim data.
