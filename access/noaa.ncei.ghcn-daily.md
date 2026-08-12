<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.ghcn-daily.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.ghcn-daily.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.ghcn-daily

## Source ids

- noaa.ncei.ghcn-daily

**Provider:** NOAA National Centers for Environmental Information (NCEI)

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt>

**Service root:** <https://www.ncei.noaa.gov>

**Api version:** GHCN-Daily 3.34; current rolling update 3.34-upd-2026080518

## Access scope

- metadata
- catalogue
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- read_station_metadata
- read_station_file
- read_station_period_csv

### Path templates

- /pub/data/ghcn/daily/ghcnd-stations.txt
- /pub/data/ghcn/daily/all/
- /pub/data/ghcn/daily/by_station/

**Parameter rules:** This contract documents only the anonymous GHCN-Daily bulk/file distribution and authorizes no execution. A future bounded station operation must accept only one previously selected canonical GHCN station identifier, construct the provider path inside the fixed all/ or by_station/ directory, and reject caller-supplied hosts, arbitrary paths, headers, query strings, redirects to unrelated products, date-window widening or bulk crawling. NCEI Climate Data Online Web Services v2 is a separate token-authenticated interface and must not be executed through this anonymous file contract.

## Response contract

### Expected media types

- text/plain
- text/csv

**Format:** Provider-native GHCN-Daily station metadata, fixed-width .dly station records, or provider by_station period-of-record CSV.

**Scientific semantics:** GHCN-Daily is a rolling, quality-controlled daily station dataset assembled from many national, international and observing-network sources. Values carry measurement, quality and source flags; source provenance and station history can differ across records. Daily elements are not interchangeable measurements, and some semantics such as TAVG depend on source protocol. A successful future file retrieval would prove only byte identity and parser compatibility, not station homogeneity, source-rights uniformity, climatological representativeness, hazard fitness or model validity.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `5242880`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific rate or crawl entitlement is assumed. The anonymous archive is a bulk/file distribution surface; any future operation must select one exact station-scoped file and must not enumerate or mirror the archive. The separate CDO v2 service uses an access token and provider request limits and is outside this contract.

**Mutability notes:** GHCN-Daily is updated as new and revised observations arrive. The provider currently identifies Version 3.34 with rolling update 3.34-upd-2026080518 and a separately recorded last fully reprocessed version. Any future receipt must bind retrieval UTC, exact file path, byte count and SHA-256, the provider version/update identity available at retrieval, station identity, selected elements and relevant MFLAG/QFLAG/SFLAG provenance.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** GHCN-Daily aggregates observations from numerous national, international and community/source networks. Provider documentation exposes source flags and records that some contributed data were historically withheld until source-service permission was granted. NCEI hosting and anonymous technical availability therefore are not treated as evidence of one uniform commercial-automation or redistribution grant for every contributing record. Exact station/source composition and intended publication scope require a dedicated rights review before any repository sample or automation promotion.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/>
- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt>
- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme-by_station.txt>
- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-version.txt>
- <https://www.ncei.noaa.gov/cdo-web/webservices/v2>

**Notes:** Static documentation contract only. The primary boundary here is NCEI's anonymous GHCN-Daily file distribution. CDO Web Services v2 is documented separately by NCEI, requires a token and must remain a separate credentialed contract if later needed. No NCEI observation/archive bytes or token request were acquired or persisted; no raw/derived admission, publication promotion or live provider probe is authorized by this change.
