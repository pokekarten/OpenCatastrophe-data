<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nl.rvo.brp-gewaspercelen.2025.inspire-collection.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nl.rvo.brp-gewaspercelen.2025.inspire-collection.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nl.rvo.brp-gewaspercelen.2025.inspire-collection

## Source ids

- nl.rvo.brp-gewaspercelen.2025

**Provider:** Rijksdienst voor Ondernemend Nederland (RVO) via PDOK / INSPIRE-harmonised Gewaspercelen

**Interface type:** ogc_api

**Status:** probe_ready

**Documentation url:** <https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&amp;lang=en>

**Service root:** <https://api.pdok.nl>

**Api version:** OGC API Features v1; harmonised INSPIRE Gewaspercelen, mutable currently served Collection, not an immutable historical BRP 2025 asset

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- collection_metadata_get

### Path templates

- /rvo/gewaspercelen-geharmoniseerd/ogc/v1/collections/gewaspercelen

**Parameter rules:** One only exact original anonymous GET to https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1/collections/gewaspercelen?f=json, fixed f=json, no arbitrary host/filename/query, linked items, schema download, bbox filters, crop data, feature pagination, retries, redirects, schedule, geometry or bulk. The INSPIRE service and prior raw BRP brpgewas collection are distinct endpoints and cannot be substituted. This Collection metadata on its own does not establish 2025 historical version. The public INSPIRE feature display includes \#DS_NL_BRP_GEWAS_2025_Definitief, but its live feature contents/geometry are NOT requested by this metadata probe.

## Response contract

### Expected media types

- application/json

**Format:** Single original OGC API Features Collection JSON: id=gewaspercelen, title=Gewaspercelen, self-link, OGC CRS84/EPSG:28992/EPSG:4258, native storageCrs=EPSG:4258 and single Netherlands-covering bbox.

**Scientific semantics:** INSPIRE-harmonised source is based on national RVO farm-declared agricultural plots and (former AAN) RVO Reference Register, not independently observed insured agrarian sums insured. The public feature pages advertise dataset \#DS_NL_BRP_GEWAS_2025_Definitief while feature validfrom=2026-05-15; 2025 nominal vintage, publication/fix date, lifecycle validfrom and May-15 agricultural reporting basis MUST NOT be conflated. No original feature, geometry, number of farms, claims or source-wide immutable 2025 file identity is certified.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Original official PDOK public OGC API lists Open data (publiek), no cost, no authentication and source service PDC terms. This gate authorizes one exact bounded metadata GET per reviewed first-party main push/manual dispatch, no intervals, retries, linked items or bulk. Parcel/feature API, commercial model use and redistribution remain separately blocked until product-specific review.

**Mutability notes:** Collection has been seen with updated 2026-04-01T13:22:57Z; this is mutable service metadata, not original 2025 snapshot SHA. Only exact original response SHA/bytes, HTTP 200, service self-link, CRS, extent and retrieval timestamp are to be recorded; no raw JSON or farmer identifiers. Provider public INSPIRE pages show \#DS_NL_BRP_GEWAS_2025_Definitief as a feature attribute, not an immutable pinned downloadable archive.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.pdok.nl/how-to-faq>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** Only the public metadata interface has been reviewed: official PDOK OGC API landing calls this service 'Open data (publiek)', no authentication or charge, under PDOK PDC/fair-use and no undue traffic. The designation is a publication claim, not an unconditional raw farmer/parcel licence; commercial automation allowed here means ONE reviewed anonymous metadata GET, NOT unattended periodic crawling, parcel geometry, farm attribute downloads or publishing output. Original crop and geometry rights, land use data privacy, 2025 fixed-version full file rights, commercial CAT/insurer model publication and geo-linkage remain unknown and not admitted.

## Probe contract

**Mode:** metadata_get

**Operation:** collection_metadata_get

**Requires credentials:** `false`

### Expected evidence

- One exact 20-second first-party original HTTPS 200 GET to PDOK INSPIRE Gewaspercelen Collection ?f=json (no redirects/retries), JSON &lt;=65536 original bytes, no content encoding
- Strict original JSON structure: id gewaspercelen/title Gewaspercelen, advertised CRS84 and EPSG:28992 and EPSG:4258, native storageCrs EPSG:4258, finite Netherlands-overlapping CRS84 bbox, exactly one exact self-link
- Original GET request SHA-256, exact original response SHA-256/byte count, source contract and code SHA-256, UTC and strictly Boolean schema flags; no JSON body/raw parcel values persisted
- Only collection metadata: 2025-definitive dataset marker is externally observed on public INSPIRE HTML feature pages, NOT validated by this request; historical file freeze, commercial CAT reuse, geometry and model admission remain false

**Implementation decision:** build_later

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://www.pdok.nl/ogc-apis/-/article/gewaspercelen-inspire-geharmoniseerd->
- <https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1?f=html&amp;lang=en>
- <https://www.pdok.nl/how-to-faq>
- <https://api.pdok.nl/rvo/gewaspercelen-geharmoniseerd/ogc/v1/collections/gewaspercelen?f=json>
- <https://www.pdok.nl/-/brp-gewaspercelen-2025-definitief>
- <https://geoforum.nl/t/brp-gewaspercelen-2025-definitief/11417>

**Notes:** This separate INSPIRE-harmonised OGC API interface is a second access contract to source nl.rvo.brp-gewaspercelen.2025, not a distinct original farmer observation or independent insurance exposure. The extant raw brpgewas metadata original-run receipt remains separately pinned. Strict new trusted-main original GET is required before first-party INSPIRE result; an external read-only intermediary previously observed the Collection metadata but did NOT verify native HTTP transport or byte SHA.
