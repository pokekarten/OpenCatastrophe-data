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

**Status:** probe_ready

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
- rolling_2026_june_rental_owner_exact_rows

### Path templates

- /ODataApi/OData/83673NED/TableInfos
- /ODataApi/OData/83673NED/TypedDataSet
- /ODataApi/OData/83673NED/DataProperties
- /ODataApi/OData/83673NED/Eigendom
- /ODataApi/OData/83673NED/RegioS
- /ODataApi/OData/83673NED/Perioden

**Parameter rules:** Exactly NINE immutable anonymous direct HTTPS GET URLs on one opt-in --live run, on official CBS OData table 83673NED only: TableInfos?$top=1; TypedDataSet?$top=1; DataProperties?$top=10; Eigendom?$top=3; RegioS?$top=5; Perioden?$top=1; TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27&amp;$top=1; Perioden?$filter=Key%20eq%20%272026VJ06%27&amp;$top=1; TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27%20and%20RegioS%20eq%20%27NL01%20%20%27&amp;$top=1. The reviewed source-specific script uses these exact literal URLs; no user-selectable host, path, table, period, tenure, region, dynamic query, OData feed, pagination, credentials, redirects, retries, private coordinates, bulk snapshot, schedule or automatic PR network execution. Each direct response &lt;=16384 original bytes and original shape/units/status/revision fail-closed.

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

**Rate limit notes:** CBS standard StatLine OData programmatic use limited to 10000 cells/request. Only nine fixed &lt;=10-row original public requests with max 16384 bytes each, manually opt-in exactly once via --live. No cron, no PR CI network, no retries or crawling, no live requests without signed source-specific agreement.

**Mutability notes:** CBS publisher Modified 2026-08-20T02:00:00 is pinned for this nine-query source adapter; if publication revision or any first/current numeric observation, two trailing spaces in native NL01 key, source schema or finality changes, abort and review new vintage rather than silently updating. Strict direct fetch must report HTTP 200, original final exact URL, application/json identity and full per-response byte counts and SHA256; no response bodies persisted. No full 2012-2026 table or actual insurer replacement costs.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Original official government register identifies CBS 83673NED public national aggregated new-building permit statistical table with CC BY 4.0. Commercial reuse with explicit CBS citation and change notice permitted. CBS permits limited machine consumption by standard OData (10000 cell per direct request). This source contract is documented_only until an approved exact runner exists. Data licence is NOT model-input admission, permission to derive person-level/individual insured replacement cost or an unrestricted raw-body redistribution/crawl right. Research Neon summary rows have original digests but the strict direct GitHub HTTP runner has not executed.

## Probe contract

**Mode:** provider_specific

**Operation:** nine_fixed_83673ned_odata_rows

**Requires credentials:** `false`

### Expected evidence

- Exactly nine official direct CBS table 83673NED GETs using frozen paths/queries, anonymous direct HTTPS 200 without redirects, application/json with identity encoding, &lt;=16 KiB each
- Exact official Modified 2026-08-20 publisher table, eight source properties mapping native _2 to EUR per m3 and _3 to EUR per m2
- Official rental/owned and national/four-regions codebooks, with two trailing spaces in native NL01 source key
- Separate final 2012VJ12 and provisional 2026VJ06 period status; three source-native historical/current rental/owner country rows
- Nine full original response body byte lengths and SHA256 hashes with UTC, retained as safe typed summary only; no provider original bytes written
- CC BY 4.0 product rights, &lt;=10000 CBS cells/request, rolling 12month pure permitted new housing, &gt;=50000 EUR threshold, no model input admission

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5>
- <https://www.cbs.nl/nl-nl/cijfers/detail/83673NED>
- <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>
- <https://opendata.cbs.nl/ODataApi/OData/83673NED>

**Notes:** Nine bounded original source-body readings via read-only web intermediary on 2026-11-13, documented as private research Neon samples \#85–93 and API receipts \#32–40. Trust boundary of original intermediary return is NOT the strict GitHub direct provider runner. Added one provider-specific --live opt-in script with nine exact immutable requests and offline regressions; does not dispatch automatically from PR CI or join existing reviewed_18 allowlist; no actual direct runner execution has yet been attested. No source bytes/TIV/insurance portfolio/model approval.
