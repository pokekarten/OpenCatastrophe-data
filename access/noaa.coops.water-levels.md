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

**Status:** probe_ready

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

**Parameter rules:** Frozen one-day probe only: begin_date=20260101&amp;end_date=20260101&amp;station=9414290&amp;product=water_level&amp;datum=MLLW&amp;time_zone=gmt&amp;units=metric&amp;application=OpenCatastrophe&amp;format=json. San Francisco station 9414290, 2026-01-01 UTC, six-minute observations relative to Mean Lower Low Water (MLLW), metric metres. Exactly one GET to /api/prod/datagetter, no redirects and at most 1048576 bytes. The script constructs the entire HTTPS URL; no user-supplied URL, host, station, dates, product, datum, timezone, units, headers or extra parameters. One-day metadata/shape probe only; no raw data persistence, crawling or model admission.

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

**Rate limit notes:** NOAA CO-OPS documents automated machine-to-machine API access but throttles high-volume clients. This probe issues one small historical-day request only, no retries, paging, scheduling, bulk crawl or other stations; any expansion requires distinct provider review.

**Mutability notes:** Six-minute water-level observations may be revised and verification/quality status can change. Retain query identity, retrieval UTC, response byte length, SHA-256 and script hash as the receipt; this probe does not persist raw observations. Datum MLLW is a tidal reference, not local flood depth above ground or NAVD88.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.tidesandcurrents.noaa.gov/web_services_info.html>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** CO-OPS government data are public domain unless specifically annotated, with attribution requested and no misrepresentation of modified material as official NOAA data. NOAA's published Web Services page explicitly supports automated machine-to-machine retrieval; the Data API page requires an application identifier and documents throttling and short 6-minute limits. These findings support this one fixed small anonymous operational capability probe, not unlimited/commercial bulk use, redistribution of other sources, scientific admission or insurer-loss modelling.

## Probe contract

**Mode:** provider_specific

**Operation:** bounded_water_level_observations

**Requires credentials:** `false`

### Expected evidence

- HTTP 200 anonymous fixed GET with expected JSON media type and station 9414290 metadata
- One UTC-day sequence of at most 240 six-minute timestamped, finite water-level observations with provider flags
- Small receipt containing retrieval UTC, exact fixed query, byte count, response SHA-256 and execution-script SHA-256; no provider measurements retained

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://api.tidesandcurrents.noaa.gov/api/prod/>
- <https://api.tidesandcurrents.noaa.gov/api/prod/responseHelp.html>
- <https://tidesandcurrents.noaa.gov/disclaimers.html>
- <https://www.tidesandcurrents.noaa.gov/web_services_info.html>

**Notes:** The fixed San Francisco 2026-01-01 CO-OPS request returned NOAA JSON water-level observations on 2026-11-02 (transient outside-repository connectivity check). A bounded repository probe with strict station/date/response validation is now specified, but a successful probe remains a connectivity/shape receipt only. No provider raw bytes, scientific validation, hazard catalogue, model input, insured exposure or insurance loss is admitted.
