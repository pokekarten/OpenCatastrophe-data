<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.coops.water-levels.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.coops.water-levels.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.coops.water-levels

## Source ids

- noaa.coops.water-levels

**Provider:** NOAA Center for Operational Oceanographic Products and Services (CO-OPS)

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://api.tidesandcurrents.noaa.gov/api/prod/>

**Service root:** <https://api.tidesandcurrents.noaa.gov>

**Api version:** CO-OPS Data API v1

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- bounded_water_level_observations

### Path templates

- /api/prod/datagetter

**Parameter rules:** Future execution must be repository-constructed and bounded to one explicitly reviewed CO-OPS station, product=water_level, a short fixed begin_date/end_date interval, datum, time_zone, units, application identifier and format=json. Callers must not supply a host, arbitrary path, headers, station identifier, product, datum, time zone, units, date range, application value or unrestricted query parameters. This static contract intentionally does not choose those scientific parameters; they require exact source/asset review before a probe is enabled.

## Response contract

### Expected media types

- application/json

**Format:** NOAA CO-OPS Data API JSON response for bounded water-level observations.

**Scientific semantics:** CO-OPS water-level values are station observations whose interpretation depends on the requested station, product, datum, time zone, units and provider verification/quality state. Connectivity alone does not establish a hazard event, spatial footprint, return period, modelled loss or insured loss. Any later scientific use must preserve the exact request parameters, observation timestamps, datum and provider quality/verification semantics rather than treating the values as interchangeable generic sea level.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `1048576`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific request-rate assumption is made. Future execution must remain a small single-station bounded query and must not widen this contract into bulk harvesting.

**Mutability notes:** Operational observations and their quality/verification state can change. Every future receipt must bind retrieval UTC, exact trusted execution-code identity, normalized request identity, response byte count and SHA-256; scientific use must separately freeze the station/product/datum/time-zone/date-range identity it actually consumes.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The CO-OPS disclaimer states that information presented on government servers is considered public domain unless specifically annotated otherwise and may be used freely by the public. For reproduction or re-dissemination, NOAA/NOS requests attribution, and modified content must not be presented as official government material. This dataset-rights and redistribution finding does not establish a CO-OPS API-service-terms or commercial-automation ceiling: those remain separately unreviewed/unknown, so this contract remains documented-only with no probe authorized.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://api.tidesandcurrents.noaa.gov/api/prod/>
- <https://api.tidesandcurrents.noaa.gov/api/prod/responseHelp.html>
- <https://tidesandcurrents.noaa.gov/disclaimers.html>

**Notes:** Static access contract only. Issue \#173 records that the NOAA CO-OPS Data API connection has previously been observed live, but that observation is not promoted here into a reusable execution receipt. No provider request, sample, external byte, workflow, adapter or admission change is introduced. Dataset rights and redistribution are now recorded from the authoritative CO-OPS disclaimer, while API-service/commercial-automation policy remains separately fail-closed. The next review must still freeze one scientifically meaningful station/product/datum/time-zone/date-range recipe before status can advance beyond documented_only.
