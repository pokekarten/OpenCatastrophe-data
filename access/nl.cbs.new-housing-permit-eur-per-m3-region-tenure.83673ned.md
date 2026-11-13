<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned

## Source ids

- nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned

**Provider:** Centraal Bureau voor de Statistiek (CBS), Netherlands

**Interface type:** rest

**Status:** documented_only

**Documentation url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Service root:** <https://opendata.cbs.nl>

**Api version:** CBS StatLine OData 3 Dutch table 83673NED, official Modified 2026-08-20; rolling 12-month permit-based dwelling construction costs

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- original_metadata_small_rows
- first_2012_permit_cost_row
- 2026_june_rolling_rental_and_owner_exact_rows

### Path templates

- /ODataApi/OData/83673NED/TableInfos
- /ODataApi/OData/83673NED/TypedDataSet
- /ODataApi/OData/83673NED/DataProperties
- /ODataApi/OData/83673NED/Eigendom
- /ODataApi/OData/83673NED/RegioS
- /ODataApi/OData/83673NED/Perioden

**Parameter rules:** Documented ONLY, no direct HTTP in GitHub runner yet. Nine strictly fixed candidate URLs: TableInfos?$top=1; TypedDataSet?$top=1; DataProperties?$top=10; Eigendom?$top=3; RegioS?$top=5; Perioden?$top=1; TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27&amp;$top=1; Perioden?$filter=Key%20eq%20%272026VJ06%27&amp;$top=1; TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27%20and%20RegioS%20eq%20%27NL01%20%20%27&amp;$top=1. No arbitrary URL/OData query, feed, pagination, private coordinates, bulk snapshots or automatic live dispatch. Need a new strict provider-specific approved script and offline test before status may become probe_ready.

## Response contract

### Expected media types

- application/json

**Format:** Original CBS OData 3 public JSON response with one table revision row, 8 data properties, two tenure codes, five regional codes, historic Jan-Dec 2012 rental NL one row, latest Jul2025-Jun2026 provisional rented and owner NL aggregate rows. Original response body size each &lt;=16KiB; nine original-body SHA-256 digests recorded externally and research-only. No source JSON bytes stored.

**Scientific semantics:** This is 12-month rolling mean for pure new-dwelling building permits with construction value &gt;=50000 EUR excluding VAT, separated by tenant/owner and Dutch landsdelen; mixed-use projects, combinations of dwellings and recreational housing are excluded. CBS OData property name GemiddeldeBouwkostenPerM_2 means EUR per cubic metre (m³), while GemiddeldeBouwkostenPerM_3 means EUR per square metre (m²), despite suffixes. For 2025 Jul-2026 Jun national rental, provisional: 488 EUR/m³, 1473 EUR/m², 149 thousand EUR/dwelling, 306m³, 101m²; owner: 438 EUR/m³, 1297 EUR/m², 215 thousand EUR/dwelling, 490m³, 165m². Early 2012 first rental data 258 EUR/m³, 748 EUR/m², 95 thousand EUR/dwelling, final. No official insured replacement cost or source insurance claims, not construction loss, cost per cadastral building, individual property TIV, or national hazard function.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `16384`

**Max sample bytes:** `16384`

**Retry policy:** none

**Rate limit notes:** CBS official StatLine OData standard API is available for automated processing and capped at 10000 cells/request; the nine tiny source observations comply in size. Direct repository automated requests are DISABLED until an exact source-specific runner has been reviewed. No background polling, bulk crawl, data feed, retry, redirect or caller-selected table/region supported.

**Mutability notes:** Exact CBS publication Modified 2026-08-20T02:00:00; latest 2026VJ06 12-month rolling period explicitly provisional, 2012VJ12 definitive. Future later revision/new rolling period may change the numeric values. Direct trusted runner must pin exact original SHA and byte scope, 200 status, no redirect, table version, region keys with TWO TRAILING SPACES, tenure and crosswalk, 50000 EUR threshold, VAT exclusion, 12-month window. No extrapolated historical values admitted.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Original official government register identifies CBS 83673NED public national aggregated new-building permit statistical table with CC BY 4.0. Commercial reuse with explicit CBS citation and change notice permitted. CBS permits limited machine consumption by standard OData (10000 cell per direct request). This source contract is documented_only until an approved exact runner exists. Data licence is NOT model-input admission, permission to derive person-level/individual insured replacement cost or an unrestricted raw-body redistribution/crawl right. Research Neon summary rows have original digests but the strict direct GitHub HTTP runner has not executed.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5>
- <https://www.cbs.nl/nl-nl/cijfers/detail/83673NED>
- <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>
- <https://opendata.cbs.nl/ODataApi/OData/83673NED>

**Notes:** Nine original small source-body observations via external read-only intermediary, not strict Github runner; private research Neon sample IDs \#85-93, API receipts \#32-40, seven product-scoped legal/use-case decisions. No original provider data bytes stored, no model input approval, no new live workflow. The exact CBS source URL and suffix-to-unit crosswalk are protected by offline synthetic tests.
