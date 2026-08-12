<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/gfz.world-stress-map.2025.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `gfz.world-stress-map.2025.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** gfz.world-stress-map.2025

## Source ids

- gfz.world-stress-map.2025

**Provider:** GFZ Helmholtz Centre for Geosciences / World Stress Map Project

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://dataservices.gfz-potsdam.de/wsm/showshort.php?id=a23de1c9-1f73-11f0-914a-f12b0080820d>

**Service root:** <https://datapub.gfz.de>

**Api version:** World Stress Map Database Release 2025; DOI 10.5880/WSM.2025.001

## Access scope

- metadata
- bulk

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- fetch_wsm2025_csv

### Path templates

- /download/10.5880.WSM.2025.001-Scbwez/WSM_Database_2025.csv

**Parameter rules:** Static documentation contract only. The scientific release identity is fixed to World Stress Map Database Release 2025, DOI 10.5880/WSM.2025.001, and the documented transport identity is the current DOI-linked GFZ Data Services CSV path WSM_Database_2025.csv. This contract authorizes no HTTP request yet. A future reviewed worker must keep host, exact path, query, headers and redirect targets repository-controlled and must re-resolve the DOI/landing evidence before execution because the direct datapub path is transport identity, not scientific identity. Caller-selected files, directory crawling, alternate mirrors, spreadsheet substitution and arbitrary redirects are forbidden.

## Response contract

### Expected media types

- text/csv
- application/octet-stream

**Format:** The fixed release file WSM_Database_2025.csv is the comma-separated representation of World Stress Map Database Release 2025; GFZ also publishes a separate Excel representation, which is not authorized by this contract.

**Scientific semantics:** World Stress Map Database Release 2025 is a global, heterogeneous, quality-ranked compilation of 100,842 present-day crustal stress indicator records. Indicator type, quality class and source/provenance remain material scientific fields. The separately published World Stress Map 2025, DOI 10.5880/WSM.2025.002, displays reliable A-C quality records and must not be conflated with the complete database release DOI 10.5880/WSM.2025.001. Database presence or absence does not establish earthquake occurrence probability, seismic hazard, fault activity probability, vulnerability, damage, loss or insured loss.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `20971520`

**Retry policy:** none

**Rate limit notes:** GFZ and the World Stress Map download page document public/free download of the 2025 database, but no repository-specific numeric request budget or separate automated-service entitlement was established in this review. This documented-only contract authorizes no HEAD, GET, Range request, retry loop, directory crawl or repeated probe.

**Mutability notes:** The scientific database release is pinned by DOI 10.5880/WSM.2025.001. The current direct datapub path is a delivery route and may be operationally mutable even when the DOI identity remains stable. Any later acquisition must re-resolve authoritative landing evidence, freeze requested/final URL identity, retrieval UTC, byte count and SHA-256, validate the expected CSV/file identity and bind parser/field semantics before scientific or publication use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** GFZ Data Services identifies World Stress Map Database Release 2025 as CC BY 4.0, and the World Stress Map project states that database download and usage are free of charge while requiring citation of the project and release. CC BY 4.0 supports reuse and redistribution with attribution. This does not by itself establish a separate automated-service entitlement for the current datapub transport path, so service automation remains unknown and execution stays disabled. Any persisted sample still requires exact asset identity, provenance, attribution and repository review before bytes are committed or published.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://doi.org/10.5880/WSM.2025.001>
- <https://dataservices.gfz-potsdam.de/wsm/showshort.php?id=a23de1c9-1f73-11f0-914a-f12b0080820d>
- <https://www.world-stress-map.org/download/>
- <https://doi.org/10.48440/wsm.2025.001>
- <https://creativecommons.org/licenses/by/4.0/>

**Notes:** Static release/access boundary only for \#173/\#246. No provider request, external byte, parser, adapter, Agent Action dispatch, admission promotion or publication decision is introduced. A future exact-byte task must preserve release DOI, representation, quality/indicator semantics and attribution, and must not infer hazard or loss from stress-indicator coverage.
