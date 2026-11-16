<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-usgs-3dep-wesm-20261116.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-usgs-3dep-wesm-20261116.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-16`  
**Purpose:** Non-admitted USGS Work Unit Extent Spatial Metadata (WESM) source original identity and quality-lineage discovery distinct from the seamless one-meter S1M raster.

**Entries:** 1

## USGS 3DEP Work Unit Extent Spatial Metadata (WESM) CSV and GeoPackage

**Candidate ID:** `usgs.3dep.wesm.workunit-metadata`  
**Provider:** U.S. Geological Survey (USGS) 3D Elevation Program  
**Categories:** `elevation`, `terrain`, `geospatial_validation`, `flood`  
**Spatial scope:** USGS published 3DEP work units; not an S1M tile-to-source spatial join and not guaranteed universal one-meter lidar coverage.  
**Temporal scope:** WESM source is reissued nearly daily; collection dates, original snapshot retrieval UTC, exact source byte hashes and separate GeoPackage geometry are mandatory for reproducibility.  
**Resolution / granularity:** Work unit source metadata and status categories, not individual S1M elevation raster pixels.  
**Potential roles:** `lidar_source_workunit_quality_review`, `source_dem_lineage_validation`, `original_lidar_survey_date_context`  
**Access hint:** `official_public_rockyweb_wesm_csv_and_geopackage`  
**Authoritative source:** <https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Official USGS WESM source CSV and GeoPackage are published on rockyweb.usgs.gov. The CSV is a non-spatial workunit table; complete source provenance and link to exact Florida S1M tile require a separately verified GeoPackage polygon spatial join. One bounded 32KiB original CSV header may later be reviewed/verified through its own access contract. This discovery record grants no full CSV, no original GeoPackage, no byte redistribution or CAT-model admission.
