<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/uk.ea.flood-depths.ckan.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `uk.ea.flood-depths.ckan.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** uk.ea.flood-depths.ckan.2026

## Source ids

- uk.ea.rivers-sea-flood-depth.present.2026
- uk.ea.rivers-sea-flood-depth.climate.2026
- uk.ea.surface-water-depth.present.2026

**Provider:** Environment Agency (Defra) via data.gov.uk National Data Library CKAN API

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://guidance.data.gov.uk/get_data/api_documentation/>

**Service root:** <https://data.gov.uk>

**Api version:** CKAN action package_show (2026 catalogue)

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

- inspect_fixed_package_metadata

### Path templates

- /api/action/package_show

**Parameter rules:** NONEXECUTABLE reference only: the original provider catalogue exposes GET package_show?id with exactly one of three fixed dataset identifiers: e4698ae1-184b-4b5d-801a-90364a93e229 (present-day river/sea); 67a734bb-2b7b-491a-aafd-3f7e52c8d7f3 (climate river/sea); b0bbfacf-ccf7-4ed9-a94c-be18d91c258d (present-day pluvial). Never accept a caller-supplied URL, dataset ID, resource href, action or query parameter; this contract authorizes no GET, HEAD, redirect, download, WMS, WFS, OGC Feature request, or byte persistence. Exact CKAN resource URLs are discovery evidence only and must not be followed under this contract.

## Response contract

### Expected media types

- application/json

**Format:** CKAN action JSON metadata with success and result.id, result.resources, and extras licence; no features/GeoJSON/ZIP asset bytes

**Scientific semantics:** Three distinct England Environment Agency 2026 scenario depth products. River/sea present-day and climate-change datasets each publish defended/undefended 0.1% AEP and 1% river / 0.5% sea AEP scenarios, seven depth bands and explicit Unavailable where national flood-zone modelling is missing. Climate case uses UKCP18 RCP8.5 river 2080s/sea 2125 assumptions; it shares lineage with present-day and is not an independent observation. Pluvial surface-water planning product publishes 3.3%, 1% and 0.1% AEP depth bands; it is not the river/sea product. Each is area-level screening, not a point estimate for an individual insured building, event loss or insurer claims. Preserve provider version, depth band, defence case, climate case, AEP, CRS and unavailable mask.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** No adapter or polling enabled. Provider CKAN metadata may be anonymously readable; underlying Defra spatial services have separate terms/rate limits and are not approved for automation here.

**Mutability notes:** Published CKAN catalogue metadata modified 2026-10-30 for both river/sea datasets and 2026-07-06 for pluvial. Catalogues and resource URLs may change; any future trusted source probe must pin dataset UUID, retrieval UTC, exact final provider host, status, response bytes, SHA-256, resource names, version and provider rights evidence.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** <https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Data.gov.uk catalogue extras show the Open Government Licence for each dataset, while top-level CKAN license_id/license_title are null for the present-day product. This is provider-published rights evidence, not an OpenCatastrophe asset-level licence review or permission to copy/republish source bytes. Exact service and downstream asset terms, attribution, derivative and commercial automation conditions remain unreviewed.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-09

## Evidence urls

- <https://data.gov.uk/api/action/package_show?id=e4698ae1-184b-4b5d-801a-90364a93e229>
- <https://data.gov.uk/api/action/package_show?id=67a734bb-2b7b-491a-aafd-3f7e52c8d7f3>
- <https://data.gov.uk/api/action/package_show?id=b0bbfacf-ccf7-4ed9-a94c-be18d91c258d>
- <https://www.data.gov.uk/dataset/e4698ae1-184b-4b5d-801a-90364a93e229/rivers-and-sea-defended-and-undefended-flood-risk-depths-present-day>
- <https://www.data.gov.uk/dataset/67a734bb-2b7b-491a-aafd-3f7e52c8d7f3/rivers-and-sea-defended-and-undefended-flood-risk-depths-climate-change>
- <https://www.data.gov.uk/dataset/b0bbfacf-ccf7-4ed9-a94c-be18d91c258d/flood-map-for-planning-surface-water-spatial-planning-depths-present-day>

**Notes:** Public metadata acquired through external web retrieval intermediary and parsed for official resource names; not a trusted original HTTP byte receipt. Provider CKAN records have 8, 8 and 4 named resources respectively. River/sea records list OGC API Features, WFS/WMS and GeoJSON/GDB ZIP links; pluvial lists WMS and exploratory download links. No GIS service, asset, PDF or ZIP was downloaded, checked or approved. This contract deliberately blocks all executable probes until exact licence, access semantics and response-byte gates have been reviewed.
