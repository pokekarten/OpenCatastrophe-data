<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.smash.eu.ot.climatology.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.smash.eu.ot.climatology.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.smash.eu.ot.climatology.documented

## Source ids

- nasa.smash.eu.ot.climatology

**Provider:** NASA

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://gis.earthdata.nasa.gov/portal/rest/services/SMASH/eu_monthly_ot_frequency_allhours/ImageServer>

**Service root:** <https://gis.earthdata.nasa.gov>

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

- /portal/rest/services/SMASH/eu_monthly_ot_frequency_allhours/ImageServer/exportImage

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- image/tiff

**Format:** Monthly, annual and hourly-binned OT days; monthly service pixel step 0.0357143 degrees, EPSG:4326

**Scientific semantics:** Live macOS HTTPS metadata response verified ImageServer scientific service, extent and pixel size. Provider lists daily-occurrence aggregates, not individual OT time/position detections. Preserve calendar/hour bins, coverage, nodata and exact units; never treat OT days as hail days. Rights for exact layer and image export not yet reviewed; no raster bytes sampled. On 2026-11-25 bounded macOS HTTPS exportImage request (bbox 10,47,12,49; bboxSR/imageSR 4326; size 64,64; format tiff; pixelType F32; f image) returned image/tiff, 66342 bytes, SHA-256 371ce0ec153e6529cf32924c378fccf72f8bf174ce16bc4f01bc169fda31f659, little-endian TIFF magic; actual variable/time slice and raster values not inspected. Earlier no-raster statement refers to prior run; this is a derived service export not original provider raster. Do not use scientifically until slice/units/rights confirmed.

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

**Terms url:** <https://science.data.nasa.gov/about/license>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Anonymous TIFF export received, but units, time slice and source rights remain unclear. Resolve layer metadata and slice selection, original source or export licence; decode numerical values. Do not infer surface hail.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://gis.earthdata.nasa.gov/portal/rest/services/SMASH/eu_monthly_ot_frequency_allhours/ImageServer>
- <https://science.data.nasa.gov/about/license>

**Notes:** Open-first qualification queue. Anonymous TIFF export received, but units, time slice and source rights remain unclear. Resolve layer metadata and slice selection, original source or export licence; decode numerical values. Do not infer surface hail. Discovery/access only: no admission, no external bytes in Git, no model approval.
