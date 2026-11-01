<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA Michael 2018 × FEMA DR-4399: corrected true-polygon spatial receipts

**Checked:** 2026-11-01; original read-only public FEMA ArcGIS spatial aggregate queries, exact independently inspected NOAA STAC tile identities, **no FEMA feature rows or point coordinates retrieved**.

## Scientific correction: projected envelope count was not true polygon overlap

FEMA's public damage FeatureServer layer 0 is **`esriGeometryPoint`**, native spatial reference **EPSG:32616 (UTM zone 16N)**. NOAA Digital Coast imagery 8883 STAC tiles use **EPSG:4326**. Source layer identity: `serviceItemId=e56e3d16fa144684bd532edbf298042c`.

The first exploratory query used an ArcGIS `esriGeometryEnvelope` in WGS84 with `inSR=4326`, `returnGeometry=false` and `returnCountOnly=true`. A native UTM service may transform an input envelope into an expanded axis-aligned UTM envelope; this makes an apparent point hit in a source WGS84 rectangle **not necessarily a true geographic polygon hit**. In the actual pilot, the large envelope returned **8**, but a finer envelope partition returned **2 + 5 = 7** in the matching lower band. Thus the original envelope counts were **not spatially additive**. The precise server implementation of the discrepancy is not proved, but rectangle reprojection is a plausible mechanism. Never promote those eight to confirmed polygon-overlapping points.

A more exact source query now supplies an **explicit closed five-vertex WGS84 polygon ring**:
`geometry={"rings":[[[W,S],[E,S],[E,N],[W,N],[W,S]]],"spatialReference":{"wkid":4326}}`,
`geometryType=esriGeometryPolygon`, `inSR=4326`, `spatialRel=esriSpatialRelIntersects`, with the **same** strict
`where=DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'`,
`returnCountOnly=true`, `returnGeometry=false`, `f=json`.

### Three exact source tile count results

| Source NOAA STAC tile | Source WGS84 bbox [W,S,E,N] | Legacy envelope query | Corrected polygon query |
| --- | --- | ---: | ---: |
| `20181011aC0855400w301330n` | `[-85.9001,30.1999,-85.8749,30.2251]` | 0 | **0** |
| `20181011aC0853300w302100n` | `[-85.5501,30.3249,-85.5249,30.3501]` | 8 | **7** |
| `20181011aC0844330w294330n` | `[-84.7251,29.6999,-84.6999,29.7251]` | 0 | **0** |

The corrected middle-tile polygon `DMG_LEVEL` group-by returned **7 × `AFF` (Affected)** and nothing else. The separately checked polygon parent-disaster `where=DIS_NUMBER = 'DR-4399'` returned **7**, and `where=1=1` also returned **7**. No source point location, personal record, building polygon or insurance policy was downloaded. These are **counts of remote-sensing classifications, not validated damaged-building or insurance-loss totals**.

One real polygon count partition (in exact NOAA source pixel-grid coordinates) into the lower western region returned a reconciled **2 + 5 = 7**. The former overlapping UTM-envelope region count **8** must not be substituted for the true WGS84 polygon count. Even polygon boundary inclusion may make two adjacent polygons non-additive when actual points lie on their shared border: **always reconcile parent and children and refuse automatic spatial promotion on mismatch**.

## Bounded original image identity

- FEMA exact public layer: https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0
- NOAA Digital Coast catalog: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/catalog.json
- Corrected seven-point pilot item: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/20181011aC0853300w302100n.json
- Selected source TIFF: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/20181011aC0853300w302100n.tif

The source TIFF first IFD 4,096 bytes were read. Three small original compressed source block ranges were separately checked and proved **341,008 disjoint pixels are fully alpha-transparent**; this is negative partial image evidence, **not** a full raster-alpha mask. The public HTML directory displays **18.94 MB**, although the original first TIFF IFD requires **at least 67,126,397 bytes**. The directory may describe a different/stale packaging state; exact authoritative file size, ETag and full SHA-256 remain unknown. See `docs/research/noaa-michael-original-center-alpha-block-20261101.md`.

## Code contract and admission

`research_runners/noaa_fema_envelope_overlap_v0.py` retains its original filename for existing import paths but its query builder now constructs **true EPSG:4326 polygon geometry**, not `esriGeometryEnvelope`. The default reconciliation profile and response fields state **polygon** counts. `build_proven_transparent_block_query` likewise uses a source-TIFF-derived rectangle represented by an exact WGS84 polygon ring. The synthetic tests pin those parameter shapes, ensure aggregate count agreement and disallow individual source positions in results. **Legacy envelope counts are retained here only as scientific error evidence.**

**Explicit NO-GO:** neither seven true-polygon remote-sensing points nor the earlier eight bounding-envelope hits prove alpha-visible NOAA pixels at those point locations, unique dated buildings, paid claims, NOAA/FEMA labeling independence, complete source TIFF validity, commercial-asset rights or admitted CAT vulnerability inputs.

The next causal test is to inspect source image **alpha blocks overlapping the seven true-polygon candidates**, after another solely aggregate, polygon-based spatial subdivision and an exact original byte-range/rights review. Do not export private claims, individual FEMA features or unrestricted source images to Git.
