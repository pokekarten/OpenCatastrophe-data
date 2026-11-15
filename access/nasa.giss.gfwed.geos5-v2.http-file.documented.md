<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.giss.gfwed.geos5-v2.http-file.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.giss.gfwed.geos5-v2.http-file.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.giss.gfwed.geos5-v2.http-file.documented

## Source ids

- nasa.giss.gfwed.geos5.daily-fwi.v2.0

**Provider:** NASA Goddard Institute for Space Studies / GFWED

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://data.giss.nasa.gov/impacts/gfwed/>

**Service root:** <https://portal.nccs.nasa.gov/datashare/GlobalFWI>

**Api version:** v2.0 dataset path segment, HTTP file archive (not an API protocol version)

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

- inspect_published_example_file_path

### Path templates

- /v2.0/fwiCalcs.GEOS-5/Default/GEOS-5/2014/FWI.GEOS-5.Daily.Default.20140501.nc

**Parameter rules:** This is an exact provider-published example file path and evidence of a potential NetCDF acquisition route, NOT an executable OpenCatastrophe download operation. No HTTP HEAD/GET/Range, crawler, recursive archive walk, redirects, user supplied URL/path/date, credential use or storage of source bytes is allowed by this contract. Later independent authorization must pin the exact version, file date, expected response size, byte caps, terms and SHA-256 evidence.

## Response contract

### Expected media types

- application/x-netcdf
- application/octet-stream

**Format:** Provider NetCDF archive path is documented, but response content type, magic bytes, compression, variables, dimensions and checksum have not been observed. This profile authorizes no response acquisition.

**Scientific semantics:** NASA GFWED computes Canadian Fire Weather Index family from reanalysis/weather model forcing including precipitation variants. The described GEOS-5 subset uses experimental near-real-time analysis, not a raw sensor fire-detection record. Retain FWI index meaning, local-noon sampling convention, model/forcing lineage, daily time, grid, missing values and version identity; fire-weather danger must not be equated to fire occurrence, footprint or insured loss.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** No automated HTTP probe is authorized until exact third-party rights, source persistence and provider usage policy have been reviewed. The provider's example wget/curl snippet describes generic retrieval ability only.

**Mutability notes:** Provider portal documents a v2.0 path and multiple precipitation/calculation variants. Do not infer that an HTTP file name freezes all upstream science, nor accept missing/cached/redirected data as a successful source receipt. Exact file SHA-256, date, response provenance and byte size are still unknown.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** NASA GISS publicly documents the GFWED NetCDF downloads, but no exact product/file licence, API automation terms, commercial insurer-use or derivative redistribution permission has been reviewed in this PR. NASA branding or government-source generalizations are not a substitute for a product-specific rights decision, including input precipitation and model lineage. Do not execute data acquisition or publish bytes until source-specific terms are established.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://data.giss.nasa.gov/impacts/gfwed/>
- <https://portal.nccs.nasa.gov/datashare/GlobalFWI/>
- <https://science.nasa.gov/earth/earth-atmosphere/studying-weather-to-help-see-the-likelihood-of-fires/>

**Notes:** T0 documented_only access contract. Explicitly nonexecutable. First future bounded step, after legal review, would be a single exact-file HEAD or range-limited NetCDF signature/header check with immutable URI/date, checksum and response receipt and no bulk downloads; scientific crosswalk with FIRMS would preserve non-independence of forcing and fire detections. No actual external file bytes or Neon records are present.
