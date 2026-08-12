<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/usgs.anss.comcat.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `usgs.anss.comcat.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** usgs.anss.comcat

## Source ids

- usgs.anss.comcat

**Provider:** U.S. Geological Survey (USGS) Earthquake Hazards Program / Advanced National Seismic System (ANSS)

**Interface type:** fdsn

**Status:** documented_only

**Documentation url:** <https://earthquake.usgs.gov/fdsnws/event/1/>

**Service root:** <https://earthquake.usgs.gov>

**Api version:** FDSN Event Web Service v1

## Access scope

- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- latest_earthquake_geojson

### Path templates

- /fdsnws/event/1/query

**Parameter rules:** No execution is authorized by this static contract. A later reviewed probe may construct exactly one bounded catalogue request with format=geojson, limit=1, orderby=time, eventtype=earthquake and nodata=204. Callers must not supply a host, arbitrary path, headers, callback, eventid, productcode/producttype, catalogue/contributor, geographic or time filters, pagination, include-all flags, deleted/superseded controls, or unrestricted query parameters. Product URLs exposed inside ComCat responses are downstream assets and must not be followed under this access contract.

## Response contract

### Expected media types

- application/json

**Format:** USGS FDSN Event GeoJSON FeatureCollection containing at most one current earthquake catalogue event for the bounded future connectivity recipe.

**Scientific semantics:** ComCat aggregates earthquake source parameters and associated products from contributing seismic networks. A response is an operational catalogue representation, not immutable event truth: preferred origins, magnitudes, review status and associated products can change, network coverage varies through space and time, and historic regional catalogues are not uniformly complete. Connectivity or receipt validity does not establish catalogue completeness, hazard-model fitness, surveyed damage, insured loss, or scientific approval of downstream products.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `1048576`

**Retry policy:** none

**Rate limit notes:** No request-rate entitlement is assumed and no execution is authorized here. USGS documents a query-result ceiling of 20000 events and recommends real-time GeoJSON feeds for automated display applications; any future OpenCatastrophe probe is intentionally limited to one event and must not be widened into bulk harvesting or a display/feed workload without separate review.

**Mutability notes:** ComCat is operational and mutable. Any future trusted receipt must bind retrieval UTC, exact execution-code identity, normalized request identity, response byte count and SHA-256. Scientific use must separately freeze the exact event identifier, preferred origin/magnitude state, contributor/catalogue context and any downstream product revision actually consumed.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** unknown

**Terms url:** <https://www.usgs.gov/media/files/advanced-national-seismic-system-anss-data-and-products-policy>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** ComCat aggregates parameters and products from USGS and contributing seismic networks/catalogues. USGS-authored federal data may be public domain, but current provider and USGS licensing guidance does not establish one uniform downstream redistribution grant for every partner/contributor record returned by an unrestricted ComCat query. Dataset reuse and redistribution therefore remain fail-closed and unknown for this contract. The FDSN Event API documentation establishes anonymous technical access only; API/service-use and commercial automation also remain unknown. This contract authorizes no provider request or publication of future response bytes.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://earthquake.usgs.gov/fdsnws/event/1/>
- <https://www.usgs.gov/programs/earthquake-hazards/anss-comprehensive-earthquake-catalog-comcat-documentation>
- <https://www.usgs.gov/media/files/advanced-national-seismic-system-anss-data-and-products-policy>
- <https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits>

**Notes:** Static documentation contract only. The source-access route and one bounded future catalogue recipe are recorded so later trusted execution can be reviewed without accepting arbitrary ComCat or product URLs. No USGS request or response byte is executed or persisted by this change. A future execution proposal must independently clear service/API-use terms, then use the existing trusted network plane and preserve event/product revision semantics; downstream ShakeMap, PAGER, moment-tensor or other product assets require their own bounded scientific/rights review.
