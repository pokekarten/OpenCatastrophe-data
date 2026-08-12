<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/copernicus.cems.glofas-v4-upstream-area.http-file.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `copernicus.cems.glofas-v4-upstream-area.http-file.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** copernicus.cems.glofas-v4-upstream-area.http-file

## Source ids

- copernicus.cems.glofas-historical

**Provider:** Copernicus Emergency Management Service (CEMS) / ECMWF

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://confluence.ecmwf.int/spaces/CEMS/pages/242067380/Auxiliary+Data>

**Service root:** <https://confluence.ecmwf.int/download/attachments/242067380>

**Api version:** GloFAS v4.0 auxiliary data; exact upstream-area provider link version=2 documented

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

- head_exact_upstream_area
- fetch_exact_upstream_area

### Path templates

- /uparea_glofas_v4_0.nc

**Parameter rules:** This contract documents one provider-published GloFAS v4.0 ancillary object only and authorizes no network operation yet. The authoritative CEMS page publishes the attachment with fixed provider query parameters api=v2, modificationDate=1668604690076 and version=2. The query-free service root plus path are therefore not asserted to identify that exact attachment revision by themselves. A future source-specific worker must freeze those provider-supplied query values as reviewed code/config constants, never caller input, and must record requested and final URLs. Caller-controlled host, attachment id, path, filename, query, headers and redirect targets remain forbidden. The approximately 87 MB body also exceeds the generic source-access sample budget and requires separate Tier-2 review before any fetch implementation.

## Response contract

### Expected media types

- application/x-netcdf
- application/netcdf
- application/octet-stream

**Format:** One exact GloFAS v4.0 upstream-area NetCDF file. Media type, provider-reported size or a query-free attachment path is discovery evidence only; later scientific use requires exact acquired-byte identity, exact revision request evidence and structural validation.

**Scientific semantics:** The file provides upstream catchment area for each GloFAS river pixel in m2 on the v4.0 WGS84/EPSG:4326 grid (7200 longitude by 3000 latitude). Upstream area is model-configuration ancillary data, not river discharge, a gauge observation or a holdout target. GloFAS auxiliary data are version-specific and must not be mixed across model cycles. For the Dresden preregistration, only the already frozen candidate cells may be read after exact bytes and v4.0 structure are verified.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `52428800`

**Retry policy:** none

**Rate limit notes:** No repository-specific request-rate or automated-access entitlement for the ECMWF Confluence attachment service is established by current evidence. This documented-only contract authorizes no HEAD, GET, Range, crawling or repeated probe. Any future probe first requires a separately reviewed service/access-terms decision and exact-revision request recipe.

**Mutability notes:** The provider documents the object as about 87 MB, which exceeds the schema's generic 50-MiB sample ceiling. That ceiling is not full-download authority. The provider-published link includes fixed attachment-version/modification query parameters, while the query-free attachment path may be mutable; exact revision identity must therefore be preserved in future request evidence. A 2022 GloFAS known issue also records that an erroneous upstream-area file in older documentation was corrected. Any later acquisition must bind requested/final URL, retrieval UTC, exact byte count and SHA-256 and validate NetCDF dimensions, coordinates, variable, units and fill value before scientific use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://ecds.ecmwf.int/licences/cems-floods>

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The current CEMS-FLOODS datasets licence applies to CEMS EFAS &amp; GloFAS data and supports covered-data reuse and redistribution subject to its terms, required source or modified-information notices, and its third-party-information caveat. That dataset licence is not treated here as proof that automated requests to the separate ECMWF Confluence attachment service are permitted; service/API terms remain unknown, so this contract authorizes no network probe or fetch. No exact NetCDF bytes are admitted by this contract, and any later publication must also inspect exact asset evidence for contrary third-party notices.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://confluence.ecmwf.int/spaces/CEMS/pages/242067380/Auxiliary+Data>
- <https://confluence.ecmwf.int/download/attachments/242067380/uparea_glofas_v4_0.nc?api=v2&amp;modificationDate=1668604690076&amp;version=2>
- <https://confluence.ecmwf.int/spaces/CEMS/pages/242067397/Data+Structure+and+Formats>
- <https://confluence.ecmwf.int/spaces/CEMS/pages/348807401/GloFAS+-+Known+Issues>
- <https://ecds.ecmwf.int/licences/cems-floods>

**Notes:** This is a narrow documented pre-acquisition contract for \#115/\#173. It records the exact provider-published v4.0 attachment recipe and dataset-rights ceiling but deliberately grants no active network authority while Confluence service automation terms and exact-revision request handling remain separately unresolved. It does not widen Agent Action request/result contracts, persist external bytes, change the frozen Dresden selector/holdout protocol, or promote raw/publication state.
