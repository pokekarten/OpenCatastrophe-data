<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/dwd.cdc.extreme-wind.http-file.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `dwd.cdc.extreme-wind.http-file.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**Schema version:** 1.0.0

**Access id:** dwd.cdc.extreme-wind.http-file

## Source ids

- dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03

**Provider:** Deutscher Wetterdienst (DWD) / Climate Data Center

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/>

**Service root:** <https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind>

**Api version:** v24.03 dataset description; exact raw file identity remains file-specific

## Access scope

- metadata
- sample
- bulk

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_historical_directory
- fetch_exact_historical_file
- fetch_metadata_file

### Path templates

- /historical/
- /meta_data/

**Parameter rules:** This is a file/directory interface, not REST. A future adapter must resolve exact provider filenames from the trusted DWD directory, reject arbitrary hosts and traversal, prefer the versioned quality-controlled historical class for frozen research, and bind each selected file to retrieval time, byte count and SHA-256 before use.

## Response contract

### Expected media types

- application/zip
- text/html
- text/plain

**Format:** Provider directory metadata plus exact historical ZIP or metadata files selected by a reviewed bounded acquisition intent.

**Scientific semantics:** Historical, recent, now and meta_data are distinct operational classes. Historical files are the preferred first reproducible research subset; recent/now data must not be silently mixed into a frozen historical reference. Timestamp and station/instrument metadata semantics from the source review remain mandatory.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `1048576`

**Max sample bytes:** `52428800`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific request-rate assumption is made. Directory inspection and file acquisition must remain bounded and respect current DWD Open Data operational guidance.

**Mutability notes:** Directory contents can change and dataset-level v24.03 is not a substitute for exact raw-byte identity. Every acquired file requires exact filename/time coverage, retrieval time, byte count and SHA-256.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The admitted source review records CC BY 4.0 for this DWD CDC product and allows commercial reuse/redistribution subject to attribution and change indication. OpenCatastrophe still requires an exact asset-specific review before any raw bytes are published in Git.

## Probe contract

**Mode:** provider_specific

**Operation:** inspect_historical_directory

**Requires credentials:** `false`

### Expected evidence

- bounded provider directory response metadata
- resolved exact candidate filename without downloading unbounded data
- retrieval timestamp
- external_bytes_persisted=false

**Implementation decision:** build_later

**Reviewed at:** 2026-08-10

## Evidence urls

- <https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/>
- <https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf>

**Notes:** This contract intentionally models authoritative machine-readable HTTP file access rather than inventing a REST API. It proves the source-access abstraction covers non-API providers while preserving the existing metadata-only admission boundary.
