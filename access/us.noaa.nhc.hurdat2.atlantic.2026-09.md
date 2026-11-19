<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/us.noaa.nhc.hurdat2.atlantic.2026-09.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `us.noaa.nhc.hurdat2.atlantic.2026-09.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** us.noaa.nhc.hurdat2.atlantic.2026-09

## Source ids

- us.noaa.nhc.hurdat2.atlantic.2026-09

**Provider:** NOAA National Hurricane Center

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.nhc.noaa.gov/data/>

**Service root:** <https://www.nhc.noaa.gov>

**Api version:** Atlantic HURDAT2 1851-2025; exact archived file hurdat2-1851-2025-092326.txt (September 2026 reanalysis of 1971-1975), original content hash still unverified

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

- inspect_nhc_hurdat2_archive_listing

### Path templates

- /data/
- /data/hurdat/
- /data/hurdat/hurdat2-1851-2025-092326.txt

**Parameter rules:** Documentation-only T0 file identity: original provider archive enumerates two distinct September 2026 Atlantic revisions, including 091226 and 092326; the later selected filename is hurdat2-1851-2025-092326.txt (Atlantic best tracks through 2025). Listing URL and exact file path are documentary source identities, not executable download authorization. No file HEAD/GET, ranged sample, free-form path, caller-selected URL/headers, archive crawling, mirroring, redirects or retries may be executed under this contract. Obtain separate exact dataset/API terms and reviewed one-shot bounded access contract before retrieval.

## Response contract

### Expected media types

- text/html

**Format:** Official NHC public archive index, not the ~6.8-MB original comma-delimited tropical-cyclone best-track file. No windfield/return-level source bytes included.

**Scientific semantics:** Best-track approximately six-hour storm centers, maximum sustained winds, central pressure, wind radii from 2004. Not an original European extratropical windfield or insurer loss. NHC/HURDAT2 and NOAA IBTrACS may share NHC original tracks; cross-database agreement not independent and events must not be doubled.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** No live archive sweep or file download under this documentation-only contract; review fixed original text path, caching, contact and one-shot request budget before parser.

**Mutability notes:** The original NHC archive lists two distinct September 2026 Atlantic releases: hurdat2-1851-2025-091226.txt and hurdat2-1851-2025-092326.txt. Do not merge their revisions or mistake directory last-modified dates for original content-hash identity. Pin downloaded full original SHA-256, file bytes, storm-row semantics and 1971-1975 reanalysis scope before comparisons or CAT model use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://www.nhc.noaa.gov/mobile/disclaimer.html>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** T0 dataset-rights review 2026-11-15, exact NOAA/NHC Atlantic HURDAT2 archived product hurdat2-1851-2025-092326.txt (not a separate Hurricane Research Division aircraft/research dataset): official NHC/NWS disclaimer states that public government-server material is in the public domain unless expressly annotated otherwise; no contrary annotation was identified on the NHC HURDAT2 product/listing. It permits lawful downstream internal/commercial data reuse and redistribution of the NOAA product subject to no false government endorsement, authorship or altered-official representation, and preservation of scholarly attribution and exact release. This source-rights ceiling DOES NOT authorize web scraping, rate-limited service automation, file HEAD/GET, raw-file publication through this repository, scientific/CAT use or model admission. Separate automatic access/service policy and original-byte identity remain unverified; commercial_automation_status stays unknown, status documented_only, probe none. If third-party or version-specific markings appear in the selected original bytes, revisit this provisional scope and fail closed before downstream use.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://www.nhc.noaa.gov/data/>
- <https://www.nhc.noaa.gov/data/hurdat/>
- <https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-092326.txt>
- <https://www.nhc.noaa.gov/mobile/disclaimer.html>
- <https://www.weather.gov/disclaimer>
- <https://www.nhc.noaa.gov/disclaimer.shtml>

**Notes:** T0 2026-11-15: NHC archive identifies two distinct 2026-09 revisions (091226 and 092326); selected exact original is hurdat2-1851-2025-092326.txt. NOAA/NHC government data-rights ceiling was reviewed against official public-domain disclaimers, while automated service permission, exact original bytes/hash and scientific admission remain unverified. No provider data GET/HEAD, sample, Neondb write or model admission performed.
