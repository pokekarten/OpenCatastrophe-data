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

### Path templates

- /v200/2021/map/
- /v200/2021/map/ESA_WorldCover_10m_2021_v200_N48E009_Map.tif

**Parameter rules:** This source-specific T1 probe freezes exactly one HEAD request for the candidate 3x3-degree N48E009 WorldCover 2021 v200 Map GeoTIFF under the documented ESA public S3 prefix. The object key is constructed from the published tile naming/3-degree grid scheme, and its actual existence must be independently established by the HEAD response. Only the fixed HTTPS HEAD request is executable. Historical list_v200_map_prefix and fetch_exact_v200_tile operation names remain documentation-only and MUST NOT be executed under this probe. No GET, Range, S3 list/sync, arbitrary host, redirect, caller-supplied key, variant, product year, other geographic tile, credential or private endpoint is allowed. The DOI 10.5281/zenodo.7254221 anchors the release identity, not this individual object hash.

## Response contract

### Expected media types

- image/tiff
- application/octet-stream

**Format:** WorldCover 2021 v200 map data are distributed as 3 by 3 degree Cloud-Optimized GeoTIFF tiles in EPSG:4326. The analytical map layer and InputQuality layer are distinct products; WMS/WMTS RGB visualizations are cartographic views and must not be treated as analysis rasters.

**Scientific semantics:** WorldCover 2021 v200 is a 10 m global land-cover map with 11 classes and a 2021 reference year. The official product-level independent validation reports 76.7% overall accuracy for v200; this is not a per-pixel correctness guarantee. WorldCover 2020 uses algorithm v100 while 2021 uses v200, so differences between the two maps contain both real land-cover change and algorithm effects and must not be interpreted as a pure change layer. Land-cover class is contextual exposure/vulnerability information, not asset count, insured value, hazard intensity, damage or loss.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `52428800`

**Retry policy:** none

**Rate limit notes:** ESA documents anonymous programmatic no-sign AWS access for the versioned S3 product. This contract permits only one fixed HEAD request when an explicitly reviewed test workflow executes. No ongoing polling, bulk listing, download or paid quota assumption is authorized.

**Mutability notes:** The 2021 v200 product identity and ESA DOI are stable reference labels; this HEAD probe checks whether the candidate exact N48E009 Map object exists and obtains its HTTP content length, ETag metadata and media type. A mutable S3 ETag is NOT an independent SHA-256 of source bytes, nor a provenance receipt sufficient for CAT model admission. Exact source hash, COG georeference/grid, class values, licence, scientific year and derived-use scope require a distinct source-byte workflow.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://esa-worldcover.org/en/data-access>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** ESA officially permits CC BY 4.0 WorldCover dataset reuse with attribution and documents anonymous programmatic AWS access. This T1 contract authorizes only a single fixed anonymous HEAD against one candidate 2021 v200 map tile. It does not authorize downloading/reproducing pixels, bulk collection, secondary redistribution by this repository, or accepting land-cover classes as insured physical buildings.

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

**Notes:** T1 anonymous HEAD-only candidate tile availability check for a single ESA WorldCover 2021 v200 3x3-degree map object near southern Germany, with pinned host, product/year/tile identity and no source-byte download. Tile existence and service Content-Type must be proven live; GeoTIFF pixels, scientific input fitness and distribution approval remain separate. No other paths or previously documented list/fetch operations become executable.
