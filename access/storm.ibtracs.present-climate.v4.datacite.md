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

**Status:** documented_only

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

**Parameter rules:** DOCUMENTATION-ONLY, NOT AN AUTHORIZED LIVE PROBE. One exact anonymous DataCite GET metadata record for DOI 10.4121/12706085.v4 is documented. Do not add query parameters, paging, search, arbitrary DOI, host, redirects, API tokens or caller-selected URL; the offline validator takes locally captured bytes and independent SHA-256. No 4TU file-list, download, or track-byte request is authorized by this contract.

## Response contract

### Expected media types

- application/json

**Format:** DataCite public singleton DOI JSON:API metadata response (data.type=dois, exact data.id and attributes.doi).

**Scientific semantics:** This DOI identifies STORM IBTrACS present-climate v4, a 10,000-synthetic-year tropical-cyclone track catalogue. Version v4 corrects past track-duplication and storm-category mistakes. A DataCite JSON record neither enumerates exact downloadable v4 files nor verifies their native schema, units, storm/year identity or hashes. Synthetic tracks are not observed storm records; tracks alone are not spatial wind/surge footprints or insured losses.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** No live DataCite call is authorized by this documentation-only contract. DataCite public singleton DOI access is documented; any T1 request requires a separate terms and bounded execution review, no bulk harvesting, redirects, arbitrary query, retry or polling.

**Mutability notes:** DOI version is fixed, but its mutable public metadata and links must not be mistaken for immutable versioned track files. A future receipt must retain retrieval UTC, exact URL, response byte count, SHA-256, parsed DOI/title/rights/version and separate 4TU original-file listing, size and SHA-256 once independently approved.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The existing admitted manifest and 2022 VU institutional v4 record identify STORM v4 as CC0-1.0 for the dataset; this does not make DataCite API automation terms reviewed or approve repository publication of any particular track file. The provider file-byte scope remains metadata-only until a separate exact asset review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-03

## Evidence urls

- <https://support.datacite.org/docs/api-get-doi>
- <https://support.datacite.org/docs/rest-api>
- <https://research.vu.nl/en/datasets/storm-ibtracs-present-climate-synthetic-tropical-cyclone-tracks-6/>
- <https://doi.org/10.4121/12706085.v4>

**Notes:** One bounded DOI-metadata route for already reviewed source storm.ibtracs.present-climate.v4; offline reader research_runners/storm_v4_datacite_preflight_v0.py validates raw response identity and independent SHA-256, with synthetic tests. No original STORM file or provider response has been fetched, stored in Git, or admitted as hazard/model input by this work.
