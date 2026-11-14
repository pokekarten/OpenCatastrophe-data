<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nl.knmi.kdp.hourly-validated-edr.v1.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nl.knmi.kdp.hourly-validated-edr.v1.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nl.knmi.kdp.hourly-validated-edr.v1

## Source ids

- nl.knmi.kdp.hourly-validated-edr.v1

**Provider:** Royal Netherlands Meteorological Institute KNMI

**Interface type:** ogc_api

**Status:** blocked_credentials

**Documentation url:** <https://developer.dataplatform.knmi.nl/edr-api>

**Service root:** <https://api.dataplatform.knmi.nl>

**Api version:** KNMI EDR v1, collection hourly-in-situ-meteorological-observations-validated; station/time coverage and wind parameters to be pinned

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** api_key

**Credential reference:** KNMI_EDR_API_KEY

**Registration url:** <https://developer.dataplatform.knmi.nl/apis>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_edr_validated_hourly_collection

### Path templates

- /edr/v1/collections/hourly-in-situ-meteorological-observations-validated

**Parameter rules:** Documentation-only, no automatic source request or caller-selected path, unbounded domain, secrets, crawler, bulk extraction or retries. Metadata path(s) are only candidate exact origins; actual provider GET requires independently reviewed provider machine-use terms, exact URL, byte cap, body hash and source-specific approved workflow.

## Response contract

### Expected media types

- application/json
- application/prs.coverage+json

**Format:** OGC EDR versioned collection metadata and eventual bounded station/time CoverageJSON only after registered credential and exact product rights review; no original readings requested.

**Scientific semantics:** Validated hourly in-situ observations are distinct from 10-minute near-real-time data and modeled WINS50. Need original parameter-name, height, gust definition, UTC intervals, station relocation/QC and collection vintage before independent ERA5 challenge.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** KNMI describes 200 requests/second and 1,000 requests/hour for registered EDR keys; use lower scoped budgets after commercial use and permission review, never assume a key exists.

**Mutability notes:** Collection coverage and station parameters vary; v1 path must remain versioned and original timestamps/metadata pinned.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** KNMI provides documented data-platform API and validates-hourly collection; exact collection's licence, attribution, restrictions on commercial automated insurance use and raw redistribution remain unreviewed. A separate EDR API key is required; Open Data API keys are NOT interchangeable.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://developer.dataplatform.knmi.nl/edr-api>
- <https://developer.dataplatform.knmi.nl/faq>
- <https://developer.dataplatform.knmi.nl/apis>

**Notes:** Blocked: no connected KNMI EDR account or original authenticated request receipt, response body or source-native sample. Never put tokens into repository, logs or prompts. Registered rate limits documented but are not a commercial-use right.
