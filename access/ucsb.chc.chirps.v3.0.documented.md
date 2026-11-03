<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ucsb.chc.chirps.v3.0.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ucsb.chc.chirps.v3.0.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ucsb.chc.chirps.v3.0

## Source ids

- ucsb.chc.chirps.v3.0

**Provider:** University of California Santa Barbara, Climate Hazards Center

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.chc.ucsb.edu/data/chirps3>

**Service root:** <https://data.chc.ucsb.edu>

**Api version:** v3.0

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

- chirps3_original_readme_metadata

### Path templates

- /products/CHIRPS/v3.0/README-CHIRPSv3.0.txt

**Parameter rules:** Documentation-only exact v3.0 README identity. No actual requests are authorized. Future callers must fix this host and path and may not choose another host, path, query, region, time, format, data file, redirection or download URL. No CHIRPS precipitation assets, preliminary/final products, daily/monthly/pentad grids, directory listing, binary range, or bulk retrieval are authorized by this contract.

## Response contract

### Expected media types

- text/plain

**Format:** Plain-text original UCSB CHC CHIRPS version 3.0 source README; NOT a rainfall dataset payload.

**Scientific semantics:** CHIRPS3 is terrestrial 0.05-degree precipitation from 1981 onward between latitudes 60S and 60N. Preliminary pentad and later final monthly-vintage products use different station inputs and validation. Pentad and month are fundamental; daily rnl is ERA5-disaggregated and daily sat is IMERG Late V07-disaggregated. They are non-independent of those daily forcing products. CHIRPS3 is not observed inundation, flood damage, an insurer exposure, an economic loss or a stochastic event set.

## Operational constraints

**Timeout seconds:** `25`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** The original README is documented as anonymously visible, but current source-use and service terms for programmatic collection have not been independently cleared. Probe mode is none; no automated provider request or numeric rate entitlement is claimed.

**Mutability notes:** The v3.0 root is a scientific version namespace but active preliminary/final files and the README may change. Any eventual authorized retrieval requires actual response UTC, original SHA-256, exact URL and byte count. Any scientific asset separately needs immutable time aggregation, region, product vintage (prelim/final), daily algorithm source, units, grid and content identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The official CHIRPS3 site explicitly declares CC BY 4.0 and publishes dataset DOI 10.15780/G2JQ0P and citation. This is evidence to review rather than a completed OpenCatastrophe exact-asset, commercial-automation, service-terms or redistribution admission. Both execution and public asset reuse stay blocked until a bounded rights and science review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-03

## Evidence urls

- <https://www.chc.ucsb.edu/data/chirps3>
- <https://data.chc.ucsb.edu/products/CHIRPS/v3.0/README-CHIRPSv3.0.txt>
- <https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/readme.txt>
- <https://doi.org/10.15780/G2JQ0P>
- <https://doi.org/10.1038/s41597-026-07096-4>
- <https://creativecommons.org/licenses/by/4.0/>

**Notes:** Documentation-only CHIRPS3 product access identity. No provider requests, source bytes, hosted third-party files, Neon writes, API-key/secret, model run or rights admission. Next: authoritative exact-product terms and scientific/vintage review before any fixed one-object metadata pilot.
