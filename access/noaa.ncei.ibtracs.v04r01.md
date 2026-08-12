<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.ibtracs.v04r01.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.ibtracs.v04r01.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.ibtracs.v04r01

## Source ids

- noaa.ncei.ibtracs.v04r01

**Provider:** NOAA National Centers for Environmental Information (NCEI)

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/products/international-best-track-archive>

**Service root:** <https://www.ncei.noaa.gov>

**Api version:** IBTrACS Version 4r01 / 4.01; DOI 10.25921/82ty-9e16

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

- read_global_netcdf

### Path templates

- /data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/netcdf/IBTrACS.ALL.v04r01.nc

**Parameter rules:** This contract documents one exact provider-versioned global NetCDF object and authorizes no execution. A future acquisition must be separately reviewed and repository-constructed from the fixed service root and exact v04r01 path; callers must not supply a host, arbitrary path, headers, basin/subset selector, version, filename, query string, redirect target or downstream asset URL. Basin, since1980, last3years, ACTIVE, CSV and shapefile variants are separate provider distributions and must not be silently substituted for the documented global NetCDF identity.

## Response contract

### Expected media types

- application/x-netcdf
- application/octet-stream

**Format:** NOAA/NCEI IBTrACS v04r01 global NetCDF distribution object \`IBTrACS.ALL.v04r01.nc\`.

**Scientific semantics:** IBTrACS is a globally merged tropical-cyclone best-track archive assembled from multiple agencies and source records. Agency-specific positions, intensities, wind conventions, pressure values, identifiers, missingness and revision histories can differ; merged or harmonized fields must not be treated as universal physical ground truth. Scientific use must freeze the exact IBTrACS release, subset/file identity, storm and source-agency fields actually consumed, and document any choice among agency-specific or harmonized variables before hazard calibration or validation. Connectivity alone does not establish event truth, loss semantics or model fitness.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `1048576`

**Max sample bytes:** `52428800`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific crawl or download-rate entitlement is assumed. This contract is documentation-only; any later acquisition must target one exact reviewed object and must not enumerate, mirror or switch among provider subsets/formats without separate review.

**Mutability notes:** The v04r01 directory is versioned, but provider distributions and auxiliary subsets may be updated or republished. Any future trusted receipt must bind retrieval UTC, exact final URL, byte count and SHA-256, provider release/version, exact filename and selected scientific variable/source-agency semantics. A different IBTrACS release or subset is a different scientific input.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** NCEI provides public anonymous electronic distribution and dataset citation/use-liability information, but the reviewed evidence does not establish one uniform downstream redistribution or commercial-automation grant for the globally merged multi-agency best-track record. Public availability is therefore not promoted into a rights decision. Exact dataset reuse/publication scope and any service-use terms require dedicated review before provider execution, repository sample persistence or redistribution.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://www.ncei.noaa.gov/products/international-best-track-archive>
- <https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/netcdf/>
- <https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C01552>

**Notes:** Static documentation contract only. This source is NOAA/NCEI observed best-track IBTrACS v04r01 and is explicitly distinct from the repository's synthetic STORM present-climate dataset. No provider file was fetched or persisted by this change. Any future acquisition or admission must independently review exact rights, freeze one versioned object and preserve multi-agency provenance and variable semantics.
