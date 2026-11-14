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

**Api version:** Atlantic HURDAT2 1851-2025, selected NHC September 23 2026 reanalysis archive file hurdat2-1851-2025-092326.txt (distinct from September 12 archive file hurdat2-1851-2025-091226.txt)

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

**Parameter rules:** Documentation-only, no automatic source request or caller-selected path, unbounded domain, secrets, crawler, bulk extraction or retries. Metadata path(s) are only candidate exact origins; actual provider GET requires independently reviewed provider machine-use terms, exact URL, byte cap, body hash and source-specific approved workflow. The sole selected future original-file candidate is /data/hurdat/hurdat2-1851-2025-092326.txt. The separate /data/hurdat/hurdat2-1851-2025-091226.txt is NOT a fallback or equivalent input. Neither file path is executable under this documentation-only contract.

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

**Mutability notes:** NHC periodically issues HURDAT2 revisions; pin exact filename, modification date, SHA and reanalysis window before comparing with IBTrACS. Provider directory reviewed 2026-11-14: earlier exact hurdat2-1851-2025-091226.txt has listed modification 2026-09-17 21:02; selected hurdat2-1851-2025-092326.txt has listed modification 2026-09-30 18:37. Directory timestamps have no stated timezone and listed 6.7M size is rounded, not an original byte-count or SHA-256. Reverify direct original assets before any T1/T3.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** NHC's official archival description is public but exact original file's redistribution/third-party lineage and service automation terms have not been independently reviewed; no blanket public-domain or insurer CAT model entitlement inferred. The official NHC/NWS general disclaimer https://www.nhc.noaa.gov/disclaimer.shtml states government-server information is public domain unless specifically annotated and prohibits presenting modified content as official government output. This general policy does not establish a product/third-party-specific terms clearance or automated-download budget for this exact file; the existing unknown statuses are deliberately unchanged.

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
- <https://www.nhc.noaa.gov/disclaimer.shtml>

**Notes:** NOAA's official archive directory on 2026-11-14 exposes two DISTINCT September 2026 Atlantic releases: hurdat2-1851-2025-091226.txt (listed modified 2026-09-17 21:02) and hurdat2-1851-2025-092326.txt (listed modified 2026-09-30 18:37). The latter is the selected candidate for the NHC September 23, 2026 revision covering historical 1971-1975 reanalysis. These are T0 web-directory identity observations, not direct original HURDAT file retrieval, trusted T1, verified exact byte sizes, hashes, source rights, permission for automation, scientific validation or admission. No provider file, dataset sample, Neon write or model input acquired.
