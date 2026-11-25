<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.goes.glm.l2.lcfa.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.goes.glm.l2.lcfa.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.goes.glm.l2.lcfa.documented

## Source ids

- noaa.goes.glm.l2.lcfa

**Provider:** NOAA NCEI / GOES-R Program

**Interface type:** object_store

**Status:** documented_only

**Documentation url:** <https://doi.org/10.7289/V5KH0KK6>

**Service root:** <https://noaa-goes16.s3.amazonaws.com>

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

- inspect_documented_route

### Path templates

- /GLM-L2-LCFA/2024/167/12/OR_GLM-L2-LCFA_G16_s20241671200000_e20241671200200_c20241671200216.nc

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/octet-stream

**Format:** Time-stamped optical lightning events, groups and flashes; NetCDF

**Scientific semantics:** NCEI catalog gov.noaa.ncdc:C01527; public archive https://registry.opendata.aws/noaa-goes/; data.gov metadata lists CC0 1.0 for this collection (formal rights review still open). On 2026-11-25 anonymous S3 prefix listing and one bounded original GET succeeded via macOS: https://noaa-goes16.s3.amazonaws.com/GLM-L2-LCFA/2024/167/12/OR_GLM-L2-LCFA_G16_s20241671200000_e20241671200200_c20241671200216.nc, 198460 bytes, SHA-256 ce0beb46fc01ea6e271f8c97eda042a8720452903a52ed7742f56c5111516506. HDF5 magic and h5py read passed; platform G16, FM1, coverage 2024-06-15 12:00:00 to 12:00:20 UTC, 71 flashes, 1189 groups and 2325 events. Verified flash_id, flash_lat/lon (degrees), flash_energy (J), flash_area (m2), flash_time_offset_of_first_event (seconds since granule start), flash_quality_flag, group_id and event_id. Counts are optical observations, not confirmed ground strikes or hail. Decode packed values, flags, parent-child relationships, viewing geometry, outages and sensor transitions before regional flash rates or tracks. No external bytes in Git or Neon, no scientific admission.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Future route must review service terms and enforce explicit provider-specific request and byte limits.

**Mutability notes:** Freeze exact version, UTC retrieval time, selected object, response byte size, SHA-256 and coverage; never use a mutable directory or catalogue as original byte identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://registry.opendata.aws/noaa-goes/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Anonymous exact granule read and SHA-256 established. Strong open-first priority; confirm exact NOAA rights and AWS public access conditions, decode packed values and quality flags, then validate flash aggregation before admission.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.7289/V5KH0KK6>
- <https://registry.opendata.aws/noaa-goes/>

**Notes:** Open-first qualification queue. Anonymous exact granule read and SHA-256 established. Strong open-first priority; confirm exact NOAA rights and AWS public access conditions, decode packed values and quality flags, then validate flash aggregation before admission. Discovery/access only: no admission, no external bytes in Git, no model approval.
