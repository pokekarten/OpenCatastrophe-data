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

**Status:** documented_only

**Documentation url:** <https://tnmaccess.nationalmap.gov/api/v1/docs>

**Service root:** <https://tnmaccess.nationalmap.gov>

**Api version:** TNM Access API v1 / USGS Seamless 1-Meter (S1M) DEM, DOI 10.5066/P13LJKFS

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

- document_s1m_datasets_and_products

### Path templates

- /api/v1/datasets
- /api/v1/products

**Parameter rules:** DOCUMENTATION ONLY. Discovery MUST identify USGS TNM dataset tag 'Seamless 1-m DEM (S1M)' from the official datasets catalogue and not infer or silently substitute older project-based 1-meter DEM, OPR DEM, 1/3 arc-second, 1/9 arc-second, LiDAR LAZ or a generic 1-meter result. A subsequent separately approved trusted metadata probe would query a single frozen S1M dataset and one fixed small bounding box with max=1 and offset=0. Until explicit T1 approval reject caller-supplied host, dataset alias, coordinates, product ID, URL, parameters, pagination, download link and redirects. Catalogues may return a product download URL; do not dereference it under this contract.

## Response contract

### Expected media types

- application/json

**Format:** USGS TNM Access API v1 JSON dataset catalogue and product search metadata only; no GeoTIFF or source point-cloud bytes.

**Scientific semantics:** The S1M is a newer 1-meter bare-earth DEM compiled from many LiDAR projects and published in 10-km COG tiles with pixel-level source lineage. Distinct from project-based 1-meter DEM, it has incomplete and expanding coverage; advertised 1-meter pixel spacing does not imply one-meter vertical accuracy. Elevation represents terrain rather than building roof or finished-floor height; horizontal CRS, vertical datum/epoch, survey vintage, blending and source work-unit quality must be verified before hydrologic or building-overlap use.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `131072`

**Max sample bytes:** `131072`

**Retry policy:** none

**Rate limit notes:** No network requests are approved by this documentation-only contract. Later T1 approval must specify one bounded metadata request and fixed AOI, max=1, offset=0, no automatic pagination or directory traversal, no GeoTIFF transfer, retry, schedule or bulk harvesting.

**Mutability notes:** USGS TNM catalogue is continuously updated. Freeze discovery UTC, exact query, resolved sbDatasetTag, dataset and product IDs, full provider metadata URLs, any tile reference/filename, response byte count and SHA-256. The full original COG would require a separately approved exact-byte retrieval receipt and independent raster validity/datum checks.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** USGS explicitly lists 3DEP products as public domain and makes S1M freely accessible; the S1M Science Data Catalog release DOI is 10.5066/P13LJKFS. This dataset-level rights evidence does not automatically establish the permitted load/rate conditions for TNMAccess services or legal status of every possible downstream ancillary layer; the machine interface and any eventual automated acquisition must be reviewed separately. No rights promotion from public-domain science data to unattended API automation or model admission.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://www.usgs.gov/3d-elevation-program/new-product-3d-elevation-program-seamless-1-meter-digital-elevation-model-s1m>
- <https://data.usgs.gov/datacatalog/data/USGS%3A4f34caac-f28f-4ea0-8d82-eafb2b8f9a5d>
- <https://tnmaccess.nationalmap.gov/api/v1/docs>
- <https://apps.nationalmap.gov/datasets/>
- <https://www.usgs.gov/faqs/there-api-accessing-national-map-data>

**Notes:** Bounded interface description only. This does not prove any S1M tile is available in a requested county, and no provider DEM, catalogue response bytes or finished-floor elevations have been acquired or staged. S1M must be distinguished from USGS older project-based 1-meter DEM and from high-resolution building roof products. No CAT model admission, insurer attribution, coverage selection or Neon write is authorized.
