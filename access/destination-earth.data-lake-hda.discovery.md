<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/destination-earth.data-lake-hda.discovery.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `destination-earth.data-lake-hda.discovery.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** destination-earth.data-lake-hda.discovery

## Source ids

- destination-earth.data-lake

**Provider:** Destination Earth Data Lake / European Commission

**Interface type:** stac

**Status:** documented_only

**Documentation url:** <https://destine-data-lake-docs.data.destination-earth.eu/en/latest/dedl-discovery-and-data-access/Harmonized-Data-Access/Harmonized-Data-Access.html>

**Service root:** <https://hda.data.destination-earth.eu>

**Api version:** Harmonised Data Access API / recommended STAC API v2 path; STAC API 1.0.0

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

- list_services
- get_stac_root
- get_conformance
- list_collections

### Path templates

- /services
- /stac/v2
- /stac/v2/conformance
- /stac/v2/collections

**Parameter rules:** Documentation-only anonymous discovery contract. No request is authorized yet. A future reviewed discovery adapter may issue only parameter-free GET requests to the four repository-controlled paths above. Callers must not supply service IDs, collection IDs, item IDs, free-text queries, bbox/datetime, CQL2/query expressions, sort clauses, paging, order payloads, data-asset paths, federation backends, URLs, headers or credentials. \`/stac\` legacy paths are explicitly excluded because current provider documentation marks the legacy STAC interface deprecated in favour of \`/stac/v2\`. Item search/browsing, \`/stac/v2/search\`, \`/collections/\{collectionId\}/items\`, \`/data/...\`, ECMWF ordering, notifications and any private/restricted collection access are outside this contract.

## Response contract

### Expected media types

- application/json

**Format:** Destination Earth HDA service-discovery and STAC API v2 catalogue metadata responses. The allowed operations expose infrastructure/service descriptions, STAC capabilities/conformance and collection metadata only; no STAC Item or provider data asset is within the response contract.

**Scientific semantics:** The Destination Earth HDA is a federated access infrastructure, not a homogeneous scientific dataset. A collection listing only establishes that a provider collection is discoverable through the HDA service; it does not establish scientific variable semantics, model generation, scenario/member identity, temporal/spatial validity, quality, licence, redistribution rights or suitability for catastrophe-model use. Every future OpenCatastrophe scientific consumer must pin a concrete collection and then separately freeze its model/product version, variables, scenario/member, spatial/temporal request, item/asset identity, processing lineage and collection-specific rights before any item search or download. Digital Twin outputs and other restricted collections can have additional permission boundaries and must never inherit authority from this generic discovery contract.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `1048576`

**Retry policy:** none

**Rate limit notes:** Current HDA documentation publishes default authenticated-service quotas including 4 requests per second, 20 Mbps per connection and 6 TB/month in the general API guide, with role-specific quota documentation also available. This discovery contract intentionally authorizes no request and needs no high-volume quota. Any future anonymous metadata probe should be a single request with no paging/retry loop. Authenticated item/data access must be designed separately under least-privilege credentials and provider quotas.

**Mutability notes:** The HDA is a live federation whose collection catalogue and backend mappings can change independently of this repository. The stable interface choice reviewed here is the recommended \`/stac/v2\` API family; the provider marks legacy \`/stac\` deprecated. Any future metadata probe must bind retrieval UTC, final URL, response byte count/SHA-256 and collection identifiers observed at that time. A collection discovered today must not be assumed to retain identical items, backend, queryables, access policy or scientific content later.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** HDA is an access federation and does not supply one provider-wide dataset licence for all collections. This review establishes technical documentation for anonymous discovery only and does not resolve HDA service automation/commercial terms or the rights of any discovered collection. Collection/item/asset rights must be reviewed individually before data access, persistence, redistribution or model use. Public collection metadata must not be interpreted as permission to download or republish underlying data.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://hda.data.destination-earth.eu/docs/>
- <https://destine-data-lake-docs.data.destination-earth.eu/en/latest/dedl-discovery-and-data-access/Harmonized-Data-Access/API-Architecture/API-Architecture.html>
- <https://destine-data-lake-docs.data.destination-earth.eu/en/latest/dedl-discovery-and-data-access/Harmonized-Data-Access/API-Guide/Authentication-And-Quotas.html>
- <https://destine-data-lake-docs.data.destination-earth.eu/en/latest/dedl-discovery-and-data-access/Harmonized-Data-Access/API-Guide/Services-and-Data-Discovery.html>
- <https://destine-data-lake-docs.data.destination-earth.eu/en/latest/dedl-discovery-and-data-access/Harmonized-Data-Access/API-Guide/Data-Access.html>

**Notes:** Bounded infrastructure-discovery documentation for Issue \#266 / \#173. Current provider authentication guidance states that public service/collection discovery does not require authentication, while item search/browsing and data access use DestinE authentication; access tokens are documented at about 10 hours and some Digital Twin Outputs require additional approval. This contract intentionally stops before those credential/data boundaries. No provider request, token, STAC Item, data byte, adapter, workflow, admission promotion or publication decision is introduced.
