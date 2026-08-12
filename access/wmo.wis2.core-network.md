<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/wmo.wis2.core-network.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `wmo.wis2.core-network.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** wmo.wis2.core-network

## Source ids

- wmo.wis2

**Provider:** World Meteorological Organization and participating WIS2 Global Service operators

**Interface type:** mqtt_http

**Status:** documented_only

**Documentation url:** <https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/wmo-information-system-wis/wis2-overview>

**Service root:** `null`

**Api version:** WIS2 operational network

## Access scope

- metadata
- catalogue
- realtime

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- discover_core_datasets
- subscribe_core_notifications
- download_core_data

### Path templates

- /

**Parameter rules:** This is a federation-level documentation contract, not an executable endpoint contract. Any future implementation must first select one authoritative WIS2 Global Discovery Catalogue, Global Broker or Global Cache from the current WMO Global Services registry and bind its centre identifier and exact HTTPS/MQTT endpoint. Only WIS2 topics and discovery records explicitly classified as \`core\` are in scope. The selected topic, centre ID, discovery metadata identifier, canonical data link and retrieval time must be fixed before payload retrieval. Recommended-data topics, provider-node fallbacks, caller-supplied brokers/hosts/paths, arbitrary topic wildcards beyond a preregistered core namespace, credentials/tokens and unrestricted recursive harvesting are outside this contract and require a separate provider/license-specific review.

## Response contract

### Expected media types

- application/json
- application/octet-stream

**Format:** WIS2 Notification Message and WCMP2 discovery metadata, plus provider-defined core data payloads referenced by canonical HTTPS links.

**Scientific semantics:** WIS2 is a federated dissemination and discovery network, not one homogeneous scientific dataset. A WIS2 notification or discovery record establishes network provenance and a provider-declared route to data; it does not make the referenced payload scientifically homogeneous, immutable or fit for catastrophe modelling. Future evidence must preserve the publishing centre, WIS2 topic, data-policy class, discovery metadata identifier, canonical link, observation/product identity, units, quality/status flags, temporal semantics and the original data provider. This contract covers only the network transport/discovery boundary for \`core\` data and does not collapse station observations, forecasts, analyses, hydrology or other Earth-system products into one observation class.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `5242880`

**Retry policy:** bounded_backoff

**Rate limit notes:** No OpenCatastrophe request-rate or subscription entitlement is assumed from public WIS2 availability. No provider request is authorized by this documentation-only contract. Any later implementation must select one registered Global Service, use a narrowly preregistered core topic or discovery query, bound message/payload counts and bytes, and avoid broad wildcard subscriptions or recursive cache harvesting unless separately reviewed.

**Mutability notes:** WIS2 is operational and continuously publishes notifications, discovery metadata and data. Global Service operators and endpoints can change, and source records can be updated. Any future receipt must bind retrieval UTC, exact selected Global Service centre ID and endpoint, WIS2 topic, notification/discovery identifier, canonical data URL, response byte count and SHA-256 where bytes are retrieved, plus the provider/product identity needed for scientific reproducibility.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://public.wmo.int/wmo-unified-data-policy-resolution-res1>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** This contract is intentionally limited to WIS2 data explicitly classified as \`core\`. WMO's Unified Data Policy and WIS2 guidance describe core data as free and unrestricted, without charge and without conditions on use; Global Caches make core data available without access restrictions. Recommended data are different: they may carry conditions/licences and access controls, are not cached by Global Caches and are outside this contract. The data-policy clearance for core payloads is not treated as proof of separate service/API automation terms for every Global Broker, Discovery Catalogue or Cache, so service execution and commercial automation remain fail closed until independently reviewed.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/wmo-information-system-wis/wis2-overview>
- <https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/wmo-information-system-wis/wis-20-global-services>
- <https://public.wmo.int/wmo-unified-data-policy-resolution-res1>
- <https://docs.wis2box.wis.wmo.int/en/latest/user/recommended.html>

**Notes:** Static WIS2 core-network access contract only. It documents the provider's federated MQTT/HTTP discovery-notification-cache architecture and the core-versus-recommended data-policy split without selecting or contacting a live Global Service. No MQTT subscription, Discovery Catalogue query, Global Cache download, provider-node request or external data byte was performed or persisted by this builder. A later executable proposal must first choose one exact Global Service endpoint and prove service-use/automation terms; any scientific sample must then receive dataset/product-specific provenance and fitness review beyond this network contract.
