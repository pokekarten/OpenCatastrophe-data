<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA Michael 2018 × FEMA DR-4399: first actual tile-envelope count receipts

**Queried:** 2026-11-01; source type: live public read-only FEMA ArcGIS FeatureServer **aggregate** queries against separately retrieved original NOAA STAC item metadata. This is a purely geographic **envelope-candidate test**. It is not evidence that an exact NOAA TIFF pixel was nontransparent, that an image was used to label a building, or that any FEMA point denotes a unique property or independently measured damage.

## Data identity and exact query contract

- FEMA source `serviceItemId=e56e3d16fa144684bd532edbf298042c`, public layer: https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0
- FEMA source-data edit timestamp **2021-06-22** (service metadata). Event key is **`DIS_NUMBER = 'DR-4399'`**, *not* all 2018 Hurricane Michael administrative disasters.
- NOAA original Digital Coast imagery collection ID **8883**: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/catalog.json
- Spatial rectangles are the source STAC item `bbox` coordinates in **EPSG:4326**; separate FEMA layer geometry is published in EPSG:32616. ArcGIS query uses explicit `inSR=4326`, so the service performs the predicate in its implementation and returns only counts, never source points or polygons.

Exact REST endpoint: `/FeatureServer/0/query`, with parameters `where=DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'`, `geometry=<source STAC west,south,east,north>`, `geometryType=esriGeometryEnvelope`, `inSR=4326`, `spatialRel=esriSpatialRelIntersects`, `returnCountOnly=true`, `returnGeometry=false`, `f=json`. A second query uses the same rectangle but `where=DIS_NUMBER = 'DR-4399'`. For the nonzero tile, a grouped aggregate additionally uses `groupByFieldsForStatistics=DMG_LEVEL` and `outStatistics=count(OBJECTID) AS n`.

## Actual zero-versus-eight spatial results

| Exact NOAA STAC item ID | Source bbox [west,south,east,north] | FEMA `DR-4399` RS/WI points in bbox |
| --- | --- | ---: |
| `20181011aC0855400w301330n` | `[-85.9001,30.1999,-85.8749,30.2251]` | **0** |
| `20181011aC0853300w302100n` | `[-85.5501,30.3249,-85.5249,30.3501]` | **8** |
| `20181011aC0844330w294330n` | `[-84.7251,29.6999,-84.6999,29.7251]` | **0** |

The source-independent **parent-disaster count** for the middle tile was also **8**, and the source `DMG_LEVEL` group-by returned **8 × `AFF`** (Affected), no other damage-level group. All queries were made as separate **read-only FEMA aggregates**, not a fabricated GIS overlay or an imported feature dataset.

**NOAA source tile selected for any subsequent bounded imagery evidence gate:** `20181011aC0853300w302100n` because the actual `DR-4399` cohort contains eight candidate assessment points within its **bounding envelope**. Its official STAC item metadata was fetched; the TIFF header was separately fetched with `Range: bytes=0-4095` and returned **4,096** original bytes confirming classic little-endian TIFF, **9,340 × 9,340**, 4-band image, Deflate compression, internal **512 × 512** tiles and 361 tile-block entries. The original TIFF `DateTime` was `2018:10:11 23:59:59`, an **unverified exact capture time**.

- Original STAC item: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/20181011aC0853300w302100n.json
- Original TIFF asset (do **not** bulk fetch/commit): https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/20181011aC0853300w302100n.tif
- Tile metadata license code **`NLPL`**, a named permissive SPDX No Limit Public License. NOAA InPort dataset code **`CC0-1.0`**, also permissive. This is a *source-scope crosswalk still requiring exact-asset review*, not evidence for a noncommercial condition.

## What this actual spatial check proves—and what it does not

**Proved:** precise, reproducible NOAA bbox query scopes exist; a bounded FEMA count query returns `0/8/0` for the three selected tiles; the middle tile is the only candidate with positive **point-versus-rectangle** occurrence among them; same rectangle and one exact source disaster yield reconciled `8` parent, `8` subset and `8 AFF` class counts.

**Not proved:** any FEMA point is over an **alpha-visible** part of the NOAA raster; original raster is wholly intact; a point maps to a unique building polygon; the source captures visible damage; all eight are independent field measurements (they are **RS**, not **FA**); NOAA was not used by the FEMA original annotators; a photo is the source of an insured claim; any exact capture time; or the rights to admit the asset to a commercial model.

The **true next dependency** is a small, rights-checked local read of **one** original NOAA TIFF to validate file hash/size, RGB/alpha mask and source timestamp, plus an independently sourced event-era building-footprint version. A `bbox` spatial hit must **never** be promoted to a positive pixel-covered building join or loss/claim record.

## Added executable, fail-closed offline step

`research_runners/noaa_fema_envelope_overlap_v0.py` generates exact provider query parameters from a validated caller-supplied NOAA STAC item and strictly reconciles **only** geometry-free count/group replies, with a missing-data zero case. The Python does not fetch provider data or accept feature IDs, parcel geometries, unreviewed damage codes or duplicate `DMG_LEVEL` rows. Output does not expose bbox coordinates, and it explicitly marks image alpha coverage, unique building identity, source-response authenticity, scientific independence and CAT-model admission **false**.

`tests/test_noaa_fema_envelope_overlap_v0.py` contains entirely synthetic unit-test fixtures with zero/nonzero count, type, leakage, source-date, group-duplication and total-agreement cases. The **real** source counts reported in the table above originate from the separately executed original FEMA API requests, not from the synthetic tests.
