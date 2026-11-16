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

**Parameter rules:** Documented exact source identity only; no new network action authorized in this contract. Historical trusted bounded research retrieved two original bytes=0-32767 (32,768 bytes) and bytes=12156322-12180980 (24,659 bytes) HTTP Range GET responses from this fixed host and path. Those ranges, header, tile position and SHA-256 are pinned in scripts/probe_dlr_wsf_native_cog_tile_v0.py. Do not fetch the full TIFF, change host or filename, follow redirects, retry automatically, accept arbitrary Range/URL/headers, enumerate tiles or use PR-defined endpoints. The EOC Geoservice AUP v1.1 has been reviewed for this download host; it does not establish an explicit WSF2019 fixed-Range automation entitlement or per-request rate budget. Any future live execution requires the exact operation, provider service budget and trusted allowlisted runner to be separately approved.

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

**Rate limit notes:** The EOC Geoservice AUP v1.1 (2023-09-01) expressly covers download.geoservice.dlr.de; it requires responsible non-disruptive service use and allows blocking misuse, but provides no numeric Range-request rate or per-product automated transfer budget. No affirmative automated WSF2019 original-tile request permission has been independently evidenced. This documented-only contract therefore authorizes no new T1/T3 acquisitions, automated bulk mirror or scheduled polling; earlier trusted fixed-read receipts remain historical research evidence.

**Mutability notes:** The original tile path is version-namespaced but not proved immutable. Historical original TIFF first 32768 bytes SHA-256 1e881e8323d3ade63ad4453a0c1b7af6d792ae254356ceb20c197d0316ab80b7 and exact 24659-byte compressed tile SHA-256 8f06d03fcc3cc63930d216a834bca6c51275da6b436e1b2639a39952ddbf0503 were checked by earlier trusted research runs; they are TWO PARTIAL ORIGINAL-BYTE hashes, NOT the full GeoTIFF SHA-256. The independently decoded tile contains 144731 class-0 and 117413 class-255 native pixels. A changed tile/header/range or URI requires a fresh review; never substitute provider thumbnail/WMS PNG for native raster classes.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://geoservice.dlr.de/resources/licenses/geoservice/EOC_Geoservice_AUP_v1.1.pdf>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The source-specific WSF2019 dataset licence is CC BY 4.0 (including commercial reuse with attribution); it is separate from service access. Official EOC Geoservice Acceptable Use Policy v1.1 dated 2023-09-01 explicitly governs geoservice.dlr.de and the EOC Download Service at download.geoservice.dlr.de. Its clauses 2, 3, 12, 13 and 16 require considerate lawful service use, forbid bypassing controls, permit operational restriction/suspension, require acknowledgements and authorize blocking abuse. The AUP does not specify an automated HTTP Range permission, request-rate quota, credential-free bulk mirror entitlement, or WSF2019-specific service budget. Therefore the general service terms are separately reviewed, but commercial_automation_status and redistribution_status remain unknown, status remains documented_only and probe.mode=none. No new T1/T3, provider bytes or model admission follows from this review.

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
- <https://geoservice.dlr.de/resources/licenses/geoservice/EOC_Geoservice_AUP_v1.1.pdf>

**Notes:** Exact one-source T0 contract; linked landscape source_id dlr.wsf.2019 is non-admitted discovery. Historical native Range evidence: scripts/probe_dlr_wsf_native_cog_tile_v0.py, tests/test_probe_dlr_wsf_native_cog_tile_v0.py, scripts/verify_dlr_wsf_native_rasterio_v0.py, and docs/research/bvv-hu-by-original-shp-vs-wsf2019-first-real-overlap-20261112.md. Previous native sample/source QA is research-only; no new original data fetched in this PR. No whole-file SHA-256, independent multi-area accuracy or historical 2019 building survey comparison is proven. Keep exposure-model admission and insurer-loss use blocked. Do not interpret a prior successful HTTP Range or STAC metadata access as new T1/T3 permission.
