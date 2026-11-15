<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/naturalearth.admin0.countries.110m.v5.1.1.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `naturalearth.admin0.countries.110m.v5.1.1.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** naturalearth.admin0.countries.110m.v5.1.1

## Source ids

- naturalearth.public-domain.admin-geography

**Provider:** Natural Earth / NACIS contributors

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/>

**Service root:** <https://www.naturalearthdata.com>

**Api version:** Natural Earth Admin 0 Countries 1:110m, theme version 5.1.1

## Access scope

- bulk

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- download_admin0_countries_110m_v511

### Path templates

- /download/110m/cultural/ne_110m_admin_0_countries.zip

**Parameter rules:** One publisher-listed 1:110m Admin 0 Countries ZIP only, as linked from the official v5.1.1 product page; no caller-selected URL, version, geography, host, headers, query, range or recursive links. The publisher page currently links a legacy download route. The final download host, redirect chain and service automation permission have not been verified; this documented_only contract authorizes no network execution or archive acquisition.

## Response contract

### Expected media types

- application/zip
- application/octet-stream

**Format:** Publisher-listed approximately 210.08 KB ZIP of ESRI Shapefile components for ne_110m_admin_0_countries, theme version 5.1.1. The published listing size is approximate, not a measured Content-Length or original-asset hash.

**Scientific semantics:** Generalized global 1:110m cultural cartography of Admin-0 countries with provider de facto boundary choices and some UN/CIA-derived thematic attributes. Intended only as country-level cartographic/context and coarse aggregation research; not a cadastral building, historical border, precise parcel, hazard-intensity, NUTS-code or insured-loss source. Disputed borders, dependent territories, attribute codes, CRS and precision require independent archive-level screening before joins.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `524288`

**Max sample bytes:** `1048576`

**Retry policy:** none

**Rate limit notes:** Provider website documents public-domain dataset reuse, but no specific automated-download rate/robots policy has been reviewed for this legacy download route. Do not run automated retrieval or schedule polls until that separate access/service boundary and redirects are verified; at most one bounded manual read-only acquisition should be proposed after review.

**Mutability notes:** The publisher labels the selected 1:110m Admin-0 Countries theme as v5.1.1 on 2026-11-14, but the page/link can change and is not an immutable source-byte identity. Future acquisition must record exact final URL, redirect chain, UTC, original ZIP byte count and SHA-256 separately from extracted or transformed files.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://www.naturalearthdata.com/about/terms-of-use/>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** Natural Earth's official Terms of Use explicitly put all website map-vector/raster versions in the public domain and allow personal, educational and commercial modification and redistribution without mandatory attribution. This establishes dataset reuse rights only, not separate automation/rate/redirect permission for the download website or approval by this repository. Terms include notices about contributing upstream components; a model-facing property/geometry quality and external-rights review is still needed. No original archive or derivative is admitted, hashed or copied into public Git.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/>
- <https://www.naturalearthdata.com/downloads/110m-cultural-vectors/>
- <https://www.naturalearthdata.com/about/terms-of-use/>

**Notes:** T0: official product v5.1.1, map role and source reuse terms read on 2026-11-14. Not verified: executable link/final host, website automation policy, original byte/sample SHA-256, ZIP/DBF/geometry/CRS semantics, sample storage, Neon staging and independent CAT quality. T1-T4 not_tested. Next causal action: review allowed automated retrieval and redirect endpoints, then build one bounded no-redirect ZIP receipt/parser with synthetic negative tests before a strictly limited live sample. No admission or model-input approval.
