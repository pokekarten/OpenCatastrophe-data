<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nl.cbs.new-housing-permit-2025v06-direct-three.83673ned.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nl.cbs.new-housing-permit-2025v06-direct-three.83673ned.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nl.cbs.new-housing-permit-2025v06-direct-three.83673ned

## Source ids

- nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned

**Provider:** Centraal Bureau voor de Statistiek (CBS), Netherlands

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Service root:** <https://opendata.cbs.nl>

**Api version:** CBS OData 3 fixed 83673NED, publisher Modified 2026-08-20, 2025VJ06 definitive (2024-07..2025-06)

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

- get_three_fixed_2025v06_rows

### Path templates

- /ODataApi/OData/83673NED/TypedDataSet
- /ODataApi/OData/83673NED/Perioden

**Parameter rules:** EXACT THREE fixed anonymous source-specific 2025VJ06 OData GET URLs only: 1. TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&amp;$top=5 ; 2. TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&amp;$top=5 ; 3. Perioden?$filter=Key%20eq%20%272025VJ06%27&amp;$top=1. Only explicit Python --live-three; additionally one exact source-branch-gated pull_request GitHub CI live probe on this research PR, no credentials. Original complete response body each &lt;=8192 bytes, HTTP 200, application/json, identity and exact URL no redirect. No custom endpoint, user-provided query, region, tenant, table, pagination, feed, retries, download or schedule.

## Response contract

### Expected media types

- application/json

**Format:** Three full original provider OData 3 public JSON responses: exactly five rental source aggregate rows including national NL01 and LD01-LD04, five owner rows in same original region order, and exactly one 2025VJ06 Perioden definitive status row. Original body SHA256 pinned separately for each: rental 70731cf7be6e73813059c250db9f1f21ad4024f0fb7cba5075ad8af666d90a5e (1457B); owner 7c9b9e307fd7fbf4ef8d5e9e26eaf3d9b9a991dd54a6b95c01409d22663c5908 (1459B); period 626dac3ab357839e615bcf0260237651d4a3983a88a0f18f6c8e3bfc24272c4d (234B). The hashes until GitHub proof are derived from read-only external intermediary and NOT yet independently trusted direct HTTP proof. No provider bytes persisted; GitHub summary contains only typed public data, SHA, byte count and UTC.

**Scientific semantics:** CBS new-dwelling granted permit construction sum &gt;=50 thousand EUR ex VAT, pure new dwelling permits only; mixed residential/business and recreation buildings excluded. Each row is a twelve-month rolling construction cost mean July2024-Jun2025 by five macroregional codes including NL country aggregate and tenure (rental/owner). Period 2025VJ06 is definitive, but period 2026VJ06 is provisional and not included in this runner. Native CBS odd field GemiddeldeBouwkostenPerM_2 is EUR per CUBIC metre, GemiddeldeBouwkostenPerM_3 is EUR per SQUARE metre. Average €/m² or €/m³ changes do not measure fixed-quality inflation, loss cost, insured replacement cost, TIV, hazard, repair cost or insurer claims. National NL01 must never be added to four landsdelen.

## Operational constraints

**Timeout seconds:** `25`

**Max probe bytes:** `8192`

**Max sample bytes:** `8192`

**Retry policy:** none

**Rate limit notes:** Official CBS StatLine standard OData API direct calls &lt;=10000 cells each; this approval is for exactly three source-specific 5,5,1-row public GETs only, one at a time, at most once per user-reviewed PR run, with no schedule, feed, mirror, retry or custom query. Automated source probe may be retriggered by PR updates only; event is branch-gated to this research PR and has no credentials.

**Mutability notes:** Official CBS publisher Modified 2026-08-20T02:00:00 and source period 2025VJ06 definitive. Source-specific script pins 3 original full-body SHA256 (including JSON whitespace), exact numeric and source-native field/region/tenure codes. Any modified original response bytes, revision or status change FAILS CLOSED and requires new human review; do not silently move to a new table revision or period.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Dutch official public CBS source 83673NED is licensed CC BY 4.0, including commercial dataset reuse with CBS citation and modifications disclosed. CBS StatLine standard API supports bounded 10000-cell direct use. Service-specific scope here is only 3 anonymous OData GETs for exactly 2025VJ06; source licence is not a CAT scientific model approval, unlimited bulk, raw original-byte publication authorization within this project, or property-level insurer TIV/claims entitlement. No original source JSON body is saved.

## Probe contract

**Mode:** provider_specific

**Operation:** get_three_fixed_2025v06_rows

**Requires credentials:** `false`

### Expected evidence

- Exact three public HTTPS CBS OData GETs to table 83673NED (two five-row tenancy subsets plus one official Perioden one-row status); no redirect, proxy or caller URL; HTTPS 200, application/json identity, &lt;=8192 bytes each
- Original three full byte SHA256+length checked against independently intermediary-observed immutable values (1457,1459,234 bytes), typed only in GitHub Actions logs/step summary, no original JSON bytes
- 2025VJ06 official definitive period; 2024 July-2025 June; 5 exact country/landsdeel codes with two trailing spaces and 2 exact tenancy native codes
- Exact public CBS five numerical mean-field values for each official row and fixed unit source crosswalk: _2=EUR per m3, _3=EUR per m2, _1=1000 EUR per permitted dwelling
- No insurer, insured TIV, catastrophe model input, no 2026 provisional status silently reclassified as definitive, no raw provider data saved

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5>
- <https://www.cbs.nl/nl-nl/cijfers/detail/83673NED>
- <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>
- <https://opendata.cbs.nl/ODataApi/OData/83673NED>

**Notes:** This NEW exact three-GET public CBS 2025VJ06 contract is distinct from the earlier draft nine-original 2012/2026 contract in PR \#1542. Existing research private Neon receipts \#97–99 and external API \#43–45 were intermediary-observed, NOT trusted direct provider calls. The three GET job is wired as a single branch-name-gated public research PR-specific GitHub Action without secrets. No full raw source body, no insurer model admission, no claims, no extrapolated values. Any change to response hash/codes/units/status blocks the strict source probe. Existing reviewed_18 workflow remains unchanged.
