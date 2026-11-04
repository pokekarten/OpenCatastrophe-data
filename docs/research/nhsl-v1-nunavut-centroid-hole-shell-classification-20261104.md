<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NHSL Nunavut v1.0 — why three reported centroids are outside their source polygons

**Research date:** 2026-11-04. **Primary original files:** [NRCan/OpenDRR National Human Settlement release v1.0](https://github.com/OpenDRR/national-human-settlement/releases/tag/v1.0), Nunavut `s_nu.zip` and `b_nu.zip`; exact original file SHA-256 and ZIP member fingerprints are pinned by [the original binary preflight](../../scripts/nhsl_v1_original_binary_preflight_v0.py).

The already-successful [original GEOS run 41905455961](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41905455961) proved all **103** settled-area polygons valid, **3** reported centroids lying outside their source geometry, **3** total interior rings/holes, zero multipolygons, and an outside-centroid share of **3.4198%** of modeled 2019-CAD regional replacement value. The maximum observed nominal-center-to-nearest-polygon separation was **29.725 m**. These observations **do not prove** the three outside centroids coincide with the three interior holes.

## Distinguishing the two geometric causes

For each reported centroid not covered by the **valid source polygon** using native Shapely/GEOS:

1. Construct the **exterior shell only** from each original polygon component, without moving the point or altering source geometry. Use `Polygon(part.exterior).covers(Point)` to determine whether the point lies inside an original exterior ring but was excluded from the actual polygon by its holes.
2. **Interior-hole case:** reported center lies inside one of the exterior shells but is not covered by the actual polygon. Because GEOS has already proven the original polygon valid and the point is outside its coverage, an interior ring/hole explains this mismatch.
3. **Outside-shell case:** reported center is outside all exterior shells, which can arise from a concave outline or, in multipart geometries, a gap between components. This is **not an invalid polygon** and is not automatically a geocoding bug.

The new code is an **extension** to [`scripts/nhsl_v1_nunavut_geos_topology_challenge_v0.py`](../../scripts/nhsl_v1_nunavut_geos_topology_challenge_v0.py), with purely synthetic concave-U, real WKB-hole and exterior cases in [`tests/test_nhsl_v1_nunavut_geos_topology_challenge_v0.py`](../../tests/test_nhsl_v1_nunavut_geos_topology_challenge_v0.py).

Results expose only **count and modeled 2019-CAD replacement-value share** for the two outside categories; **no SAUIDs, individual coordinates, original rings, source rows, original ZIP/GPKG bytes or modeled insurance terms are committed or logged**. The two category counts must add to the independently confirmed three outside centroids, and the rounded cost shares must reconcile to 3.4198% within 0.000002.

## Execution and independent verification

In pull requests, the existing [NHSL source workflow](../../.github/workflows/nhsl-nunavut-original-sauid-conservation.yml) runs **only synthetic tests** plus repository CI (Python 3.11–3.14, licences, GIS). After reviewed merge to `main`, the same workflow downloads only the two exact publisher original ZIPs with SHA/CRC/SQLite and seven-metric numeric conservation checks. GEOS independently classifies all three original centroids and prints **aggregate-only** proof.

**Actual source classification: pending reviewed-main source run.** Do not infer counts merely from there being three holes and three outside centroids. When available, record the exact merged commit, run ID, hole/exterior counts and cost shares from the completed original job.

## Scientific use and outstanding next step

This resolves the reason why a **mathematical polygon centroid** might not be an admissible **point inside the settled-area exposure footprint**, but it does **not** locate any individual roofs. For hazard modeling, the next step is to quantify the difference between centroid-cell lookup and weighted original-polygon support using an **independent, peril-specific and legally usable hazard raster or grid**, and then evaluate the effect on modeled event losses. The existing 0.25/1/5/10-km support-scale diagnostics are not measured risk bias. No loss simulation, insurer coverage, OED location or other admission is implied; source use remains `not_admitted`.
