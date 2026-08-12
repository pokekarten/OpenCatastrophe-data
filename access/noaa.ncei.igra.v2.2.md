<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.igra.v2.2.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.igra.v2.2.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.igra.v2.2

## Source ids

- noaa.ncei.igra.v2.2

**Provider:** NOAA National Centers for Environmental Information (NCEI)

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/products/weather-balloon/integrated-global-radiosonde-archive>

**Service root:** <https://www.ncei.noaa.gov>

**Api version:** IGRA v2.2

## Access scope

- metadata
- bulk

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- sounding_period_of_record
- sounding_year_to_date

### Path templates

- /data/integrated-global-radiosonde-archive/access/data-por/
- /data/integrated-global-radiosonde-archive/access/data-y2d/

**Parameter rules:** Documentation-only file contract. A future reviewed resolver must accept only an IGRA station identifier selected from the authoritative station inventory and exactly one sounding scope: period-of-record (data-por) or recent/year-to-date (data-y2d). Period-of-record sounding files use the provider pattern &lt;IGRA-station-id&gt;-data.txt.zip. Callers must not supply a host, arbitrary path, URL, headers, query string or filename. Monthly-mean and derived-parameter products are distinct products and are not authorized by these operations.

## Response contract

### Expected media types

- application/zip

**Format:** IGRA station sounding text packaged as a provider ZIP, using the separately published IGRA v2 sounding format definition.

**Scientific semantics:** IGRA v2.2 is an actively maintained radiosonde archive. Sounding observations are station- and launch-time-indexed vertical profiles; native record fields, source/background/quality flags, pressure/height/temperature/moisture/wind units and missing-value semantics must be preserved according to the provider format documentation. Period-of-record and recent/year-to-date products have different update scopes and must not be conflated. Monthly means and derived parameters are separate provider products and cannot substitute for sounding observations.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `131072`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** No repository-specific numeric NCEI rate-limit assumption is made. This contract authorizes no live request; any future retrieval must remain one preselected station/product-scope request under current provider guidance.

**Mutability notes:** IGRA v2.2 began in 2023 and the public station archives are actively refreshed. A live path is therefore not immutable scientific byte identity. Any later receipt must bind IGRA v2.2, exact station identifier, POR versus Y2D scope, retrieval UTC, provider path, exact byte count and SHA-256, plus the station-list/version identity used for selection.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Anonymous public NCEI file access is connectivity evidence only and is not represented as redistribution, derivative-use or commercial-automation permission. Exact dataset/use constraints and any attribution requirements require independent asset-specific review before repository persistence or publication.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://www.ncei.noaa.gov/products/weather-balloon/integrated-global-radiosonde-archive>
- <https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/access/>
- <https://www.ncei.noaa.gov/data/integrated-global-radiosonde-archive/doc/igra2-data-format.txt>
- <https://doi.org/10.7289/V5X63K0Q>

**Notes:** Static IGRA v2.2 sounding-access boundary only. No provider request, station sample, external byte, parser execution, admission promotion, hazard-model claim or publication decision is introduced. A future bounded sample must preselect station and POR/Y2D scope before inspecting target values and must retain provider flags and vertical-profile semantics.
