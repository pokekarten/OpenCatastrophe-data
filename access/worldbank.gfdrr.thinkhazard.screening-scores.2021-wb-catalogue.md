<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/worldbank.gfdrr.thinkhazard.screening-scores.2021-wb-catalogue.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `worldbank.gfdrr.thinkhazard.screening-scores.2021-wb-catalogue.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** worldbank.gfdrr.thinkhazard.screening-scores.2021-wb-catalogue

## Source ids

- worldbank.gfdrr.thinkhazard.screening-scores

**Provider:** World Bank / GFDRR ThinkHazard archived hazard-ranking dataset

**Interface type:** web_portal

**Status:** documented_only

**Documentation url:** <https://datacatalog.worldbank.org/search/dataset/0060151/thinkhazard-hazard-ranking>

**Service root:** <https://datacatalog.worldbank.org>

**Api version:** World Bank Data Catalog dataset 0060151, published score-table snapshot 2021-11-29; not 2026 ThinkHazard portal

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

- inspect_worldbank_2021_licence_and_vintage

### Path templates

- /search/dataset/0060151/thinkhazard-hazard-ranking

**Parameter rules:** Documentation-only. This one fixed World Bank catalogue page identifies an archived 2021 Excel release with CC BY 4.0. The 2026 ThinkHazard portal is a scientifically different publication. No data file, generic Data Catalog API query, preview, API Service link, redirect or script download is authorized. Do not follow provider-returned file URLs or synthesize unreviewed URLs; later access needs a separate exact-file, rights and response-byte receipt review.

## Response contract

### Expected media types

- text/html

**Format:** Official World Bank Data Catalog metadata page, not a scoring data API, 2026 dynamic portal or downloaded Excel asset.

**Scientific semantics:** The dataset page metadata was revised in March 2025 but the listed hazard ranking Excel file itself was last updated November 29, 2021. The 2026 ThinkHazard site separately states data published September 18, 2026 and additional city classifications. Neither temporal lineage can be silently substituted. Hazard level classes are screening guidance, not event footprints, exceedance probabilities, observed damage or actuarial losses.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** No provider requests are executable under this documented-only contract. World Bank Data Catalog API and download service automation terms require separate exact-path review.

**Mutability notes:** Freeze data product version and file publication date (2021-11-29), catalog metadata date (2025-03-07) and separate live portal publication (2026-09-18) distinctly. Underlying source layers, administrative boundaries, urban-area support and hazard category methods can differ. A later dataset file byte hash and attribution are required before modelling.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The official World Bank Data Catalog record 0060151 explicitly lists Creative Commons Attribution 4.0 for the dated 2021 hazard-ranking Excel dataset. That dataset-specific licence permits redistribution with attribution but does not prove automated Data Catalog API access terms, the rights for upstream layers or that a newer 2026 portal product uses the same dataset. All executed access remains disabled.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-03

## Evidence urls

- <https://datacatalog.worldbank.org/search/dataset/0060151/thinkhazard-hazard-ranking>
- <https://int.thinkhazard.org/en/about>
- <https://gfdrr.github.io/thinkhazard/>
- <https://datacatalog.worldbank.org/public-licenses>

**Notes:** Research-only source product/version access boundary, not a model admission. Product 2021 file remains unread, no bytes or licence files ingested and no hazard score or data record stored in Neon. The dynamic ThinkHazard 2026 portal requires distinct version and layer-level provenance before use.
