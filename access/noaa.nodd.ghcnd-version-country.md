<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.nodd.ghcnd-version-country.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.nodd.ghcnd-version-country.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.nodd.ghcnd-version-country

## Source ids

- noaa.ncei.ghcn-daily

**Provider:** NOAA National Centers for Environmental Information / NOAA Open Data Dissemination (NODD)

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://registry.opendata.aws/noaa-ghcn/>

**Service root:** <https://noaa-ghcn-pds.s3.amazonaws.com>

**Api version:** GHCN-Daily rolling 3.x; original ghcnd-version.txt and ghcnd-countries.txt objects

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- probe_version_and_country_metadata

### Path templates

- /ghcnd-version.txt
- /ghcnd-countries.txt

**Parameter rules:** Two fixed anonymous HTTPS GETs only: https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-version.txt and https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-countries.txt; no query, redirect, caller-selected path/station/year/URL/headers or object listing. Max 4096 bytes per object and total 8192 bytes. No retries. Strict UTF-8 parsing: one rolling update/version pair, unique two-character GHCN country codes with names. This metadata probe does not retrieve, authorize, or admit any GHCN observation files. Country codes are GHCN-native, NOT ISO-3166 without independent crosswalk.

## Response contract

### Expected media types

- application/octet-stream
- text/plain

**Format:** NOAA NODD original small UTF-8 text version metadata and GHCN-native country-code list; not observation CSV.

**Scientific semantics:** Version identity and GHCN country-code metadata are useful acquisition/lineage prerequisites only. The rolling update can change; GHCN country codes are a dataset-native vocabulary, not proof of ISO-3166 or insured geography. The station observation archive integrates heterogeneous sources and QA flags; no observation, hazard event, peril frequency, insurer exposure or model fitness is established by this probe.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `4096`

**Max sample bytes:** `4096`

**Retry policy:** none

**Rate limit notes:** Exactly two small anonymous public-object GETs on explicit --live, no retry, loop, directory traversal, listing, bulk station file or scheduled acquisition. NODD notes that AWS GHCN prefixes can change; exact paths must be re-reviewed rather than guessed.

**Mutability notes:** NOAA publishes a rolling GHCN-Daily update identity and fully reprocessed version. Record retrieval UTC, exact object paths, response byte counts and SHA-256 plus code SHA; never infer immutable snapshot identity from a rolling product label.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://registry.opendata.aws/noaa-ghcn/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** NOAA's NODD registry explicitly identifies GHCN-Daily data distributed by the public no-account noaa-ghcn-pds bucket as CC0-1.0, allows unrestricted reuse, asks for NOAA attribution and prohibits implying NOAA endorsement or mislabeling modified data as original. This particular contract is restricted to two NOAA-distributed public text metadata objects. It does NOT change the independently fail-closed rights review for other NCEI archival interfaces, contributor-level data semantics or future bulk observation ingestion. Public anonymous S3 GET is a static-object access route, not a claim about separate commercial API entitlements.

## Probe contract

**Mode:** metadata_get

**Operation:** probe_version_and_country_metadata

**Requires credentials:** `false`

### Expected evidence

- Two fixed HTTPS 200 responses with no redirects, query strings or user-controlled URLs
- Strict UTF-8 rolling GHCN 3.x update/reprocessed version marker and nonempty validated unique GHCN country codes
- Two bounded original-content SHA-256 and byte counts, retrieval UTC and script hash; no raw provider bytes persisted
- No weather observations or CAT model input admitted; no ISO-3166 country mapping inferred

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://registry.opendata.aws/noaa-ghcn/>
- <https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-version.txt>
- <https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-countries.txt>
- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt>

**Notes:** The fixed version and country-code endpoints responded with public text on 2026-11-02 during external live review. The exact Python program still needs its own hosted execution receipt; response visibility through a web viewer is not byte/hash proof. No external bytes are committed, no station observations are copied, and no Neon/model input admission is performed.
