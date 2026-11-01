<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/us.landfire.lfps.portal.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `us.landfire.lfps.portal.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** us.landfire.lfps.portal

## Source ids

- us.landfire.fuel-vegetation.2025

**Provider:** LANDFIRE / U.S. Geological Survey and U.S. Forest Service

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://landfire.gov/faqs>

**Service root:** <https://lfps.usgs.gov>

**Api version:** LANDFIRE Product Service (LFPS) with versioned 2025 data releases

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

- inspect_lfps_documentation

### Path templates

- /

**Parameter rules:** Documentation-only record of official LFPS REST entry point. Do not create asynchronous layer export jobs, request raster assets, submit bounding boxes, arbitrary output projections, spatial selections or user-supplied URL/paths/headers. Only after an exact endpoint, source product (such as FBFM40), region, release, output resolution, upstream licence and bounded response envelope are reviewed may a separate active probe be defined.

## Response contract

### Expected media types

- text/html

**Format:** LANDFIRE LFPS service documentation/entry page only; not a raster or task response.

**Scientific semantics:** LANDFIRE 2025 includes regional, product-specific fuel classes, vegetation characteristics, canopy data and disturbance layers released on a phased schedule. They are derived mapping products, not observed event footprints, ignition rates, building vulnerability or insured losses; preserve product name, edition, units, geography and epoch.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `524288`

**Max sample bytes:** `524288`

**Retry policy:** none

**Rate limit notes:** Provider documents LFPS REST with asynchronous exports; no requests or jobs are authorized here and provider concurrency/export limits remain unreviewed.

**Mutability notes:** The 2025 releases are phased by area and product; availability may differ from other LANDFIRE years and exact source bytes must be versioned at future admission.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** USGS and Forest Service publication and public access do not by themselves establish exact release-specific terms, automated service quota, licensing for every derived layer or permission to rehost output. A separate rights and product review is required.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://landfire.gov/data>
- <https://landfire.gov/faqs>
- <https://lfps.usgs.gov/>

**Notes:** T0 documentation-only LFPS entry-point contract. No API endpoint for an individual product, no asynchronous job, no original raster or SHA-stamped sample receipt was acquired. Future CAT use requires exact product/version, scientific role and external data-byte provenance.
