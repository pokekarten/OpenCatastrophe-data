<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/esa.worldcover.2021.v200.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `esa.worldcover.2021.v200.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** esa.worldcover.2021.v200

## Source ids

- esa.worldcover.2021.v200

**Provider:** European Space Agency (ESA) WorldCover consortium / VITO

**Interface type:** object_store

**Status:** documented_only

**Documentation url:** <https://esa-worldcover.org/en/data-access>

**Service root:** <https://esa-worldcover.s3.eu-central-1.amazonaws.com>

**Api version:** WorldCover 2021 v200; AWS bucket esa-worldcover; prefix v200/2021/map

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

- list_v200_map_prefix
- fetch_exact_v200_tile

### Path templates

- /v200/2021/map/

**Parameter rules:** This contract documents the official WorldCover 2021 v200 delivery identity but authorizes no network operation yet. The provider documents anonymous no-sign access to bucket esa-worldcover and the versioned map prefix v200/2021/map. A future source-specific worker must first freeze one exact v200/2021 map tile object key from authoritative provider evidence and then keep bucket, region, version, year, prefix, object key, query, headers and redirect targets repository-controlled. Caller-selected object paths, prefix-wide sync, bucket enumeration and arbitrary raster downloads are forbidden. The Zenodo DOI 10.5281/zenodo.7254221 is an immutable release/provenance identity, not caller-controlled alternate download authority.

## Response contract

### Expected media types

- image/tiff
- application/octet-stream

**Format:** WorldCover 2021 v200 map data are distributed as 3 by 3 degree Cloud-Optimized GeoTIFF tiles in EPSG:4326. The analytical map layer and InputQuality layer are distinct products; WMS/WMTS RGB visualizations are cartographic views and must not be treated as analysis rasters.

**Scientific semantics:** WorldCover 2021 v200 is a 10 m global land-cover map with 11 classes and a 2021 reference year. The official product-level independent validation reports 76.7% overall accuracy for v200; this is not a per-pixel correctness guarantee. WorldCover 2020 uses algorithm v100 while 2021 uses v200, so differences between the two maps contain both real land-cover change and algorithm effects and must not be interpreted as a pure change layer. Land-cover class is contextual exposure/vulnerability information, not asset count, insured value, hazard intensity, damage or loss.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `52428800`

**Retry policy:** none

**Rate limit notes:** The provider and AWS Open Data Registry document public no-sign bucket access, but this repository has not separately established a service-automation entitlement or rate budget. This documented-only contract authorizes no S3 ListObjects, HEAD, GET, Range request, prefix sync, crawling or repeated probe.

**Mutability notes:** The product identity is versioned as 2021 v200 and is also anchored by immutable release DOI 10.5281/zenodo.7254221. The official AWS prefix is v200/2021/map, but no exact tile object is frozen by this contract. Any later acquisition must bind the exact object key and requested/final storage identity, retrieval UTC, byte count and SHA-256, validate the COG structure, EPSG:4326 grid/extent and class coding, and preserve the v200 product identity before scientific use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://creativecommons.org/licenses/by/4.0/>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The official WorldCover data-access page states that the WorldCover product is provided free of charge without restriction under Creative Commons Attribution 4.0 and requires acknowledgement to the ESA WorldCover project. Those dataset reuse and redistribution rights are recorded separately from AWS/S3 service automation permission. Public no-sign availability is not by itself treated as proof of unrestricted automated service use, so this contract authorizes no network probe or fetch and admits no raster bytes.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://esa-worldcover.org/en/data-access>
- <https://registry.opendata.aws/esa-worldcover-vito/index.html>
- <https://zenodo.org/records/7254221>
- <https://creativecommons.org/licenses/by/4.0/>

**Notes:** This is a narrow pre-execution source-access contract for \#173/\#242. It freezes WorldCover 2021 v200 machine-delivery, release, scientific and dataset-rights identities without selecting or downloading a raster tile. A later exact-tile task must separately review the provider object key, service execution boundary, byte identity, attribution and intended scientific role before any sample, admission or publication step.
