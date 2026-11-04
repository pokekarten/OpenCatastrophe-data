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


## Observed original-source execution receipt — **passed** (2026-11-04)

**This section supersedes the earlier `Evidence pending` paragraph above.** The reviewed [PR #1317](https://github.com/pokekarten/OpenCatastrophe-data/pull/1317) passed the complete CI (Python 3.11–3.14, REUSE, synthetic WKB/centroid adversarial tests) and was squash-merged into `main` as **`03c8f59ef73d75d68eb5342a2a25d8dffb5d9567`**.

The trusted-main original source workflow [run **41903569037**](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41903569037) subsequently **completed successfully** with both exact original v1.0 Nunavut ZIP downloads, pinned byte identity and native SQLite/GP/WKB validation. The script performed 103 polygon and 2,087 archetype comparisons **on the original provider data**, not synthetic fixtures. The separate seven-field original numeric conservation remained green.

### Actual measured Nunavut geometry-support diagnostics

| Metric from native original provider GPKG geometry | Observed value |
| --- | ---: |
| Settled-area polygons | **103** |
| Building archetype rows | **2,087** |
| Archetype coordinate mismatches vs parent reported centroid (1e-6 degree tolerance) | **0** |
| Reported centroids inside/on footprint, *planar lon/lat test* | **100** |
| Reported centroids outside footprint, *planar lon/lat test* | **3** |
| Center-to-farthest-original-WKB-vertex distance: median/p50 | **0.497527 km** |
| Same radius proxy: p90 | **0.932649 km** |
| Same radius proxy: p95 | **1.020144 km** |
| Largest center-to-vertex distance | **11.267188 km** |
| Largest center-to-lon/lat-bounding-box corner proxy | **12.753365 km** |
| Internal source admission / OED location export | **false / false** |

| Strictly descriptive polygon vertex radius threshold | Area count above threshold | Share of settled areas | Share of original modelled **2019-CAD replacement value** in those areas |
| --- | ---: | ---: | ---: |
| Greater than **0.25 km** | **94/103** | **91.26%** | **99.04%** |
| Greater than **1 km** | **6/103** | **5.83%** | **23.74%** |
| Greater than **5 km** | **1/103** | **0.97%** | **2.96%** |
| Greater than **10 km** | **1/103** | **0.97%** | **2.96%** |

**Interpretation:** The six SAUIDs larger than a 1-km *center-to-vertex distance proxy* contain **23.74% of total modeled replacement cost** across this regional source. This indicates a **concentrated spatial-support sensitivity worth testing** with actual hazard resolution, **not** an observed 23.74% model error, a measured insured-loss exposure proportion, a claim of uncertain real roof positions or the probability that a building falls in a wrong hazard cell.

The **three reported centers outside the WKB footprint** are *diagnostics only*. Causes could include non-convex polygons, holes, mismatched centroid construction, planar ring handling or source geometry peculiarities. Do not silently move these points or classify them as missing insured buildings. Next bounded source challenge: independently compare these three situations with exact polygon topology (e.g. a vetted geospatial geometry engine), report only aggregate counts and the value share, then perform a real hazard-cell support sensitivity analysis.

The native run emits only counts, source hashes, aggregated threshold/value shares and radius quantiles. No SAUID strings, original WKB, raw coordinates, source files, hazard events or insurance-level data are committed. The source remains **`not_admitted`**; no conversion from NHSL replacement value to actual or synthetic insurer TIV is asserted by this verification.


## Independent GEOS topology verification of three outside reported centroids

**Objective (review phase, pending original-source runner):** A separate geometry engine must independently challenge the finding from the original in-house WKB parser and lon/lat ray-casting approach: **3/103** NHSL Nunavut reported SAUID centroid coordinates fall outside their GeoPackage polygons. A purely synthetic unit test cannot establish the real result.

**New implementation:** [`scripts/nhsl_v1_nunavut_geos_topology_challenge_v0.py`](../../scripts/nhsl_v1_nunavut_geos_topology_challenge_v0.py) with [independent GEOS synthetic regressions](../../tests/test_nhsl_v1_nunavut_geos_topology_challenge_v0.py) and the same exact-byte-pinned original GitHub workflow. This step:

- Requires the already-green exact SHA-256/ZIP CRC/native SQLite original-source audit and prior numeric and spatial SAUID consistency checks.
- Uses repository-pinned **Shapely 2.1.2 / GEOS**, not the previous custom WKB polygon implementation, to parse original GeoPackage geometries and independently run `geometry.is_valid`, `geometry.covers(Point)` and `geometry.touches(Point)`. Counts individual valid/invalid source geometries, multipart areas and interior rings, **without emitting SAUID identities or WKB**.
- For the reported original centroids lying outside the actual polygon support, measures **nearest-point distance** in the **planar lon/lat GEOS geometry** and then calculates a descriptive Haversine separation (km). Also computes original center vs GEOS planar polygon centroid distance; **these proxies are not geodesic topology or actual location errors**.
- Quantifies the *source-modeled replacement-cost share* of the polygons whose centroids are outside, rather than assuming equal area/value weight or a loss bias. This is not insured TIV or the probability that an actual building lies outside the footprint.
- Fails closed if GEOS finds invalid polygon topology, original SHA/geometry fails, or the independent outside count disagrees with the original **3**. The workflow is synthetic-only for pull requests and downloads original provider bytes **on reviewed main only** after merge; raw ZIPs are removed and no original location identifiers are logged.

**Method ceiling:** GEOS `covers` operates in a planar interpretation of geographic EPSG:4326 degrees. This is a useful independent *topological* challenge for these small original Nunavut polygons, **not a geodesic area overlay**, a surveyed site-location confirmation or an insured portfolio. Actual hazard-cell resolution mismatch and spatial asset distribution remain separate work.

**Exact source GEOS results: pending the reviewed-main run.** Record the trusted main run URL, GEOS validity and count, value share, multipart/hole counts and maximum nearest-distance proxy **only after reading a successful original-data receipt**. The previous 100-inside/3-outside figures remain independently measured by the original in-house method, not yet corroborated by GEOS at this stage.
