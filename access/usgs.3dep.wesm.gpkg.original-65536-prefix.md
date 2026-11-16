<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/usgs.3dep.wesm.gpkg.original-65536-prefix.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `usgs.3dep.wesm.gpkg.original-65536-prefix.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** usgs.3dep.wesm.gpkg.original-65536-prefix

## Source ids

- usgs.3dep.wesm.workunit-metadata

**Provider:** U.S. Geological Survey (USGS) 3D Elevation Program Work Unit Extent Spatial Metadata (WESM)

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata>

**Service root:** <https://rockyweb.usgs.gov>

**Api version:** One original USGS WESM.gpkg current source object observed 2026-11-16; exact provider HTTP206 full-object Content-Range total 3827232768 bytes, no source body read in first discovery

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- one_wesm_original_gpkg_65536_header

### Path templates

- /vdelivery/Datasets/Staged/Elevation/metadata/WESM.gpkg

**Parameter rules:** One and only one opt-in HTTPS original source GET for the exact USGS-published WESM.gpkg resource at https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/metadata/WESM.gpkg. Only literal header Range: bytes=0-65535; Accept-Encoding: identity, no arbitrary caller URL/host/path/query/header/body, no credentials, no retries, no redirects, no HEAD/list/full download/GeoPackage page traversal, no SQLite query of provider bytes. Require original HTTP 206, exact Content-Range bytes 0-65535/&lt;total&gt;, 65536 original bytes, entire advertised original file total MUST equal exactly 3827232768 bytes (3.56 GiB), frozen from two independent source HTTP 206 transport responses; any other size fails closed before reading source body, identity transfer, accepted static application/octet-stream or GeoPackage/SQLite MIME. HTTP 200 must be rejected BEFORE any source body read, and require exact response 65536 bytes before header analysis. No source data persisted.

## Response contract

### Expected media types

- application/octet-stream
- binary/octet-stream
- application/geopackage+sqlite3
- application/x-sqlite3
- application/vnd.sqlite3

**Format:** Original public WESM.gpkg SQLite/OGC GeoPackage source: only the exact first 65536 bytes, with original source SHA-256 and bounded SQLite database header metadata. No additional SQLite pages, feature tables, polygon records or named work-unit identities.

**Scientific semantics:** USGS WESM GeoPackage is the geographic work-unit representation corresponding to frequently updated USGS WESM metadata. The source is mutable, and an original SQLite/GeoPackage file-header digest or application_id establishes only partial transport and file-structure provenance. It does not verify the entire GeoPackage content, features, valid geometries, spatial reference system, WESM CSV-to-GPKG file-version equivalence, S1M Florida tile overlap, per-cell lidar source lineage, survey era, vertical accuracy, NoData, ground elevation, flood hazard, model fitness or commercial insurers' CAT admission.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** At most one exact anonymous USGS WESM GeoPackage 64KiB Range GET per explicitly triggered research PR workflow, no automated schedule, retries or page/range follow-ups. No provider bytes committed or uploaded to Git, Neon or workflow artifacts. Logs contain public URL, original digest, total advertised byte length, UTC and static SQLite header integers only.

**Mutability notes:** The publisher says WESM is newly published almost daily. A successful source-original 65536-byte digest and Content-Range will identify one point-in-time prefix, not a complete original GeoPackage SHA or a stable versioned asset. A subsequent changed prefix/total shall fail closed when a digest is pinned; never auto-approve a refreshed source. The previous 2026-11-16 WESM.csv source full SHA-256 a5f56b54f26767311156116b4721d477bf5d7b6069056117127898852d2d1b83 belongs to CSV bytes ONLY, not the GeoPackage. First source-exact 206 attempts (public GitHub Actions jobs 133652534037 and 133653353855) returned original advertised object total 3827232768 bytes. Both were intentionally blocked BEFORE any original body read by the initial 1GiB safety ceiling. The new guard accepts ONLY this exact advertised total, not a generic increase to 4GiB, while still reading no more than a single original 65536-byte range. No full-object download, SQLite query, polygon data or model admission is authorized.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** The official USGS 3DEP Spatial Metadata webpage directly links the exact WESM.gpkg on rockyweb, and the USGS National Map downloadable 3DEP data are public domain. This distinct internal source-review scope permits only one transient anonymous 64KiB original GeoPackage prefix request for research metadata, not whole-file acquisition, feature geometry extraction, raw or derivative publication, continuous automated use, or CAT-model consumption. Attribute USGS in downstream research.

## Probe contract

**Mode:** provider_specific

**Operation:** one_wesm_original_gpkg_65536_header

**Requires credentials:** `false`

### Expected evidence

- Exact official source URL, one HTTPS GET Range bytes=0-65535, original HTTP 206 and exact Content-Range with source advertised complete file length
- Actual original 65536-byte body SHA-256, retrieval UTC, code/contract SHA-256 and original request fingerprint, with no source bytes retained
- Strict original SQLite header magic 'SQLite format 3', page-size and GeoPackage application_id 0x47504b47 plus bounded metadata; no provider SQLite original table or geometry parse
- full_original_wesm_gpkg_sha256_verified=false; source_geo_srs_verified=false; original_gpkg_features_verified=false; csv_gpkg_version_parity_verified=false; florida_s1m_tile_workunit_intersection_verified=false; model_input_approved=false
- Before reading 65536 original bytes, reject any original full-object Content-Range total other than 3827232768; this exact total was observed in prior blocked provider HTTP206 metadata-only jobs.

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-16

## Evidence urls

- <https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata>
- <https://www.usgs.gov/ngp-standards-and-specifications/wesm-data-dictionary>
- <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>
- <https://www.geopackage.org/spec/>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43968011136/job/133652534037>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43968198021/job/133653353855>

**Notes:** A separate original WESM.gpkg object identity from the previously verified WESM.csv at the same source_id. The official provider link and static OGC SQLite GeoPackage header semantics are T0 only until a real exact 64KiB provider result is obtained. No approved model input, no polygons in Git/Neon, and no inference of geographical intersection with Florida S1M tile. Original GeoPackage reported 3827232768 bytes (~3.56GiB) on GitHub 2026-11-16; new gate deliberately remains partial 64KiB, with no full original GeoPackage acquisition approved.
