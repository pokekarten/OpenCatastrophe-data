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

**Status:** documented_only

**Documentation url:** <https://figshare.com/articles/dataset/Global_Dam_Watch_database_version_1_0/25988293>

**Service root:** <https://api.figshare.com>

**Api version:** v2

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

- gdw_v10_archive_metadata

### Path templates

- /v2/articles/25988293

**Parameter rules:** Static documentation contract only. The archival metadata identity is fixed to Figshare public article 25988293 for Global Dam Watch database version 1.0. A future reviewed implementation may resolve only this fixed public article metadata record. Callers must not supply a host, article ID, version, file ID, file name, path, query, headers, redirect target or download URL. This contract does not authorize /download, /files, version-file listing, Range requests or ZIP retrieval. Figshare is archival/access infrastructure and must not be represented as a native Global Dam Watch scientific query API.

## Response contract

### Expected media types

- application/json

**Format:** Figshare public article metadata JSON for the fixed Global Dam Watch v1.0 archival record.

**Scientific semantics:** Global Dam Watch v1.0 is a global river-barrier and reservoir reference database. The published release contains a barrier point layer and an associated reservoir polygon layer; these are distinct scientific objects linked by identifiers/location, and not every barrier has an associated reservoir polygon. The two release ZIPs are alternate Geodatabase and Shapefile delivery representations, not independent scientific releases. The published v1.0 inventory reports 41,145 barrier points and 35,295 associated reservoir polygons. Presence in the database does not establish dam-failure probability, structural fragility, reservoir operating state, current asset status, downstream inundation or catastrophe-model fitness.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** No repository-specific numeric Figshare API rate-limit assumption is made. Figshare publicly documents API v2 and public article metadata endpoints, but this contract remains documentation-only and authorizes no live probe. Any future metadata receipt must remain a single fixed-record lookup under the reviewed public API/access policy and current operational guidance.

**Mutability notes:** The scientific release is pinned to Global Dam Watch version 1.0, Figshare article 25988293 and version DOI 10.6084/m9.figshare.25988293.v1. The public metadata service is an access route, not scientific byte identity. Any later selected file must separately freeze the exact Figshare file identity and representation, retrieval UTC, byte count and SHA-256 before scientific, admission or publication use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://info.figshare.com/user-guide/figshare-policies/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The exact Global Dam Watch v1.0 Figshare dataset record states CC BY 4.0, and the peer-reviewed data paper likewise identifies GDW v1.0 as available under CC BY 4.0. Figshare's public Data Access Policy and API guidance allow public metadata/data access and API mining subject to the content licence. These verified rights and service permissions are ceilings, not repository execution or publication approval: this contract deliberately remains documented_only with no live probe or file request. Any persisted sample still requires exact asset identity, provenance, required attribution and repository review before bytes are committed or published.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://figshare.com/articles/dataset/Global_Dam_Watch_database_version_1_0/25988293>
- <https://doi.org/10.6084/m9.figshare.25988293.v1>
- <https://doi.org/10.1038/s41597-024-03752-9>
- <https://www.globaldamwatch.org/>
- <https://info.figshare.com/user-guide/figshare-policies/>
- <https://info.figshare.com/user-guide/how-to-use-the-figshare-api/>
- <https://docs.figshare.com/>

**Notes:** Static metadata/access boundary only for \#173/\#244. No provider request, external byte, file/download authority, adapter, Agent Action dispatch, admission promotion or publication decision is introduced. Future byte acquisition must select one exact v1.0 release representation and file only after a separate asset-specific review; do not infer dam safety, failure likelihood, hazard intensity or loss from inclusion in the inventory.
