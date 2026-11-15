<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/eu.ecad.meteogate.nonblended-stations.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `eu.ecad.meteogate.nonblended-stations.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** eu.ecad.meteogate.nonblended-stations.2026

## Source ids

- eu.ecad.meteogate.nonblended-stations.2026

**Provider:** ECA&amp;D / KNMI MeteoGate

**Interface type:** other_documented_machine_interface

**Status:** restricted_by_terms

**Documentation url:** <https://www.ecad.eu/dailydata/>

**Service root:** <https://www.ecad.eu>

**Api version:** ECA&amp;D daily nonblended observational station scope; MeteoGate 2026 route claimed but endpoint/path must be independently verified

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

- inspect_official_ecad_research_policy

### Path templates

- /dailydata/
- /documents/ECAD_datapolicy.pdf

**Parameter rules:** Documentation-only, no automatic source request or caller-selected path, unbounded domain, secrets, crawler, bulk extraction or retries. Metadata path(s) are only candidate exact origins; actual provider GET requires independently reviewed provider machine-use terms, exact URL, byte cap, body hash and source-specific approved workflow.

## Response contract

### Expected media types

- text/html
- application/pdf

**Format:** Provider policy and public station catalogue only. This contract deliberately does not contain a data-query endpoint or permission to download non-downloadable stations.

**Scientific semantics:** Daily station series include variable availability and optional gust fields; daily extrema are not equivalent to hourly or 3-second gust footprint. Nonblended and blended station observations must remain separate, and underlying provider source restrictions persist.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Provider restrictions apply; no API data retrieval or bulk download under this contract. Catalogue policy inspection only.

**Mutability notes:** Individual stations may be non-downloadable or reassigned; restrictions apply at observation provenance and source time-series levels.

## Rights and policy

**Dataset rights status:** restricted

**Api terms status:** unknown

**Terms url:** <https://www.ecad.eu/documents/ECAD_datapolicy.pdf>

**Commercial automation status:** prohibited

**Redistribution status:** restricted

**Notes:** The ECA&amp;D/E-OBS provider data policy restricts observed station data to noncommercial research/education, including upstream station-use restrictions and non-downloadable records. There is no commercial insurance CAT calibration authorisation. An announced API does not override these source terms. Seek explicit product-use permission before any commercial scenario.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** do_not_automate

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.ecad.eu/dailydata/>
- <https://www.ecad.eu/documents/ECAD_datapolicy.pdf>

**Notes:** Not to automate or stage as commercial model inputs. No original MeteoGate response, authenticated client, licensed derivative data, or validated station sample. The MeteoGate endpoint itself is not yet pinned as an official exact URL.
