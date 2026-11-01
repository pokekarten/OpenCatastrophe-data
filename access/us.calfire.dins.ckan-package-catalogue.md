<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/us.calfire.dins.ckan-package-catalogue.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `us.calfire.dins.ckan-package-catalogue.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** us.calfire.dins.ckan-package-catalogue

## Source ids

- us.calfire.dins.structure-damage

**Provider:** California Department of Forestry and Fire Protection via the California Open Data CKAN catalogue

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://data.ca.gov/docs/developer-documentation>

**Service root:** <https://publish.data.ca.gov>

**Api version:** CKAN Action API 3, package_show for the exact DINS package UUID

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

- dins_package_show_catalogue

### Path templates

- /api/3/action/package_show

**Parameter rules:** One documented public CKAN read-only package_show for fixed dataset id=1fdaea07-4bcd-4795-aa88-cd72b98e8a03. One original metadata-only response was independently obtained at 2026-11-01T18:01:22Z (16,916 bytes, SHA-256 1998a87aff518a059162d9c4faff3ce3c2e145f007323c6a91cf3fb3617927f8). This contract remains documentation-only and does not authorize future automated requests, any CKAN resource download, ArcGIS feature /query, bulk pagination, address/APN retrieval, caller-controlled URLs, redirects, parameters or headers.

## Response contract

### Expected media types

- application/json

**Format:** CKAN package_show JSON object success=true with one fixed CAL FIRE DINS package id/name, public accessLevel, cc-by metadata label, metadata_modified=2026-10-21T20:55:50.264159, and precisely 11 format/id-tagged resources. Resource URLs are metadata pointers, not permission to download assets.

**Scientific semantics:** This public catalogue metadata establishes a dataset listing, version marker and references to 11 published formats; it does NOT establish actual resource byte availability, inspection count, event identity, scientific coverage, commercial CAT reuse, building exposure denominator, claim loss, or provider feature service usage rights.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** The state CKAN developer documentation says public read-only datasets require no API token and describes programmatic reuse; no published service-specific automated commercial-query quota was established. One bounded metadata-only response has been captured, but this record cannot be used as a schedule or unrestricted automation permission.

**Mutability notes:** The package is mutable and includes resource IDs and metadata_modified; as captured at 2026-11-01T18:01:22Z the original UTF-8 JSON body length is 16916 bytes and SHA-256 is 1998a87aff518a059162d9c4faff3ce3c2e145f007323c6a91cf3fb3617927f8. Exact-byte replays may change and must fail closed against this snapshot rather than silently replace it.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://data.ca.gov/docs/developer-documentation>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The official CKAN package metadata and portal label this DINS package public and cc-by/Creative Commons Attribution; state developer documentation explicitly describes anonymous read-only package metadata access. This verifies only the public cataloguing metadata and a source-published licence label. It does NOT resolve exact ArcGIS feature service policies, sensitive address/APN output, attribution version terms, commercial bulk automation, external asset redistribution or scientific admission. Public data availability does not bypass privacy rules.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://publish.data.ca.gov/api/3/action/package_show?id=1fdaea07-4bcd-4795-aa88-cd72b98e8a03>
- <https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data>
- <https://data.ca.gov/docs/developer-documentation>

**Notes:** Unlike the DINS ArcGIS POSTFIRE FeatureServer T0 contract this entry records a separate CKAN catalogue interface. One original metadata-only body was obtained and hashed with a SHA-256 implementation verified against standard empty/abc vectors. The 11 resource identifiers/formats and source receipt are recorded in docs/research/calfire-dins-ckan-original-metadata-receipt-20261101.md. Neither raw catalogue bytes, provider feature records nor URLs returned by the provider have been committed, and no model data are admitted.
