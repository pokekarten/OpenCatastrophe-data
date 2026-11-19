<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USGS WESM: one original 32 KiB CSV-prefix scientific provenance receipt

**Source:** official U.S. Geological Survey [3DEP Spatial Metadata](https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata), separately published [WESM CSV](https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.csv). A WESM source work unit is NOT the same as one cell of the separate Seamless 1-Meter S1M tile.

## Original provider response, observed 2026-11-16

The public GitHub Actions [source-native run 43961768133 / job 133630902143](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43961768133/job/133630902143) at **2026-11-16T21:36:52.911364+00:00** executed one anonymous, exact original HTTP **206**, no redirect, no retry:

- Exact original URL: `https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.csv`
- Exact source request `Range: bytes=0-32767`; actual original `Content-Range: bytes 0-32767/2267051`.
- Original prefix body bytes **32768**, original prefix **SHA-256 `19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d`**.
- Advertised whole current WESM CSV bytes **2267051**, **not** independently hashed in this run.
- Header contains **28** columns and explicitly identified work-unit ID, project ID and seamless status category **field names**; **no original data-row values** returned/logged.
- Ordered source-header-name SHA-256 `c2893167ec1839f74db9c67704f9f3fbd3c4ed9d6d65359bf1914ce19abb2746`.
- Source request SHA-256 `3161afef28acdc3f4f83abe1d4b9a6f2f76b89b38e5d8373a5d4f5796dc24472`.
- Executed source script SHA-256 `297b177dbefbd5032877b46f9e9b76810fd696bc2d8afa3113e5e06ae95a28b5`, executed access-contract SHA-256 `8d3b6e573d156a6ed71a31a27f048a0a5503876213bab84d4232185b33df5f17`. Historical digests are immutable provenance, not current code hash guarantees.
- `original_data_row_values_read=false`; `full_original_wesm_csv_sha256_verified=false`; `original_wesm_geopackage_verified=false`; `florida_s1m_spatial_workunit_join_verified=false`; `cat_model_input_approved=false`. No provider bytes committed to Git, no original content stored in Neon, no database writes.

USGS says that WESM source files are refreshed almost daily. This therefore represents **only a source-original date/time-specific prefix snapshot**. A matching 32 KiB prefix plus whole-file Content-Range cannot prove the rest of the entire 2.27 MB CSV remained unchanged. A per-file SHA-256 of the exact entire original CSV and the associated original GeoPackage must be independently acquired before any authoritative source-version and spatial-work-unit quality claims.

## Classification

- **T0:** official provider link, source identity and WESM metadata semantics reviewed.
- **T1/T3 partial original:** the actual 32768-byte CSV header and its SHA-256 and request/UTC provenance are **verified**.
- **T3 entire source CSV:** **NOT verified**; advertised file byte length is not whole-file SHA-256.
- **T3 WESM GeoPackage, original Florida S1M source-unit spatial intersection:** **NOT verified**.
- **T4 actuarial/flood/CAT modelling:** **BLOCKED**, including commercial insurer portfolio exposure joins.

**FINAL_CLASSIFICATION: TECHNICALLY_VERIFIED_ONLY** for the original immutable *partial* WESM CSV prefix. **BLOCKED_WITH_EVIDENCE** for complete source and model use.

**Next causal action:** freeze this original prefix SHA and advertised file size in the reviewed bounded runner; then independently revalidate them in one precisely bounded source replay. Separately review one complete current WESM CSV/GeoPackage acquisition, calculate full-file SHA-256, validate all source rows against provider status categories without leaking provider bodies, and spatially intersect the exact source work-unit polygons with the original 2026-08-21 Florida S1M tile. Do not infer tile-level source quality from the CSV header.
