<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/eurostat.gisco.census-population-grid.2021.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `eurostat.gisco.census-population-grid.2021.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** eurostat.gisco.census-population-grid.2021

## Source ids

- eurostat.gisco.census-population-grid.2021

**Provider:** Eurostat / GISCO / European Commission

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids>

**Service root:** <https://gisco-services.ec.europa.eu>

**Api version:** Census Grid 2021; Version 2021 (30 May 2026); V3

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

- fetch_census_grid_2021_v3_zip

### Path templates

- /census/2021/Eurostat_Census-GRID_2021_V3.zip

**Parameter rules:** Static documentation contract only. The release is fixed to the GISCO-listed Census Grid 2021 Version 2021 dated 30 May 2026 and the exact V3 ZIP path above. This contract authorizes no HTTP request yet. A future reviewed worker must keep host, path, query, headers and redirects repository-controlled; caller-selected years, versions, filenames, directories, mirrors, arbitrary redirects and silent upgrades to future releases are forbidden.

## Response contract

### Expected media types

- application/zip
- application/octet-stream

**Format:** One fixed ZIP distribution for Census Grid 2021 V3. The official GISCO listing identifies CSV, GeoPackage and raster representations. Any later acquisition must inventory the exact archive members and bind their parser/metadata identities before use rather than assuming an internal layout from the filename alone.

**Scientific semantics:** Harmonised 2021 population and housing census statistics on an EU-wide 1 km² grid. Eurostat lists 13 census variables covering total population/usual residence, sex, age, employment where available, place of birth and prior usual residence categories. Raster and GeoPackage representations use ETRS89 / LAEA (EPSG:3035). These are census counts/categories, not structure-level or insured exposure; national census source/method choices can differ despite EU harmonisation, employment is availability/voluntary-basis dependent, and missingness or suppression must remain explicit. Do not infer building occupancy, asset value, damage, vulnerability or insured loss from the grid alone.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `52428800`

**Retry policy:** none

**Rate limit notes:** The current GISCO page exposes a static anonymous ZIP link, but this review did not establish a separate repository-specific automated-service request budget or commercial automation entitlement. This documented-only contract therefore authorizes no HEAD, GET, Range request, retry loop, directory crawl or scheduled mirroring.

**Mutability notes:** The scientific/release identity is pinned to Census Grid 2021 Version 2021 dated 30 May 2026 and filename V3. The provider may publish later 2021 revisions at new download links. Any future acquisition must freeze requested/final URL, retrieval UTC, exact byte count and SHA-256, archive-member inventory, metadata/read-me identity, representation, CRS/grid semantics and variable definitions; never silently replace V3 with a later release.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** Eurostat's current population-distribution rights section states that the Eurostat Census Grid 2021 is subject to EU copyright rules with CC BY 4.0 licensing. This 2021 census-grid statement must not be conflated with the materially more restrictive historical GEOSTAT 2006/2011 terms shown on the same page. CC BY 4.0 supports reuse and redistribution with attribution, but successful static-file access is not repository publication/admission approval and no separate automated-service/commercial-automation entitlement was established here.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids>
- <https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution>
- <https://ec.europa.eu/eurostat/web/population-demography/population-housing-censuses/information-data>
- <https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip>
- <https://creativecommons.org/licenses/by/4.0/>

**Notes:** Static metadata/access boundary for \#259 and the later \#270 flood × census exposure pilot. No provider request, external byte, parser, adapter, admission promotion or model-input authorization is introduced. A future exact-byte task must preserve V3 identity, archive metadata, census-cell identifiers, representation, CRS/grid, variable definitions, missingness/suppression and attribution before scientific or publication use.
