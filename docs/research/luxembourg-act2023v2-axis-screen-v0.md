<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT2023v2 Luxembourg: source axis-order plausibility screen

**Scope:** original metadata geometry envelope only, research-only, no source admission, no building-to-building match.

## Why

The official ACT 2023v2 dataset identifies its 2D polygons as **roof extents** from summer-2023 aerial surveys, published with LUREF Luxembourg TM / EPSG:2169. The ACT publisher describes X as northing and Y as easting; EPSG also formally specifies axis order northing/easting. Many GIS binary geometries use easting/northing in storage. A CRS code alone cannot settle how the bytes are arranged. **Never apply an automatic coordinate swap or assume EUBUCCO EPSG:3035 compatibility.**

Official sources:
- ACT dataset / source resource: https://data.public.lu/en/datasets/base-de-donnees-nationale-des-batiments-3d-2023/ and https://data.public.lu/en/datasets/r/d62942ec-0dc8-40e2-9fa4-27841e6e1ac1
- EPSG:2169 authoritative area-of-use extent / axis: https://epsg.io/2169 (WGS84 bounding box 5.73°E–6.53°E, 49.44°N–50.19°N)
- EUBUCCO v0.2 geometry CRS and provenance: https://docs.eubucco.com/v0.2/data-format/
- EUBUCCO ODbL region exceptions: https://docs.eubucco.com/v0.2/license/

## Actual pinned original file

A successful GitHub Actions original-source run already observed:
- ZIP 63,246,093 bytes / SHA-256 `a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a`.
- GeoPackage 157,261,824 bytes / SHA-256 `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`.
- Single declared EPSG:2169 MULTIPOLYGON layer with 238,189 roof-derived footprints.

These are exact retrieved-content identities, **not** a provider-issued independent signature. The archive can change at a mutable URL; reject any byte drift rather than ingest new contents under the old identity.

## Executable research-only method

`research_runners/luxembourg_axis_extent_audit_v0.py` reuses the original ZIP preflight, verifies ZIP and extracted GeoPackage SHA-256 and reads only the aggregated `gpkg_contents` extent and geometry CRS metadata, not any source building records. It transforms the four envelope corners from EPSG:2169 to WGS84 under two separate hypotheses:

1. **as_stored_xy**: source stored X/Y passed to `pyproj.Transformer(always_xy=True)`.
2. **swapped_xy**: source stored X/Y exchanged before the same transformation.

It compares each resulting lon/lat bounding box to the published EPSG area of use, with a deliberately loose 0.12° screening margin. Output is `native_only_plausible`, `swapped_only_plausible`, `ambiguous_both_plausible`, or `neither_plausible`. The tool always emits `coordinate_order_verified=false`, `building_match_authorised=false`; **a plausible envelope is not proof of feature coordinates, geometry topology, source rights or model fitness.** The rectangle corners may cover unoccupied Luxembourg-adjacent land.

Offline use after permitted original-file acquisition:

```bash
python -m pip install -r requirements-eu-flood-spatial.txt
python research_runners/luxembourg_axis_extent_audit_v0.py \
  --source-zip /private/act2023v2-buildings3d-footprints.gpkg.zip
```

The pinned, narrowly scoped GitHub Actions workflow runs the same diagnostic on an ephemeral official ZIP; no raw source files are committed or uploaded. Ten synthetic regression tests exercise normal, swapped, ambiguous, invalid, bad-CRS and incorrect-hash cases in the existing pinned spatial CI job.

## Remaining hard decision

Use **multiple independently identified control points/footprints with verified Luxembourg geodetic coordinates** to confirm actual stored order, including both X/Y directions and projected control residuals. Freeze that decision in source review *before* creating real-area samples or transforming to EUBUCCO EPSG:3035. Next, review EUBUCCO v0.2 LU00 source lineage, licence, release date and per-building uncertainty; do not equate ACT's 2023 roof footprint count with the EUBUCCO building count. No insurer portfolio, building replacement cost, claims or policy identities are established by this check.
