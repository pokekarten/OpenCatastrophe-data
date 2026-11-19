<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/jp.mlit.plateau.citygml.3d-city-models.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `jp.mlit.plateau.citygml.3d-city-models.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** jp.mlit.plateau.citygml.3d-city-models

## Source ids

- jp.mlit.plateau.citygml.3d-city-models

**Provider:** Japan Ministry of Land, Infrastructure, Transport and Tourism (MLIT) / municipal publishers

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://docs.plateauview.mlit.go.jp/datasets/citygml/>

**Service root:** <https://api.plateauview.mlit.go.jp>

**Api version:** `null`

## Access scope

- catalogue
- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- list_plateau_datasets_metadata

### Path templates

- /datacatalog/plateau-datasets

**Parameter rules:** Only the provider-documented GET /datacatalog/plateau-datasets catalogue operation is recorded. There is NO executable request authorization in this contract. No free-form URL/host, query parameters, city selector, GraphQL mutation, ZIP redirect, large body, source file download, retries or pagination is approved. Future bounded metadata GET must separately validate current API-specific terms, response byte cap, timeout and redirect/DNS policy and freeze one municipality and year before original-asset retrieval.

## Response contract

### Expected media types

- application/json

**Format:** JSON catalogue listing CityGML releases, including city/prefecture codes, municipality, source year, registration year, specification, feature types, URLs and file size when available.

**Scientific semantics:** PLATEAU publishes municipal CityGML city-model releases with varying acquisition dates and LoD. Municipality/year is a source release selector, not a certificate of completeness. The API latest field can change as data are updated; exact release year, native identifier, geometry CRS, vertical datum and attribute missingness must be retained. CityGML LOD1 height abstractions, polygon overlap or construction-year fields must not be converted into insured properties or certified vulnerability/valuation data.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `1048576`

**Retry policy:** none

**Rate limit notes:** Provider describes this service as experimental and does not guarantee response schema, lifetime or service level. An unrestricted catalogue may exceed the proposed 64 KiB probe cap; do not execute until scope/response budget and terms can be proven. No request is authorized by this static contract.

**Mutability notes:** Dynamic catalogue entries and 'latest' redirect targets change. A future receipt must record UTC, selected exact city/year, canonical catalogue request, code SHA, full bounded response bytes/SHA-256 and authoritative municipal licence identity; no mutable latest value as a model asset identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://www.mlit.go.jp/plateau/faq/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** MLIT FAQ describes programme data as multi-open-licensed and commercially reusable in principle, but the exact municipality/year CityGML licence/attribution, experimental API service automation and OpenCatastrophe redistribution/publication scope have not yet passed separate reviews. Do not extrapolate general policy to the API or to all city data.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://www.mlit.go.jp/plateau/en/>
- <https://www.mlit.go.jp/plateau/faq/>
- <https://docs.plateauview.mlit.go.jp/datasets/citygml/>

**Notes:** Exact official host and catalogue route are now recorded as a non-executable T0 access path. No request, byte receipt, API readiness evidence, rights grant, source-data admission, building match, risk exposure import or model execution was performed.
