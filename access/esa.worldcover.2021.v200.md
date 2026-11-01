<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/esa.worldcover.2021.v200.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `esa.worldcover.2021.v200.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** esa.worldcover.2021.v200

## Source ids

- esa.worldcover.2021.v200

**Provider:** European Space Agency (ESA) WorldCover consortium / VITO

**Interface type:** object_store

**Status:** probe_ready

**Documentation url:** <https://esa-worldcover.org/en/data-access>

**Service root:** <https://esa-worldcover.s3.eu-central-1.amazonaws.com>

**Api version:** WorldCover 2021 v200; AWS bucket esa-worldcover; prefix v200/2021/map

## Access scope

- metadata
- bulk

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- list_v200_map_prefix
- fetch_exact_v200_tile
- probe_exact_v200_tile_head
- sample_exact_v200_tile_header_4096
- sample_exact_v200_tile_tables_10368

### Path templates

- /v200/2021/map/
- /v200/2021/map/ESA_WorldCover_10m_2021_v200_N48E009_Map.tif

**Parameter rules:** Only three frozen operations are executable for the single N48E009 WorldCover 2021 v200 Map tile: one HEAD, one GET Range bytes=0-4095 (verified TIFF header), and one separately reviewed GET Range bytes=13644-24011 containing the complete adjacent LONG32 TileOffsets and TileByteCounts tables, declared by the actual original first IFD (1,296 elements each). The source URI, product, year, tile and each range are constant, with no caller-supplied host, query, parameter, header, object, date or range; no redirects, retries, sync, arbitrary S3 listings, full object GET or additional tile block fetches. Existing list_v200_map_prefix and fetch_exact_v200_tile names remain documentation only. For the new 10,368-byte response require HTTP 206, exact Content-Range bytes 13644-24011/94851935, strict Content-Length, identity coding, array bounds, non-overlapping compressed block addresses and no source-byte persistence. This is not permission to download actual raster pixels or infer a source-wide SHA-256.

## Response contract

### Expected media types

- image/tiff
- application/octet-stream
- binary/octet-stream

**Format:** WorldCover 2021 v200 map data are distributed as 3 by 3 degree Cloud-Optimized GeoTIFF tiles in EPSG:4326. The analytical map layer and InputQuality layer are distinct products; WMS/WMTS RGB visualizations are cartographic views and must not be treated as analysis rasters. The exact public S3 object may be served with generic binary/octet-stream transport metadata; that MIME alone does not verify the GeoTIFF payload, COG layout, EPSG:4326 or land-cover classes.

**Scientific semantics:** WorldCover 2021 v200 is a 10 m global land-cover map with 11 classes and a 2021 reference year. The official product-level independent validation reports 76.7% overall accuracy for v200; this is not a per-pixel correctness guarantee. WorldCover 2020 uses algorithm v100 while 2021 uses v200, so differences between the two maps contain both real land-cover change and algorithm effects and must not be interpreted as a pure change layer. Land-cover class is contextual exposure/vulnerability information, not asset count, insured value, hazard intensity, damage or loss.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `52428800`

**Retry policy:** none

**Rate limit notes:** ESA WorldCover data-access officially permits public no-sign S3 programmatic access. One exact source-header 4 KiB GET and independently one exact 10,368-byte table-directory GET are reviewed research canaries, plus existing one HEAD metadata request. No bulk, recurring monitoring, retries, source synchronization or caller-selected ranges authorized.

**Mutability notes:** The actual 2026-11-01 first 4096 source bytes (SHA256 a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529) identified TileOffsets LONG\[1296\] at original bytes 13644–18827 and TileByteCounts LONG\[1296\] at 18828–24011, each length 5184. The next 10368-byte GET verifies only those tables. Frozen source object total length 94851935; changes to TIFF header/table layout require a separate review. Individual compressed pixels, decoded raster classes, full-object SHA256 and COG structure stay unverified.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://esa-worldcover.org/en/data-access>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** ESA WorldCover 2021 v200 CC BY 4.0 permits reviewed public distribution and attributed downstream use; official data-access documentation permits no-sign programmatic S3. Research now reviews a single exact 10,368-byte TIFF offset/count directory GET against the previously fixed 2021 v200 N48E009 Map tile, in addition to earlier HEAD and 4KiB header probes. No provider raw bytes retained and no pixel block download or raster publication/model admission approved. Specific future block downloads require independent validation and review.

## Probe contract

**Mode:** head

**Operation:** probe_exact_v200_tile_head

**Requires credentials:** `false`

### Expected evidence

- fixed region-specific HTTPS HEAD returned HTTP 200, or explicit blocked status
- nonzero Content-Length and Content-Type recorded without obtaining raster bytes
- source object identity, contract SHA-256, execution-code SHA-256 and UTC receipt
- ETag hash recorded as transport metadata, never treated as source SHA-256
- source_bytes_downloaded=false and model_input_approved=false

**Implementation decision:** build_later

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://esa-worldcover.org/en/data-access>
- <https://registry.opendata.aws/esa-worldcover-vito/index.html>
- <https://zenodo.org/records/7254221>
- <https://creativecommons.org/licenses/by/4.0/>
- <https://github.com/ESA-WorldCover/esa-worldcover-datasets>
- <https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf>

**Notes:** The exact 2026-11-01 original 4096-byte TIFF header proves two adjacent 1296-element LONG32 tile directory locations; a new one-shot, no-persistence 10368-byte Range GET may read only those original tables. Table-derived offset/bytecounts must be scientifically treated as source data until checked and frozen. No pixel retrieval, full file download or production CAT use admitted.
