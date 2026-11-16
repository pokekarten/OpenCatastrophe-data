<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/usgs.3dep.s1m.florida-native-tiff-prefix.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `usgs.3dep.s1m.florida-native-tiff-prefix.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** usgs.3dep.s1m.florida-native-tiff-prefix

## Source ids

- usgs.3dep.seamless-1m.s1m

**Provider:** U.S. Geological Survey / The National Map (TNMAccess-provided public S1M object on AWS S3)

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://www.usgs.gov/3d-elevation-program/new-product-3d-elevation-program-seamless-1-meter-digital-elevation-model-s1m>

**Service root:** <https://prd-tnm.s3.amazonaws.com>

**Api version:** One original S1M tile, exact TNMAccess product sourceId 6a9785801ba49b050c166274, vintage 20260821; exact provider-original 65536-byte prefix SHA-256 pinned from trusted 2026-11-16 GitHub HTTP206 job; complete original TIFF SHA-256 still unknown

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- probe_exact_florida_s1m_header_65536

### Path templates

- /StagedProducts/Elevation/S1M/n04e15/n0450e1510/S1M_n0450e1510_20260821.tif

**Parameter rules:** One explicitly opted-in, PR-branch-specific public HTTPS GET to exactly this TNMAccess-observed USGS S1M original COG URL with only the literal request header Range: bytes=0-65535, Accept-Encoding: identity and fixed non-secret User-Agent. No caller-provided URL, host, path, query, filename, range, token, credentials, cookies, redirects, retries, HEAD/list/object traversal, presigned links or alternate source. Require HTTP 206 with exact Content-Range bytes 0-65535/&lt;total&gt; (total 1 MiB to 1 GiB), Content-Length 65536 if present, identity encoding, binary/TIFF media and no more than 65536 bytes. Reject HTTP 200 (Range ignored) without reading provider body. The current existing metadata-only TNMAccess contract remains unchanged; this separate exact source-object access review authorizes only the bounded original header, not the complete TIFF, other objects, image pixels or GeoPackage.

## Response contract

### Expected media types

- application/octet-stream
- binary/octet-stream
- image/tiff
- application/x-tiff

**Format:** Only a 65,536-byte, content-addressed original COG beginning from the one fixed USGS S3 file; raw source bytes processed transiently in memory. Classic/BigTIFF first metadata may or may not fit in that range. No original pixel block, full file or companion GeoPackage is acquired.

**Scientific semantics:** A provider-original byte prefix with checked TIFF signature and first-IFD structural tags, if present, establishes only an original partial-file transport and structure check, not native EPSG 6350/vertical EPSG 5703 GEOID18, float height values, NoData, full-file SHA-256, COG validity, 10-km spatial coverage, lidar source lineage, backfill/blend quality or model fitness. The separate accepted offline USGS S1M raster-science gate and original-file hash gate require real complete source data before any CAT hazard/exposure use. An original prefix hash cannot be represented as the whole TIFF hash. A subsequent one-range replay may inspect GeoKeyDirectory projected/vertical EPSG keys, GDAL_NODATA ASCII and ModelPixelScale floating values only when fully inside that same independently frozen original prefix. A geoid transformation chain, complete image, per-cell elevation accuracy and all flood/CAT uses remain separate unverified questions.

## Operational constraints

**Timeout seconds:** `25`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Single named GitHub pull-request research branch source-original canary, at most one exact fixed 64-KiB HTTP 206 request per workflow run, no retry even on error, no schedule, inventory crawl, item listing or bulk import. Published TNM programmatic-download support does not create rights to arbitrary throughput. The host must be exact HTTPS public prd-tnm.s3.amazonaws.com and redirects are rejected.

**Mutability notes:** The metadata-only TNMAccess Florida original sourceId, title and USGS-hosted object URL were previously reviewed on 2026-11-02; the original TIFF ~447MB is mutable until an independent full-file SHA and raw byte count are frozen. Each prefix receipt binds fixed URL/range, original 65536-byte SHA-256, complete-asset size from Content-Range, retrieval UTC, code and contract digest, HTTP status and first-IFD partial status. Receipt is research-only and must not be promoted to full-original/model-usage verification. First trusted original prefix job 43948359780 / 133583989829 at 2026-11-16T20:18:29.460229Z returned exact HTTP 206 Content-Range bytes 0-65535/447032917; original 65536-byte SHA-256 56d8d147056fcd28ad916799cd6b917c57d9d08b3e07dfe06931f2a4d5edb2f2. The fixed script now rejects a changed prefix digest or advertised total before parsing scientific tag values. This is a prefix receipt and never a whole-TIFF hash.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** USGS states National Map downloads/public data are freely available in the US public domain and published S1M is accessed on The National Map; the separate National Map download FAQs expressly describe API/programmatic public retrieval and no account requirement. This exact URL is a USGS TNMAccess product downloadURL from a previously inspected metadata record and uses an anonymous direct public object-download route rather than an account-gated commercial API. This review approves one bounded non-redistributed source-original prefix for scientific T1/T3 preflight only, not an unreviewed high-volume automation service, a complete TIFF download, third-party proprietary ancillary data, the companion lineage GeoPackage, or publication of source bytes. Attribute 'U.S. Geological Survey, National Geospatial Program'; leave broader redistribution and insurance CAT model use unchanged and unapproved.

## Probe contract

**Mode:** provider_specific

**Operation:** probe_exact_florida_s1m_header_65536

**Requires credentials:** `false`

### Expected evidence

- One exact HTTPS GET to pinned original S1M TIFF with Range bytes=0-65535, HTTP 206, no redirect/retry, strict bounded body and Content-Range
- Actual original prefix SHA-256, exact original response size, total advertised object bytes, request fingerprint, script/contract SHA-256, retrieval UTC
- Classic or BigTIFF magic and a conservative bounded first-IFD examination; unsupported or incomplete native metadata is explicitly not verified
- Only digest, public object identity and structural metadata in PR job output; no original TIFF byte strings or raster pixel values printed, stored or committed
- full_original_file_hash_verified=false, geo_package_lineage_verified=false, model_input_admitted=false, original_provider_body_persisted=false
- Replay must independently reproduce pinned original 64KiB SHA256 56d8d147056fcd28ad916799cd6b917c57d9d08b3e07dfe06931f2a4d5edb2f2 and advertised complete TIFF bytes 447032917; test source GeoKey and NoData value claims only after this identity check

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-16

## Evidence urls

- <https://www.usgs.gov/3d-elevation-program/new-product-3d-elevation-program-seamless-1-meter-digital-elevation-model-s1m>
- <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>
- <https://www.usgs.gov/faqs/what-types-elevation-datasets-are-available-what-formats-do-they-come-and-where-can-i-download>
- <https://data.usgs.gov/datacatalog/data/USGS%3A4f34caac-f28f-4ea0-8d82-eafb2b8f9a5d>
- <https://tnmaccess.nationalmap.gov/api/v1/docs>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43948359780/job/133583989829>

**Notes:** T0 rights/product/path decision. No original source prefix or full original TIFF bytes were acquired while drafting this contract. On execution, the bounded original prefix is an independent source-native research receipt but not a full-file trusted checksum, pixel-value quality check, commercial model admission, or permission to store data in Neon. This is a second, separate, much narrower original-byte access contract for one fixed source object; it must not widen the existing TNMAccess catalogue metadata contract. Historical trusted original source receipt in docs/research/usgs-s1m-florida-original-tiff-prefix-receipt-20261116.md was acquired after this access approval. The current prefix-SHA check freezes that source revision, and the live workflow must reject any conflicting original bytes or 206 metadata. The full 447032917-byte TIFF has NOT been hashed or downloaded.
