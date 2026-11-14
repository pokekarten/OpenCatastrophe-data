<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/meteoswiss.national-hail-climatology.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `meteoswiss.national-hail-climatology.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** meteoswiss.national-hail-climatology

## Source ids

- meteoswiss.national-hail-climatology

**Provider:** Federal Office of Meteorology and Climatology MeteoSwiss / Federal Spatial Data Infrastructure

**Interface type:** stac

**Status:** probe_ready

**Documentation url:** <https://opendatadocs.meteoswiss.ch/c-climate-data/c5-radar-based-climate-data>

**Service root:** <https://data.geo.admin.ch>

**Api version:** STAC 1.0.0

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

- /api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid

**Parameter rules:** Exactly one manually dispatched anonymous HTTPS GET to https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid, no query string, retries, redirects or caller-supplied URL, headers, collection/item IDs, bbox, search filters, asset href, NetCDF path, date, product or return period. The probe checks only the STAC Collection metadata body and does not traverse its linked items/assets or schedule polling.

## Response contract

### Expected media types

- application/json

**Format:** One official STAC 1.0.0 Collection JSON response with frozen collection id/title/type, MeteoSwiss producer/licensor, CC-BY, canonical self-link and national Swiss hail-climate scope; release dates/items are mutable. Asset files are never requested.

**Scientific semantics:** The collection contains several non-interchangeable radar-derived hail climate product families: monthly/yearly MESHS and anomalies, monthly/yearly hail-day counts and anomalies, long-term hail-day climatologies and standard deviations, and separate HailStoRe-derived return-value hazard maps. Hail fields are radar/algorithm-derived pseudo-observations rather than comprehensive ground measurements; return-value maps additionally depend on stochastic resampling and represent annual exceedance hazard under today's climate, not observed event catalogues. A hail day uses the provider-defined 06 UTC to 06 UTC window. The hail-climatology datasets are calculated only for the April-through-September hail season; absence or non-publication for October through March must not be interpreted as an observed zero, a verified no-hail day or month, or complete year-round observational coverage. Monthly and yearly products update over time, while return-value maps are static. Data are provided on the Swiss LV95 / EPSG:2056 grid at approximately 1 km scale. Any later asset consumer must preserve exact product class, temporal/release identity, observed-versus-model-derived status and CRS rather than treating the collection as one homogeneous hail variable.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** Provider official fair-use and MeteoSwiss Open Data terms allow registration-free anonymous STAC metadata GETs, but prohibit excessive/repeated traffic and recommend identifiable clients. Limit this contract to exactly one manually triggered HTTPS metadata GET (30s, 256 KiB, no retry). No scheduled live polling, automatic item traversal, NetCDF acquisition or bulk requests.

**Mutability notes:** The STAC collection metadata and current monthly/yearly item inventory are mutable as MeteoSwiss publishes updates. Provider documentation states monthly updates are available after the following month and yearly updates at the end of October, while hail-hazard return values are static. Any future asset receipt must bind retrieval UTC, exact collection/item/asset identity, final provider URL, byte count and SHA-256.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.geo.admin.ch/en/general-terms-of-use-fsdi>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** MeteoSwiss original Open Data terms grant CC BY 4.0 commercial reuse with mandatory attribution (Source: MeteoSwiss), excluding endorsement. FSDI/STAC service docs permit public GET and apply fair-use limits; automated excessive download traffic is forbidden. This review authorizes only a single manual Collection metadata GET. STAC response license identifier is CC-BY, not a licence granted for unreviewed third-party linked assets, all attribute families, NetCDF publication or model admission.

## Probe contract

**Mode:** metadata_get

**Operation:** collection_metadata_get

**Requires credentials:** `false`

### Expected evidence

- Exactly one original official STAC v1 Collection HTTPS GET HTTP 200 without redirect, max 262144 response bytes and application/json
- Exact collection id ch.meteoschweiz.ogd-radar-derived-grid, STAC version 1.0.0, Collection type and Spatial climate analyses - Hail identity
- Producer/licensor Federal Office of Meteorology and Climatology MeteoSwiss, CC-BY licence, canonical self-link and Swiss hail season semantics
- Retrieval UTC, fixed request SHA-256, original body SHA-256, response bytes and reviewed code/contract hashes
- No linked items, NetCDF assets, original values, provider payloads or CAT model inputs acquired or persisted

**Implementation decision:** build_later

**Reviewed at:** 2026-11-12

## Evidence urls

- <https://opendatadocs.meteoswiss.ch/c-climate-data/c5-radar-based-climate-data>
- <https://www.meteoswiss.admin.ch/climate/the-climate-of-switzerland/hail-climatology.html>
- <https://www.meteoswiss.admin.ch/climate/the-climate-of-switzerland/hail-climatology/data-and-methods.html>
- <https://opendatadocs.meteoswiss.ch/general/terms-of-use>
- <https://www.geo.admin.ch/en/general-terms-of-use-fsdi>
- <https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid>

**Notes:** A single metadata-only, original-provider STAC Collection probe is now reviewed. The canonical collection ID is ch.meteoschweiz.ogd-radar-derived-grid and DOI 10.18751/Climate/Griddata/CHHC/1.0. A successful metadata probe does not authorize STAC item traversal, hail return-level asset downloads, annual exceedance interpretation, event catalog generation, scientific admission, CAT loss, insured exposure or data write. Separate asset identity/licence/quality/science reviews required.
