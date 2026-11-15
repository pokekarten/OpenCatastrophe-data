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

**Api version:** Atlantic HURDAT2 1851-2025, 2026-September historical 1971-1975 reanalysis revision; exact original filename and content hash to be pinned

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

**Parameter rules:** Documentation-only, no automatic source request or caller-selected path, unbounded domain, secrets, crawler, bulk extraction or retries. Metadata path(s) are only candidate exact origins; actual provider GET requires independently reviewed provider machine-use terms, exact URL, byte cap, body hash and source-specific approved workflow.

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

**Mutability notes:** NHC periodically issues HURDAT2 revisions; pin exact filename, modification date, SHA and reanalysis window before comparing with IBTrACS.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** NHC's official archival description is public but exact original file's redistribution/third-party lineage and service automation terms have not been independently reviewed; no blanket public-domain or insurer CAT model entitlement inferred.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.nhc.noaa.gov/data/>
- <https://www.nhc.noaa.gov/data/hurdat/>

**Notes:** Original September 2026 archive revision is confirmed on publisher page, but 6.8-MB original text file URL, byte SHA, header parser, historical revisions and independent windfield challenge are not yet fixed. No provider asset download/Neon write/model admission.
