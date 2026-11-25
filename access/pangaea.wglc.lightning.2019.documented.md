<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/pangaea.wglc.lightning.2019.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `pangaea.wglc.lightning.2019.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** pangaea.wglc.lightning.2019.documented

## Source ids

- pangaea.wglc.lightning.2019

**Provider:** Kaplan and Lau / PANGAEA

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://doi.pangaea.de/10.1594/PANGAEA.904253>

**Service root:** <https://store.pangaea.de>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /Publications/KaplanJ-LauH_2019/WWLLN.zip

**Parameter rules:** Exact documented asset locator only; no executable acquisition authorized. Review service conditions and explicit byte budget before any future request.

## Response contract

### Expected media types

- application/zip

**Format:** 0.5 degree monthly NetCDF4, 108 months and 12 climatological bins

**Scientific semantics:** Distinct immutable DOI release; not a licence for 2026 WGLC or raw WWLLN. PANGAEA landing page explicitly CC BY 4.0 and gives ZIP locator https://store.pangaea.de/Publications/KaplanJ-LauH_2019/WWLLN.zip. On 2026-11-25 bounded HTTPS GET on macOS downloaded 37038662 bytes, SHA-256 ef9ef83797f861c68930856ab4f57e392d575c79e7ca46bc7c2f8cf13e19f7d5. ZIP CRC check passed; two entries WWLLN_climatology.nc (5947906 bytes) and WWLLN_monthly.nc (31343698 bytes). HDF5 inspection of climatology verified lon 720, lat 360, time 12, lightning shape 12 x 360 x 720, units strokes km-2, CF-1.7 and source AE detection-efficiency corrected stroke counts. Calendar units days since 0000-01-01 00:00:00 require explicit CF calendar handling; monthly file not yet parsed. Stroke counts not optical flashes; monthly density cannot track storms. Open-first priority: complete exact archive reuse/API review, inspect monthly data/missingness/cell-area and compare to independent radar hail frequencies. No raw bytes in Git or Neon; not admitted. Subsequent same-day offline inspection of the retained original ZIP parsed the full monthly member (31343698 bytes, SHA-256 eb43bf169e7b3c7ec67bfb0a067e0e7a4475b2f84e503a05139e9a74bafbe694). Float32 lightning shape 108 x 360 x 720; coordinate centers lat -89.75 to 89.75, lon -179.75 to 179.75, strictly increasing. Time is strictly increasing from 0 to 3256 days since 2010-01-01, explicit 365_day calendar; do not interpret as Gregorian offsets. All 27993600 stored values finite and not fill (NaN), 20306788 zero, no negatives, range 0 to 14.3060941696167 strokes km-2; every month has 259200 finite cells. Numeric completeness is not detection coverage or physical no-lightning evidence. Provider variable long_name says flashes but units and documentation explicitly describe strokes. Retain stroke semantics; verify geographic/time detection bias and area weights before modelling. PANGAEA exact DOI still explicitly CC BY 4.0; platform terms https://www.pangaea.de/about/terms.php section 5.5 restrict mass retrieval and automated commercial web-page extraction absent authorization. Data reuse with attribution is distinct from automated access; no new live request authorized here.

## Operational constraints

**Timeout seconds:** `45`

**Max probe bytes:** `65536`

**Max sample bytes:** `41943040`

**Retry policy:** none

**Rate limit notes:** No scheduled or automated acquisition authorized; provider-specific fair-use and exact scope must be respected.

**Mutability notes:** Freeze DOI, exact product/member, retrieval UTC, original byte count and SHA-256. A listing or protected locator is not a download receipt.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.pangaea.de/about/terms.php>

**Commercial automation status:** restricted

**Redistribution status:** allowed

**Notes:** Exact 2019 DOI grants CC BY 4.0 for the published grids; cite Kaplan and Lau (2019), DOI 10.1594/PANGAEA.904253, credit source and indicate changes. This does not license raw WWLLN or 2026 release. Platform section 5.5 restricts mass retrieval and automated commercial extraction of webpages; no automatic collection authorized. Previously obtained ZIP and both members inspected outside Git. Reuse of exact licensed archive subject to attribution, privacy/science/admission review; do not infer global observation completeness from finite values.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.pangaea.de/10.1594/PANGAEA.904253>
- <https://www.pangaea.de/about/terms.php>

**Notes:** Open-first source access coverage; Exact 2019 DOI grants CC BY 4.0 for the published grids; cite Kaplan and Lau (2019), DOI 10.1594/PANGAEA.904253, credit source and indicate changes. This does not license raw WWLLN or 2026 release. Platform section 5.5 restricts mass retrieval and automated commercial extraction of webpages; no automatic collection authorized. Previously obtained ZIP and both members inspected outside Git. Reuse of exact licensed archive subject to attribution, privacy/science/admission review; do not infer global observation completeness from finite values. No model admission or new acquisition authorization.
