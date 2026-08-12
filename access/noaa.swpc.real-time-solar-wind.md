<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.swpc.real-time-solar-wind.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.swpc.real-time-solar-wind.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.swpc.real-time-solar-wind

## Source ids

- noaa.swpc.real-time-solar-wind

**Provider:** NOAA / NWS Space Weather Prediction Center

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://www.swpc.noaa.gov/products/solar-wind>

**Service root:** <https://services.swpc.noaa.gov>

**Api version:** `null`

## Access scope

- sample
- realtime

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- rtsw_mag_1m_json

### Path templates

- /json/rtsw/rtsw_mag_1m.json

**Parameter rules:** The initial probe is repository-constructed only: one HTTPS GET of the exact static path /json/rtsw/rtsw_mag_1m.json with no query string and no caller-supplied host, path, headers, spacecraft selector, time range or other parameters. The file is a rolling operational product rather than a caller-selected historical slice. Any later plasma, ephemeris, energetic-particle, archive or variable-window retrieval requires a separately reviewed bounded operation instead of widening this contract.

## Response contract

### Expected media types

- application/json

**Format:** NOAA SWPC rolling static JSON for recent real-time solar-wind magnetometer observations.

**Scientific semantics:** SWPC defines real-time solar-wind data as operational-quality in-situ observations from spacecraft upwind of Earth, typically near L1. The current service can contain observations from SOLAR-1, IMAP I-ALiRT, DSCOVR and ACE, and SWPC can change which spacecraft is active for a data type. Any consumer must preserve spacecraft identity and observation time and must not splice changing operational spacecraft into a single homogeneous sensor lineage. A successful probe demonstrates only service connectivity and response-contract compatibility, not continuity, completeness, immutable archival identity or scientific fitness for loss modelling.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `4194304`

**Max sample bytes:** `4194304`

**Retry policy:** none

**Rate limit notes:** NWS appropriate-use guidance requires requesting only needed data, respecting product refresh frequency and reacting conservatively to errors. This contract permits one fixed rolling-file capability probe with no immediate retry; it is not a harvesting or polling policy. Any recurring acquisition cadence requires separate review against current provider guidance.

**Mutability notes:** The static JSON is a rolling recent-data product and can change continuously; SWPC can also switch the active spacecraft used operationally. Every future receipt must bind retrieval UTC, exact trusted execution-code identity, normalized request identity, response byte count and SHA-256. NCEI archival products are the appropriate separate route when an immutable historical identity is required.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://www.weather.gov/disclaimer>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The SWPC product and services are NOAA/NWS government services. The NWS disclaimer states that NWS web information is public domain unless specifically noted otherwise and may be used without charge for lawful purposes, subject to non-endorsement, attribution/official-presentation and appropriate-use constraints. The current SWPC product documentation lists NOAA and NASA federal spacecraft for this data family. This records the source-service rights ceiling only; if SWPC later introduces separately licensed third-party observations, rights must be re-reviewed before use. The landscape candidate remains not admitted, so this contract does not authorize committing future response bytes or derived samples without exact asset/sample and provenance review.

## Probe contract

**Mode:** provider_specific

**Operation:** rtsw_mag_1m_json

**Requires credentials:** `false`

### Expected evidence

- provider success status without unsafe payload logging
- application/json response media type
- response byte count and SHA-256 within the bounded limit
- rolling RTSW magnetometer response-contract validation with spacecraft identity retained
- retrieval UTC and trusted execution-code identity
- external_bytes_persisted=false

**Implementation decision:** build_later

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://www.swpc.noaa.gov/products/solar-wind>
- <https://www.swpc.noaa.gov/content/data-access>
- <https://services.swpc.noaa.gov/json/rtsw/>
- <https://www.weather.gov/disclaimer>

**Notes:** Static contract only. SWPC documents separate recent-data JSON files for magnetometer, plasma and ephemeris observations and states that each contains data for all available spacecraft. This slice contracts only the fixed magnetometer JSON capability probe; it adds no adapter and performs no live provider fetch. Future hosted probing must reuse the reviewed trusted Actions network plane and must not treat connectivity as source admission, scientific validation or response-byte publication approval.
