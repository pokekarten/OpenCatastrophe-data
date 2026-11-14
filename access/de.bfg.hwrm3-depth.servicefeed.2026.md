<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/de.bfg.hwrm3-depth.servicefeed.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `de.bfg.hwrm3-depth.servicefeed.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** de.bfg.hwrm3-depth.servicefeed.2026

## Source ids

- de.bfg.hwrm3-flood-depth.2026

**Provider:** Bundesanstalt fuer Gewaesserkunde (BfG), WasserBLIcK and federal/state water authorities

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://data.gov.de/suche/daten/uberflutungstiefen-de-hochwasserrisikomanagement-rl-3-zyklus-2022-2027>

**Service root:** <https://geoportal.bafg.de>

**Api version:** 2025 BfG flood-depth service-feed discovery; exact protocol version unverified

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

- inspect_exact_documented_feed

### Path templates

- /download/opendata/ueberflutungstiefen-2025/servicefeed.xml

**Parameter rules:** DOCUMENTATION ONLY. BfG original-feed path was listed by harvested original-provider metadata at md.umwelt.info, but exact XML original bytes could not be fetched through the public research retrieval path (HTTP 403). No provider access test succeeded and no HTTP request, redirect, XML parse, linked data URL follow, download or publication is authorized under this contract. Never synthesize a WFS/WMS or asset URL from this feed path without separate original-provider validation and permission.

## Response contract

### Expected media types

- application/xml
- text/xml

**Format:** Advertised XML service feed; no original payload read, content-type checked, feature layer sampled or data-file obtained

**Scientific semantics:** German nationally harmonised HWRM-RL third-cycle 2022-2027 report of static inland/river and coastal flood-depth scenarios, not observed individual flood events or insurer losses. Lo/Me/Hi refer to low/medium/high probability scenarios, not a single standardized national annual probability without reviewing regional reporting metadata. Five binned depth classes; T_class combines protected/informational/inundation area type and depth bin (for example 23 denotes an informational area with 1-2 m depth), so T_class must not be interpreted as water depth in metres. National layer is not necessarily the current most detailed state or municipality layer; preserve source cycle, geographic coverage and missing areas.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** Only published feed metadata referenced; 403/unavailable through research retrieval. No active polling, service-capabilities request, data download or XML linked-resource traversal permitted.

**Mutability notes:** Metadata record issued 2026-03-06; published feed path carries ueberflutungstiefen-2025. Do not interpret feed-path vintage as verified scientific data year or reuse rights. Future review must prove original feed byte hash, exact service/products, layer version, CRS, depth-class encoding and provider attribution.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** GovData lists BfG as publisher; harvested metadata indicates a public service feed. Public listing or claimed open data is not an exact rights confirmation for every linked GIS dataset, commercial automation, derivative publication or downstream raw bytes. Verify original authoritative terms and the current BfG/WasserBLIcK licence per product.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-09

## Evidence urls

- <https://data.gov.de/suche/daten/uberflutungstiefen-de-hochwasserrisikomanagement-rl-3-zyklus-2022-2027>
- <https://md.umwelt.info/dataset/geodatenkatalog-bfg/fd355bf6-e240-4409-959b-153e3e6758d2>
- <https://geoportal.bafg.de/download/opendata/ueberflutungstiefen-2025/servicefeed.xml>

**Notes:** This is a documentation-only candidate route. Harvested metadata shows the exact feed URL but public intermediary access to that original URL returned HTTP 403 on 2026-11-09. Do not call it verified or infer provider outage from one intermediary failure; a trusted direct provider probe under reviewed terms is required. No external flood-depth values, original bytes or commercial modelling permission are present.
