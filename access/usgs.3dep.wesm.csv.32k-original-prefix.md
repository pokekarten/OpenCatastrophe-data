<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/usgs.3dep.wesm.csv.32k-original-prefix.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `usgs.3dep.wesm.csv.32k-original-prefix.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** usgs.3dep.wesm.csv.32k-original-prefix

## Source ids

- usgs.3dep.wesm.workunit-metadata

**Provider:** U.S. Geological Survey (USGS) 3DEP Work Unit Extent Spatial Metadata (WESM)

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata>

**Service root:** <https://rockyweb.usgs.gov>

**Api version:** WESM CSV public current mutable daily snapshot, 2026-11-16 reviewed fixed original URL only

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- one_wesm_original_csv_32768_header

### Path templates

- /vdelivery/Datasets/Staged/Elevation/metadata/WESM.csv

**Parameter rules:** Single explicitly triggered PR-branch GitHub workflow GET to one exact official USGS rockyweb WESM.csv URL, with fixed header Range: bytes=0-32767, Accept-Encoding: identity and no credentials, redirects, requests parameters, cookies, retries, host/URL/range input, HEAD, full file downloads or GeoPackage reads. Require HTTP 206, exact Content-Range start 0 and end 32767, known complete original byte size between 32768 and 2GiB, identity transfer encoding, acceptable CSV/octet-stream MIME and at most exactly 32768 source bytes. HTTP 200 must be rejected before reading any original body. Analyze only complete first CSV column header, never original record values; preserve source digest and UTC only, no raw source bytes persisted. Do NOT infer a spatial workunit-to-S1M tile join.

## Response contract

### Expected media types

- text/csv
- text/plain
- application/octet-stream
- binary/octet-stream
- application/vnd.ms-excel

**Format:** Original USGS WESM.csv publicly published mutable Work Unit Extent Spatial Metadata table; bytes 0-32767 only, at most first UTF-8 CSV header and unlabeled continuation. No downloaded original rows, complete source SHA or spatial polygons.

**Scientific semantics:** WESM is a work-unit-level attribute dataset. Quality status may differ by LPC, source DEM and seamless product. WESM is reissued almost daily and independently supplied WESM CSV metadata must not be equated to S1M pixel-source lineage, certified original individual workunit status, vertical error check, tile overlap or actuarial CAT source approval. This probe checks only one provider-original CSV prefix header and immutable HTTP receipt; it neither validates the whole source nor binds exact Florida tile.

## Operational constraints

**Timeout seconds:** `25`

**Max probe bytes:** `32768`

**Max sample bytes:** `32768`

**Retry policy:** none

**Rate limit notes:** One original anonymous HTTP 206 partial GET, no retry, no bulk and no scheduled polling; no original WESM CSV record values printed or persisted. Only one active branch with exact reviewed code is allowed to run the live probe.

**Mutability notes:** USGS WESM is reissued almost daily. A successful original 32768-byte prefix SHA256, full-size as advertised from Content-Range, original request SHA256, UTC and code/contract SHA are a point-in-time partial research receipt, NOT full original WESM CSV/GeoPackage identity and cannot support spatial/model claims. A changed next-day prefix is expected to block any frozen later replay rather than being silently accepted.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** Official USGS 3DEP WESM page links the public WESM.csv object directly; USGS National Map downloaded data are public domain and commercial reuse may be permitted by provider rights. This internal access review authorizes only one transient 32KiB anonymous original header-range request, not redistributing WESM bytes, not the full CSV/GPKG download, not continuous automation, not private insured exposure, not new model admission. Attribute USGS.

## Probe contract

**Mode:** provider_specific

**Operation:** one_wesm_original_csv_32768_header

**Requires credentials:** `false`

### Expected evidence

- Single fixed USGS WESM.csv Range bytes=0-32767, HTTP 206 with Content-Range and original total byte count
- Actual original 32768-byte prefix SHA256, retrieval UTC, code/contract digest and request fingerprint; original body discarded
- Fail-close on unrecognized CSV UTF-8 header shape or overlong number of columns; no record values logged
- provider_original_full_csv_sha256_verified=false, original_wesm_geopackage_verified=false, s1m_florida_tile_workunit_intersection_verified=false, cat_model_input_approved=false

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-16

## Evidence urls

- <https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata>
- <https://www.usgs.gov/ngp-standards-and-specifications/wesm-data-dictionary>
- <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>

**Notes:** Separate WESM work-unit source product, not the already verified original S1M Florida GeoTIFF. This live bounded prefix is a research-only technical source check. Independent whole CSV/GPKG hash and original row geometries remain unverified; no Neon write, no original row content persistence and no model approval.
