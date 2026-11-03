<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/isimip3a.tc.er11-wind.maxrain.filelist.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `isimip3a.tc.er11-wind.maxrain.filelist.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** isimip3a.tc.er11-wind.maxrain.filelist.documented

## Source ids

- isimip3a.tc.er11-wind.historical.maxrain.1950-2021

**Provider:** ISIMIP / Potsdam Institute for Climate Impact Research (PIK)

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.isimip.org/gettingstarted/input-data-bias-adjustment/details/182/>

**Service root:** <https://data.isimip.org>

**Api version:** ISIMIP repository API v1 dataset-filelist metadata route, not the NetCDF product version

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

- inspect_published_filelist_metadata

### Path templates

- /api/v1/datasets/f08ab32e-b3ad-4984-81d1-495235765b6c/filelist/

**Parameter rules:** This contract documents exactly one ISIMIP metadata-filelist route and is not permission to run automated HTTP requests. Do not fetch NetCDF, crawl adjacent datasets, modify dataset UUID or file family, use query parameters, redirects or credentials. A future independently approved read-only metadata receipt must record the original exact URI, date, byte count, SHA256 and 72-file completeness.

## Response contract

### Expected media types

- text/plain
- application/octet-stream

**Format:** Expected provider text/plain annual URL list (ASCII); prior public research fetch observed 72 yearly ER11-wind maxrain file names from 1950 to 2021, but did not preserve an independently verified raw response checksum. Content-Type and original byte integrity remain unverified.

**Scientific semantics:** One annual file may contain storm-event-derived maximum 24-hour TC rainfall; this is not observed wind intensity, not annual insured loss, not 72 independent simulated model years and not a second independent IBTrACS observation. Storm rain modelling also uses ERA5 and physical reconstruction; preserve event ID, parent cyclone lineage, grid, units and aggregation before NextGen integration.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `32768`

**Max sample bytes:** `32768`

**Retry policy:** none

**Rate limit notes:** No automated probe/download currently authorised. Future provider access policy and dataset-specific commercial rights review must precede even bounded metadata probes under repository governance.

**Mutability notes:** ISIMIP catalogues and file availability may change independently of this fixed UUID. Filename presence is not a NetCDF content signature or checksum; exact model years and output semantics must be confirmed after approval.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** <https://www.isimip.org/gettingstarted/terms-of-use/terms-use-publicly-available-isimip-data-after-embargo-period/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** ISIMIP public terms forbid sale of provided data and require compliance with each source file/dataset's assigned licence; ISIMIP3 general CC0 preference refers to model outputs and does not automatically cover this ISIMIP3a InputData product or downstream insurer applications. No dataset-specific commercial-use, automation, output derivative or redistribution permission established.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-03

## Evidence urls

- <https://www.isimip.org/gettingstarted/input-data-bias-adjustment/details/182/>
- <https://data.isimip.org/api/v1/datasets/f08ab32e-b3ad-4984-81d1-495235765b6c/filelist/>
- <https://www.isimip.org/gettingstarted/terms-of-use/terms-use-publicly-available-isimip-data-after-embargo-period/>
- <https://www.isimip.org/gettingstarted/terms-of-use/licenses-publicly-available-isimip-data/>

**Notes:** T0 nonexecutable source-access record; exact route ties to the existing offline 72-year filelist checker. No data transfer, original NetCDF file headers, independent response SHA256, insurer asset records, official legal permission or model admission. Cross-cyclone peril components only link after verified common physical event IDs.
