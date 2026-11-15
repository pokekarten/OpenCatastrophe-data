<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.swdi.v2.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.swdi.v2.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.swdi.v2

## Source ids

- noaa.ncei.swdi.v2

**Provider:** NOAA National Centers for Environmental Information (NCEI), Severe Weather Data Inventory (SWDI)

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/products/severe-weather-data-inventory>

**Service root:** <https://www.ncei.noaa.gov>

**Api version:** SWDI v2.0 interface (January 2022); one mutable October 2026 NEXRAD hail CSV.gz object, directory revision observed 2026-11-14

## Access scope

- catalogue
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_official_v2_directory_metadata
- retrieve_exact_nexrad_hail_202610_gzip

### Path templates

- /pub/data/swdi/database-csv/v2/
- /pub/data/swdi/database-csv/v2/hail-202610.csv.gz

**Parameter rules:** This is a nonexecutable documentation-only contract. The proposed future sample is exactly the already listed historical NEXRAD hail-signature October 2026 gzip CSV hail-202610.csv.gz, not hail-tiles, tornado, NWS preliminary reports or Vaisala NLDN lightning. No caller-controlled URL, host, dataset, date, path, filename, query, headers, pagination or range is permitted. Before any single GET, independently approve dataset/service rights and freeze an allowlisted no-redirect request with strict compressed and decompressed size limits, gzip magic/footer CRC, CSV header/row semantics and SHA-256 original-byte receipt. The directory HTML is catalogue evidence only; a 200 HTML error is not data. No operation is currently executable.

## Response contract

### Expected media types

- application/gzip
- application/octet-stream
- text/html

**Format:** NOAA NCEI SWDI v2 HTTPS file directory listing (HTML) or exact hail-202610.csv.gz compressed NEXRAD hail radar-signature CSV (gzip). A future parser must validate the downloaded payload as gzip, never accept HTML as sample bytes, enforce both compressed and decompressed limits, and verify real CSV field identity against official layer documentation.

**Scientific semantics:** United States NEXRAD Level III algorithm-derived hail signatures as indexed by SWDI. Radar signatures describe probable hail conditions, not confirmed stone sizes at insured premises, measured ground impact, independently observed claims or a stochastic event catalogue. NCEI expressly warns of incomplete temporal/geographic records and no extra SWDI quality control. Lightning data from Vaisala NLDN have a separate third-party provenance and are excluded from this product-scoped future retrieval. Correlation with NOAA Storm Events/NWS reports must not be interpreted as independent scientific holdout without lineage challenge.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `8000000`

**Retry policy:** none

**Rate limit notes:** No exact automated-service quota or licence is verified in this documentary review. Only one explicitly reviewed retrieval of the fixed 202610 file could be proposed, with no polling, retries, pagination, monthly-directory scanning or bulk mirroring.

**Mutability notes:** Official directory listing checked 2026-11-14 showed hail-202610.csv.gz last modified 2026-11-05 11:48 and declared size 4,750,539 bytes. These are unverified directory declarations, NOT an independently retrieved source file, content-length validation or SHA-256. A 2026-11 hail file is still in the current incomplete month and intentionally excluded. Monthly historical archives may be replaced or corrected. Require exact UTC request, origin/redirect trace, parser version, original SHA-256, file size, gzip integrity, unit/CRS/time semantics, source identity and revision date on a future sample.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** NOAA NCEI makes SWDI public HTTP bulk archives and query services available, but this review does not establish exact current raw hail signature commercial modelling/automated retrieval rights or interface-specific service rate terms for the chosen 202610 object. SWDI is a multi-source inventory; separate Vaisala NLDN lightning rights are expressly excluded, and public data availability must never be used to infer a licence for the whole inventory. Internal repo data-rights review, source-ownership scope and public redistribution remain open; no live probe, database write, model-use approval or raw-data publication is authorized.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.ncei.noaa.gov/products/severe-weather-data-inventory>
- <https://www.ncei.noaa.gov/maps/swdi/>
- <https://www.ncei.noaa.gov/pub/data/swdi/database-csv/v2/>
- <https://www.ncei.noaa.gov/pub/data/swdi/database-csv/v2/hail-202610.csv.gz>

**Notes:** Only T0 official product/directory and candidate byte-size evidence. This does not represent a completed original gzip fetch, HTTP data probe, calculated SHA-256, CRC check, parsed scientific sample or CAT admission. Existing discovery authority: landscape/sources-global-atlas-swdi-tsunami-20261103.json; prior study: docs/research/ngi-ptha-noaa-swdi-source-boundaries-20261103.md. Next step is exact NEXRAD hail dataset and HTTP-service rights review; once cleared, build one bounded original-byte integrity plus negative-case offline preflight and separately authorize a single fixed GET outside public Git. Do not use the unrelated NLDN lightning layer or reinterpret 2026-10 radar signatures as final observations or insured losses.
