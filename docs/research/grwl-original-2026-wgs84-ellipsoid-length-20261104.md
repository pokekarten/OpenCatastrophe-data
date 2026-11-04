<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL 2026 — original WGS84 ellipsoid length audit and antimeridian holdout

Prepared 2026-11-04. **Status at PR creation: implemented offline and awaiting reviewed-main original-source execution.** This is an independent geodetic *diagnostic*, not a production river-network length, topology or flood-hazard admission.

## Confirmed original-source context

The GRWL 2018 and 2026 simplified originals were obtained from [official Zenodo 2018 / record 1297434](https://zenodo.org/records/1297434) and [2026 / record 18624542](https://zenodo.org/records/18624542), both with independently measured and pinned ZIP SHA-256. The source-vintage comparisons are documented in [the original GRWL length audit](grwl-original-shape-leng-audit-20261104.md).

**Previously observed live evidence**, not merely preview metadata:
- 2018 original `SHAPE_LENG` is the planar WGS84 longitude/latitude degree length at all **42,077** matching uniquely identified **export `OBJECTID` candidates**, with zero records exceeding 1e-9 relative mismatch to independently calculated angular length; the documented unit is kilometres, so the original 2018 field is *unsafe as km*.
- 2026 original `SHAPE_LENG` is generally compatible with geographic length in **kilometres**: independent spherical WGS84 haversine control was within 1% for **42,076/42,077**, median absolute relative error 0.0021206151.
- Exactly one original 2026 polyline has a source longitude difference exceeding 180° between consecutive original vertices, and exactly this same record is the one source/spherical-km 1%-outlier, ratio **222.0488171062**.
- GRWL width attributes did **not** change at matching export `OBJECTID` values. `OBJECTID` is nonetheless an original file export identifier and has not been independently verified as a lasting physical river feature ID.
- Confirmed original 2026 ZIP SHA-256: `78aa43a7104d24b1696e9b1547347eec13ba5d660aa990c1e7cea98e7ae70e4a`. The 2018 ZIP SHA-256: `16830e5444d47d6ba74790613533b6a81b4036a15f3ad7a7066241da28f95306`.

## Independent mathematical control

New `research_runners/grwl_original_wgs84_ellipsoid_length_v0.py` uses the [GeographicLib 2.1 Python](https://geographiclib.sourceforge.io/html/python/code.html) implementation of [Karney's ellipsoid geodesic inverse](https://geographiclib.sourceforge.io/html/python/), licensed MIT/X11. It is pinned to `geographiclib==2.1` solely in `requirements-grwl-ellipsoid.txt` and installed only in the dedicated read-only `.github/workflows/grwl-original-wgs84-ellipsoid-length.yml` execution profile. No dependency change to the core OpenCatastrophe source/model runtime.

For **every consecutive pair of points in every part of the 2026 original polyline**, use `Geodesic.WGS84.Inverse(latitude1, longitude1, latitude2, longitude2).s12` and sum metres/1000. The inverse computes the shortest ellipsoidal geodesic and intrinsically treats longitude transitions across ±180° correctly. Geometry parts are not spuriously connected. For the original single antimeridian crossing, compare the **source-reported `SHAPE_LENG`** against this independent *shortest* geodesic reference. We also compare the previous spherical Haversine result to the new ellipsoidal result.

The source-reader reuses the audited GRWL original ZIP/DBF/SHP gates, performs the provider-length + MD5 + independent exact original-ZIP SHA256 checks and requires **42,077** unique export `OBJECTID` candidates. The distinct 2018 units proof was already performed using both originals, so **this job fetches only the exact 2026 provider ZIP** to limit source burden and execution cost. It rejects unexpected original byte hashes, numeric invalidity, non-finite coordinates and malformed shape records.

### Privacy-preserving receipt only

Output contains source ZIP SHA-256; the number of original matched rows/points; aggregate distributions (min, p05/p50/p95/p99/max) of *source / ellipsoidal-km*, absolute fractional error, and spherical-km / ellipsoidal-km; and counts beyond 0.01%, 0.1%, 1%, 5% and 10%, **separately for dateline and non-dateline original lines**.

No original ZIP, original `OBJECTID`, raw `SHAPE_LENG`, vertex, geometry, address, centroid or source row may be emitted, uploaded or committed. All source bytes are restricted to a temporary directory in the trusted GitHub runner. Both the GitHub `pull_request` event and default CLI invocation prevent real original download; PR-head CI executes offline synthetic fixtures only.

## Tests and interpretation

`tests/test_grwl_original_wgs84_ellipsoid_length_v0.py` includes independent ellipsoid tests for equatorial and meridional WGS84 distances, the shortest antimeridian crossing, reversed coordinate order, multipart separation, zero-distance vertices, source/outlier classifications and fail-closed duplicate/missing exporter keys. The tests are mandatory in the specialized workflow after the explicit dependency is installed. The general repository test matrix may skip optional ellipsoid-only tests when this isolated dependency is absent; non-network source gates still run.

**Even a successful ellipsoid comparison does not prove the original 2026 `SHAPE_LENG` processing algorithm**, especially near the dateline. Any large discrepancy needs a separate documented source-lineage or method review before a derived physical line length could be admitted.

**Authority limits:** original export `OBJECTID` is not a independently certified river identity; shortest-geodesic original vertex paths are not coast-aware/land-aware river paths, reach topology, flood-stage channel widths or inundation hazard. `model_input_admitted=false`, `flood_stage_or_insured_loss_calculated=false`, `production_database_modified=false`.

**No live original ellipsoid results should be claimed before the reviewed-main workflow succeeds and its original source log is inspected.**
