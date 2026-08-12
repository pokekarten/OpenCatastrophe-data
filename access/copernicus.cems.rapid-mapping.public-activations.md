<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/copernicus.cems.rapid-mapping.public-activations.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `copernicus.cems.rapid-mapping.public-activations.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** copernicus.cems.rapid-mapping.public-activations

## Source ids

- copernicus.cems.on-demand-mapping

**Provider:** Copernicus Emergency Management Service (CEMS) / European Commission

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/>

**Service root:** <https://rapidmapping.emergency.copernicus.eu>

**Api version:** `null`

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

- list_public_activations
- get_public_activation

### Path templates

- /backend/dashboard-api/public-activations-info/
- /backend/dashboard-api/public-activations/

**Parameter rules:** The initial probe is repository-constructed only: list_public_activations fixes limit=1 and does not accept caller-supplied host, path, headers, offset, ordering, download URL or unrestricted query parameters. A future get_public_activation operation may accept exactly one validated public Rapid Mapping activation code and map it to the documented code query parameter; it must reject sensitive/restricted records and must not follow product download URLs under this contract. Any product ZIP, GeoPackage, GeoJSON, COG, vector-tile or other asset fetch requires a separately reviewed bounded sample/acquisition operation.

## Response contract

### Expected media types

- application/json

**Format:** Copernicus CEMS Rapid Mapping public dashboard JSON for activation catalogue or bounded activation metadata.

**Scientific semantics:** The public Rapid Mapping interface exposes operational emergency-mapping activation, AOI, product, imagery, layer and summary-statistics metadata. A successful probe demonstrates only anonymous service connectivity and response-contract compatibility. It does not make an activation immutable, prove product completeness or accuracy, clear sensitive/third-party content, or authorize a mapping product as universal ground truth.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `5242880`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific request-rate entitlement is assumed. The initial contract permits only a one-record catalogue probe and bounded single-activation metadata lookup; bulk harvesting, pagination and concurrent crawling are outside this contract.

**Mutability notes:** The service is an operational rolling catalogue. Activation status, AOIs, products, imagery, statistics and product versions can change. Every future execution receipt must bind retrieval UTC, exact trusted execution-code identity, normalized request identity, response byte count and SHA-256; scientific use must separately freeze the exact activation/AOI/product/version selected.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://mapping.emergency.copernicus.eu/terms-and-conditions/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The reviewed CEMS On-Demand Mapping terms permit reproduction, distribution, public communication, adaptation, modification and combination of covered data subject to source citation. Some CEMS data can be restricted and third-party information can carry separate terms. This contract therefore covers only documented public Rapid Mapping catalogue/metadata access and does not authorize persistence or redistribution of a future sensitive, restricted or third-party-bearing response without asset-specific review.

## Probe contract

**Mode:** catalogue_query

**Operation:** list_public_activations

**Requires credentials:** `false`

### Expected evidence

- provider success status without unsafe payload logging
- application/json response media type
- response byte count and SHA-256
- bounded one-record activation-catalogue response validation
- retrieval UTC and trusted execution-code identity
- external_bytes_persisted=false

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/>
- <https://mapping.emergency.copernicus.eu/about/how-to-harvest-cems-mapping-data/emergency-response-data/>
- <https://mapping.emergency.copernicus.eu/terms-and-conditions/>

**Notes:** Static access contract for a future trusted read-only adapter. The provider documentation exposes richer activation/product metadata and product download links, but this first contract intentionally stops at public catalogue and bounded activation metadata. Product acquisition must be added as a separate reviewed operation after exact product/version, sensitivity, third-party rights, size and provenance requirements are defined.
