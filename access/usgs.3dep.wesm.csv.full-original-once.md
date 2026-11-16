<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/usgs.3dep.wesm.csv.full-original-once.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `usgs.3dep.wesm.csv.full-original-once.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** usgs.3dep.wesm.csv.full-original-once

## Source ids

- usgs.3dep.wesm.workunit-metadata

**Provider:** United States Geological Survey (USGS), 3D Elevation Program WESM

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata>

**Service root:** <https://rockyweb.usgs.gov>

**Api version:** USGS WESM daily-mutable CSV snapshot: exact 2026-11-16 original prefix SHA and original advertised total bound

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- one_wesm_original_csv_full_verified

### Path templates

- /vdelivery/Datasets/Staged/Elevation/metadata/WESM.csv

**Parameter rules:** One intentionally triggered official HTTPS GET to only the exact USGS WESM.csv original URL (no custom URL, host, parameters, cookies, credentials, content transforms, redirects, HEAD, S3 listing or follow-on requests). One full HTTP 200 provider response is permitted only with Content-Length 2267051 if provided, no redirects, identity Content-Encoding, and exact 2267051 received bytes; never read &gt;2267052, no retries, no further object downloads. Independently verify the first 32768 original body bytes against the already source-proven SHA256 19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d BEFORE interpreting any source row. The provider file can change daily; drift in source prefix or total must fail closed. Original rows are handled transiently in memory, not logged/persisted/committed. The only outputs are whole-source SHA256, row count, known category aggregate histograms, column names digest, validity flags and retrieval/source fingerprints. No original WESM GeoPackage or Florida S1M tile spatial join permitted.

## Response contract

### Expected media types

- text/csv
- text/plain
- application/octet-stream
- binary/octet-stream
- application/vnd.ms-excel

**Format:** Exact original WESM.csv entire 2267051-byte snapshot only, UTF-8 28-field CSV source table; no GeoPackage, no source polygons.

**Scientific semantics:** Original WESM quality status categories characterize USGS lidar work units, not guaranteed the original 20260821 Florida S1M tile cell. A complete original CSV hash and bounded source-header/row counts can establish only one original source snapshot. Cross-source work-unit geometry, S1M companion per-pixel lineage, source void/backfill, geoid accuracy, independent lidar/checkpoints and CAT insurance suitability are not evaluated. Data quality categories require original product-family-specific semantics. Unknown/blank labels must be counted as unresolved and never silently promoted to Meets.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `2267051`

**Max sample bytes:** `2267051`

**Retry policy:** none

**Rate limit notes:** Exactly ONE public full WESM CSV GET per user-triggered source PR branch workflow, with maximum 2267052 body read and no redirect/retry. No sensitive data, original source rows, raw provider bytes or signed URLs in Git, logs or Neon. No recurring schedule; no GeoPackage access.

**Mutability notes:** The upstream USGS original WESM CSV is updated nearly daily. Exact 2026-11-16T21:36:52Z authentic prefix original SHA256 is 19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d, original Content-Range bytes 0-32767/2267051. Separate original read is authorised ONLY for that same 2267051-byte apparent source version. A changed full CSV tail is possible even with identical first 32KiB; compute the full independent SHA256 and bind retrieval UTC/real provider response metadata. No claim to immutable upstream historical download URL.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** The official USGS National Map WESM link is an anonymous public data download governed by USGS public-domain National Map reuse information. This internal scope approves one transient full original CSV research QA with hash and aggregates only. Raw original source content, WESM polygons, ongoing automated download, redistribution of external rows, and use for CAT modelling or insurer exposure remain out of reviewed repository scope. Attribute USGS.

## Probe contract

**Mode:** provider_specific

**Operation:** one_wesm_original_csv_full_verified

**Requires credentials:** `false`

### Expected evidence

- Exactly one fixed anonymous HTTPS GET to official rockyweb WESM.csv, HTTP 200 without redirect; original body byte count and optional Content-Length equal 2267051
- Source-original first 32768 bytes hash exactly 19e025e68687bbb2b61d7f58a5eeedfa6d59b29a9ba98aa159556cc801e6eb8d
- Original entire 2267051-byte file SHA256, UTF-8 CSV header name digest c2893167ec1839f74db9c67704f9f3fbd3c4ed9d6d65359bf1914ce19abb2746 and 28 columns
- Aggregated original source work-unit row count and known quality status label counts only, no row values, no duplicate workunit raw IDs, no provider body persisted
- original_wesm_geopackage_verified=false, florida_s1m_tile_lineage_verified=false, cat_model_input_approved=false

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-16

## Evidence urls

- <https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata>
- <https://www.usgs.gov/ngp-standards-and-specifications/wesm-data-dictionary>
- <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43961768133/job/133630902143>

**Notes:** Second and separately reviewed exact USGS WESM original CSV access operation. This is not authorization for the alternate WESM.gpkg spatial dataset, not an S1M original DEM, not a perpetual CSV revision collector, and not a full-source model asset admission. Only an exact current-provider version matching the preverified 32KiB prefix and advertised size may be hashed; source update blocks rather than auto-selects another day.
