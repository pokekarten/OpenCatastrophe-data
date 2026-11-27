<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec-jrc.global-surface-water.1984-2024.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec-jrc.global-surface-water.1984-2024.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec-jrc.global-surface-water.1984-2024

## Source ids

- ec-jrc.global-surface-water.1984-2024

**Provider:** European Commission Joint Research Centre / Copernicus / Google; CloudFerro source file hosting

**Interface type:** object_store

**Status:** documented_only

**Documentation url:** <https://global-surface-water.appspot.com/download>

**Service root:** <https://s3.waw4-1.cloudferro.com>

**Api version:** JRC Global Surface Water 1.5; long-term aggregated occurrence 1984-2024; corrected 2026-11-10

## Access scope

- metadata
- catalogue
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- preflight_original_v15_listing
- inspect_fixed_v15_occurrence_tiff

### Path templates

- /swift/v1/global-surface-water/
- /swift/v1/global-surface-water/download2024/Aggregated/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif

**Parameter rules:** Documentation and offline preflight ONLY: no provider GET, HEAD, HTTP Range, automated listing/asset download, pagination, streaming, crawling, retries, caller-selected path, query string, host, product family, period, header or redirect is authorized by this contract. The exact selected v1.5 occurrence asset is occurrence_10E_50N_v1_5_2024.tif. The existing scripts/preflight_jrc_gsw_v15_listing_v0.py accepts separately and lawfully acquired, full original UTF-8 listing bytes with no network request. First review CloudFerro endpoint/service terms, provider access conditions, bounded request/redirect/rate policy and corrected-asset version identity. Then separately propose a fixed provider runner; do not change status to probe_ready solely on a successful HTML source-page request.

## Response contract

### Expected media types

- text/plain
- application/octet-stream
- image/tiff

**Format:** Original public CloudFerro JRC GSW v1.5 UTF-8 relative-path listing, and after separate review one exact v1.5 10-degree occurrence GeoTIFF. The offline listing preflight only checks the fixed asset path, listing syntax and original listing SHA-256; it does not examine GeoTIFF bytes, verify source pixel values or compute original whole-TIFF checksum.

**Scientific semantics:** Occurrence represents a historical observed-water occurrence percentage over available valid Landsat observations, not event flood hazard, annual exceedance probability, inundation return period, modelled flood extent, or insured damage. v1.5 aggregates Landsat Collection 1 (1984-2021) and Collection 2 (2022-2024), with geolocation/co-registration seams which can exceed one approximately 30 m cell; the 1984-2015 research-vetted record and subsequent extensions have different validation. Official original Occurrence GeoTIFFs and GEE assets were corrected 2026-11-10 for sporadic &gt;100% out-of-range values, so stale cached tiles must be rejected. Monthly Recurrence has a separately acknowledged unresolved sparse-observation bias; it is NOT cleared by the Occurrence correction. Historic water masks cannot alone be promoted to flood-frequency or CAT-model input without CRS, nodata, class semantics, temporal availability, independent validation and loss-model fit.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `8000000`

**Retry policy:** none

**Rate limit notes:** The JRC publisher allows download and reuse, but no reviewed machine-client/API service terms, CloudFerro anonymous GET/HEAD/Range limits, byte-range acceptance, redirect policy, server-advertised usage quotas, or automated polling entitlement has been bound to this exact service. Zero executable requests under this contract; no bulk mirror, tiled crawl or surprise downloads.

**Mutability notes:** Pin exact 1984-2024 v1.5 product, tile, path, layer, and provider’s 2026-11-10 corrected occurrence publication; a filename alone does not prove the corrected bytes. Before any data request, independently verify source directory listing integrity and choose a currently corrected tile. Later original response receipt must include full original byte count/hash (or a clearly scoped Range-only hash), COG/TIFF header, raster type/CRS/NoData, retrieval UTC and explicit cache freshness. v1.4 FTP source is deprecated and not interchangeable.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The official JRC Global Surface Water download page, reviewed 2026-11-13, states that Copernicus Programme data are free without restriction of use and requires acknowledgement/citation and map attribution 'Source: EC JRC/Google' with Pekel et al. (2016). This product-scoped reuse allowance includes commercial analysis in principle; it is NOT a reviewed grant for arbitrary automated CloudFerro asset crawling, provider transfer limits, unqualified republishing of third-party content, unverified historical/corrected versions, or CAT scientific admission. Service/API terms and source byte persistence/public redistribution remain independently unresolved and fail-closed until reviewed.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://global-surface-water.appspot.com/download>
- <https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/>
- <https://doi.org/10.1038/nature20584>
- <https://global-surface-water.appspot.com/download#download>

**Notes:** Product-/version-scoped rights and exact-host/path preflight for existing candidate ec-jrc.global-surface-water.1984-2024. Only offline listing checker exists; no original CloudFerro listing bytes or GeoTIFF pixels have been acquired by this change. Official 2026-11-10 occurrence correction is required; monthly recurrence sparse-observation issue remains unresolved. This JSON must NOT be promoted to an executable source access contract without a separate manual API terms, automation cadence and original byte/pixel/holdout scientific review.
