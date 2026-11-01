<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hurricane Michael NOAA GeoTIFF: original zero-alpha source blocks and size crosswalk

**Evidence date:** 2026-11-01. **Status:** three bounded original compressed byte-range samples plus a 4-KiB IFD, **not** a full GeoTIFF download, an exhaustive image-coverage audit or a licensed/model-ready dataset. No original TIFF pixels, source header bytes, FEMA feature records or original image files are included in this repository.

## Exact original source and bounded byte evidence

- NOAA authoritative dataset: https://www.fisheries.noaa.gov/inport/item/57759
- NOAA Digital Coast imagery collection `8883`, exact source STAC item: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/20181011aC0853300w302100n.json
- Exact original source GeoTIFF: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/20181011aC0853300w302100n.tif
- Exact bounded HTTP `Range: bytes=0-4095`: original **4,096 bytes**, classic little-endian TIFF, source-native **9,340 × 9,340**, four 8-bit bands, Deflate, 512 × 512 raster blocks, EPSG:4326, 361 compressed block offsets/byte counts.
- Read the **one actual source block** referenced by its original TIFF IFD: zero-based TIFF block index **180** (raster tile row **9**, column **9**), original byte offset **64,665,046**, compressed byte count **1,039**, exact HTTP `Range: bytes=64665046-64666084`.
- Complete original **compressed block** SHA-256 (not complete GeoTIFF hash): `1e6d5d105f8ee78fd7a403adeac8aef4913dc356ac3f66d3ab300309a1ca8a66`.
- The 1,039 bytes are a valid **zlib/Deflate** stream. Decompression returned exactly **1,048,576 bytes** = 512 × 512 × four 8-bit bands; **every decoded byte was zero**. The source stream's complete compressed-byte SHA-256 equals the independently generated `zlib.compress(bytes(512*512*4), level=6)` fixture SHA-256. Thus, **all 262,144 in-image pixels of this interior block have fully transparent alpha** regardless of horizontal TIFF predictor effects: all channels are zero.
- This center-block result is **one original 512 × 512 block**, not 262,144 confirmed damaged/undamaged buildings and not the full 9,340 × 9,340 image. Two additional exact original compressed blocks were subsequently matched byte-for-byte; see the separately bounded evidence section below. Equal compressed-byte *lengths* elsewhere do not prove equal contents.

The original first-4KiB TIFF `ModelPixelScale` was `(0.000002698072805138984, 0.0000026980728051393644)` degrees/pixel; the original source `ModelTiepoint` was `(-85.5500986509636, 30.3500986509636)` at the top left pixel.

Block 180's **pixel-grid envelope** computed directly from the original transform in EPSG:4326:

`[-85.53766593147752, 30.336284518201285, -85.5362845182013, 30.337665931477517]`
(`[west,south,east,north]`).

This pixel-grid boundary is derived from source metadata. It is **not** an original flight footprint, the alpha-visible polygon or a verified 2018 building footprint.

## Source-native FEMA count comparison (aggregate only)

With the exact raster block envelope above and the same public FEMA layer `serviceItemId=e56e3d16fa144684bd532edbf298042c`, a live read-only ArcGIS aggregate query used:

`where=DIS_NUMBER = 'DR-4399' AND ASMT_TYPE = 'RS' AND DMG_TYPE = 'WI'`,
`geometryType=esriGeometryEnvelope`, `geometry=west,south,east,north`,
`inSR=4326`, `spatialRel=esriSpatialRelIntersects`,
`returnCountOnly=true`, `returnGeometry=false`, `f=json`.

**Actual source response: `{"count":0}`** for block 180's geographic rectangle.

A previously executed **legacy ArcGIS `esriGeometryEnvelope`** query over the full STAC bbox returned **8** `AFF` assessments, with coarse west/east legacy envelope counts 8/0. This was **not a true geographic WGS84 polygon count**: a corrected closed-ring `esriGeometryPolygon` query returned **7** for the full tile, all `AFF`. FEMA's native CRS is EPSG:32616; overinclusive transformed envelopes can produce non-additive counts. The seven still have **no proven alpha-visible pixels**; never interpret the older eight as exact spatial overlap.

The zero count over a proven all-transparent block is **consistent** with zero available assessments there. It does **not** demonstrate that the seven true-polygon assessments elsewhere are covered by visible pixels, independently labeled or correspond to unique buildings.

## Two additional byte-verified source blocks and measured minimum file extent

Two **separate** original source HTTP Range requests against the exact same named GeoTIFF were completed and compared byte-for-byte to the previously verified 1,039-byte Deflate stream of block 180. Both original ranges returned **identical complete compressed bytes**; the same separately decoded SHA-256 `1e6d5d105f8ee78fd7a403adeac8aef4913dc356ac3f66d3ab300309a1ca8a66` therefore applies to the three specifically checked blocks. Matching the compressed streams transfers the previously established all-zero RGBA pixel content **only** to those exact blocks.

| TIFF IFD zero-based block | Full compressed HTTP Range (inclusive) | Position | Valid image pixels all alpha zero |
| --- | --- | --- | ---: |
| 18 | `bytes=26029152-26030190` | row 0, col 18, rightmost partial column | **63,488** (512 × 124) |
| 180 | `bytes=64665046-64666084` | row 9, col 9, interior | **262,144** (512 × 512) |
| 360 | `bytes=67125358-67126396` | row 18, col 18, bottom-right partial block | **15,376** (124 × 124) |
| **Total, these 3 verified disjoint blocks only** | | | **341,008** |

Other blocks are **not** proven transparent. The TIFF IFD gives **241 blocks of compressed size 1,039 bytes**, but matching *byte lengths alone* does not prove matching *byte content*. In particular, one must never multiply 241 × 262,144 or classify all those blocks without independently inspecting bytes and valid edge extents.

**Independent directory-size integrity warning:** NOAA's public HTML inventory (the original `index.html` linked above) displays the exact asset `20181011aC0853300w302100n.tif` as **18.94 MB**. The actual first TIFF IFD lists **361** `TileOffsets` and `TileByteCounts`, whose maximum `offset + byte_count` is **67,126,397 bytes**. Therefore **any complete file containing that exact successfully retrieved IFD must be at least 67,126,397 bytes**. The original source also returned byte-range samples at offsets **67,126,395–67,126,396**, directly corroborating data at the extreme end of this lower bound.

The HTML display is **incompatible** with these same source header bytes even after allowing decimal/binary megabytes and 0.01 MB rounding. This is **not evidence of TIFF corruption**: the directory may be stale, based on a different object/version, or represent a separate packaging convention. No authoritative `Content-Length`, immutable `ETag`/release ID, full-file SHA-256 or successful end-to-end file download was verified. A failed request *beyond* the maximum IFD byte is not affirmative proof of exact object size. **The HTML-displayed 18.94 MB must not be recorded as current authoritative file identity or used as a download-size acceptance threshold.**

`research_runners/noaa_michael_tiff_header_v0.py` now reports the **minimum byte extent derived from its source IFD**, and `compare_provider_directory_size()` challenges a rounded directory MB claim against that lower bound. Its report explicitly leaves HTTP Content-Length and full-file identity **unverified**, even if a directory-size comparison happens to pass.

## Reproducible scientific gate

`research_runners/noaa_michael_alpha_tile_probe_v0.py` accepts **caller-supplied**, strictly bounded *original* TIFF first-4KiB metadata plus exactly one compressed tile. It validates the underlying TIFF/STAC metadata, original block offset and byte-count fields, bounded Deflate decoding (maximum 1,048,576 bytes), and the fully zero **RGBA** result. It produces a block-specific SHA-256 and transparent-pixel count **only** for a fully all-zero block. It does not infer positive visible-alpha coverage from arbitrary nonzero DEFLATE output because TIFF predictor interpretation is not yet reviewed. Tests use regenerated **synthetic** TIFF/Deflate data and malicious/truncated blocks, never committed copyrighted original image bytes.

The `build_proven_transparent_block_query()` function in `research_runners/noaa_fema_envelope_overlap_v0.py` derives the exact `EPSG:4326` rectangle directly from the **same verified source TIFF** pixel scale/tiepoint and the selected zero-alpha raster block. It emits only an explicit FEMA `returnCountOnly=true`, `returnGeometry=false` query contract and does not fetch image or FEMA feature rows. Synthetic tests check exact geographic derivation, fail-closed refusal of any nonzero-alpha-inconclusive block and byte-length mismatches. The **real** count of zero for this exact block came from the separate provider request above; tests do not manufacture live provider authenticity.

**NO-GO for positive image building coverage:** even this exact **byte-verified transparent block** cannot prove whether any of the eight FEMA assessments in the full image bbox fall on valid visible NOAA pixels. Asset-wide integrity/sha256, complete alpha mask, licensing scope, historical footprint identity and independent FEMA image-label lineage are unverified. These remain separate explicit gates.
