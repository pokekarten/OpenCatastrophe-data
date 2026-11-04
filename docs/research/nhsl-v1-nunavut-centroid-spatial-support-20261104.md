<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NHSL v1 Nunavut: original polygon spatial support vs archetype centroids

**Date:** 2026-11-04. **Scope:** quantify the **geometry-induced uncertainty proxy** when a spatially aggregated Canadian NHSL settled-area footprint is reduced to a centroid for catastrophe hazard-grid matching. This is **not** actual historical loss, a hazard simulation, per-building ground truth, portfolio insurance TIV or a quantitative estimate of risk loss bias.

## Scientific motivation and source lineage

The [Oasis disaggregation specification](https://oasislmf.github.io/2.5.7/oasislmf/explanation/disaggregation.html) explicitly distinguishes centroid-based hazard matching from spatially disaggregated exposures/aggregate hazard footprints: a centroid may sample just one intensity for an entire geographically uncertain exposure. [Papadopoulos et al. (2024)](https://doi.org/10.1007/s10518-024-01929-6) show why asset relocation and aggregation influence earthquake model loss estimates and require separate model-resolution sensitivity analyses. Neither document supplies a direct Nunavut calibration factor; **do not transfer numerical risk-bias percentages from other regions/perils**.

The original [NHSL v1.0 provider](https://github.com/OpenDRR/national-human-settlement/releases/tag/v1.0) documents archetype point coordinates as the **settled-area centroid**, not an individually surveyed roof. The exact Nunavut source ZIPs and SHA-256 are pinned in [original binary audit](nhsl-v1-original-dictionary-and-nunavut-zip-byte-proof-20261104.md). Earlier [trusted-main original SAUID reconciliation](nhsl-v1-nunavut-original-sauid-reaggregation-20261104.md) proved 103 areas, 2,087 archetypes and seven exact original aggregate fields at the declared tolerance, on source data with passing native SQLite integrity and GP/WKB/SRS type checks (run [41894323152](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41894323152)).

## New reproducible geometry experiment

[Original-only offline script](../../scripts/nhsl_v1_nunavut_spatial_support_v0.py), [pure synthetic tests](../../tests/test_nhsl_v1_nunavut_spatial_support_v0.py), and [existing trusted-main source workflow](../../.github/workflows/nhsl-nunavut-original-sauid-conservation.yml).

- Requires **exact** original ZIP byte-length/SHA-256/CRC and native SQLite integrity, valid GPKG geometry headers and SRS; **fails closed** when original seven-metric SAUID conservation is not satisfied. Uses **only** provider original Nunavut polygons and archetypes, without GIS/network dependencies during parsing.
- Reads complete original 2D Polygon/MultiPolygon ISO WKB rings in `EPSG:4326`, checks ring closure, finite coordinates, longitude/latitude bounds, byte-order and declared counts; does **not** assert validated polygon topology, geodesic perimeter, polygon area or hazard-cell intersections. Unsupported WKB dimensions, malformed geometries and dateline-spanning simple longitude boxes **fail closed** rather than silently approximating them.
- For each original polygon and its reported `E_SauidLon/Lat` center, computes the **maximum Haversine distance from that center to the stored polygon vertices**, a *support-scale diagnostic*, **not** a formal maximum error bound for arbitrary interior positions. Also returns a rectangular-corner radius proxy (not a polygon-to-hazard-cell exact distance).
- Counts centers inside/on or outside the associated original polygon with a **simple planar lon/lat ring point-in-polygon diagnostic**; this is not a geodetic topological certification. A reported centroid may be outside its original concave footprint and remains a valid diagnostic event, not an automatic license to relocate it.
- Checks **all 2,087 archetype `BldgLon/Lat` values** against the corresponding parent polygon center within **1e-6 degrees**, reporting mismatches and maximum offset. This is a documentary centroid-alignment test, **not** a roof-position accuracy test.
- Reports nearest-rank p50/p90/p95/maximum vertex-radius proxies and, for thresholds **0.25/1/5/10 km**, counts of SAUIDs with a greater radius and the fraction of original modeled 2019-CAD asset replacement value in those SAUIDs. Thresholds are **hypothetical spatial-support comparisons**, not observed hazard grid resolutions or loss curves.
- **No SAUID IDs, WKB, coordinates, original source rows, GeoPackage bytes, synthetic site points, insurance terms, vulnerability curve, loss ratio or OED Location/Account files** are emitted in JSON output or Git.

### Repeat the proof

Review the original provider licence, then download only the **two exact public original ZIPs** outside Git. The script is completely offline after download:

```bash
python scripts/nhsl_v1_nunavut_spatial_support_v0.py \
  --polygon-zip /tmp/nhsl_physical_exposure_indicators_s_nu.zip \
  --archetype-zip /tmp/nhsl_physical_exposure_indicators_b_nu.zip

python -m unittest tests.test_nhsl_v1_nunavut_spatial_support_v0 -v
```

PR-head CI runs **only synthetic** 103-area/2,087-archetype test fixtures, wrong/missing centroid and negative geometry cases. The same reviewed-main trusted original workflow **downloads exact official ZIPs on merge only**, runs the existing numeric conservation proof first, and then the new spatial script. It prints **aggregate-only** output and removes temporary raw provider binaries.

**Evidence pending until trusted-main run:** actual percentile radius, count of reported centroids outside the corresponding polygon, amount of modeled replacement value supported by broad footprints, and actual archetype center mismatch count. Do **not** fill in invented results. After the reviewed-main original run, amend this research receipt with the exact job URL and observed summary; failed checks remain clear blockers.

## Next scientific step for OAS/NextGen

Select a **real open and licensed hazard footprint at a stated peril/resolution**, overlay it on the actual polygon supports and compare a single-centroid lookup to polygon-area-weighted hazard intensities. Where an independent building-density source can be used lawfully (e.g. classified footprint or settlement probability), use it as a **separate scenario** with uncertainty bounds. Preserve original NHSL polygon `Sauid` and archetype construction/occupancy totals while documenting hazard-support uncertainty, rather than turning 2,087 archetypes into 2,087 surveyed policy rooftops.

**Risk/admission boundaries:** original NHSL modeling values are replacement-cost stock **not insured BuildingTIV/ContentsTIV**. This script never makes source admission, insuring fraction, hazard vulnerability or AEP/OEP/EP curve claims. All relevant model-use/legal/scientific approvals remain separately pending.
