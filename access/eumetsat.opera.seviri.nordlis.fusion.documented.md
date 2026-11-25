<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/eumetsat.opera.seviri.nordlis.fusion.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `eumetsat.opera.seviri.nordlis.fusion.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** eumetsat.opera.seviri.nordlis.fusion.documented

## Source ids

- eumetsat.opera.seviri.nordlis.fusion

**Provider:** EUMETSAT / EUMETNET / NORDLIS / European Weather Cloud

**Interface type:** object_store

**Status:** blocked_credentials

**Documentation url:** <https://europeanweather.cloud/index.php/news/update-opera-seviri-fusion-dataset>

**Service root:** <https://s3.r1.cloud.eumetsat.int>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** provider_account

**Credential reference:** EWC_CREDENTIAL

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /opera-seviri-nordlis.composite.zarr/.zmetadata

**Parameter rules:** Documentation only. Exact asset path; no new automated requests or bulk transfer authorized.

## Response contract

### Expected media types

- application/json

**Format:** Co-registered OPERA radar composites, SEVIRI rapid scan radiances and ground lightning in Zarr

**Scientific semantics:** EWC guide https://confluence.ecmwf.int/spaces/EWCLOUDKB/pages/488063253/Using%2BEUMETSAT%2Bdata%2Bbuckets%2Blocal%2Bdata%2Bpool lists bucket opera-seviri-nordlis.composite.zarr, endpoint https://s3.r1.cloud.eumetsat.int, 2018-2023. EWC-internal credential-free access does not imply public internet access or uniform rights. OPERA data policy https://www.eumetnet.eu/data-access/data-policy/ announces CC BY 4.0 via MeteoGate for qualifying products; SEVIRI and NORDLIS terms must be checked independently. No bucket bytes tested; verify Zarr chunk layout, spatial/time alignment, coverage masks and licensing per layer. Radar composites not necessarily hail size labels. On 2026-11-25 an anonymous HTTPS GET of https://s3.r1.cloud.eumetsat.int/opera-seviri-nordlis.composite.zarr/.zmetadata from authorized macOS returned HTTP 403. This confirms public-internet access was not demonstrated; it does not refute documented EWC-internal availability. Request EWC access and exact layer terms; no Zarr bytes downloaded.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** Review provider terms and explicit request/byte budget before any future execution.

**Mutability notes:** Freeze exact asset/version, UTC retrieval, size and SHA-256; mutable metadata is not data identity.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Anonymous GET 403. Request EWC access and individual OPERA, SEVIRI and NORDLIS permissions; confirm storage/compute conditions, chunk size and alignment. Do not automate public access.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://europeanweather.cloud/index.php/news/update-opera-seviri-fusion-dataset>

**Notes:** Open-first qualification. Anonymous GET 403. Request EWC access and individual OPERA, SEVIRI and NORDLIS permissions; confirm storage/compute conditions, chunk size and alignment. Do not automate public access. No admission or authorization to acquire data.
