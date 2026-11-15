<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/dlr.wsf.2019.native-geotiff.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `dlr.wsf.2019.native-geotiff.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** dlr.wsf.2019.native-geotiff

## Source ids

- dlr.wsf.2019

**Provider:** German Aerospace Center (DLR), Earth Observation Center / EOC Geoservice

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://geoservice.dlr.de/data-assets/twg5xsnquw84.html>

**Service root:** <https://download.geoservice.dlr.de>

**Api version:** WSF2019 v1 (2019 observation epoch), fixed original tile WSF2019_v1_10_48.tif; DOI 10.15489/twg5xsnquw84

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- fixed_original_geotiff_two_ranges

### Path templates

- /WSF2019/files/WSF2019_v1_10_48.tif

**Parameter rules:** Documented exact source identity only; no new network action authorized in this contract. Historical trusted bounded research retrieved two original bytes=0-32767 (32,768 bytes) and bytes=12156322-12180980 (24,659 bytes) HTTP Range GET responses from this fixed host and path. Those ranges, header, tile position and SHA-256 are pinned in scripts/probe_dlr_wsf_native_cog_tile_v0.py. Do not fetch the full TIFF, change host or filename, follow redirects, retry automatically, accept arbitrary Range/URL/headers, enumerate tiles or use PR-defined endpoints. Any future live execution requires separately reviewed DLR file-service terms, per-request preflight and a trusted allowlisted runner.

## Response contract

### Expected media types

- image/tiff
- image/geotiff
- application/octet-stream

**Format:** Native little-endian ClassicTIFF / GeoTIFF LZW-compressed single-band uint8 512x512 tiled file. Previous two-range study inspects one fixed native 512x512 compressed tile without materializing or publishing the full original GeoTIFF.

**Scientific semantics:** 2019 multi-temporal Sentinel-1/Sentinel-2-derived 10 m nominal global settlement extent, not individual buildings, actual building footprints, cadastral parcels, insured TIV, vulnerability or losses. Exact tested tile uses EPSG:4326 and native angular pixel scale 0.00008983152841195215 degrees. Binary classes 0=nonsettlement, 255=settlement in the independently decoded sample. Absence of a TIFF NoData tag is not a proof of completeness. Dataset coverage is approximately 60 degrees S to 78 degrees N, not every polar landmass. Two 32x32 native windows from one original tile are not a geographically representative validation set.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `32768`

**Max sample bytes:** `57427`

**Retry policy:** none

**Rate limit notes:** No explicit DLR file-service rate, Range, cache or automated-access quota was independently verified for this fixed HTTP-file path. This document-only contract does not authorize new T1/T3 acquisitions or scheduled polling. Previously trusted fixed-read research receipts are historical evidence, not a provider-automation clearance.

**Mutability notes:** The original tile path is version-namespaced but not proved immutable. Historical original TIFF first 32768 bytes SHA-256 1e881e8323d3ade63ad4453a0c1b7af6d792ae254356ceb20c197d0316ab80b7 and exact 24659-byte compressed tile SHA-256 8f06d03fcc3cc63930d216a834bca6c51275da6b436e1b2639a39952ddbf0503 were checked by earlier trusted research runs; they are TWO PARTIAL ORIGINAL-BYTE hashes, NOT the full GeoTIFF SHA-256. The independently decoded tile contains 144731 class-0 and 117413 class-255 native pixels. A changed tile/header/range or URI requires a fresh review; never substitute provider thumbnail/WMS PNG for native raster classes.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** DLR's official WSF2019 product page and STAC collection identify the exact scientific product and CC BY 4.0 data licence (including commercial data use with attribution, licence notice and modification notice); DOI 10.15489/twg5xsnquw84. The licence applies to the dataset, not automatically to unlimited use of the HTTP file service or a new fixed-Range request. Current DLR-specific file-service API/automation cadence, throttling and bulk/redistribution conditions are not separately evidenced for this contract. Hence this document-only contract does not clear automated source retrieval or publication of full original rasters. Model scientific admission remains independent.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://geoservice.dlr.de/data-assets/twg5xsnquw84.html>
- <https://cube.geoservice.dlr.de/web/datasets/wsf_2019>
- <https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_2019>
- <https://download.geoservice.dlr.de/WSF2019/files/>
- <https://download.geoservice.dlr.de/WSF2019/files/WSF2019_README.txt>
- <https://creativecommons.org/licenses/by/4.0/>

**Notes:** Exact one-source T0 contract; linked landscape source_id dlr.wsf.2019 is non-admitted discovery. Historical native Range evidence: scripts/probe_dlr_wsf_native_cog_tile_v0.py, tests/test_probe_dlr_wsf_native_cog_tile_v0.py, scripts/verify_dlr_wsf_native_rasterio_v0.py, and docs/research/bvv-hu-by-original-shp-vs-wsf2019-first-real-overlap-20261112.md. Previous native sample/source QA is research-only; no new original data fetched in this PR. No whole-file SHA-256, independent multi-area accuracy or historical 2019 building survey comparison is proven. Keep exposure-model admission and insurer-loss use blocked. Do not interpret a prior successful HTTP Range or STAC metadata access as new T1/T3 permission.
