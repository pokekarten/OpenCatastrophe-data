<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/jp.nied.jshis.pshm.site-amplification.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `jp.nied.jshis.pshm.site-amplification.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** jp.nied.jshis.pshm.site-amplification

## Source ids

- jp.nied.jshis.pshm.site-amplification

**Provider:** National Research Institute for Earth Science and Disaster Resilience (NIED) / J-SHIS

**Interface type:** web_portal

**Status:** restricted_by_terms

**Documentation url:** <https://www.j-shis.bosai.go.jp/en/downloads>

**Service root:** <https://jmapweb6v.bosai.go.jp>

**Api version:** `null`

## Access scope

- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- review_jshis_map_terms_manually

### Path templates

- /en/agreement
- /map/JSHIS2/download.html

**Parameter rules:** Documentation only: no executable source-data GET, POST, download query, generated archive, web scraping, user-input URL, numerical map extraction, pagination or mirroring. Exact map release, reference date, hazard metric, mesh, usage terms and intended research/commercial scope must be resolved before any separate rights-reviewed work.

## Response contract

### Expected media types

- text/html

**Format:** Provider human-readable J-SHIS terms and seismic hazard download catalogue, not an approved downloadable asset.

**Scientific semantics:** NIED J-SHIS probabilistic hazard maps specify a probability measure over a reference horizon and may include site amplification; these are modelled probabilistic outputs, not observed shaking, building damage, claims, insurer insured values, or independent validation of correlated upstream seismic models. Mesh vintages and horizon must be pinned before comparison.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `32768`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Provider terms impose restrictions on raw duplication and distribution. No automated action is enabled. The documented byte limits are conservative design ceilings, not authorized provider requests.

**Mutability notes:** The terms state they may change without notice. Freeze dated terms, individual citations for site amplification, exact hazard-map release/mesh/horizon and response identity only after an explicit approved original-source request.

## Rights and policy

**Dataset rights status:** restricted

**Api terms status:** separate_unreviewed

**Terms url:** <https://jmapweb6v.bosai.go.jp/en/agreement>

**Commercial automation status:** unknown

**Redistribution status:** restricted

**Notes:** Provider Article 5 allows processing and certain distribution of transformed results subject to restrictions, explicitly prohibits copying/distribution/transfer of original seismic hazard map data even in another format, and requires contact for proposed sale of processed results (application may be needed). Attribution and special references for amplification factors apply (Article 4). This is NOT blanket commercial/derived-data approval; no open Git redistribution or automation.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** do_not_automate

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://jmapweb6v.bosai.go.jp/en/agreement>
- <https://jmapweb6v.bosai.go.jp/map/JSHIS2/download.html?lang=en>
- <https://www.j-shis.bosai.go.jp/en/downloads>

**Notes:** T0 official rights finding only. No HTTP source-data access, hash receipt, original asset acquisition, use-permission request, model-data admission, local map product, insurer exposure link, or automatic geospatial operation is authorized.
