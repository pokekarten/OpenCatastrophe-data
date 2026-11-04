<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL 2018 versus 2026 — original `SHAPE_LENG` recalculation and units audit

Evidence prepared 2026-11-04. This is a **metadata-only source research experiment**, not a certified length computation, river identity, flood-stage estimate or CAT-model input.

## Why this test

Previous source-byte-pinned GRWL original runs:
- [Original source hashes, archive/member integrity #41822336297](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41822336297)
- [Original attribute values by unique candidate `OBJECTID` #41852020214](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41852020214)
- [Original direction-aware vertex metric #41884435108](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41884435108)

Original 2018 and 2026 simplified SHP/DBF ZIPs have identical feature counts of **42,077**, original `WIDTH_MIN_`, `WIDTH_MED_`, `WIDTH_MEAN`, `WIDTH_MAX_`, `WIDTH_SD_M` values **equal at the same uniquely matching export `OBJECTID`**, but **every one of the 42,077 `SHAPE_LENG` numeric values differs**. Despite 37,355 changed XY record bytes, corresponding vertex separations are below 1 cm for all but one feature; the maximum approximate separation is ~0.375415 m. Even 4,722 byte-identical coordinate sequences have different stored `SHAPE_LENG` values.

A public GEE community data catalogue [describes](https://gee-community-catalog.org/projects/grwl/) `Shape_Leng` for the simplified GRWL product as segment length in **kilometres**. This is a source description and **not yet independent verification of the original GIS calculation procedure, CRS or units for both original releases**. The provider originals remain [2018 Zenodo record 1297434](https://zenodo.org/records/1297434) and [2026 record 18624542](https://zenodo.org/records/18624542); product attribution: Allen & Pavelsky, 2018, *Science*.

## New reproducible evidence boundary

`research_runners/grwl_original_shape_leng_audit_v0.py` uses only the exact 2018 and 2026 source ZIPs, with independent original ZIP SHA-256 pins:

| Release | Provider original `GRWL_summaryStats` ZIP SHA-256 |
| --- | --- |
| 2018, V01.01 | `16830e5444d47d6ba74790613533b6a81b4036a15f3ad7a7066241da28f95306` |
| 2026, V01.02 | `78aa43a7104d24b1696e9b1547347eec13ba5d660aa990c1e7cea98e7ae70e4a` |

Trusted main uses a fixed allowlisted anonymous Zenodo GET with exact filename/byte count/MD5, independently computed SHA-256 and original ZIP/Shapefile preflight before looking at source data. All original data remain temporary in a GitHub-hosted worker; no original source ZIP, `OBJECTID`, `SHAPE_LENG` values, raw DBF rows, individual coordinates or exact feature geometry are printed, stored in Git or uploaded.

At matching unique original export `OBJECTID` candidates, the code reports **aggregated only**:
- original `SHAPE_LENG` value-change count; quantiles of numeric delta (2026 minus 2018);
- ratio distribution `SHAPE_LENG(2026) / SHAPE_LENG(2018)` (median, p05, p95, p99, min/max) and absolute relative-change fractions;
- count of features with source-length relative change greater than 1e-9, 1e-6, 1e-4, 1%, 10%;
- separate relative-change distributions for byte-identical XY pairs versus changed XY pairs;
- independently computed *approximate spherical* sum of WGS84 great-circle distances for all original line segments (per part), in kilometres;
- diagnostic distributions of source `SHAPE_LENG` divided by calculated spherical polyline kilometres, by release.

Zero source-length ratios are **excluded and counted explicitly**; zero spherical-length geometries are **excluded from the source/spherical comparison and counted**. Negative, nonfinite, missing or ambiguous source values fail closed. Per-feature raw data never leave the runner.

## Observed original-source length evidence, before the planar-degree confirmation

**Successfully completed [GitHub main run 41905516679](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41905516679)** at reviewed merge commit `f687227300652bb7b00a0b40a8d55a2ed65d60dc` on 2026-11-04. Both original ZIPs matched the independent exact 2018/2026 SHA-256 pins. All **42,077 unique candidate export `OBJECTID`** pairs were included; no source ZIP, coordinates or original DBF field values were published.

| Original-data statistic | Value |
| --- | ---: |
| Pairs with differing `SHAPE_LENG` | **42,077 / 42,077** |
| Median `SHAPE_LENG(2026) / SHAPE_LENG(2018)` | **100.4982643653** |
| P05 / P95 ratio of the two original length fields | 50.4211902202 / 110.8953075458 |
| Median original 2018 `SHAPE_LENG` / independently calculated spherical WGS84 kilometres | **0.0099510154** |
| Median original 2026 `SHAPE_LENG` / same 2026 spherical-km control | **1.0002575005** |
| P05 / P95 original 2026 `SHAPE_LENG` / calculated spherical-km control | 0.9970136457 / 1.0037708757 |
| Maximum original 2026 `SHAPE_LENG` / spherical-km control | **222.0488171062** |
| Original byte-identical XY pairs with `SHAPE_LENG` changed | **4,722** |

This strongly favors a **unit/calculation-method change**, not 42,077 spatially relocated rivers. One plausible mechanism is that the 2018 field stored ordinary planar longitude/latitude **angular degree** lengths, despite the [official 2026 Zenodo product description](https://zenodo.org/records/18624542) clearly labeling the simplified product's `Shape_Leng` unit as **kilometres**. The older original angular/metric ratio depends on latitude; a uniform ×100 conversion must **not** be assumed or applied.

The extreme ratio (222.0488) between one 2026 source length and spherical-km control needs independent examination (antimeridian, geometry processing, projection, segmentation or a source attribute issue); no interpretation is justified from an aggregate outlier alone.

### Next falsifiable control: original planar angular WGS84 length

This PR adds a direct calculation of **sum of sqrt(Δlongitude² + Δlatitude²)** across every original SHP polyline part, in decimal degrees with **no longitude wrapping**. It compares the *original 2018* `SHAPE_LENG` against this planar-degree result and counts segments exceeding 1e-9, 1e-6, 1e-4, 1%, and 10% relative error. Separately it counts the 2026 segments exceeding those same error thresholds versus **approximate spherical kilometres**.

If old `SHAPE_LENG / planar angular length` is near exactly 1 for all records, that substantially substantiates the 2018-angle-unit hypothesis. If the 2026 / spherical-km residual is small except rare exceptions, the 2026-km hypothesis is strengthened. This **still does not identify** the exact 2026 vendor software, projection, ellipsoid or update code, nor does it establish that every outlier is a genuine geographic feature error.

## How to interpret

If 2026 / 2018 ratios cluster tightly around one fixed factor, a deterministic recalculation/scaling/units hypothesis becomes testable, but is **not proof of a particular GIS tool, CRS, ellipsoid or source code**. If both original `SHAPE_LENG` units match the documentation's kilometre description, the per-release source/spherical reference ratios might be near 1, but curvature, projection, endpoint discretization and segment method may differ. A source/spherical ratio not near 1 can suggest mismatched units, but cannot identify the correct source unit without provider documentation or independent geographic validation.

The spherical reference is **not** precise ellipsoidal geodesic distance, original UTM length, hydraulic channel length, original author's projection or verified river measurement. It is an independent, bounded numerical control. Export `OBJECTID` uniqueness is not a stable hydrologic ID, even when the values match both releases.

Tests are synthetic-only:

```bash
python -m unittest tests.test_grwl_original_shape_leng_audit_v0 -v
```

Live source processing is allowed only from reviewed `main` via `.github/workflows/grwl-original-shape-leng-audit.yml` and `python -m research_runners.grwl_original_shape_leng_audit_v0 --live`. PR heads run **offline tests only**. Full repository CI remains required.

**The first original source length comparison completed successfully**, as documented above. The additional planar-degree experiment is pending a new reviewed-main live run; do not claim its results until that separate GitHub log has been verified.

## Model boundaries

- No confirmed original `SHAPE_LENG` recalculation formula, GIS operation, official version-change rationale or independent ellipsoidal distance validation.
- No licensed raw source data ingestion into production.
- No change to Flood/Hazard models, RiverATLAS conflation, insurer exposure portfolio, return-period distributions, OEP/AEP/IP curves or gross/net losses.
- `model_source_admitted=false`, `flood_hazard_or_insured_loss_calculated=false`, `production_database_modified=false`.
