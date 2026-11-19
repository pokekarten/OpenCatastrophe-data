<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.event-footprint-catalog.portal.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.event-footprint-catalog.portal.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.event-footprint-catalog.portal

## Source ids

- noaa.ncei.event-footprint-catalog.2026

**Provider:** NOAA National Centers for Environmental Information (NCEI)

**Interface type:** web_portal

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/products/event-footprint-catalog>

**Service root:** <https://www.ncei.noaa.gov>

**Api version:** Event Footprint Catalog v1.0 (2026)

## Access scope

- catalogue
- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- review_catalogue_and_bulk_documentation

### Path templates

- /products/event-footprint-catalog

**Parameter rules:** Documentation-only portal description. NOAA publishes individual and bulk tornado/hail GeoJSON/CSV but no stable reviewed programmatic directory path or query API is yet frozen. Do not scrape a map UI, enumerate data folders, guess file patterns, send arbitrary URL/headers, or execute downloads with this contract. A distinct verified exact asset/download route and automated service terms review are required before any future request.

## Response contract

### Expected media types

- text/html

**Format:** Human-readable NOAA EFC product documentation; not an event GeoJSON or CSV response.

**Scientific semantics:** EFC 2026 combines damage assessments and Storm Events Database for tornadoes, MRMS radar for hail. Tornado 2010+ and hail 2020+ coverage differ; derived polygons are not independent of their DAT/SED/MRMS ancestors, certified storm records or insured losses.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `524288`

**Max sample bytes:** `524288`

**Retry policy:** none

**Rate limit notes:** No automated portal scrape or bulk download authorized by this metadata-only access contract.

**Mutability notes:** NOAA says catalog updates about every 24 hours, does not preserve prior footprint update versions, and incorporates upstream revisions. Any future exact file must be frozen with receipt UTC, filename, date range, hazard type, hash and provenance.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** NOAA data.gov lists EFC as public and CC0, while NCEI requests a source/subset/access-date citation; the exact bulk asset and service automation/reuse terms remain source-specific review items. No repository admission or unrestricted application API use follows.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://www.ncei.noaa.gov/products/event-footprint-catalog>
- <https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncei%3AC01773>
- <https://catalog.data.gov/dataset/event-footprint-catalog>

**Notes:** T0 documented product/portal only. Official public download options were identified; no exact approved API route, source data bytes, response hash, credential, or live probe receipt is claimed.
