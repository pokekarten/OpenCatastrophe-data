<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.nodd.ghcnd-central-park-range.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.nodd.ghcnd-central-park-range.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.nodd.ghcnd-central-park-range

## Source ids

- noaa.ncei.ghcn-daily

**Provider:** NOAA NCEI through NOAA Open Data Dissemination (NODD)

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://registry.opendata.aws/noaa-ghcn/>

**Service root:** <https://noaa-ghcn-pds.s3.amazonaws.com>

**Api version:** GHCN-Daily rolling 3.x; single-station provider-native CSV byte-range observation sample

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- probe_fixed_station_range

### Path templates

- /csv/by_station/USW00094728.csv

**Parameter rules:** One fixed public HTTPS GET to /csv/by_station/USW00094728.csv for GHCN station USW00094728 (New York Central Park); send only Range: bytes=0-65535 and Accept: text/csv, with no redirects, retries, query, caller-supplied host, station, filename, headers or sample expansion. Accept only HTTP 206 with Content-Range bytes 0-65535/TOTAL for TOTAL&gt;65536 and exactly 65536 returned bytes. Parse only complete CSV lines in this prefix; discard incomplete trailing line and never treat sample as complete annual/station history. No external data bytes persisted, no provider observations printed, no source/model admission.

## Response contract

### Expected media types

- application/octet-stream
- text/plain
- text/csv
- application/vnd.ms-excel

**Format:** First 65536 original bytes of one station-scoped GHCN-Daily provider-native CSV. Strict 8-column ID,DATE,ELEMENT,DATA_VALUE,M_FLAG,Q_FLAG,S_FLAG,OBS_TIME records, possible CSV header; this is only a byte-range sample.

**Scientific semantics:** Individual daily station ELEMENT values use NOAA element-specific units and represent local observation semantics, not event losses, calibrated catastrophe intensities or insured locations. Measurement, quality and source flags are essential; blank Q_FLAG does not prove scientific fitness or representativeness. The prefix begins at the earliest provider records and is not a representative or recent climate sample. Central Park observations cannot be inferred to describe New York exposure, insurer portfolios or catastrophe return periods. Exact station identity is needed as a research canary only.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Only one fixed anonymous range request, no bulk collection, pagination, retries or hourly automation; source data bytes are transient and never committed or inserted into Neon.

**Mutability notes:** GHCN-Daily is rolling and may be reprocessed. Report UTC retrieval time, requested byte range, total source size, SHA-256 of the returned 65536-byte prefix and parser-script SHA-256. Hash of a prefix is NOT the checksum of the full original file; pin the GHCN version separately when building a model.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://registry.opendata.aws/noaa-ghcn/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The NOAA NODD data registry expressly labels distributed GHCN Daily as CC0-1.0 with no use restrictions, attribution requested and no implication of NOAA endorsement. This specific single-station, 64-KiB range sample is compatible with public anonymous download. The NOAA-origin distribution rights do not warrant data completeness, source-agency homogeneity or scientific/model fitness, and do not justify unreviewed scraping of other providers.

## Probe contract

**Mode:** provider_specific

**Operation:** probe_fixed_station_range

**Requires credentials:** `false`

### Expected evidence

- One exact HTTPS 206 for fixed station CSV and Content-Range bytes 0-65535/TOTAL, no redirects
- Exactly 65536 original prefix bytes and SHA-256; strict UTF-8, strict station identity and eight original CSV fields
- Bounded row count and measurement/source/quality flag coverage in small metadata-only receipt; no raw weather values printed or stored
- UTC retrieval, provider rolling sample qualification, code SHA and all scientific/model admission flags false

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://registry.opendata.aws/noaa-ghcn/>
- <https://github.com/NOAA-Big-Data-Program/nodd-data-docs/blob/main/GHCN-D/Readme.md>
- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme-by_station.txt>

**Notes:** Prior NODD version/country metadata source-access contract is separate and already merged; this pilot attempts real original weather-observation CSV bytes only in a tightly bounded, read-only Range request. The fixed station path is defined by NOAA public NODD station distribution documentation; no claim of a successful exact range request is made before hosted run evidence.
