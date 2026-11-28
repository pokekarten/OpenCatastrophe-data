<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec.jrc.census2021-population-grid-100m.r2026.07.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec.jrc.census2021-population-grid-100m.r2026.07.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec.jrc.census2021-population-grid-100m.r2026.07.documented

## Source ids

- ec.jrc.census2021-population-grid-100m.r2026.07

**Provider:** European Commission Joint Research Centre / Eurostat

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://data.jrc.ec.europa.eu/dataset/98336641-fd1c-4992-8c7b-c470dd5eb81e>

**Service root:** <https://jeodpp.jrc.ec.europa.eu>

**Api version:** Census 2021 / revision 2026.07 / DOI 10.2905/JRC.VP18KXG

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

- /ftp/jrc-opendata/MAPS/JRC-ESTAT_Census_Population_2021_100m/JRC-ESTAT_Census_Population_2021_100m.zip

**Parameter rules:** Exact catalogue-linked ZIP path only. Documentation-only; no live request, automated retrieval, archive expansion or bulk acquisition authorized. Review exact source version and acquisition terms before any bounded HEAD or Range canary.

## Response contract

### Expected media types

- application/zip
- application/octet-stream

**Format:** Publisher catalogue describes GeoTIFF raster distribution; exact download link ends in ZIP. Archive member names, byte length, checksum, CRS, NoData and data type are not yet independently verified.

**Scientific semantics:** 100 m estimated resident population derived from Census V2-0 (2024-06-16), not V3. Disaggregation uses residential built-up volume and shared EUBUCCO, Overture, GHSL and TomTom inputs. Not independent footprint evidence or surveyed individual exposure. Validate 1 km aggregate conservation against exact V2-0, mask and pixel semantics before any CAT consumer.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Catalogue declares anonymous access without registration. Separate service automation and rate constraints remain unreviewed; zero original-byte requests authorized. A binary link was identified from public catalogue metadata, not a successful source download.

**Mutability notes:** Catalogue revision and DOI identify the product, not an immutable ZIP digest. Future source receipt must pin exact URL, response size, retrieval time, SHA-256, archive members and native raster profile before scientific comparison.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://commission.europa.eu/legal-notice_en>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Catalogue declares European Commission reuse subject to attribution and excludes third-party intellectual property. Review upstream input rights and exact derivative scope; anonymous access does not independently establish commercial automation, raw redistribution or model admission.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-27

## Evidence urls

- <https://data.jrc.ec.europa.eu/dataset/98336641-fd1c-4992-8c7b-c470dd5eb81e>
- <https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids>

**Notes:** Catalogue metadata and exact linked ZIP route reviewed on 2026-11-27. No original ZIP body, checksum, pixel sample, insurer data, or model admission. The web reader could not process the ZIP response; do not infer availability of a complete valid archive from this observation.
