<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/copernicus.c3s.era5-land.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `copernicus.c3s.era5-land.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** copernicus.c3s.era5-land

## Source ids

- copernicus.c3s.era5-land

**Provider:** Copernicus Climate Change Service (C3S) / ECMWF

**Interface type:** provider_sdk

**Status:** blocked_credentials

**Documentation url:** <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=documentation>

**Service root:** <https://cds.climate.copernicus.eu>

**Api version:** `null`

## Access scope

- metadata
- sample
- bulk

## Authentication

**Mode:** api_key

**Credential reference:** CDS_PERSONAL_ACCESS_TOKEN

**Registration url:** <https://cds.climate.copernicus.eu/>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- retrieve_reviewed_era5_land_subset

### Path templates

- /api

**Parameter rules:** Use only the official cdsapi client with dataset short name reanalysis-era5-land. This static contract does not authorize a retrieval. A later execution review must freeze the exact variable set, year/month/day/hour, geographic area or full-grid choice, grid, data format and target representation before any provider request. The request identity must include dataset short name, DOI 10.24381/cds.e2161bac and every selection parameter. Do not substitute reanalysis-era5-land-timeseries or another ERA5/ERA5-Land representation under this operation. Caller-supplied service roots, arbitrary dataset names, unrestricted date ranges or unreviewed variables are outside this contract.

## Response contract

### Expected media types

- application/x-grib
- application/x-netcdf
- application/octet-stream

**Format:** Provider-generated ERA5-Land gridded output for an independently reviewed cdsapi request; the exact selected output format must be receipt-bound before execution.

**Scientific semantics:** ERA5-Land is a global land-surface reanalysis produced by replaying the land component of ERA5 at enhanced spatial resolution. Its land fields are model estimates forced by ERA5 atmospheric fields and are not direct station observations. Preserve the canonical gridded reanalysis identity, spatial/temporal resolution, variables, units, accumulation conventions and requested representation. The separate ARCO point time-series product reanalysis-era5-land-timeseries is a regridded analysis-ready representation that selects the nearest grid point and must not be treated as byte- or representation-equivalent to the canonical gridded product.

## Operational constraints

**Timeout seconds:** `120`

**Max probe bytes:** `1048576`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No repository-specific CDS quota or concurrency assumption is made. CDS request limits and queue behaviour can change; any future execution must use one separately reviewed bounded request and must not widen this static contract into an unrestricted CDS client.

**Mutability notes:** The ERA5-Land catalogue is updated daily and the live service is operationally mutable. Reproducible evidence must bind retrieval UTC, dataset short name, DOI, complete normalized request parameters, selected output representation, response byte count/SHA-256 and trusted execution-code identity. Historical scientific identity must not be inferred from a moving latest-service response alone.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://cds.climate.copernicus.eu/licences/terms-of-use-cds>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The current ERA5-Land CDS record identifies DOI 10.24381/cds.e2161bac and CC BY 4.0. CDS Terms of Use govern access to the service and defer Content use to the licence attributed to each dataset; the official CDS API documentation requires registration, a personal access token and manual acceptance of the dataset Terms of Use before download. This records the source/service rights ceiling only. It does not authorize repository publication of future response bytes or derived samples without exact asset, attribution, provenance and admission review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=documentation>
- <https://cds.climate.copernicus.eu/stac-browser/collections/reanalysis-era5-land>
- <https://cds.climate.copernicus.eu/how-to-api>
- <https://cds.climate.copernicus.eu/licences/terms-of-use-cds>
- <https://cds.climate.copernicus.eu/licences/licence-to-use-copernicus-products>
- <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=overview>

**Notes:** Static credential-gated source-access contract only. The official CDS product remains reanalysis-era5-land, ERA5-Land hourly data from 1950 to present, DOI 10.24381/cds.e2161bac. No CDS credential has been provisioned or used by this repository lane, no provider request is executed, and no external bytes are persisted. A later credentialed execution slice must recheck current CDS/API terms, freeze a tiny historical request before inspecting target values, and keep connectivity separate from scientific fitness, data admission and publication approval.
