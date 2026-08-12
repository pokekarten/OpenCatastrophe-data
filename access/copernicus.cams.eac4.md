<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/copernicus.cams.eac4.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `copernicus.cams.eac4.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** copernicus.cams.eac4

## Source ids

- copernicus.cams.eac4

**Provider:** Copernicus Atmosphere Monitoring Service (CAMS) / ECMWF

**Interface type:** provider_sdk

**Status:** blocked_credentials

**Documentation url:** <https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4?tab=documentation>

**Service root:** <https://ads.atmosphere.copernicus.eu>

**Api version:** `null`

## Access scope

- metadata
- sample
- bulk

## Authentication

**Mode:** api_key

**Credential reference:** ADS_PERSONAL_ACCESS_TOKEN

**Registration url:** <https://ads.atmosphere.copernicus.eu/>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- retrieve_reviewed_eac4_subset

### Path templates

- /api

**Parameter rules:** Use only the official cdsapi client with ADS dataset short name cams-global-reanalysis-eac4. This static contract does not authorize a retrieval. A later execution review must freeze one exact provider-generated request before any provider call: variable and authoritative parameter identity, analysis versus forecast, level type and exact level, date/time, forecast initialization and step where applicable, geographic area/grid selection, and output format/conversion mode. The request identity must include dataset short name cams-global-reanalysis-eac4, DOI 10.24381/d58bbf47 and every selection parameter. Do not substitute the separate EAC4 monthly-mean dataset, EGG4, a MARS-only route or another CAMS representation under this operation. Caller-supplied service roots, arbitrary dataset names, unrestricted dates, slow-access parameters or unreviewed variables are outside this contract.

## Response contract

### Expected media types

- application/x-grib
- application/x-netcdf
- application/octet-stream

**Format:** Provider-generated CAMS EAC4 sub-daily gridded output for an independently reviewed cdsapi request; native GRIB is preferred for the first byte-level receipt and any conversion mode must be receipt-bound before execution.

**Scientific semantics:** EAC4 is a global atmospheric-composition reanalysis produced with ECMWF model dynamics and 4D-Var data assimilation. It is model-plus-assimilation output, not a direct observation layer. ADS sub-daily fields are provided on a 0.75 degree by 0.75 degree grid. Analyses are 3-hourly; forecasts have initialization/step semantics that differ by field class and must not be collapsed into analysis values. Monthly means are a separate temporal product with a separate DOI and must not be substituted for the sub-daily dataset. Preserve selected variable, units, level, analysis/forecast type, timestamp/forecast step, grid/area and output representation in every future receipt.

## Operational constraints

**Timeout seconds:** `120`

**Max probe bytes:** `1048576`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No repository-specific ADS quota, queue position or concurrency entitlement is assumed. The supported CDS API is credentialed and provider-managed; any future execution must use one separately reviewed bounded request after intentional credential provisioning and manual dataset-Terms acceptance, and must not widen this static contract into an unrestricted ADS client.

**Mutability notes:** The ADS catalogue and service are operationally mutable. The EAC4 dataset record was updated on 2026-06-23 and current provider announcements extend sub-daily availability through December 2025, while older documentation can lag. Reproducible evidence must therefore bind retrieval UTC, dataset short name, DOI, complete normalized request parameters, ADS catalogue/update context, selected output representation, response byte count/SHA-256 and trusted execution-code identity rather than infer scientific identity from a moving latest-service response.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://ads.atmosphere.copernicus.eu/licences/terms-of-use-ads>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The current ADS EAC4 record identifies DOI 10.24381/d58bbf47 and a CC-BY licence. ADS Terms of Use require registration for download and state that Content use follows the licence attributed to each dataset; the official CDS API documentation provides programmatic access after login/token setup, and the Copernicus Products licence permits lawful use including reproduction, distribution, communication, adaptation and combination with attribution. Manual acceptance of the dataset Terms of Use remains a precondition before download. This records the source/service rights ceiling only and does not authorize repository publication of future response bytes or derived samples without exact asset, attribution, provenance and admission review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4?tab=overview>
- <https://ads.atmosphere.copernicus.eu/how-to-api>
- <https://ads.atmosphere.copernicus.eu/licences/terms-of-use-ads>
- <https://ads.atmosphere.copernicus.eu/licences/licence-to-use-copernicus-products>
- <https://confluence.ecmwf.int/spaces/CKB/pages/83395896/CAMS%2BReanalysis%2Bdata%2Bdocumentation>
- <https://forum.ecmwf.int/t/cams-global-reanalysis-eac4-data-from-september-to-december-2025-now-available-on-the-ads/15099>

**Notes:** Static credential-gated source-access contract only. The supported public machine route is the ADS CDS API for cams-global-reanalysis-eac4, DOI 10.24381/d58bbf47. No ADS credential has been provisioned or used by this repository lane, no provider request is executed and no external bytes are persisted. A later credentialed execution slice must recheck current ADS/API terms and dataset-form request options, freeze one tiny historical sub-daily request before inspecting target values, prefer native GRIB for the first byte-level receipt, and keep connectivity separate from scientific fitness, data admission and publication approval.
