<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nl.rvo.brp-gewaspercelen.2025.ogc-collection.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nl.rvo.brp-gewaspercelen.2025.ogc-collection.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nl.rvo.brp-gewaspercelen.2025.ogc-collection

## Source ids

- nl.rvo.brp-gewaspercelen.2025

**Provider:** Rijksdienst voor Ondernemend Nederland (RVO) via PDOK

**Interface type:** ogc_api

**Status:** probe_ready

**Documentation url:** <https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/api?f=html&amp;lang=en>

**Service root:** <https://api.pdok.nl>

**Api version:** RVO BRP Gewaspercelen OGC API Features / live brpgewas collection, historical 2025 release not pinned by this endpoint

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

- /rvo/gewaspercelen/ogc/v1/collections/brpgewas

**Parameter rules:** One explicitly invoked, source-scoped HTTPS GET to https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json exactly; immutable literal query f=json. No arbitrary source, host, path, query, bbox, geometry, crop-year, headers, items, item links, schema links, redirects, retries, pagination, bulk access, or automated recurring polling. A successful response confirms collection metadata only; the mutable latest collection does not prove the 2025 historical snapshot or actual parcel geometry.

## Response contract

### Expected media types

- application/json

**Format:** Single JSON OGC API Features Collection object for ID brpgewas, title BRP Gewaspercelen, self link, advertised CRS and spatial bbox; no feature values, personal details, crop codes or polygons.

**Scientific semantics:** RVO BRP Gewaspercelen records declared Netherlands agricultural crop parcels based on user submissions, with annual reference date 15 May. Official PDOK announcement 2026-03-17 describes the final 2025 release, but the live OGC Features service serves the most recent collection and its metadata does NOT certify the underlying 2025 snapshot. Crop declarations and geometries are not observed phenology, insurable agricultural sums insured, claims, a complete insured-farm register, hail/flood vulnerability or an independent duplicate of the Netherlands contribution to EuroCropsV2. No period-specific exposure model admission without immutable 2025 original file/ID, licence, geometry and source-quality evidence.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** Official PDOK states free anonymous OGC access for commercial/private users subject to Producten-en-Diensten-Catalogus (PDC) acceptable use and no excess/disruptive traffic, not unlimited download entitlement. This reviewed operation permits at most one source-scoped collection-metadata GET per reviewed trusted-main workflow run, no retries, no GeoJSON feature requests, no recurring job. Heavy traffic, separate bulk extracts, regional polygons or derived publication require independent review.

**Mutability notes:** The live collection can be revised or replaced; it is NOT a release-frozen copy of the final 2025 BRP release. Preserve collection ID brpgewas, exact GET request fingerprint, retrieval UTC, original body SHA-256/bytes, source code/contract digests and observed response media type. A mutable updated timestamp and bbox do not establish source file SHA, 2025 historical crop coverage, parcel-level rights or model readiness.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.pdok.nl/how-to-faq>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** PDOK's authoritative original BRP OGC API landing/docs label the service data 'Public Domain Mark 1.0' (PDM 1.0), no fee and no authentication. PDM is a provider public-domain status label, not itself a legal licence grant, a warranty about underlying third-party rights, or proof that an arbitrary archived 2025 extraction/geometry is clear. PDOK official service terms allow ordinary user/programmatic access subject to fair use and PDC; this review confirms only one reviewed trusted-main run of the fixed public collection-metadata GET, never unrestricted commercial API traffic or source bytes/geometry redistribution. Specific data/year rights, extraction date, attribution and derivative publication require a separate source-scope review. This source-access status does not grant rights for insurer geolocation, crop values or science.

## Probe contract

**Mode:** metadata_get

**Operation:** collection_metadata_get

**Requires credentials:** `false`

### Expected evidence

- One exact anonymous reviewed trusted-main execution GET to fixed PDOK brpgewas collection metadata URL, no redirects or retries, HTTP 200, application/json, original bytes at most 131072
- Strict bounded UTF-8 JSON object, exactly one self-link, collection id/title, OGC CRS84 and EPSG:28992, finite bounding box overlapping Netherlands
- UTC retrieval timestamp, exact request SHA-256, original response SHA-256 and byte count, source access contract/code digests; no original response body or features saved
- Collection not tied to immutable 2025 source vintage; zero feature, polygon, crop-value, personal-data and insurer model inputs requested or admitted

**Implementation decision:** build_later

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://api.pdok.nl/rvo/gewaspercelen/ogc/v1?f=html&amp;lang=en>
- <https://www.pdok.nl/ogc-apis/-/article/basisregistratie-gewaspercelen-brp->
- <https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/api?f=html&amp;lang=en>
- <https://www.pdok.nl/how-to-faq>
- <https://www.pdok.nl/features>
- <https://api.pdok.nl/rvo/gewaspercelen/ogc/v1/collections/brpgewas?f=json>

**Notes:** Metadata-only exact live API access contract, added after publicly available authoritative PDOK terms and original collection metadata were reviewed. An external read-only intermediary on 2026-11-13 returned a JSON collection with id brpgewas/title BRP Gewaspercelen/CRS; intermediary observation does not expose strict original HTTP transport headers or original response byte SHA and must NOT be counted as direct strict repository-runner execution. Requires python -m scripts.probe_pdok_brp_2025_collection_v0 --live on a trusted authorized network execution lane for T1 receipt. No original bytes persisted, crop items queried, or model input admitted. 2025 release freeze remains open.
