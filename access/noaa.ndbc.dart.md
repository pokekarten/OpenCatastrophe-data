<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ndbc.dart.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ndbc.dart.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ndbc.dart

## Source ids

- noaa.ndbc.dart

**Provider:** NOAA National Data Buoy Center (NDBC)

**Interface type:** other_documented_machine_interface

**Status:** documented_only

**Documentation url:** <https://www.ndbc.noaa.gov/dart_data_access.shtml>

**Service root:** <https://www.ndbc.noaa.gov>

**Api version:** `null`

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- bounded_water_column_observations

### Path templates

- /dart_data.php

**Parameter rules:** Future execution must be repository-constructed and bounded to one independently reviewed operational DART station plus explicit UTC start and end dates. Although NDBC documents a provider maximum window of two years, an OpenCatastrophe probe/sample must use a much smaller predeclared window and may not accept an arbitrary station, host, path, headers or query parameters from a caller. Before enabling a probe, freeze the exact station/deployment and owner, confirm that it is operational rather than an internal/test station, and preserve the station state relevant to the requested period. The deterministic /data/historical/dart/ annual gzip archive is authoritative secondary access infrastructure but is intentionally not an executable path in this contract; exact archive-file acquisition requires a separately reviewed station/year/asset identity and media/rights decision.

## Response contract

### Expected media types

- text/plain

**Format:** NDBC DART plain-text water-column-height observations for one bounded station/date request.

**Scientific semantics:** NDBC documents UTC observation timestamps as YYYY MM DD hh mm ss, followed by measurement type T and water-column HEIGHT in meters after the documented pressure conversion. T=1 denotes 15-minute measurements, T=2 one-minute measurements and T=3 15-second measurements; bounded query output is documented in descending timestamp order. DART observations are deep-ocean bottom-pressure-derived water-column-height measurements, not a tsunami event catalogue or hazard footprint. Station ownership, deployment, location, payload and quality-control state can vary, including internationally owned stations whose data are not quality controlled by NDBC, so any later scientific use must bind the exact station/deployment provenance and preserve those limitations.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `2097152`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific request-rate assumption is made. Future execution must remain a single small station/date query and must not turn this documented endpoint into bulk harvesting. NDBC's documented two-year request ceiling is a provider limit, not an OpenCatastrophe sample target.

**Mutability notes:** NDBC station pages warn that payload types and station locations can change, and station operational state can change or be discontinued. Dynamic query results and directory listings are therefore discovery/access surfaces rather than durable byte identities. Every future receipt must bind retrieval UTC, exact trusted execution-code identity, station/deployment identity, normalized request identity, response byte count and SHA-256; a historical gzip file must additionally bind its exact station/year filename before use.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Anonymous access is an operational fact, not a rights decision. NDBC's DART station listing includes an Owner field and current station pages include internationally owned stations; for example station 32066 is owned and maintained by Ecuador INOCAR and is explicitly not quality controlled by NDBC. Do not infer one uniform NOAA ownership, licence, commercial-use permission or redistribution right from the NDBC host. Exact station/asset ownership and applicable terms must be independently reviewed before any probe, persistence or publication decision.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://www.ndbc.noaa.gov/dart/dart.shtml>
- <https://www.ndbc.noaa.gov/dart_data_access.shtml>
- <https://www.ndbc.noaa.gov/historical_data.shtml>
- <https://www.ndbc.noaa.gov/data/historical/dart/>
- <https://www.ndbc.noaa.gov/station_page.php?station=dartn>
- <https://www.ndbc.noaa.gov/station_page.php?station=32066>

**Notes:** Static access contract only. It selects NDBC's documented bounded DART dynamic query as the primary future machine operation and records the deterministic annual gzip archive as separate secondary infrastructure without enabling archive acquisition. No DART observation query, historical data file, sample or other external dataset byte was acquired or persisted by this builder. Internal/test stations such as DARTN are explicitly unsuitable as operational science samples under current provider labeling. Connectivity does not establish tsunami event identity, return period, hazard footprint, model fitness, damage/loss or insured loss. Before status can advance beyond documented_only, an independent review must freeze one operational station/deployment and short scientific window, resolve exact station/asset rights and API/service-policy scope, and define the expected provider response/media evidence for that exact request.
