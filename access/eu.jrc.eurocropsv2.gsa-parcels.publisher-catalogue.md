<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/eu.jrc.eurocropsv2.gsa-parcels.publisher-catalogue.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `eu.jrc.eurocropsv2.gsa-parcels.publisher-catalogue.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

**Status:** documented_only

**Access id:** eu.jrc.eurocropsv2.gsa-parcels.publisher-catalogue

## Source ids

- eu.jrc.eurocropsv2.gsa-parcels

**Provider:** European Commission Joint Research Centre / national agricultural paying agencies

**Interface type:** http_file

**Documentation url:** <https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3>

**Service root:** <https://jeodpp.jrc.ec.europa.eu>

**Api version:** EuroCropsV2 JRC distribution; edition and member-state/year GPQT must be pinned individually, no mutable directory admission

## Access scope

- metadata
- catalogue

## Request contract

### Allowed operations

- inspect_official_catalogue_metadata

### Path templates

- /ftp/public/JRC-OpenData/DRLL/EuroCropsV2/copyright.txt
- /ftp/public/JRC-OpenData/DRLL/EuroCropsV2/readme.md

**Parameter rules:** Documentation only: no HTTP request from this contract. Never infer that one JRC listing URL or its 2026 CC BY notice identifies a frozen country/year parcel file. Before any runnable adapter, independently review the exact country-year/version GeoParquet path, use-case rights, automated-access terms, redirects and bytes. No user-selected path, arbitrary host, crawler, bulk GPQT, crop code list or GIS upload is authorized.

## Response contract

### Expected media types

- text/plain
- text/markdown
- text/html

**Format:** Publisher copyright notice and explanatory catalogue/readme only; no parcel geometry or data product bytes.

**Scientific semantics:** EuroCropsV2 harmonizes multi-year farmer-declared agricultural parcel and crop categories across participating European regions. The paper reports almost 47 million parcels, incomplete region-year coverage and a mix of member-state source vintages; a parcel declaration is neither an observed insured field nor TIV, crop yield, loss, vulnerability or independent validation against its contributing national agency. Native raster/projection use requires checked EPSG:3035 geometry, code dictionaries, source vintage and national lineage.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** No independent machine-use/automated retrieval terms established by this documentation contract. No scheduled or bulk requests. A reviewed future metadata-only request must establish rate limits and transport rights first.

**Mutability notes:** The publisher listing exposes multiple gpqt, gpqtv2 and later patch directories with varying update dates; do not equate current catalogue discovery with an immutable full version or underlying source-country snapshot.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://jeodpp.jrc.ec.europa.eu/ftp/public/JRC-OpenData/DRLL/EuroCropsV2/copyright.txt>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The official JRC copyright.txt says that rights on the published dataset are licensed CC BY 4.0 subject to attribution and indication of changes. Dataset reuse permission does not by itself establish rights to automate this server or to redistribute particular reprocessed member-state parcel geometries unchanged; scope and upstream country/year provenance must be independently reviewed. No source byte, sample, input or insured exposure admission.

## Evidence urls

- <https://jeodpp.jrc.ec.europa.eu/ftp/public/JRC-OpenData/DRLL/EuroCropsV2/copyright.txt>
- <https://jeodpp.jrc.ec.europa.eu/ftp/public/JRC-OpenData/DRLL/EuroCropsV2/>
- <https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3>
- <https://doi.org/10.5194/essd-18-4075-2026>

**Notes:** Static documented-only source-access identity for the existing EuroCropsV2 candidate. Publisher catalogue and rights notice inspected externally 2026-11-14; no repository-native original provider GET, byte-level GeoParquet sample, scientific fitness or CAT admission proven. Separate product-specific review required before API execution.
