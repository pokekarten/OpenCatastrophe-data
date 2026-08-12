<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec-jrc.rdh.disaster-losses.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec-jrc.rdh.disaster-losses.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec-jrc.rdh.disaster-losses

## Source ids

- ec-jrc.rdh.disaster-losses

**Provider:** European Commission Joint Research Centre / Disaster Risk Management Knowledge Centre / Risk Data Hub

**Interface type:** ogc_api

**Status:** blocked_credentials

**Documentation url:** <https://drmkc.jrc.ec.europa.eu/risk-data-hub-api/docs/>

**Service root:** <https://drmkc.jrc.ec.europa.eu/risk-data-hub-api/risk-data-hub-service>

**Api version:** Risk Data Hub API 3.1.0 / OGC API suite 1.0.1

## Access scope

- metadata
- catalogue
- bulk

## Authentication

**Mode:** bearer_token

**Credential reference:** JRC_RDH_API_TOKEN

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- get_losses
- get_hazard_taxonomy
- get_asset_taxonomy
- get_metric_taxonomy

### Path templates

- /losses/losses/items
- /admin/hazard/items
- /admin/asset/items
- /admin/metric/items

**Parameter rules:** Documentation-only contract. No request is authorized by this file. A future reviewed adapter must compile a typed bounded request and must never accept caller-supplied URLs, bearer material, arbitrary CQL/filter strings, vendorSpecificParameters, arbitrary property names, sort expressions, CRS identifiers or unbounded paging. For the first reviewed loss-page recipe, constrain format to a repository allow-list of GeoJSON/JSON/JSON-LD/CSV, keep limit small and repository-bounded, require offset &gt;= 0, and select only documented loss properties. Taxonomy operations must use their own documented property allow-lists. HTML is not an ingestion format. Any expansion to bbox/datetime/filter/sort or larger paging requires a separate security/science review.

## Response contract

### Expected media types

- application/geo+json
- application/json
- application/ld+json
- text/csv

**Format:** OGC API feature collections. GeoJSON is the documented default; JSON, JSON-LD and CSV representations are also documented. Loss rows and supporting hazard/asset/metric taxonomy collections must remain distinguishable by operation and schema.

**Scientific semantics:** The RDH Disaster Losses collection contains harmonised and derived European disaster-loss records compiled from multiple openly accessible upstream sources. A loss row binds event identity and dates, administrative geography, hazard taxonomy, asset, metric, dimension, quantity kind, source list and averaged loss values. \`value_event_src_average\` and \`value_2015_event_src_average\` have different value semantics and must not be conflated. These records are not raw insurance claims, not homogeneous observations from one reporting system and not independent ground truth; source coverage, reporting thresholds, national practices and harmonisation choices can create selection and measurement bias. Supporting hazard, asset and metric dictionaries are material interpretation context rather than optional labels.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** RDH documents authenticated programme-level API access and paging up to a provider maximum of 10000 items, but this contract authorizes no request, pagination loop or retry. No repository-specific rate budget or durable commercial automation entitlement was established. Any future canary must keep the page size intentionally tiny, be ephemeral by default and run only through the trusted credential/network plane.

**Mutability notes:** The API is a live service and the Disaster Losses dataset is maintained over time; the current JRC catalogue records annual update frequency, modification on 2026-05-06 and temporal coverage 1980-01-01 through 2025-03-31. Reproducible use must freeze API version, request fingerprint, retrieval UTC, returned feature/schema identity, source-list lineage and any relevant administrative-reference vintage. Do not treat a later API response as byte-identical to an earlier extraction merely because the endpoint is unchanged.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The JRC API documentation/service catalogue is public and identifies CC BY 4.0 at the API-service/documentation level, while the Disaster Losses dataset catalogue records the European Commission reuse notice and describes a curated multi-source collection. This review does not assume that the service-level CC BY statement relicenses every upstream loss record or resolves all third-party/database rights. Before any extraction is persisted or redistributed, review the concrete dataset/resource conditions, \`data_source_list\` lineage and any source-specific obligations. Separate authenticated API operational/commercial terms and rate policy also remain unresolved, so automation stays disabled.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://drmkc.jrc.ec.europa.eu/risk-data-hub-api/docs/>
- <https://data.jrc.ec.europa.eu/dataset/0030f450-6f4f-40c5-9390-66bb11dc2442>
- <https://doi.org/10.2905/JRC.DSZ3GW0>
- <https://data.jrc.ec.europa.eu/service/6551028a-2af8-4185-8db4-dbb353a2a9d6>

**Notes:** Bounded source-access documentation for Issue \#260 / \#173. RDH documents EU Login followed by an API TOKEN page and a bearer token lifetime of 10 hours; the real token must never enter Git, issue text, logs or receipts. No live request, credential provisioning, provider byte, parser, adapter, workflow, admission promotion or publication decision is introduced. A future first canary should prefer one tiny taxonomy page or tiny loss page only after credentials and source/API rights are intentionally cleared.
