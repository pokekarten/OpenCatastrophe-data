<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/wsv.pegelonline.rest-v2.dresden.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `wsv.pegelonline.rest-v2.dresden.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**Schema version:** 1.0.0

**Access id:** wsv.pegelonline.rest-v2.dresden

## Source ids

- wsv.pegelonline.elbe-dresden-discharge.2020-2023

**Provider:** Wasserstraßen- und Schifffahrtsverwaltung des Bundes (WSV) / PEGELONLINE

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://pegelonline.wsv.de/webservice/dokuRestapi>

**Service root:** <https://pegelonline.wsv.de/webservices/rest-api/v2>

**Api version:** v2

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- resolve_station_metadata

### Path templates

- /stations/\{station_uuid\}.json

**Parameter rules:** Only the frozen Dresden station UUID 70272185-b2b3-4178-96b8-43bea330dcae is allowed for this contract. resolve_station_metadata adds includeTimeseries=true and must not request currentMeasurement or measurement values. Callers cannot supply a host, arbitrary path, headers or unrestricted query parameters.

## Response contract

### Expected media types

- application/json

**Format:** PEGELONLINE REST-v2 station JSON parsed by scripts/parse_pegelonline_metadata.py.

**Scientific semantics:** The metadata response must resolve station 501060 / DRESDEN / ELBE and exactly one Q / ABFLUSS_ROHDATEN series in m³/s. The existing parser rejects currentMeasurement, station drift, Q-semantic drift, non-finite coordinates and incompatible sampling intervals.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `1048576`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific rate-limit assumption is made. Use one bounded metadata request for a probe and respect current provider documentation before increasing request volume.

**Mutability notes:** Live station metadata can change operationally. Every accepted probe receipt must record retrieval time, response byte count and SHA-256; frozen scientific identity is reviewed separately.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.pegelonline.wsv.de/webservice/downloads>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The paired source review records PEGELONLINE webservice/download data under Datenlizenz Deutschland – Zero – Version 2.0. Repository admission remains metadata-only; this contract does not authorize committing acquired measurement bytes.

## Probe contract

**Mode:** metadata_get

**Operation:** resolve_station_metadata

**Requires credentials:** `false`

### Expected evidence

- HTTP/provider success status without unsafe payload logging
- response media type
- response byte count and SHA-256
- strict parser result for the frozen station/Q metadata contract
- external_bytes_persisted=false

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-08-10

## Evidence urls

- <https://pegelonline.wsv.de/webservice/dokuRestapi>
- <https://www.pegelonline.wsv.de/webservice/downloads>
- <https://pegelonline.wsv.de/gast/hilfe>

**Notes:** This is the first concrete OpenCatastrophe source-access contract. It covers the already implemented metadata-only REST path, not the separate long-term target-value download. The long-term JSON acquisition route remains governed by the existing preregistered Dresden evidence workflow and requires exact byte-level acquisition receipts before use.
