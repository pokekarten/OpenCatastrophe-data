<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/sk.gku.inspire-buildings.gpkg.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `sk.gku.inspire-buildings.gpkg.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** sk.gku.inspire-buildings.gpkg

## Source ids

- sk.gku.inspire-hvd-buildings.2026

**Provider:** Geodetic and Cartographic Institute Bratislava (GKÚ Bratislava)

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.skgeodesy.sk/geoportal-en/inspire/download-data/>

**Service root:** <https://opendata.skgeodesy.sk>

**Api version:** Official INSPIRE Buildings GeoPackage download listing updated 2026-02-02; no immutable asset release verified

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

- fetch_fixed_buildings_gpkg_zip

### Path templates

- /static/INSPIRE/Buildings/inspire_bu_gpkg.zip

**Parameter rules:** Documentation-only, non-executing route for the single official Buildings GeoPackage ZIP. The URL is the fixed target of the Buildings/GEOPACKAGE link on the official INSPIRE download page. No network execution is authorized. A later independently reviewed worker must construct the host and path from this contract, reject caller-supplied host, directory, alternative filename, redirects, query parameters or headers, and first establish realistic file-size and bounded acquisition limits. Do not recursively crawl INSPIRE downloads or substitute parcel/elevation datasets.

## Response contract

### Expected media types

- application/zip
- application/octet-stream

**Format:** Provider-listed ZIP distribution of Slovakia INSPIRE Buildings, GeoPackage representation. Archive member names, internal feature layers, feature counts and exact ZIP bytes have not been fetched or verified.

**Scientific semantics:** The national INSPIRE Buildings layer may provide building or building-part geometries, but the publication page alone does not establish which feature classes, identifiers, geometry types, completeness or attribute semantics are present. Official download listing states ETRS89 EPSG:4258; confirm the actual GeoPackage layer CRS, geometry validity, geometry-vs-building-part cardinality and coverage directly from original bytes before any use. Buildings are not verified insured risks, occupancy, construction, rebuilding value, damage or catastrophe vulnerability. Compare the original national source and EUBUCCO only with explicit lineage to avoid double-counting the same underlying cadastral origin.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `52428800`

**Retry policy:** none

**Rate limit notes:** No host-wide request budget or archive size is verified. This record does not permit a HEAD, Range, full download or repeated automated request. A later independent acquisition review must set a defensible source-specific size ceiling and server/redirect policy.

**Mutability notes:** The public static download path is not content-addressed or versioned. The listing update date 2026-02-02 is not the original file creation, survey or feature-vintage date. A future acquisition receipt must pin the requested and final URL, retrieval UTC, observed content length, compressed ZIP SHA-256, member inventory, feature count and CRS; changed bytes are a new scientific/version review.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://www.skgeodesy.sk/geoportal-en/inspire/download-data/>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The official GKÚ INSPIRE page explicitly lists Buildings GeoPackage as CC BY 4.0. That establishes a published dataset licence with attribution, indication of changes and licence reference, but it does not independently resolve bulk-host service terms or prove a particular ZIP byte identity. Do not upgrade commercial automation, persistence or repository publication solely because the linked ZIP is public. This review applies only to the listed Buildings product and not to parcels, orthophotos or third-party derived assets.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-09

## Evidence urls

- <https://www.skgeodesy.sk/geoportal-en/inspire/download-data/>
- <https://opendata.skgeodesy.sk/static/INSPIRE/Buildings/inspire_bu_gpkg.zip>
- <https://creativecommons.org/licenses/by/4.0/>

**Notes:** Metadata and terms review only for the existing, non-admitted landscape candidate sk.gku.inspire-hvd-buildings.2026. The official download-page table and fixed ZIP link were read; no ZIP bytes, archive member list, live HEAD response, GeoPackage features or source-version checksum were acquired. This contract does not add a model, insured portfolio, admissible raw data or permission to automate the download.
