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

### Path templates

- /v200/2021/map/
- /v200/2021/map/ESA_WorldCover_10m_2021_v200_N48E009_Map.tif

**Parameter rules:** Only these two exact operations are executable after separate review: (a) one fixed HEAD probe_exact_v200_tile_head, and (b) one fixed 4,096-byte GET with Range: bytes=0-4095 under sample_exact_v200_tile_header_4096, to the same N48E009 WorldCover 2021 v200 Map tile URL. No second range, retry, no full-object GET, no unsigned broad S3 list, no sync, no caller-supplied URL/path, object key, headers, redirects or product substitution. Existing list_v200_map_prefix and fetch_exact_v200_tile operation names remain documentation-only. Range 206, Content-Range bytes 0-4095/&lt;original total&gt;, strict response length, same frozen public object identity and TIFF magic are mandatory. Sample bytes stay ephemeral and never enter Git or the CAT database; a sample SHA-256 MUST NOT be represented as full-object SHA-256.

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

**Rate limit notes:** The official ESA public S3 distribution documents anonymous programmatic no-sign access. The reviewed narrow execution operations are one HEAD canary or one exact 4096-byte GET Range=0-4095 sample against the single named N48E009 tile; no bulk collection, crawling, retries, polling, alternate source or paid entitlement assumed.

**Mutability notes:** One full-object HEAD from 2026-11-01 observed a 94,851,935-byte object with generic binary/octet-stream transport MIME. A later range request must return HTTP 206 with exact bytes 0-4095 and matching total object length, and can fingerprint those sampled 4096 bytes. This DOES NOT verify entire 94.85MB TIFF SHA-256, COG spatial index, EPSG:4326, land-cover codes or scientific fitness; full-byte and geospatial validation remain distinct.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://esa-worldcover.org/en/data-access>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** ESA's documented WorldCover 2021 v200 CC BY 4.0 product rights and anonymous S3 data access permit an independently reviewed, strictly bounded 4096-byte original TIFF header sample with no persistence, in addition to the previous exact HEAD metadata check. Source sample and identity receipts are research evidence only. No image pixels, bulk sampling, raw file publication or insurer asset admission is approved.

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

**Notes:** T1 fixed HEAD has succeeded; research T3 preliminary proof now authorizes at most one exact source 4096-byte HTTP Range GET with Content-Range and TIFF/BigTIFF magic inspection on the same N48E009 v200 Map tile. The sample is ephemeral, source-wide hash/COG metadata/CRS remain unverified, and no other operation or original bytes are accepted as CAT model input.
