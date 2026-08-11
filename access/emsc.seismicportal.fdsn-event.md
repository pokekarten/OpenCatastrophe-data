<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/emsc.seismicportal.fdsn-event.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `emsc.seismicportal.fdsn-event.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** emsc.seismicportal.fdsn-event

## Source ids

- emsc.seismicportal.fdsn-event

**Provider:** Euro-Mediterranean Seismological Centre (EMSC) / SeismicPortal

**Interface type:** fdsn

**Status:** probe_ready

**Documentation url:** <https://www.seismicportal.eu/fdsn-wsevent.html>

**Service root:** <https://www.seismicportal.eu>

**Api version:** FDSN Event service /1; OpenAPI 2.2

## Access scope

- catalogue
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- latest_event_json

### Path templates

- /fdsnws/event/1/query

**Parameter rules:** The initial probe is repository-constructed only: format=json, limit=1, orderby=time, nodata=204, includeallorigins=false and includearrivals=false. Callers cannot supply a host, arbitrary path, headers, event identifier, catalogue, contributor, geographic filter, time range, pagination offset or unrestricted query parameters. Any later parameterized scientific query requires a separately reviewed bounded operation rather than widening this probe contract.

## Response contract

### Expected media types

- application/json

**Format:** EMSC SeismicPortal FDSN-event JSON response for one catalogue event.

**Scientific semantics:** This service exposes EMSC earthquake event parameters under the FDSN Event interface. A successful probe demonstrates only service connectivity and response-contract compatibility; it does not establish catalogue completeness, event accuracy, suitability for hazard calibration or an immutable scientific event identity. Event parameters may be updated as the operational catalogue evolves.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `1048576`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific request-rate assumption is made. The provider documents a maximum query limit of 20000 events; this contract intentionally fixes the probe limit to one event and must not be used for bulk harvesting.

**Mutability notes:** The EMSC event catalogue is operational and mutable. Every future probe receipt must bind retrieval UTC, exact trusted execution code, normalized request identity, response byte count and SHA-256; a later scientific run must separately freeze the event/product identity it actually uses.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.seismicportal.eu/terms.html>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The FDSN Event service documentation explicitly states that data provided by this service are distributed under CC BY 4.0. The general SeismicPortal terms note that service-specific datasets can carry CC BY 4.0 and direct users to each web-service documentation. This contract records that service-specific ceiling only; it does not authorize repository persistence/publication of future response bytes without the normal exact-asset/sample review and attribution/provenance evidence.

## Probe contract

**Mode:** catalogue_query

**Operation:** latest_event_json

**Requires credentials:** `false`

### Expected evidence

- provider success status without unsafe payload logging
- application/json response media type
- response byte count and SHA-256
- bounded one-event response-contract validation
- retrieval UTC and trusted execution-code identity
- external_bytes_persisted=false

**Implementation decision:** build_later

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://www.seismicportal.eu/fdsn-wsevent.html>
- <https://www.seismicportal.eu/fdsnws/event/1/docs>
- <https://www.seismicportal.eu/terms.html>

**Notes:** Static contract only. The provider documentation currently exposes query/count/catalog/contributor/version operations and JSON, QuakeML/XML and text outputs; this OpenCatastrophe slice deliberately contracts only one anonymous one-event JSON probe. No adapter or live network execution is added here. Future hosted probing must reuse the reviewed trusted Actions network plane and must not treat connectivity as admission, scientific fitness or publication approval.
