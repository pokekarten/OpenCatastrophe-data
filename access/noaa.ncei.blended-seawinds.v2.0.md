<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.blended-seawinds.v2.0.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.blended-seawinds.v2.0.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.blended-seawinds.v2.0

## Source ids

- noaa.ncei.blended-seawinds.v2.0

**Provider:** NOAA CoastWatch / NOAA National Centers for Environmental Information

**Interface type:** other_documented_machine_interface

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc%3AC01702>

**Service root:** <https://coastwatch.noaa.gov>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- science_quality_daily_metadata
- science_quality_daily_subset

### Path templates

- /erddap/info/noaacwBlendedWindsDaily/index.json
- /erddap/griddap/noaacwBlendedWindsDaily

**Parameter rules:** This contract is documentation-only and does not currently authorize execution. Any future request must be repository-constructed and must bind the NOAA NCEI Blended Sea Winds Version 2 Science Quality daily dataset ID \`noaacwBlendedWindsDaily\`. A metadata check may target only the fixed ERDDAP info route. A later data subset must use one preregistered historical UTC day or smaller bounded time slice, one small predeclared ocean bbox and an explicit minimal variable set. Any subset containing \`windspeed\`, \`u_wind\` or \`v_wind\` must also include the provider \`mask\`; the resulting receipt must bind the provider mask semantics, including \`mask=6\` meaning \`model\` and \`_FillValue=-9999\`, rather than treating model-filled or fill-valued cells as independent observed wind or zero. Callers may not provide an arbitrary host, dataset ID, path, headers, output URL, time window, bbox or variable list. The separate near-real-time dataset \`noaacwBlendednrtWindsDaily\`, six-hourly/monthly variants, wind-stress variants and source-file browsing are outside this contract and require separate reviewed operations.

## Response contract

### Expected media types

- application/json
- application/x-netcdf

**Format:** NOAA CoastWatch ERDDAP metadata JSON or a separately reviewed bounded netCDF subset for the NBS v2.0 Science Quality daily grid.

**Scientific semantics:** NOAA/NCEI Blended Sea Winds v2.0 is a Level-4, 0.25-degree, 10 m neutral ocean-surface wind product produced by blending multiple satellite wind observations onto a gap-reduced global grid. The Science Quality stream is not equivalent to the near-real-time stream: NOAA CoastWatch metadata identifies ERA5 reanalysis as the direction/stress source for the Science Quality product, while the NRT product uses GFS forecast direction/stress lineage. The gridded vector field is therefore a blended/model-assisted product, not a raw satellite or in-situ observation at every grid cell. NOAA CoastWatch exposes a provider \`mask\` with \`mask=6\` meaning \`model\`; wind and mask fields use \`_FillValue=-9999\`. A model-flagged cell is not an independent satellite or in-situ observation merely because the Level-4 grid is spatially gap-reduced, and fill values must not be interpreted as zero or observed values. Any scientific receipt must preserve Version 2, Science Quality versus NRT state, cadence, exact ERDDAP dataset ID, requested variables, UTC interval, bbox, units, direction lineage and the provider mask/fill semantics whenever wind fields are included.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `5242880`

**Retry policy:** bounded_backoff

**Rate limit notes:** No OpenCatastrophe request-rate entitlement is inferred from anonymous CoastWatch/ERDDAP reachability. While this contract is documentation-only, no provider request is authorized. If service-use terms are independently cleared later, the first check must remain one small metadata request; a future data subset must remain a tiny preregistered historical query and must not become broad ERDDAP harvesting.

**Mutability notes:** The NBS v2.0 Science Quality record is ongoing and NOAA metadata describes daily updates. ERDDAP time coverage and source files can therefore advance. A future receipt must bind retrieval UTC, trusted execution-code identity, normalized request identity, dataset ID, response byte count and SHA-256, while scientific use must additionally bind Version 2, Science Quality mode, cadence, exact historical time/bbox/variables and the provider DOI \`10.25921/mxt4-b075\`.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The authoritative NCEI dataset record states the data are available for use with the required dataset citation and publishes direct/THREDDS access. This establishes a reviewed dataset-use/citation posture for the source. It does not by itself prove that NOAA CoastWatch ERDDAP service-use terms permit OpenCatastrophe automation or that future response bytes may be redistributed. No authoritative ERDDAP-specific service/commercial-automation term has been identified in this review, so API terms, commercial automation and redistribution remain fail-closed rather than being inferred from public technical access.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc%3AC01702>
- <https://coastwatch.noaa.gov/erddap/info/noaacwBlendedWindsDaily/index.html>
- <https://coastwatch.noaa.gov/erddap/griddap/noaacwBlendedWindsDaily.html>
- <https://coastwatch.noaa.gov/erddap/info/noaacwBlendednrtWindsDaily/index.html>
- <https://www.ncei.noaa.gov/news/blending-multi-satellite-data-improve-hurricane-forecasting>

**Notes:** Static source-access contract only. The first executable boundary remains intentionally disabled because dataset reuse/citation evidence is not treated as an ERDDAP service-use grant. The selected identity is the retrospective Science Quality daily NBS v2.0 ERDDAP dataset; NRT is retained only as evidence of a distinct product lineage and is not an allowed operation. No CoastWatch/ERDDAP query, netCDF subset, source file or other external dataset byte was acquired or persisted by this builder. Connectivity, if later established, would not itself establish tropical-cyclone event truth, independent wind observations at every grid cell, model fitness, damage/loss or insured loss.
