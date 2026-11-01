<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/jp.gsi.fgd.building-outline.gml.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `jp.gsi.fgd.building-outline.gml.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** jp.gsi.fgd.building-outline.gml

## Source ids

- jp.gsi.fgd.building-outline.gml

**Provider:** Geospatial Information Authority of Japan (GSI)

**Interface type:** web_portal

**Status:** blocked_registration

**Documentation url:** <https://service.gsi.go.jp/kiban/app/help/>

**Service root:** <https://service.gsi.go.jp>

**Api version:** `null`

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** provider_account

**Credential reference:** `null`

**Registration url:** <https://service.gsi.go.jp/kiban/app/>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- review_gsi_fgd_terms_manually

### Path templates

- /kiban/app/
- /kiban/app/help/

**Parameter rules:** Documentation and manual rights review only. The GSI download UI requires registered ID/password; no scripted login, credentials, headless browser, mass or per-mesh download, arbitrary URL, query parameter, crawler, or authentication bypass is authorized. Freeze exact prefecture/mesh, product vintage and schema version before considering a separately permitted original-source byte receipt.

## Response contract

### Expected media types

- text/html

**Format:** Official GSI Fundamental Geospatial Data basic-items portal/help pages (JPGIS/GML building outline product). No programmatic raw data response is approved.

**Scientific semantics:** Building exterior line is a 2D topographic map feature, not 3D building/roof geometry, residential address, insured asset, TIV, vulnerability or complete census. GSI notes municipalities and other surveys contribute upstream base map data. Source mesh, compilation date, coverage, precision and post-2025 JGD2011-to-JGD2024 datum changes must be preserved; raw geometric identity cannot be inferred from overlap with PLATEAU.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `32768`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Provider requires registration for downloads and may require a Survey Act reproduction/use application. No autonomous service interaction is authorized by this contract or a public page's visibility.

**Mutability notes:** Official help documents GML application schema 5.1 from 2025-04-01 and basic-items download specification 5.3 from 2026-07-31; datum transition to JGD2024 reflected in post-July-2025 files. Pin exact individual downloaded asset/product vintage and CRS before any geospatial cross-source comparison.

## Rights and policy

**Dataset rights status:** restricted

**Api terms status:** unknown

**Terms url:** <https://service.gsi.go.jp/kiban/app/help/>

**Commercial automation status:** unknown

**Redistribution status:** restricted

**Notes:** Official GSI help states downloads require registration and a username/password; the basic survey products can require approval to reproduce or use under the Survey Act, depending on exact intended use. This is not free anonymous machine access nor blanket commercial or public redistribution clearance. No rights to upload raw bytes to OpenCatastrophe or reuse for an insurer model have been granted.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** do_not_automate

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://service.gsi.go.jp/kiban/app/>
- <https://service.gsi.go.jp/kiban/app/help/>

**Notes:** Registration and conditional survey-rights blocker recorded. No user credentials requested, registration undertaken, login attempted, provider bytes downloaded, raw map copied, sample imported, source admitted or insurer exposure joined.
