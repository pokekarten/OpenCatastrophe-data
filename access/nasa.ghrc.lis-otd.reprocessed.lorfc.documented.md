<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.ghrc.lis-otd.reprocessed.lorfc.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.ghrc.lis-otd.reprocessed.lorfc.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.ghrc.lis-otd.reprocessed.lorfc.documented

## Source ids

- nasa.ghrc.lis-otd.reprocessed.lorfc

**Provider:** NASA GHRC DAAC / Cecil et al.

**Interface type:** http_file

**Status:** blocked_registration

**Documentation url:** <https://doi.org/10.5067/LIS/LISCLIMO/DATA101>

**Service root:** <https://data.ghrc.earthdata.nasa.gov>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** provider_account

**Credential reference:** EARTHDATA_CREDENTIAL

**Registration url:** <https://urs.earthdata.nasa.gov/>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /ghrcw-protected/lorfc__2/COMB_OTD_TRMM_ISS_AnnualMean.hdf

**Parameter rules:** Exact documented asset locator only; no executable acquisition authorized. Review service conditions and explicit byte budget before any future request.

## Response contract

### Expected media types

- application/octet-stream

**Format:** 0.1 degree gridded annual mean flash rate, annual/diurnal cycle and mission-specific time series

**Scientific semantics:** NASA catalog https://catalog.data.gov/dataset/lis-otd-reprocessed-flash-climatology identifies US government works rights label and collection C3671144020-GHRC_DAAC; paper https://doi.org/10.1175/JAMC-D-25-0110.1. Live anonymous CMR granule query on 2026-11-25 returned COMB_OTD_TRMM_ISS_AnnualMean.hdf, COMB_OTD_TRMM_ISS_AnnualDiurnalCycle.hdf, COMB_OTD_TRMM_ISS_AnnualCycle.hdf and OTD monthly/annual files under https://data.ghrc.earthdata.nasa.gov/ghrcw-protected/lorfc__2/. Combined granules span 1995-04-13 to 2023-11-16; not continuous observing time. CMR reported granule_size 0, not evidence files are empty or free to acquire. Exact version, Earthdata account and HDF reader required; review mission-specific rights, detection efficiency, observation opportunity, time bins and units. No original payload downloaded. Use as frequency/diurnal context, not hail events.

## Operational constraints

**Timeout seconds:** `45`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No scheduled or automated acquisition authorized; provider-specific fair-use and exact scope must be respected.

**Mutability notes:** Freeze DOI, exact product/member, retrieval UTC, original byte count and SHA-256. A listing or protected locator is not a download receipt.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://www.earthdata.nasa.gov/data/catalog/ghrc-daac-lorfc-2>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Official NASA collection DOI and 0.1 degree annual mean verified; exact granule in CMR. NASA catalogue labels US government works, but exact mission/product rights, Earthdata terms, file size and HDF fields still require review. Register Earthdata account, keep credentials outside Git, obtain a bounded HDF sample or supported subset. No download attempted under this contract.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5067/LIS/LISCLIMO/DATA101>
- <https://www.earthdata.nasa.gov/data/catalog/ghrc-daac-lorfc-2>

**Notes:** Open-first source access coverage; Official NASA collection DOI and 0.1 degree annual mean verified; exact granule in CMR. NASA catalogue labels US government works, but exact mission/product rights, Earthdata terms, file size and HDF fields still require review. Register Earthdata account, keep credentials outside Git, obtain a bounded HDF sample or supported subset. No download attempted under this contract. No model admission or new acquisition authorization.
