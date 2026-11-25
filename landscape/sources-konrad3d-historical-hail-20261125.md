<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: landscape/sources-konrad3d-historical-hail-20261125.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source landscape: `sources-konrad3d-historical-hail-20261125.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. It does not create a second source of truth or change admission, rights or scientific-review state.

**Schema version:** `1.0.0`  
**Review date:** `2026-11-25`  
**Purpose:** Non-admission discovery and bounded original-sample evidence for historical DWD convective storm objects.

**Entries:** 1

## DWD KONRAD3D historical convective cells v1.7

**Candidate ID:** `dwd.konrad3d.zenodo.18087045`  
**Provider:** Deutscher Wetterdienst  
**Categories:** `hail`, `lightning`, `radar`, `convective_storm`  
**Spatial scope:** Germany and adjacent radar domain  
**Temporal scope:** 2018-03-01 to 2025-06-30  
**Resolution / granularity:** Monthly tar.bz2 archives of XML snapshots; 5-minute analysis cadence in April 2019 sample  
**Potential roles:** `storm_tracking`, `hail_proxy_calibration`, `convective_feature_training`  
**Access hint:** `public_versioned_download`  
**Authoritative source:** <https://zenodo.org/records/18087045>  
**Review state:** candidate `evidence_checked`; rights `not_reviewed`; scientific `not_reviewed`; admission `not_admitted`.

**Note:** Distinct historical reprocessing archive, not the already documented operational endpoint dwd.konrad3d.operational. Zenodo API returned 88 files, 2219772181 bytes, license cc-by-4.0 on 2026-11-25. Bounded macOS download of https://zenodo.org/records/18087045/files/KONRAD3D_201904.tar.bz2?download=1 succeeded: 8792122 bytes, SHA-256 d573694526df63d2233bafa21176510c0336b23c30bb36c84f60155b76e188aa, MD5 14200f3dd87df73eec5c7a04ac56dc3c matches provider. Streaming tar scan without extraction: 8640 XML members, sum member bytes 209615753; v1.7 root and UTC reference times confirmed. File KONRAD3D_20190401T193500.xml includes cell identifier, geodetic centroid, polygons, echo top, reflectivity thresholds, VIL/VII, hail_flag, HYMEC hail/large-hail area and volume, ICON-EU CAPE/shear and lightning_rate (strokes/5min), lightning_density. Sentinel -1000000000 observed; preserve missingness and radar-sweep availability. Header grid DE4800_WGS84 250 m is underlying processing grid, not measured hail footprint resolution. Hail flag and HYMEC are radar-derived, not observed ground hail size; cell detection uses lightning, so not independent validation of lightning-only predictors without lineage-aware split/holdout. Archive was retrospectively processed in 2025; do not treat creation date as event date or forecast as observation. No raw bytes committed, no database ingestion; formal rights review and scientific admission remain open.
