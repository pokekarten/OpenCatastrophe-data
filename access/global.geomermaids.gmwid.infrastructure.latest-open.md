<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/global.geomermaids.gmwid.infrastructure.latest-open.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `global.geomermaids.gmwid.infrastructure.latest-open.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

**Status:** documented_only

**Access id:** global.geomermaids.gmwid.infrastructure.latest-open

## Source ids

- global.geomermaids.gmwid.infrastructure

**Provider:** GeoMermaids / OpenStreetMap contributors and separately credited infrastructure providers

**Interface type:** object_store

**Documentation url:** <https://gmwid.geomermaids.com/>

**Service root:** <https://parquetry.geomermaids.com>

**Api version:** GMWID latest (weekly mutable) ODbL branch only; gmwid/nsta and separate licensed provider trees explicitly excluded

## Access scope

- metadata
- catalogue

## Request contract

### Allowed operations

- inspect_open_catalogue_metadata

### Path templates

- /gmwid/latest/_coverage.json
- /gmwid/latest/ATTRIBUTION.txt

**Parameter rules:** Documentation-only, no executable source request or adapter permission. The only contemplated future read is original provider attribution/coverage metadata on fixed gmwid/latest paths, not a layer file. No arbitrary layer, bbox, query, parquet bulk, member-state insurer mapping, gmwid/nsta/ or abandoned/ requests. Any future fetch must review original source automation terms and hash/size budgets first.

## Response contract

### Expected media types

- application/json
- text/plain
- application/octet-stream

**Format:** Coverage metadata JSON and open-build attribution text, not the original GeoParquet asset rows or restricted sidecar data.

**Scientific semantics:** Provider advertises 27 global infrastructure layers and per-row origin provenance. Weekly latest builds are non-frozen and incomplete by region/type. OSM and enrichment rows cannot be treated as independent double-counted infrastructure; the same physical site can appear across sources. These inventories are not building insurance portfolios, insurer allocations, TIVs, physical hazard or vulnerability models. Source vintage, ODbL share-alike/attribution, national source obligations and deduplication are separate requirements.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** Provider illustrates anonymous online Parquet and coverage access but has not been checked for automation rate limits, commercial polling, server load or downstream asset bulk redistribution; no executable probe allowed until separately reviewed.

**Mutability notes:** gmwid/latest is rebuilt weekly; catalogue URLs are mutable. Review and pin build date, exact source country/layer and original content SHA before any model staging. The noncommercial gmwid/nsta tree must never be UNION-ed into a commercial model by this access contract.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** <https://gmwid.geomermaids.com/>

**Commercial automation status:** unknown

**Redistribution status:** restricted

**Notes:** Publisher explicitly states gmwid/latest ODbL 1.0 (commercial use with attribution/share-alike) and distributes UK NSTA-only data separately under noncommercial source terms; these are NOT an interchangeable product. ODbL obligations and attribution must be assessed for any published derived database; source-country enrichment provenance remains per row. No automatic server polling or republishing rights inferred. A separate access contract and human approval would be required for any gmwid/nsta use.

## Evidence urls

- <https://gmwid.geomermaids.com/>
- <https://parquetry.geomermaids.com/gmwid/>
- <https://www.openstreetmap.org/copyright>

**Notes:** Static documented-only source-access contract for the existing GMWID candidate. Exact publisher licensing split reviewed 2026-11-14. No original GeoParquet/coverage bytes, strict API receipt, downstream commercial model admission, insurer portfolio or database write carried out.
