<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.nodd.ghcnd-central-park-complete.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.nodd.ghcnd-central-park-complete.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.nodd.ghcnd-central-park-complete

## Source ids

- noaa.ncei.ghcn-daily

**Provider:** NOAA NCEI / NOAA Open Data Dissemination (NODD)

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://registry.opendata.aws/noaa-ghcn/>

**Service root:** <https://noaa-ghcn-pds.s3.amazonaws.com>

**Api version:** NOAA GHCN-Daily rolling 3.x; complete, provider-original single-station CSV research preflight

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- read_one_full_station_for_hash_and_schema

### Path templates

- /csv/by_station/USW00094728.csv

**Parameter rules:** One anonymous HTTPS GET for the fixed NOAA NODD object https://noaa-ghcn-pds.s3.amazonaws.com/csv/by_station/USW00094728.csv, without query string, Range, redirects, retries, credentials, caller-supplied station/URL or arbitrary headers. Require 200 and Content-Length matching original received body, between 1 MiB and 24 MiB; no Content-Range or compressed response. The full original file is read into transient bounded memory, SHA-256 hashed and parsed as original eight-column station CSV, but no original observations may be printed, persisted, committed to GitHub or admitted to Neon/model tables. One-shot workflow on reviewed merge only; pull requests use offline fixtures.

## Response contract

### Expected media types

- binary/octet-stream
- application/octet-stream
- text/csv
- text/plain

**Format:** The \*complete\* original NOAA NODD USW00094728.csv eight-column by_station product. Exact provider header ID,DATE,ELEMENT,DATA_VALUE,M_FLAG,Q_FLAG,S_FLAG,OBS_TIME is mandatory; subsequent provider-native rows are individually validated.

**Scientific semantics:** GHCN station records are observations with original physical element units, M/Q/S provenance flags, missing-value conventions and revisions. The file is a mutable rolling provider object; exact source bytes and header evidence are not a time-versioned scientific release. Validating all CSV rows, date-element uniqueness and source/quality flags does not establish climatological homogeneity, coverage, instrumental consistency, hazard-calibration relevance or insured exposure. Values are never converted, cleaned or model-admitted in this source preflight.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `25165824`

**Max sample bytes:** `25165824`

**Retry policy:** none

**Rate limit notes:** Exactly one fixed, whole-file original source GET, no retry, indexing, mirrors, S3 listing, other station IDs, bulk requests or periodic acquisition. Only the reviewed main workflow runs the live source check; PRs are fully offline.

**Mutability notes:** Record exact retrieval UTC, full response SHA-256, body bytes, Content-Length, ETag if valid, Last-Modified if present, first/last date, element/flag counts, code SHA. The separately acquired GHCN version marker is NOT automatically a cryptographically bound station-version manifest. On source changes compare full-file hashes, and do not silently reuse scientific interpretations.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://registry.opendata.aws/noaa-ghcn/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** This fixed NOAA NODD public GHCN product is catalogued as CC0-1.0, with attribution requested and no NOAA endorsement. The public right to fetch does not constitute scientific admission, validation of third-party source networks, availability guarantee or permission to mirror outside this reviewed source contract. Original bytes are not redistributed or persisted by this preflight.

## Probe contract

**Mode:** provider_specific

**Operation:** read_one_full_station_for_hash_and_schema

**Requires credentials:** `false`

### Expected evidence

- Exactly one direct HTTPS 200, fixed official station object, bounded Content-Length 1-24 MiB and exact full response byte count
- Full-original-body SHA-256, provider response ETag/Last-Modified metadata where safe, UTC retrieval and script SHA
- Original mandatory header, every record checked for station/date/element/signed integer value/M-Q-S flags/time, uniqueness of date-element, row counts and flagged/element statistics
- No raw observations saved/printed; no geographic insurance inference, scientific-quality admission or CAT model input

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://registry.opendata.aws/noaa-ghcn/>
- <https://github.com/awslabs/open-data-docs/blob/main/docs/noaa/noaa-ghcn/README.md>
- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme-by_station.txt>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41497232656>

**Notes:** After a successful 65536-byte first-original prefix probe, a single full original USW00094728.csv research preflight is separately reviewed here. Prior live prefix receipt observed 16,003,495 bytes on 2026-11-02; size is advisory only, not a hard-coded completeness claim. Provider can republish rolling records. A valid full-file receipt is not an approved modelling dataset.
