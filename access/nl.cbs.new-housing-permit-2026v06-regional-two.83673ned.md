<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nl.cbs.new-housing-permit-2026v06-regional-two.83673ned.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nl.cbs.new-housing-permit-2026v06-regional-two.83673ned.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nl.cbs.new-housing-permit-2026v06-regional-two.83673ned

## Source ids

- nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned

**Provider:** Centraal Bureau voor de Statistiek (CBS), Netherlands

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Service root:** <https://opendata.cbs.nl>

**Api version:** CBS OData 3 fixed 83673NED 2026VJ06 provisional July2025–June2026, official table Modified 2026-08-20

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

- get_two_fixed_2026v06_regional_rows

### Path templates

- /ODataApi/OData/83673NED/TypedDataSet

**Parameter rules:** EXACT TWO fixed public provider HTTPS GETs ONLY: TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&amp;$top=5 and TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&amp;$top=5. No user-controlled URL, period, region, tenure, property, query, Feed or pagination. Anonymous OData 3 public standard API, max 10000 cells/request; each of these responses 5 aggregate original rows under 8192 bytes. Only one exact same-repository named research pull_request branch condition triggers direct GitHub job; offline tests before network, no schedule, redirects, proxies, retry, credentials, cookies, source body artifacts or raw provider JSON persistence.

## Response contract

### Expected media types

- application/json

**Format:** Exactly two complete original CBS OData v3 public five-row JSON bodies, each national NL01 followed by LD01 through LD04 in original order with exact two trailing spaces in geo codes. Rental A028867 complete original JSON 1457 bytes SHA256 2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0; owner A028868 complete original JSON 1459 bytes SHA256 67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3. Previous hashes from externally intermediated tiny original source bodies remain intermediary-only until direct GitHub execution proves exact bytes and HTTP. Exact original numeric values, row IDs, period, tenure and region, area/cubic mean and source dimensional rounding checked. Separate previous nine-GET original public CBS 83673NED runner source proof has already validated official table 2026-08-20 vintage, native key codebooks, correct metric units and official 2026VJ06 status Voorlopig, not Definitief. No raw provider JSON saved.

**Scientific semantics:** CBS granted pure-new-dwelling building permits &gt;= EUR 50000 excluding VAT, NOT all properties/rebuilding, no insured TIV. Four landsdelen plus national (NL01 is overlapping aggregate, not additive). 2026VJ06 rolling Jul2025–Jun2026 provisional; comparing to 2025VJ06 definitive cannot establish constant-quality construction inflation. CBS native property GemiddeldeBouwkostenPerM_2 actually means EUR per cubic metre; GemiddeldeBouwkostenPerM_3 means EUR per square metre. Five aggregated public stats each rent/owner across national and four landsdelen are not individual insured buildings, claims, policy values, CAT vulnerability, loss event sets or calibrated insurer replacement costs.

## Operational constraints

**Timeout seconds:** `25`

**Max probe bytes:** `8192`

**Max sample bytes:** `8192`

**Retry policy:** none

**Rate limit notes:** Exactly two fixed public standard CBS OData calls with only five source aggregate data rows each, well below the CBS standard API 10000-cell ceiling. No schedule, unrelated table, all historical rows, Feed, full source mirror, high-frequency traffic, retries or provider API key. Exact same-repo source branch only; one fresh direct read of two fixed queries for proof.

**Mutability notes:** CBS original response bodies pinned by full original SHA256 and byte length. Table version previously independent original TableInfos 2026-08-20T02:00:00 and previous original 2026VJ06 Perioden status Voorlopig. Any source changes, data corrections or unit/status mismatches block direct admission pending explicit source vintage review. Only research receipt, never model price escalation.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Dutch official public CBS source 83673NED is licensed CC BY 4.0, including commercial dataset reuse with CBS citation and modifications disclosed. CBS StatLine standard API supports bounded 10000-cell direct use. Service-specific scope here is only 3 anonymous OData GETs for exactly 2025VJ06; source licence is not a CAT scientific model approval, unlimited bulk, raw original-byte publication authorization within this project, or property-level insurer TIV/claims entitlement. No original source JSON body is saved.

## Probe contract

**Mode:** provider_specific

**Operation:** get_two_fixed_2026v06_regional_rows

**Requires credentials:** `false`

### Expected evidence

- 2 exact public source-native original OData HTTPS GET URL+HTTP 200 no redirects, application/json, identity, 1457/1459 original body bytes, SHA256 2b224f3... and 67a2647..., no original JSON persisted
- Five national+4 landsdelen original provider rows each for rental and owner with source-native 2-spaced geo codes and ID values, correct original field units _2=EUR/m3 and _3=EUR/m2
- Prior trusted original source 2026VJ06 status Voorlopig and CBS 2026-08-20 revision, independent public CBS CC BY 4.0 and standard OData access &lt;=10000 cells
- No individual dwelling or CAT insurer portfolio model admission, no original provider body GitHub/Neon persistence; results only UTC, typed public aggregate and original body hashes

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>
- <https://www.cbs.nl/nl-nl/cijfers/detail/83673NED>
- <https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5>
- <https://opendata.cbs.nl/ODataApi/OData/83673NED>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43501313224>

**Notes:** NEW direct evidence run for only 2 native 2026VJ06 five-row regional CBS OData public JSON bodies on PR \#1553. Prior interim summary exact body original source samples private Neon \#95 (owner), \#96 (rental) and external API smoke \#41/\#42, both with direct runner flag false. Prior separate direct 9-GET table/codebook/period proof PR \#1542 and 2025 definitive 3-GET PR \#1566 succeeded, but neither included these two exact 2026 five-region URLs. This contract is a separate source-specific reviewed access interface; access_id unique and no change to original 18 API readiness allowlist. Only an observed successful GitHub Actions direct job would authorize additional append-only direct-proof metadata in Neon; no raw source bodies/insured TIV.
