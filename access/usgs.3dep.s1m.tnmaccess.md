<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/usgs.3dep.s1m.tnmaccess.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `usgs.3dep.s1m.tnmaccess.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** usgs.3dep.s1m.tnmaccess

## Source ids

- usgs.3dep.seamless-1m.s1m

**Provider:** U.S. Geological Survey (USGS) 3D Elevation Program / The National Map (TNMAccess)

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://tnmaccess.nationalmap.gov/api/v1/docs>

**Service root:** <https://tnmaccess.nationalmap.gov>

**Api version:** TNM Access API v1 / USGS Seamless 1-Meter (S1M) DEM, DOI 10.5066/P13LJKFS

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- probe_single_florida_s1m_product

### Path templates

- /api/v1/products

**Parameter rules:** Exactly one explicit opt-in HTTPS GET to service root https://tnmaccess.nationalmap.gov and exact path /api/v1/products using ONLY literal query datasets=Seamless%201-m%20DEM%20%28S1M%29&amp;bbox=-81.00,25.95,-80.95,26.00&amp;max=1&amp;offset=0. The fixed source/collection is Seamless 1-m DEM (S1M), not older project-based 1m DEM; the pinned Florida bbox is \[-81.00,25.95,-80.95,26.00\] WGS84, max=1 and offset=0. Never accept caller-selected host, source, AOI, dates, headers, pagination, extra parameters, retries, redirects, alternate URL, object download, raw GeoTIFF, metadata crawl or schedule. A successful catalogue response remains metadata-only, not CAT admission. One response may have an empty item.datasets array: its title, sourceId, exact S1M TIFF URL and AOI must match the one independently frozen record.

## Response contract

### Expected media types

- application/json

**Format:** USGS TNM Access API v1 JSON dataset catalogue and product search metadata only; no GeoTIFF or source point-cloud bytes.

**Scientific semantics:** The S1M is a newer 1-meter bare-earth DEM compiled from many LiDAR projects and published in 10-km COG tiles with pixel-level source lineage. Distinct from project-based 1-meter DEM, it has incomplete and expanding coverage; advertised 1-meter pixel spacing does not imply one-meter vertical accuracy. Elevation represents terrain rather than building roof or finished-floor height; horizontal CRS, vertical datum/epoch, survey vintage, blending and source work-unit quality must be verified before hydrologic or building-overlap use. Official S1M CONUS collection metadata (USGS S1M DOI 10.5066/P13LJKFS, observed 2026-11-15) specifies horizontal NAD83(2011) / USA Contiguous Albers Equal Area EPSG:6350, vertical NAVD88 EPSG:5703 updated to GEOID18, and metres for both horizontal and elevation units. The float COG has nominal 1-m pixel spacing and -999999 as its NoData value. These are published product-level declarations, NOT a verified TIFF header or per-tile height accuracy. Original source project footprints and processing lineage are in a separate spatial-metadata GeoPackage: voids wider than 10 m may be backfilled from 1/9- or 1/3-arcsecond DEMs, smaller gaps bilinearly interpolated, and work units blended. A one-metre output grid does NOT prove every pixel is a measured one-metre lidar observation. Do not apply the separate legacy project-based 1-m DEM UTM default to S1M or interpret the -999999 sentinel as ground elevation. Source bytes, exact TIFF and GeoPackage hashes, per-tile datum and backfill flags remain unverified.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** One manually triggered exact HTTPS GET (max=1 offset=0), no retries, redirects, concurrent calls, pagination, interval schedule, alternate areas or asset download. USGS public-domain statement does not imply a throughput entitlement. No provider bytes saved in repository, Neon or local cache.

**Mutability notes:** TNM S1M product catalogue can change; record original response SHA-256, byte count, retrieval UTC, exact GET request hash, parser and code hash, one vetted source ID and expected TIFF URL. Failure to match the pinned 2026-08-21 Florida record must block rather than search alternate tiles. Source TIFF ~447MB is not touched in this T1 metadata probe. Independent S1M product science documentation reviewed 2026-11-15: future original TIFF and companion spatial-lineage GeoPackage receipts must be bound to one tile and independently checked for EPSG:6350 horizontal, EPSG:5703/GEOID18 vertical, metre units, -999999 NoData, 1-m pixel spacing, collection vintage and void/backfill/blend flags before any flood-hazard use. A metadata-only TNM catalogue response cannot satisfy these checks.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** Official USGS National Map FAQ states mapping services and downloaded data are public domain, free and unrestricted with recommended agency acknowledgement; National Map FAQ and public TNMAccess OpenAPI explicitly support developers making programmatic HTTP GET/POST requests. This review approves only one human-triggered, fixed anonymous GET retrieving public product metadata. It does NOT approve sustained/high-rate API use, provider bytes redistribution, alternate assets or original GeoTIFF downloads; preserve explicit data attribution and retain no external response body.

## Probe contract

**Mode:** metadata_get

**Operation:** probe_single_florida_s1m_product

**Requires credentials:** `false`

### Expected evidence

- One exact fixed request to /api/v1/products with reviewed S1M dataset, bbox, max=1, offset=0 and without redirects or credentials
- HTTP 200, application/json and uncompressed content under 131072 original bytes
- Strict JSON shape with exactly one product matching frozen S1M sourceId, exact title, TIFF URL, valid bounds and original collection identity
- SHA-256 and byte count of original response, request fingerprint, parser/code SHA and retrieval UTC; no raw response body persisted
- model_input_admitted=false; original_tiff_downloaded=false; external_bytes_persisted=false

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://www.usgs.gov/3d-elevation-program/new-product-3d-elevation-program-seamless-1-meter-digital-elevation-model-s1m>
- <https://data.usgs.gov/datacatalog/data/USGS%3A4f34caac-f28f-4ea0-8d82-eafb2b8f9a5d>
- <https://tnmaccess.nationalmap.gov/api/v1/docs>
- <https://apps.nationalmap.gov/datasets/>
- <https://www.usgs.gov/faqs/there-api-accessing-national-map-data>
- <https://www.usgs.gov/faqs/what-are-terms-uselicensing-map-services-and-data-national-map>
- <https://catalog.data.gov/dataset/seamless-1-meter-digital-elevation-models-dems-usgs-national-map-3dep-downloadable-data-co>

**Notes:** One metadata-only, explicitly opt-in T1 route for the single verified public South Florida S1M product sourceId 6a9785801ba49b050c166274. Dataset is public-domain but any different AOI, raw COG, DEM pixel, footprint overlay, building height or insurer loss requires new source-scientific authorization. No automatic data import or Neon write follows. Additional 2026-11-15 T0 scientific reference: USGS S1M public DOI 10.5066/P13LJKFS publisher catalogue specifies EPSG 6350 / 5703, GEOID18, -999999 NoData and variable source/backfill provenance. New pure-offline synthetic profile checks in research_runners/usgs_s1m_tnm_metadata_preflight_v0.py only compare a caller-supplied profile to published reference values. They do NOT attest original TIFF/GeoPackage bytes, licence/model admission, flood accuracy or T3.
