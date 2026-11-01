<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA Michael × FEMA: source-positive polygon candidates meet four proven zero-alpha raster blocks

**Original source evidence observed 2026-11-01. Research only.** All FEMA provider queries were read-only aggregate `returnCountOnly=true`, `returnGeometry=false`, with an explicit WGS84 `esriGeometryPolygon`, `inSR=4326`, `where=DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'`. We did not retrieve FEMA point coordinates, `OBJECTID` rows, building identities or insurance policy records. The source has **remote-sensing** classifications `AFF`, not independently assessed actual monetary damage.

## Bounded source identities

- NOAA original Digital Coast source ID **8883**, tile `20181011aC0853300w302100n`:
  https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/20181011aC0853300w302100n.json
- Original source GeoTIFF:
  https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/20181011aC0853300w302100n.tif
- FEMA exact public layer `serviceItemId=e56e3d16fa144684bd532edbf298042c`:
  https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0
- Original TIFF first 4096 bytes, 9340×9340 RGBA 8-bit, Deflate, 512×512 tile blocks, WGS84 `EPSG:4326`, 361 source IFD blocks. Original tiepoint at pixel (0,0): **(-85.5500986509636,30.3500986509636)**; pixel scale **(0.000002698072805138984,0.0000026980728051393644)** degrees. The source IFD reports `Predictor=2` and alpha as the fourth `ExtraSamples=2` band.
- Original source `DMG_LEVEL` aggregate and true-polygon parent census: **seven `AFF`**; earlier legacy UTM-reprojected envelope returned **eight**, an overinclusive count. See `noaa-fema-michael-2018-three-tile-spatial-receipt-20261101.md`.

## Exact source-native 512-pixel raster-block count partition

The pilot WGS84 polygon contains **seven FEMA RS/WI** source classifications. A first true-polygon subdivision found all seven in the raster's southwest region; the source pixel grid was then divided into **all 12** raster blocks for **rows 16–18, columns 0–3** (19 columns per TIFF row), with original source-pixel-grid corners converted into explicit closed WGS84 polygons. Direct FEMA public count queries were made for **every one** of those 12 blocks. All 12 source counts **sum to seven**, matching the independently queried entire tile's true polygon count. This is numerical agreement of aggregates, **not formal proof of no boundary double counting or one FEMA record per building**.

| TIFF block index | Row | Column | Original FEMA aggregate polygon count | Original compressed block evidence | Source alpha conclusion |
| ---: | ---: | ---: | ---: | --- | --- |
| 304 | 16 | 0 | 0 | Not read | Not investigated |
| **305** | 16 | 1 | **1** | **HTTP bytes 66442350–66443388**, 1039 bytes | **All alpha zero** |
| **306** | 16 | 2 | **2** | **HTTP bytes 66443389–66444427**, 1039 bytes | **All alpha zero** |
| 307 | 16 | 3 | 0 | Not read | Not investigated |
| 323 | 17 | 0 | 0 | Not read | Not investigated |
| **324** | 17 | 1 | **1** | TIFF IFD bytes 66694287–66776265; 81979 bytes advertised, partial retrieval | **Unknown; not classified** |
| **325** | 17 | 2 | **1** | **HTTP bytes 66776266–66777304**, 1039 bytes | **All alpha zero** |
| **326** | 17 | 3 | **1** | **HTTP bytes 66777305–66778343**, 1039 bytes | **All alpha zero** |
| 342 | 18 | 0 | 0 | Not read | Not investigated |
| 343 | 18 | 1 | 0 | Not read | Not investigated |
| **344** | 18 | 2 | **1** | TIFF IFD bytes 67029595–67050833; 21239 bytes read, no successful pixel decoding | **Unknown; not classified** |
| 345 | 18 | 3 | 0 | Not read | Not investigated |
| **Sum** | | | **7** | | **5 counts inside proven transparent blocks; 2 counts remain unresolved** |

The full original 1,039-byte Deflate stream at **each of source blocks 305, 306, 325, 326** was read and compared **byte-for-byte**, including length and full encoded body, with the previously independently verified transparent source block 180. All four source blocks exactly match its **original compressed-block SHA-256**:

`1e6d5d105f8ee78fd7a403adeac8aef4913dc356ac3f66d3ab300309a1ca8a66`

The reference stream is a valid zlib/Deflate stream yielding exactly **1,048,576 all-zero original RGBA bytes** per 512×512 block. Its fourth alpha sample is therefore zero for all 262,144 pixels **of each of these four blocks**, including predictor effects. **One + two + one + one = five** of the *seven public FEMA aggregate block counts* thus fall within independently byte-verified NOAA blocks whose pixels **cannot show any building**. This says nothing about whether the original FEMA classifications are true or false; it only demonstrates the inspected **NOAA TIFF** is unsuitable as direct visual independent evidence for these five source count scopes.

The remaining two FEMA aggregate counts (blocks 324 and 344) are **unresolved**, not confirmed visible pixels. The size of the compressed source blocks alone is not an alpha-visibility proof. The separate NOAA item-level `NLPL`/InPort `CC0-1.0` licence mapping and original image lineage need further review before commercial model use.

## Executable research-only guardrail

`research_runners/noaa_fema_alpha_negative_blocks_v0.py` accepts one **locally supplied original 4096-byte TIFF header**, exact caller-supplied source-shaped STAC metadata, the complete **12-block count-only response partition**, the full true-polygon source parent count, and optional complete original compressed bytes for audited blocks. It checks TIFF/STAC identity and geometry, rejects incomplete/duplicate/malformed aggregate partitions, applies the previously strict per-block Deflate/IFD proof, and reports only **negative image alpha evidence**. It explicitly refuses to infer visible alpha under any FEMA point, unique feature identity, independent assessment source or model admission. Its tests use **synthetically generated raster headers, compressed all-zero bytes and counts**, not redistributed original provider image content.

## Follow-up: original blocks 324 and 344 resolved at alpha-pixel level

A separate successful real GitHub Actions source-byte run (https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41329301340) fetched both original TIFF Deflate blocks, checked HTTP206 `Content-Range`, matching `ETag`, zlib/Adler-32 and TIFF Predictor=2. Source **block 324** has **39,316** alpha-positive pixels out of 262,144; source **block 344** has **7,948** alpha-positive pixels out of 63,488 valid bottom-edge pixels. A new conservative true-WGS84-polygon FEMA query enclosing **all** visible pixels in block 344 returned **0** of its **1** full-block FEMA count: **six** of the seven source candidates are now excluded as NOAA-image-visible damage-validation samples, while the **one** candidate in block 324 remains **unresolved**. Neither is an independently verified damaged building. The original object's authoritative HTTP `Content-Range` total is **67,126,397** bytes; no complete-file SHA-256 was computed. See `docs/research/noaa-michael-324-344-original-alpha-provenance-20261101.md` for exact source hashes, grid boundaries and limitations.

**Key limitation:** Aggregate block counts plus numeric conservation do not establish exact boundary-point ownership, unique buildings, image capture time, independently sourced labels or a validated claim/loss amount. To progress scientifically, independently prove complete alpha interpretation for **only source blocks 324 and 344** and test a dated 2018-era independent building polygon reference; do not assert seven usable damage labels or train on the original FEMA RS labels.
