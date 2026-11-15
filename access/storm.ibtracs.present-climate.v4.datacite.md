<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/storm.ibtracs.present-climate.v4.datacite.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `storm.ibtracs.present-climate.v4.datacite.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** storm.ibtracs.present-climate.v4.datacite

## Source ids

- storm.ibtracs.present-climate.v4

**Provider:** DataCite Public REST API (metadata) for 4TU.ResearchData STORM IBTrACS v4

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://support.datacite.org/docs/api-get-doi>

**Service root:** <https://api.datacite.org>

**Api version:** DataCite Public REST API v2; singleton DOI 10.4121/12706085.v4

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

- retrieve_fixed_v4_doi_metadata

### Path templates

- /dois/10.4121/12706085.v4

**Parameter rules:** Exactly one opt-in, anonymous, repository-constructed GET for the fixed DOI 10.4121/12706085.v4 (no query parameters, redirects, pagination, retries, caller-supplied URLs, headers, tokens or alternative DOIs). DataCite publicly documents this singleton metadata API. Only public DataCite DOI JSON metadata may be read and SHA-receipted transiently. No 4TU/STORM track files, asset URLs, enumeration, polling or dataset bytes are authorized. A response identity/licence mismatch must fail closed.

## Response contract

### Expected media types

- application/json
- application/vnd.api+json

**Format:** DataCite public singleton DOI JSON:API metadata response (data.type=dois, exact data.id and attributes.doi).

**Scientific semantics:** This DOI identifies STORM IBTrACS present-climate v4, a 10,000-synthetic-year tropical-cyclone track catalogue. Version v4 corrects past track-duplication and storm-category mistakes. A DataCite JSON record neither enumerates exact downloadable v4 files nor verifies their native schema, units, storm/year identity or hashes. Synthetic tracks are not observed storm records; tracks alone are not spatial wind/surge footprints or insured losses.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** DataCite documents unrestricted anonymous public DOI metadata retrieval and rate limits; this contract is intentionally much narrower: one manual, fixed DOI GET per --probe-once, 20-second timeout, 256-KiB cap, no redirects, no retries, no recurring polling, no broad harvest. DataCite recommends identifiable User-Agent for frequent scripted calls; this runner does not make frequent requests. Never escalate automatically to dataset assets.

**Mutability notes:** DOI v4 is version-pinned but the public metadata record is mutable: original capture 2026-11-03, 14,825 bytes, SHA-256 90bbb620c7e04632e45b5c86c2998b3b023a55d246b56c2c7f09cc1a66c62f66, with provider reported metadata updated 2025-06-01T05:36:28Z. Any subsequent response must produce a new bounded original byte digest; a differing digest is not by itself evidence that STORM v4 track bytes changed. Track file inventory, sizes, checksums, native schema and year/event semantics remain separately unverified.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://support.datacite.org/docs/harvesting-datacite-doi-metadata>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** DataCite official public REST API guidance explicitly invites anonymous DOI metadata retrieval/harvesting, and the DataCite Data File Use Policy states its deposited bibliographic metadata are CC0 and available for any purpose. This source-specific judgement permits only one narrow public metadata GET; it is not general website scraping. General website Terms restrict systematic website scraping, which this fixed API canary does not perform. This metadata scope does not transfer CC0 to linked provider datasets, files, names/logos, sensitive elements or STORM track assets; separate 4TU source rights and exact-file admission remain necessary.

## Probe contract

**Mode:** metadata_get

**Operation:** retrieve_fixed_v4_doi_metadata

**Requires credentials:** `false`

### Expected evidence

- one exact public GET URL and response HTTP 200 with no redirect
- response application/json or application/vnd.api+json and at most 262144 bytes
- same-body response SHA-256, retrieval UTC and source access_id
- strict exact v4 DOI, dataset title, version, types and licence conflict gate
- no provider response body or data files persisted
- metadata-only receipt with source_admission_extended=false and model_input_approved=false

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-03

## Evidence urls

- <https://support.datacite.org/docs/api-get-doi>
- <https://support.datacite.org/docs/rest-api>
- <https://research.vu.nl/en/datasets/storm-ibtracs-present-climate-synthetic-tropical-cyclone-tracks-6/>
- <https://doi.org/10.4121/12706085.v4>
- <https://support.datacite.org/docs/harvesting-datacite-doi-metadata>
- <https://support.datacite.org/docs/rate-limit>
- <https://api.datacite.org/dois/10.4121%2F12706085.v4>
- <https://support.datacite.org/docs/datacite-data-file-use-policy>
- <https://support.datacite.org/docs/best-practices-for-integrators>

**Notes:** T1: one manual opt-in DataCite DOI metadata GET through research_runners/storm_v4_datacite_probe_v0.py with fail-closed exact contract and offline synthetic tests. No provider request has yet been successfully executed or receipted in this PR; probe_ready means executable contract, not verified live access. STORM track assets and actual CAT model data remain outside scope, unacquired and unapproved.
