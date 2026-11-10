<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/uk.ea.flood-depth-3p3.ckan.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `uk.ea.flood-depth-3p3.ckan.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** uk.ea.flood-depth-3p3.ckan.2026

## Source ids

- uk.ea.rivers-sea-depth-3p3.present.2026
- uk.ea.rivers-sea-depth-3p3.climate.2026

**Provider:** UK Environment Agency / Defra Data Services Platform / National Data Library CKAN

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://www.data.gov.uk/dataset/2b1dc7a4-ff9f-42fd-9971-11638eabf814/rivers-and-sea-3-3-defended-flood-risk-depths-present-day>

**Service root:** <https://data.gov.uk>

**Api version:** CKAN package_show public catalogue metadata, 2026 release

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

- inspect_fixed_3p3_ckan_package_metadata

### Path templates

- /api/action/package_show

**Parameter rules:** NONEXECUTABLE documentary contract for two fixed public metadata packages only: 2b1dc7a4-ff9f-42fd-9971-11638eabf814 (present-day 3.3% AEP defended depth) and 9d5e56d5-7713-42a1-890f-3d0a3e895cd5 (climate-change 3.3% AEP defended depth). No caller-supplied URLs, IDs, arbitrary query params, redirect chasing, access to any of the nine resource hrefs, WMS/WFS/OGC feature requests, ZIP download, GIS reads, or automatic network probe is allowed by this contract. Freeze source-specific rights and protocol before a future bounded metadata request.

## Response contract

### Expected media types

- application/json

**Format:** CKAN action success=true with fixed result.id, result.name, metadata_modified, extras.licence and exact 9 UUID/name/format/url resource references per product; no original geospatial data

**Scientific semantics:** The two newly released England Environment Agency 3.3% AEP (approximately one-in-30) river/sea flood-depth products contain seven binned water-depth classes from under 150 mm to over 2300 mm. Only defended risk is modelled and flood defences are assumed to operate as designed; no failure is represented. Present-day and UKCP18 RCP8.5 climate-change cases share modelling lineage and are not two independent insured flood-loss observations. Climate allowance uses river 2080s central (2070-2125) and sea upper end to 2125. Only national-model-supported coverage is present and Unavailable must remain missing, never a zero-depth category. EPSG:27700; products are area-level flood screening and cannot yield reliable individual-building depth, occurrence event loss or AEP without independent scientific work.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** The published CKAN pages advertise the metadata endpoint without credential requirement; Defra DSP service-specific fair use and product rights are not individually cleared by this record. Zero automated requests and zero GIS feature retrievals are authorized.

**Mutability notes:** Original public publisher JSON response bodies were read on 2026-11-10 through an external HTTP transport and their exact byte lengths/SHA-256 recorded in scripts/preflight_ea_flood_ckan_v0.py: present 13959 bytes SHA256 64d01c89e24c82e7c9384f1a8a2762ddc065890bbbff81e19e16bc4fc8a32857; climate 15093 bytes SHA256 15ba47630e376659d3c22dcdcd72ac504e3ee5ff8b150b0491e5613848e3e1fa. Both catalogues marked modified 2026-10-30. SHA comparison alone does not authenticate the origin, license or asset bytes; future releases fail closed under the current preflight.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** <https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Both original data.gov.uk product listings state Open Government Licence, and publisher CKAN extras list that licence; CKAN top-level license_id remains null and isopen is false. This is metadata-level published rights evidence, not confirmed exact GIS asset reuse/commercial automation/service permission. Check OGL exceptions, source attribution, rights on linked GeoJSON/GeoPackage/GDB download, downstream Ordnance Survey contributions and Defra service conditions. All provider asset bytes and geospatial analysis remain blocked.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-10

## Evidence urls

- <https://data.gov.uk/api/action/package_show?id=2b1dc7a4-ff9f-42fd-9971-11638eabf814>
- <https://data.gov.uk/api/action/package_show?id=9d5e56d5-7713-42a1-890f-3d0a3e895cd5>
- <https://www.data.gov.uk/dataset/2b1dc7a4-ff9f-42fd-9971-11638eabf814/rivers-and-sea-3-3-defended-flood-risk-depths-present-day>
- <https://www.data.gov.uk/dataset/9d5e56d5-7713-42a1-890f-3d0a3e895cd5/rivers-and-sea-3-3-defended-flood-risk-depths-climate-change>

**Notes:** An offline-only preflight checks exact frozen publisher metadata and original response SHA-256, with fixed package IDs and a total of 18 links across both 3.3% products. No original GIS data bytes, XML Capabilities, feature samples or insured-loss observations have been retrieved or admitted. This contract deliberately does not authorize any provider request or derived risk model.
