<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026

## Source ids

- ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026

**Provider:** European Commission Joint Research Centre / Copernicus Emergency Management Service

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://data.jrc.ec.europa.eu/dataset/1d128b6c-a4ee-4858-9e34-6210707f3c81>

**Service root:** <https://jeodpp.jrc.ec.europa.eu>

**Api version:** River flood hazard maps for Europe and the Mediterranean Basin region v3.1.1 (2026-03-05)

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

- fetch_release_asset

### Path templates

- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP10_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP20_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP30_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP40_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP50_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP75_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP100_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP200_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_RP500_filled_depth.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_permanent_water_bodies.tif
- /ftp/jrc-opendata/CEMS-EFAS/flood_hazard/Europe_spurious_depth_areas.tif

**Parameter rules:** Static documentation contract only. The release is fixed to v3.1.1 and the 11 provider-listed TIFF filenames above. A future reviewed worker may map the single repository-controlled operation only to one exact allow-listed path; caller-selected paths, return periods outside the fixed list, directory crawling, alternate mirrors, query strings, arbitrary redirects and silent substitution with a newer release are forbidden. README.txt, CHANGELOG.txt and copyright.txt remain evidence/metadata and are not authorized as scientific raster assets by this contract.

## Response contract

### Expected media types

- image/tiff
- application/octet-stream

**Format:** Eleven fixed TIFF rasters: nine flood-water-depth maps for return periods 10, 20, 30, 40, 50, 75, 100, 200 and 500 years, plus permanent-water and spurious-depth masks. Provider documentation identifies WGS84, 3 arc seconds (~90 m), and flood-water depth in metres for the hazard rasters.

**Scientific semantics:** This is modelled river-flood hazard for the European extended domain, produced from LISFLOOD hydrology and LISFLOOD-FP inundation modelling for basins greater than 150 km2; it is not an official national flood hazard map or an observed event footprint. The v3.1.1 release corrected modelling/DEM-related artefacts. The permanent-water layer is material for residual coastal flooding, and the spurious-depth layer marks areas where depths above 10 m in small channels for RP10 plus a 2 km buffer may reflect hydraulic-model, resolution or DEM limitations. Preserve release version, return period, units, projection, masks and upstream MERIT-DEM, MERIT-HYDRO and EFAS v5.0 lineage in every derived use.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `52428800`

**Retry policy:** none

**Rate limit notes:** The JRC catalogue and provider README document anonymous public access, but this review did not establish a separate numeric automation budget for the static file host. This documented-only contract authorizes no HEAD, GET, Range request, retry loop, directory crawl or bulk mirror.

**Mutability notes:** Scientific identity is pinned to dataset v3.1.1 dated 2026-03-05 and DOI/PID evidence. The provider directory is a delivery route whose contents can change over time. Any later acquisition must re-check README/CHANGELOG/copyright, freeze requested and final URL identity, retrieval UTC, byte count and SHA-256, verify the selected filename belongs to v3.1.1, and keep masks/version semantics bound to the acquired asset.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The JRC Data Catalogue identifies CC BY 4.0 use conditions and anonymous/no-limitations access; the provider copyright notice licenses copyright and sui-generis rights under CC BY 4.0 with attribution and change indication. Dataset reuse is therefore verified, including redistribution under the licence conditions. No separate automation/service policy or numeric request entitlement for the JEODPP static host was established here, so execution remains disabled. Any persisted raster sample still requires exact asset identity, provenance, attribution and repository publication review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://data.jrc.ec.europa.eu/dataset/1d128b6c-a4ee-4858-9e34-6210707f3c81>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/README.txt>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/CHANGELOG.txt>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/copyright.txt>
- <https://doi.org/10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81>
- <https://creativecommons.org/licenses/by/4.0/>

**Notes:** Issue \#257 access contract only, after parent landscape merge \#256. No provider request, raster byte, parser, adapter, admission promotion, model-input authorization or publication decision is introduced. A later exact-byte canary must select one fixed release asset under a separately reviewed acquisition task and preserve uncertainty masks rather than silently treating masked/problem areas as clean flood-depth observations.
