<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.etopo.2022.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.etopo.2022.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.etopo.2022

## Source ids

- noaa.ncei.etopo.2022

**Provider:** NOAA National Centers for Environmental Information

**Interface type:** other_documented_machine_interface

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/products/etopo-global-relief-model>

**Service root:** <https://www.ngdc.noaa.gov>

**Api version:** `null`

## Access scope

- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- bedrock_15s_catalog

### Path templates

- /thredds/catalog/global/ETOPO2022/15s/15s_bed_elev_netcdf/catalog.html

**Parameter rules:** This initial contract documents only one repository-constructed HTTPS GET of the exact NCEI THREDDS catalogue linked by the authoritative ETOPO 2022 metadata record for 15 arc-second Bedrock elevation NetCDF tiles. No query string and no caller-supplied host, path, headers, tile ID, geographic subset, OPeNDAP constraint, Grid Extract parameters, format, resolution, surface model or variable are allowed. Ice Surface, sourceID, geoid, GeoTIFF and 30/60 arc-second products require separate scientific and asset selection before any data retrieval.

## Response contract

### Expected media types

- text/html

**Format:** NCEI THREDDS catalogue for ETOPO 2022 v1 15 arc-second Bedrock elevation NetCDF tiles.

**Scientific semantics:** ETOPO 2022 is a global relief model integrating topography and bathymetry rather than an observed hazard-event catalogue. NCEI publishes distinct Ice Surface and Bedrock surfaces, plus elevation, sourceID and geoid products at multiple resolutions; these are not interchangeable. This first catalogue boundary is deliberately limited to the 15 arc-second Bedrock elevation family. The authoritative metadata describes global WGS 84 / EPSG:4326 horizontal referencing and EGM2008 / EPSG:3855 vertical datum metadata and explicitly states that ETOPO is not suitable for navigation. Any later model input must preserve exact surface variant, variable, resolution, tile or subset identity, vertical reference and source lineage. Connectivity does not establish scientific fitness, event frequency, vulnerability, damage/loss or insured-loss semantics.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** No repository-specific THREDDS polling or rate-limit assumption is made. This documented-only contract authorizes no automated request. Any later catalogue probe or data retrieval must be separately reviewed for current NCEI service guidance and bounded to one preselected operation.

**Mutability notes:** ETOPO 2022 is the current named release and its authoritative metadata identifies DOI 10.25921/fd45-gt74 and metadata ID gov.noaa.ngdc.mgg.dem:etopo_2022. The dataset is complete with updates as needed, while service catalogue presentation may change independently. Any future receipt must bind retrieval UTC, exact trusted execution identity, final catalogue/data URL, selected product variant, byte count and SHA-256.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The authoritative NCEI metadata states that ETOPO 2022 data produced by NOAA are not subject to copyright protection in the United States and that NOAA waives potential copyright and related rights worldwide through CC0-1.0. NCEI requests the published dataset citation and states that the data are not for navigation. This records the dataset reuse ceiling only. Separate THREDDS/Grid Extract service automation terms were not independently established in this review, so commercial automation remains unknown and execution stays disabled. No repository persistence or publication of future data bytes is authorized without exact asset, provenance and admission review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://www.ncei.noaa.gov/products/etopo-global-relief-model>
- <https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.dem%3Aetopo_2022>
- <https://www.ngdc.noaa.gov/thredds/catalog/global/ETOPO2022/15s/15s_bed_elev_netcdf/catalog.html>
- <https://doi.org/10.25921/fd45-gt74>

**Notes:** Static source-access documentation only. No THREDDS probe, OPeNDAP request, Grid Extract call, tile selection, NetCDF/GeoTIFF acquisition, provider byte persistence, source admission, publication promotion or model execution is performed or authorized by this contract.
