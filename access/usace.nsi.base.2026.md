<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/usace.nsi.base.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `usace.nsi.base.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**Schema version:** 1.0.0

**Access id:** usace.nsi.base.2026

## Source ids

- usace.nsi.base.2026

**Provider:** U.S. Army Corps of Engineers Hydrologic Engineering Center

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/2026/api-reference-guide>

**Service root:** <https://nsi.sec.usace.army.mil>

**Api version:** NSI 2026 Base API

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- stats_bbox

### Path templates

- /nsiapi/stats

**Parameter rules:** Documentation-only future recipe; no repository network probe is authorized while current NSI 2026 reuse/API terms remain unresolved. If a later rights review authorizes execution, the smallest candidate operation is GET /nsiapi/stats with one repository-fixed small bounding box. Callers must never supply a host, arbitrary path, headers, or unrestricted query parameters; must never route through /internal/; and must not substitute the generic Download Tool unless its served release is independently confirmed as NSI 2026. Structure retrieval, POST geometry, broader extraction, or caller-selected spatial windows require separate review rather than widening this contract.

## Response contract

### Expected media types

- application/json

**Format:** USACE NSI statistics JSON for a bounding-box query; documented for future review only.

**Scientific semantics:** NSI 2026 Base is a nationally consistent modeled structure and exposure inventory for consequence analysis. The documented statistics endpoint aggregates modeled structure attributes; a successful future connection would not establish structure-level truth, legal or regulatory fitness, unbiased temporal change, or scientific adequacy for an insurance model. USACE documents substantial methodology and input-vintage changes between 2022 and 2026, so differences between releases must not be treated as a growth time series.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `1048576`

**Retry policy:** none

**Rate limit notes:** No automated dataset probe is authorized by this documentation-only contract. USACE recommends storing and reusing an inventory locally when the same inventory is needed repeatedly rather than repeatedly calling the API; any later execution must re-check current provider guidance and define a bounded cadence.

**Mutability notes:** USACE states that the API root has changed during the life of the service, so trusted repository configuration must own the service root rather than accepting a caller-supplied endpoint. NSI 2026 is live through the API, while the provider release notes state that the generic Download Tool may still serve 2022 data during its transition. A future authorized 2026 receipt must bind the exact API route, retrieval UTC, normalized request identity, trusted execution-code SHA, response byte count and SHA-256.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Current authoritative USACE 2026 material establishes public access to the public NSI API and distinguishes private USACE fields under /internal/, but this review did not establish a current canonical NSI 2026 licence or an explicit commercial-automation and redistribution grant. The canonical source landscape already records rights_review_status=not_reviewed. Historical 2022 guidance that the public NSI release removes licensed-derived fields is not promoted into a 2026 rights decision. Fail closed: this contract authorizes no live probe, response-byte persistence, redistribution, source admission, or publication.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/2026/api-reference-guide>
- <https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/2026/release-notes>
- <https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/2026/technical-documentation>
- <https://www.hec.usace.army.mil/confluence/nsi/technicalreferences/latest/frequently-asked-questions>

**Notes:** Static documented-only contract. It records an anonymous public NSI 2026 machine route and a future bounded /stats recipe while deliberately authorizing no probe until source/API reuse rights are resolved. Public /nsiapi/ and USACE-only /internal/ are distinct trust boundaries. A later rights review may separately propose executable probing; connectivity would still remain separate from source admission, response-byte publication, and scientific fitness.
