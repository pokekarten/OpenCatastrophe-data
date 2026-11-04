<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/globaldamwatch.gdw.v1.0.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `globaldamwatch.gdw.v1.0.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** globaldamwatch.gdw.v1.0

## Source ids

- globaldamwatch.gdw.v1.0

**Provider:** Global Dam Watch / Figshare archival record

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://docs.figshare.com/v2/>

**Service root:** <https://api.figshare.com>

**Api version:** Figshare API v2; frozen public article 25988293, version 1

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- gdw_v10_archive_metadata_version1

### Path templates

- /v2/articles/25988293/versions/1

**Parameter rules:** One explicit opted-in anonymous GET of https://api.figshare.com/v2/articles/25988293/versions/1 only, no redirect, caller ID/URL/version/host/path/query/headers, pagination, follow-up download or retry. Exact original v1 provider metadata was separately retrieved with HTTP 200 on 2026-11-04; the reviewed parser must verify all three fixed metadata identities including item-level size and BOTH MD5 values. Verification does not permit file download or source promotion.

## Response contract

### Expected media types

- application/json

**Format:** Figshare original public version-1 article metadata JSON: original release file identity contains two alternate GIS archives (GDW_v1_0_gdb.zip and GDW_v1_0_shp.zip) AND a separately published final technical document (GDW_TechDoc_v1_0.pdf). These are 3 archival files, not 3 independent scientific datasets.

**Scientific semantics:** Figshare v1 metadata identifies the Global Dam Watch dataset, two alternative GIS archive formats and a separately published final 15-page TechDoc. Original v1 manual identifies 41,145 WGS84 barrier points, 35,295 associated reservoir polygons linked by GDW_ID; 5,850 point-only barrier records legitimately lack a polygon. Original numeric missing values use -99 and missing elevations -9999; blank text is unknown. These are source-defined conventions for a separately reviewed future import, not measured zero, independently verified source archive bytes, dam-failure probabilities, hydraulic inundation, site-specific insured exposure or model readiness.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** Figshare official API documentation recommends at most one request per second and reserves throttle/block rights. This contract permits one explicitly invoked fixed metadata GET without pagination, redirects, retry, file retrieval or a scheduled acquisition loop.

**Mutability notes:** Original version-specific Figshare v1 public article JSON retrieved 2026-11-04 and reported article total 127,938,795 bytes comprising final PDF (716,288 bytes, file 47913739), Geodatabase ZIP (57,476,758 bytes, 47913742) and Shapefile ZIP (69,745,749 bytes, 47913754). Provider-supplied and computed MD5 fields agreed for each file; these are metadata declarations, not independently recalculated byte receipts. Any version or metadata drift must fail closed. Original ZIP/GIS file acquisition requires distinct review, exact SHA-256, attribute/geometry quality gates and full final v1 TechDoc rights check.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://info.figshare.com/user-guide/figshare-policies/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Final publisher v1.0 TechDoc (July 2024, Figshare file 47913739, section 4.1) and original Figshare v1 item both explicitly state CC BY 4.0. The final technical document also asks users to refrain from full original-format mirror/rehosting on third-party websites without authors' written permission. This is an author request, not proof of a different legal licence; project publication policy remains metadata-only with no original provider files in Git. Figshare's public Data Access Policy and API guidance support bounded anonymous metadata access and responsible rate usage. A live source-specific parser receipt, exact original archive bytes, derivative/publication decision and model rights remain separate stages.

## Probe contract

**Mode:** metadata_get

**Operation:** gdw_v10_archive_metadata_version1

**Requires credentials:** `false`

### Expected evidence

- fixed Figshare article-version v1 original metadata endpoint returns HTTP 200 without redirect
- strict bounded JSON, response byte count and SHA-256, retrieval UTC and probe code SHA-256
- article id 25988293, version 1, DOI 10.6084/m9.figshare.25988293.v1, CC BY 4.0
- two GIS archives plus one separately listed final TechDoc PDF with exact reviewed file names/ids/sizes, matching provider declared supplied/computed MD5
- provider article total declared 127938795 bytes, no file-link resolution or download
- no original GIS/PDF file bytes persisted, CAT admission or database write

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-04

## Evidence urls

- <https://figshare.com/articles/dataset/Global_Dam_Watch_database_version_1_0/25988293>
- <https://doi.org/10.6084/m9.figshare.25988293.v1>
- <https://doi.org/10.1038/s41597-024-03752-9>
- <https://www.globaldamwatch.org/>
- <https://info.figshare.com/user-guide/figshare-policies/>
- <https://info.figshare.com/user-guide/how-to-use-the-figshare-api/>
- <https://docs.figshare.com/>
- <https://docs.figshare.com/v2/>
- <https://api.figshare.com/v2/articles/25988293/versions/1>
- <https://ndownloader.figshare.com/files/47913739>

**Notes:** Provider's exact public v1 metadata was independently inspected on 2026-11-04 (HTTP 200) and lists 3 files: 2 alternate GIS archive formats plus a separate final technical PDF. Exact original file IDs, provider declared byte sizes, matching supplied/computed MD5, licence, DOI and total size are frozen in the new probe. This is independent provider metadata evidence, not a successful execution receipt from the reviewed Python probe itself, not a checked archive SHA-256, and not source admission or acquisition permission. Freeze one original GIS archive separately only after review. See PR \#1233. The final v1.0 Technical Documentation (not pre-release delta) was also reviewed through the public documentation interface: WGS84, GDW_ID pairing, numeric/elevation missing-value sentinels and the author request against whole original-data rehosting were confirmed. Actual GIS file bytes remain unacquired.
