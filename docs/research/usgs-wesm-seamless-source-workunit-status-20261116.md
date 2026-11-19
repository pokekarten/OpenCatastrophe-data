<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USGS WESM source-lineage quality status preflight — 2026-11-16

## Scope, evidence class and exact source distinction

**Purpose:** supply a strict **offline work-unit scientific triage** of U.S. Geological Survey's 3DEP **Work Unit Extent Spatial Metadata (WESM)**, which can later be used to qualify the lidar/source-DEM projects behind **one** USGS S1M tile. This is NOT an additional original-data acquisition, approved dataset manifest, model admission or source-workunit-to-tile spatial join.

Authoritative provider evidence:
- [USGS 3DEP Spatial Metadata](https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata): WESM work-unit IDs, source metadata, lidar quality, status codes, and underlying datasets. The WESM changes almost daily; a record without a dated, hash-identified original WESM version is not reproducible source evidence.
- [Official WESM Data Dictionary](https://www.usgs.gov/ngp-standards-and-specifications/wesm-data-dictionary): native source field names `workunit_id`, `project_id`, `lpc_category`, `sourcedem_category`, `seamless_category`, `seamless_reason`, and survey/source-related metadata.
- [USGS Category Dictionary](https://www.usgs.gov/ngp-standards-and-specifications/wesm-data-dictionary-product-status-codes-categories): `Expected to meet` exists for upstream LPC/source DEM, **not** seamless. A seamless product can have `Pending publication`, `Under review`, `Meets`, `Meets with variance` or `Does not meet`. These labels are **not interchangeable**.
- [USGS Seamless Reason Codes](https://www.usgs.gov/ngp-standards-and-specifications/wesm-data-dictionary-reason-codes-1m-and-seamless): pending means awaiting final vertical accuracy; `Meets with variance` includes earlier-spec LPC; failures include LPC failure, coarse source DEM and missing DEM.
- Official USGS-displayed WESM [CSV endpoint](https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/WESM.csv) and [GeoPackage endpoint](https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.gpkg) are **source URL references only**. Neither was read or version-hashed in this PR; no metadata connector or full-file original download is authorised by this code.

## Executable scientific status contract

`research_runners/usgs_wesm_seamless_workunit_quality_v0.py::classify_wesm_seamless_workunit` accepts one caller-extracted synthetic/externally proven WESM-like row. It:
1. Requires nonempty safe `workunit_id` / `project_id` and all four actual status/reason source fields; allows unrelated native columns without trusting their truth.
2. Enforces provider-valid category sets *per product*, not a permissive global enum. `Expected to meet` and `Not applicable` **cannot** be used for the seamless status.
3. Enforces exact official category/reason pairing. `Meets 3DEP 1-m requirements` cannot substitute for `Meets 3DEP seamless requirements`.
4. Requires both upstream LPC and source DEM to be `Expected to meet` when seamless is `Pending publication`. Fails closed on contradictory upstream source quality where downstream seamless is marked `Meets` or `Meets with variance`.
5. Outputs one explicit quality classification while preserving `provider_original_csv_full_hash_verified=false`, `provider_original_geopackage_full_hash_verified=false`, `workunit_geometry_intersection_with_exact_s1m_tile_verified=false`, `tile_specific_lidar_vintage_and_void_fill_verified=false` and `cat_model_input_approved=false`, **even when seamless status is `Meets`**.

The offline gate is source metadata **logic**, not original WESM source validation. It does not infer a unique work-unit from the Florida S1M filename `S1M_n0450e1510_20260821.tif`. A 1m *grid spacing* and clean GeoTIFF EPSG/NoData/1m header do not prove source lidar accuracy; blends and backfilled voids require S1M per-pixel lineage and independent terrain holdouts.

## Evidence and remaining source gate

- **Existing actual original S1M TIFF header:** PR [#1728](https://github.com/pokekarten/OpenCatastrophe-data/pull/1728) now merged, with original 65,536-byte SHA-256 `56d8d147056fcd28ad916799cd6b917c57d9d08b3e07dfe06931f2a4d5edb2f2`, original EPSG 6350/5703, NoData −999999, 1-m model scale. This original **TIFF** header does not contain a WESM per-work-unit quality result.
- **Current WESM quality gate:** T0 official provider published status semantics + offline synthetic negative regressions, **no WESM CSV/GeoPackage bytes, date/hash or current Florida work-unit intersection verified**.
- **Next causal action:** separately qualify the exact publicly linked WESM CSV/GeoPackage (retrieve and hash a frozen original snapshot through an explicitly reviewed bounded source operation). Spatially intersect verified work-unit polygons against the **exact** S1M tile; resolve duplicates/overlaps, survey dates, geoid and source variance; then compare actual raster pixels with independent observations. No source data admitted or Neon written in this change.

**Classification:** `TECHNICALLY_VERIFIED_ONLY` for **offline USGS WESM status-code classifier**; `BLOCKED_WITH_EVIDENCE` for real original WESM snapshot, Florida tile lineage and model use.
