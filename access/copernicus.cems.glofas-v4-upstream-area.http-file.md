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

**Status:** probe_ready

**Documentation url:** <https://confluence.ecmwf.int/spaces/CEMS/pages/242067380/Auxiliary+Data>

**Service root:** <https://confluence.ecmwf.int/download/attachments/242067380>

**Api version:** GloFAS v4.0 auxiliary data; exact upstream-area filename frozen

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

**Parameter rules:** This contract freezes one provider-published GloFAS v4.0 ancillary object only. A caller must not supply or override host, attachment id, path, filename, query, headers or redirects. The query-free canonical path is the semantic object identity; any provider-added transport query or redirect must be recorded in the execution receipt and may not select another attachment. The HEAD operation is the only probe authorized by this contract. The fetch operation is descriptive future scope and is not executable under the generic source-access sample budget: a full-body worker requires separate Tier-2 review with a dataset-specific bound above the provider-declared approximately 87 MB.

## Response contract

### Expected media types

- application/x-netcdf
- application/netcdf
- application/octet-stream

**Format:** One exact GloFAS v4.0 upstream-area NetCDF file. Media type or provider-reported size is discovery evidence only; later scientific use requires exact acquired-byte identity and structural validation.

**Scientific semantics:** The file provides upstream catchment area for each GloFAS river pixel in m2 on the v4.0 WGS84/EPSG:4326 grid (7200 longitude by 3000 latitude). Upstream area is model-configuration ancillary data, not river discharge, a gauge observation or a holdout target. GloFAS auxiliary data are version-specific and must not be mixed across model cycles. For the Dresden preregistration, only the already frozen candidate cells may be read after exact bytes and v4.0 structure are verified.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `65536`

**Max sample bytes:** `52428800`

**Retry policy:** none

**Rate limit notes:** No repository-specific request-rate entitlement is assumed. The contract authorizes at most a bounded metadata/HEAD probe. Do not use Range requests, pagination, crawling or repeated probes to reconstruct the NetCDF body.

**Mutability notes:** The provider documents the object as about 87 MB, which exceeds the schema's generic 50-MiB sample ceiling. That ceiling is not full-download authority. A 2022 GloFAS known issue records that an erroneous upstream-area file in older documentation was corrected; therefore filename/version documentation, requested and final URL, retrieval UTC, exact byte count and SHA-256 must be bound at acquisition, and the NetCDF dimensions/coordinates/variable/units/fill value must be validated before scientific use.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://ecds.ecmwf.int/licences/cems-floods>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The current CEMS-FLOODS datasets licence applies to CEMS EFAS &amp; GloFAS data and grants free access plus reproduction, distribution, public communication, adaptation/modification and combination subject to its terms and required source or modified-information notices. The licence warns that third-party information can carry different terms. No exact NetCDF bytes are admitted by this contract; a later acquisition must inspect provider response/file metadata for any contrary third-party notice before publication or redistribution.

## Probe contract

**Mode:** head

**Operation:** head_exact_upstream_area

**Requires credentials:** `false`

### Expected evidence

- requested exact canonical provider URL
- final URL after bounded redirect validation
- retrieval timestamp
- HTTP status and safe response metadata
- provider-reported content length and media type when present
- external_bytes_persisted=false

**Implementation decision:** build_later

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://confluence.ecmwf.int/spaces/CEMS/pages/242067380/Auxiliary+Data>
- <https://confluence.ecmwf.int/spaces/CEMS/pages/242067397/Data+Structure+and+Formats>
- <https://confluence.ecmwf.int/spaces/CEMS/pages/348807401/GloFAS+-+Known+Issues>
- <https://ecds.ecmwf.int/licences/cems-floods>

**Notes:** This is a narrow pre-acquisition contract for \#115/\#173. It deliberately separates a safe exact-object metadata probe from the later ~87-MB acquisition worker. It does not widen Agent Action request/result contracts, authorize caller-controlled URLs, persist external bytes, change the frozen Dresden selector/holdout protocol, or promote raw/publication state.
