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

**Parameter rules:** Exactly one explicit opt-in anonymous GET of https://api.figshare.com/v2/articles/25988293/versions/1. No caller-selected ID, version, URL, query, headers, redirects, pagination, archive download, file URL follow, or second request. Public article metadata only. Any changed version, licence or file-list identity blocks. The first live receipt must be reviewed before scientific/data promotion.

## Response contract

### Expected media types

- application/json

**Format:** Figshare public, immutable-version-targeted article details JSON: article ID 25988293, version 1, exact version DOI and CC BY 4.0; metadata describing two alternate v1.0 ZIP representations (gdb and shp) only. Reject unverified/missing required metadata instead of assuming files.

**Scientific semantics:** Global Dam Watch v1.0 is a global river-barrier and reservoir reference database. The published release contains a barrier point layer and an associated reservoir polygon layer; these are distinct scientific objects linked by identifiers/location, and not every barrier has an associated reservoir polygon. The two release ZIPs are alternate Geodatabase and Shapefile delivery representations, not independent scientific releases. The published v1.0 inventory reports 41,145 barrier points and 35,295 associated reservoir polygons. Presence in the database does not establish dam-failure probability, structural fragility, reservoir operating state, current asset status, downstream inundation or catastrophe-model fitness.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** Figshare official API documentation recommends at most one request per second and reserves throttle/block rights. This contract permits one explicitly invoked fixed metadata GET without pagination, redirects, retry, file retrieval or a scheduled acquisition loop.

**Mutability notes:** Use the version-specific /versions/1 API route rather than mutable latest article details. Archive file identities, declared sizes and optional provider MD5 from that response are metadata, not verified original ZIP bytes. A live result must record retrieval UTC, response byte count/SHA-256 and code identity. For archived file acquisition, separately review exact asset, permissions, declared and independently computed SHA-256 and CRS/column semantics.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://info.figshare.com/user-guide/figshare-policies/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Global Dam Watch v1.0 original Figshare item and peer-reviewed article identify CC BY 4.0; Figshare's public Data Access Policy and official API guide authorize anonymous public metadata access and responsible API use. This permits one explicit version-pinned metadata canary only. It does not approve any GIS ZIP download, raw/derived data redistribution in this repository, scientific model use or unattended crawling. The final release Technical Documentation and exact selected file must be reviewed before acquiring or publishing original GIS bytes.

## Probe contract

**Mode:** metadata_get

**Operation:** gdw_v10_archive_metadata_version1

**Requires credentials:** `false`

### Expected evidence

- exact version-specific Figshare metadata endpoint HTTP 200 without redirect
- strict bounded UTF-8 application/json; response byte count and SHA-256
- article id 25988293, version 1, version DOI 10.6084/m9.figshare.25988293.v1
- CC BY 4.0 licence identity from provider metadata
- exact two alternate archive names, item identifiers, positive declared sizes and any provider MD5
- retrieval UTC and execution code identity
- no archive download, provider bytes persisted, CAT admission or database write

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

**Notes:** A single fixed, version-specific Figshare public metadata canary is ready for explicitly opted-in execution, never an unbounded harvester. It cannot retrieve either archive, follow links or admit GIS source data. Publisher paper confirms 41,145 barriers and 35,295 reservoir polygons; 5,850 barrier points have no matched polygon. The source is not dam-failure hazard or insured loss. First live provider response remains unverified in this change.
