<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/jp.mlit.plateau.graphql.citygml-shinjuku2024.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `jp.mlit.plateau.graphql.citygml-shinjuku2024.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** jp.mlit.plateau.graphql.citygml-shinjuku2024

## Source ids

- jp.mlit.plateau.citygml.3d-city-models

**Provider:** Japan Ministry of Land, Infrastructure, Transport and Tourism (MLIT) / PLATEAU experimental catalogue

**Interface type:** other_documented_machine_interface

**Status:** documented_only

**Documentation url:** <https://docs.plateauview.mlit.go.jp/api/graphql/schema/>

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

- document_one_fixed_city_year_graphql_metadata_projection

### Path templates

- /datacatalog/graphql

**Parameter rules:** DOCUMENTATION ONLY; NO live GraphQL POST is authorized. Future separate rights-reviewed call would have a single fixed read-only GraphQL operation: query OcShinjuku2024 \{ citygmlDatasets(input: \{cityCodes: \["13104"\], years: \[2024\]\}) \{ id cityCode prefectureCode year registrationYear url compositeUrl featureTypes metadataZipUrls \} \}. Require exact submitted query identity, exact municipality/year, no variables, arbitrary fields, aliases, introspection, mutations, pagination, retries, dynamic query injection, credentialed access or ZIP URL following. Provider schema is experimental and may change. An offline synthetic response preflight is available; this is not a request runner.

## Response contract

### Expected media types

- application/json

**Format:** GraphQL JSON data.citygmlDatasets array for the exact documented nine-field CityGMLDataset projection: id, cityCode, prefectureCode, year, registrationYear, url, compositeUrl, featureTypes and metadataZipUrls. There is NO GraphQL fileSize field in the official CityGMLDataset type; source ZIP byte size is unknown until a separate, rights-reviewed original receipt. Any provider errors fail closed.

**Scientific semantics:** The exact 2024 fiscal-year city model catalogue record is a release candidate only; cityCode is 13104 (Shinjuku). The native GraphQL ID is independent of the municipality code, and prefectureCode must be 13. CityGMLDataset has NO fileSize field: do not infer CMS original ZIP bytes from REST G-Spatial archives or metadataZipUrls. compositeUrl must pin city/year, never latest. Building feature presence alone does not prove coverage, height availability, vulnerability, insured values, independent origin or commercial reuse rights.

## Operational constraints

**Timeout seconds:** `15`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** GraphQL query complexity limits and response size apply. If separately authorized, enforce an exact static query body, fixed host/DNS and response-size cap before parsing; do not use this T0 contract as request permission.

**Mutability notes:** Experimental schema is subject to changes without notice or SLA. Pin query bytes/code SHA and response bytes SHA-256, UTC, fiscal-year record and CMS original identity in a separately reviewed T1 receipt; do not equate stable redirect URL with immutable original bytes.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://www.mlit.go.jp/plateau/faq/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Public technical API documentation and general PLATEAU open-data principles do not establish endpoint-specific automation rights or municipality/version-level source redistribution. This contract records a potential bounded metadata query only. No model/data/raw distribution permission is conferred.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://docs.plateauview.mlit.go.jp/api/graphql/>
- <https://docs.plateauview.mlit.go.jp/api/graphql/schema/>
- <https://docs.plateauview.mlit.go.jp/api/>

**Notes:** Official GraphQL schema rechecked 2026-11-01: unsupported fileSize removed from exact query, replaced by documented prefectureCode and metadataZipUrls. Non-executable documented candidate for one filtered municipality/year. No GraphQL POST, network receipt, provider source-file read, extraction, enrolment, data admission or model execution.
