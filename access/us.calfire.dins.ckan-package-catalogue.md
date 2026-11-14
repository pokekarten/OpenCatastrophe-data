<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/us.calfire.dins.ckan-package-catalogue.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `us.calfire.dins.ckan-package-catalogue.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** us.calfire.dins.ckan-package-catalogue

## Source ids

- us.calfire.dins.structure-damage

**Provider:** California Department of Forestry and Fire Protection via the California Open Data CKAN catalogue

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://data.ca.gov/docs/developer-documentation>

**Service root:** <https://publish.data.ca.gov>

**Api version:** CKAN Action API 3, package_show for the exact DINS package UUID

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

- dins_package_show_catalogue

### Path templates

- /api/3/action/package_show

**Parameter rules:** Exactly one maintainer-triggered, read-only CKAN Action package_show metadata GET for fixed id=1fdaea07-4bcd-4795-aa88-cd72b98e8a03; immutable route, exactly one request, descriptive user agent, at most 65,536 original response bytes, timeout 30 seconds, no redirect/retry/authentication. Require original package ID/name, public/cc-by fields, frozen modified date and all eleven original resource IDs/formats. Respond to any drift with BLOCKED and review. No following returned resource URLs, ArcGIS queries, CSV/GeoJSON/ZIP downloads, feature IDs, address/APN/individual inspection reads, bulk harvesting, pagination, caller-selected host/URLs, parameters or headers. The historical 2026-11-01 body receipt is a reference only; this contract authorizes a bounded future \*metadata\* probe, not third-party source data retention.

## Response contract

### Expected media types

- application/json

**Format:** CKAN package_show JSON object success=true with one fixed CAL FIRE DINS package id/name, public accessLevel, cc-by metadata label, metadata_modified=2026-10-21T20:55:50.264159, and precisely 11 format/id-tagged resources. Resource URLs are metadata pointers, not permission to download assets.

**Scientific semantics:** This public catalogue metadata establishes a dataset listing, version marker and references to 11 published formats; it does NOT establish actual resource byte availability, inspection count, event identity, scientific coverage, commercial CAT reuse, building exposure denominator, claim loss, or provider feature service usage rights.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Provider documentation on 2026-11-12 lists 60 anonymous requests/minute/IP and asks automated clients to identify with descriptive User-Agent. This workflow deliberately allows ONE manual fixed metadata request only (not weekly polling), no retries, no bulk and no additional data resources. Separate review required before any higher cadence, feature access, raw sample retention or commercial bulk use.

**Mutability notes:** The package is mutable and includes resource IDs and metadata_modified; as captured at 2026-11-01T18:01:22Z the original UTF-8 JSON body length is 16916 bytes and SHA-256 is 1998a87aff518a059162d9c4faff3ce3c2e145f007323c6a91cf3fb3617927f8. Exact-byte replays may change and must fail closed against this snapshot rather than silently replace it.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://data.ca.gov/docs/developer-documentation>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** The official state developer docs explicitly allow public anonymous CKAN reads, describe automated access and a 60/minute/IP limit, and require a descriptive User-Agent for automation. CAL FIRE's exact DINS package page labels metadata public, no restrictions on public use and Creative Commons Attribution. 'allowed' here applies only to one bounded CKAN package metadata GET under these provider conditions; NOT to ArcGIS service, individual inspection details, personal/address/APN attributes, bulk commercial mining, raw feature redistribution or insurance/CAT modelling. Any upstream contributor rights exceptions still require asset-specific review.

## Probe contract

**Mode:** metadata_get

**Operation:** dins_package_show_catalogue

**Requires credentials:** `false`

### Expected evidence

- exact fixed CKAN package_show URL, one anonymous GET and descriptive User-Agent
- 200 application/json original response, &lt;=65536 bytes, no redirect/retry
- strict 11-resource public package metadata and 2026-10-21 reviewed snapshot identity
- retrieval UTC, request and original response SHA-256, contract/code identity
- no provider response text, URLs, addresses, contacts or original raw bytes retained
- research-only, model_input_approved=false, external_bytes_persisted=false

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-12

## Evidence urls

- <https://publish.data.ca.gov/api/3/action/package_show?id=1fdaea07-4bcd-4795-aa88-cd72b98e8a03>
- <https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data>
- <https://data.ca.gov/docs/developer-documentation>
- <https://data.ca.gov/docs/open-data-policy>
- <https://handbook.data.ca.gov/conditions-of-use/>

**Notes:** Authoritative state CKAN metadata route and individual provider DINS package were reviewed 2026-11-12. Exactly one manually dispatched bounded public metadata canary is enabled; original historical 16,916-byte SHA receipt and strict eleven-resource preflight are retained. A changed public package version must fail closed rather than silently update. Asset downloading, independent scientific damage modelling, commercial bulk and address/parcel access remain separate blocked gates; no data admission or Neon write.
