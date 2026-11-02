<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.opera.dswx-s1.v1.cmr-discovery.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.opera.dswx-s1.v1.cmr-discovery.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.opera.dswx-s1.v1.cmr-discovery

## Source ids

- nasa.opera.dswx-s1.v1

**Provider:** NASA JPL OPERA / Physical Oceanography Distributed Active Archive Center (PO.DAAC) / NASA Common Metadata Repository (CMR)

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html>

**Service root:** <https://cmr.earthdata.nasa.gov>

**Api version:** NASA CMR search API; OPERA_L3_DSWX-S1_V1 collection C2949811996-POCLOUD, version 1.0

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** <https://urs.earthdata.nasa.gov>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- document_fixed_collection_and_granules

### Path templates

- /search/collections.umm_json
- /search/granules.umm_json

**Parameter rules:** DOCUMENTATION-ONLY, NO LIVE AUTOMATION AUTHORIZED: CMR collections search must select exact concept_id=C2949811996-POCLOUD. A future independently reviewed granule search may select that exact collection_concept_id with a fixed UTC time window, bounded AOI and page_size=1. Reject arbitrary collection IDs, product versions, hosts, URLs, credentials, custom headers, arbitrary download links, redirects, pagination and all caller-supplied filters until new review. Never treat public CMR catalogue links as permission to download protected NASA Earthdata files.

## Response contract

### Expected media types

- application/json

**Format:** NASA CMR UMM-JSON public collection and granule discovery metadata only; no satellite GeoTIFF or calibrated classified pixels.

**Scientific semantics:** Metadata returns OPERA DSWx-S1 product and granule discovery identity, not independent flood occurrence, water depth, return period or site-specific hazard. Product is Sentinel-1 SAR-derived 30 m surface-water classification plus confidence layers; 6-12 day nominal revisit does not ensure event-time coverage. Retain observed acquisition UTC, tile ID, product processing version, classification/QA flags and possible overlap in Sentinel-1 evidence with CEMS Global Flood Monitoring.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** No API fetch or catalogue probing is authorized by this documentation-only contract. On a separate reviewed T1 scope, use at most one trusted anonymous CMR metadata request and no redirects, bulk enumeration, unbounded pagination, or recurring polling. Keep any future granule download on a separately authorized credentialed pathway.

**Mutability notes:** CMR metadata and per-granule links may change. Any future execution receipt must bind request identity, CMR concept ID and revision, granule collection and observation UTC, retrieval UTC, response byte count, SHA-256, parser version and final redirect chain; it cannot establish an immutable data-byte identity without a separate original-file receipt.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The AWS Open Data Registry names CC BY 4.0 for the NASA SNWG/OPERA project and identifies OPERA_L3_DSWX-S1_V1 assets as a protected S3 collection requiring Earthdata Login/AWS temporary credentials in us-west-2. This is useful rights evidence but does not constitute source-specific reviewed attribution/republication/commercial entitlement for individual modified Copernicus Sentinel input and granule products. Both data redistribution and automated catalogue/service terms remain unapproved; no probe until independently reviewed.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://podaac.jpl.nasa.gov/dataset/OPERA_L3_DSWX-S1_V1>
- <https://registry.opendata.aws/nasa-snwg-opera/>
- <https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html>
- <https://www.jpl.nasa.gov/go/opera/products/dswx-product-suite/>

**Notes:** This file documents only a public CMR metadata interface and provider-controlled asset-access boundary. Actual DSWx-S1 GeoTIFFs live under protected podaac-ops-cumulus-protected/OPERA_L3_DSWX-S1_V1 and require Earthdata Login and AWS short-term credentials. No retrieval, tiles, samples, Earthdata tokens, real building overlays, original provider bytes, model inputs, or Neon database writes are authorized. See source intake \#1130 and candidate PR \#1133.
