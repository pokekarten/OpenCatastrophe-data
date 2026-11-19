<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nl.cbs.new-build-input-cost-index.85728ned.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nl.cbs.new-build-input-cost-index.85728ned.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nl.cbs.new-build-input-cost-index.85728ned

## Source ids

- nl.cbs.new-build-input-cost-index.85728ned

**Provider:** Statistics Netherlands (Centraal Bureau voor de Statistiek, CBS)

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Service root:** <https://opendata.cbs.nl>

**Api version:** CBS StatLine standard OData 3 interface, fixed table 85728NED, 2021=100, published revision 2026-10-30

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

- four_fixed_odata_rows

### Path templates

- /ODataApi/OData/85728NED/TableInfos
- /ODataApi/OData/85728NED/Componenten
- /ODataApi/OData/85728NED/Perioden
- /ODataApi/OData/85728NED/TypedDataSet

**Parameter rules:** Exactly four immutable anonymous HTTPS GET URLs on one explicit manually invoked --live run. Each OData path is fixed to StatLine 85728NED, with exact query ?$top=1 except Componenten with ?$top=3. Do not permit caller-specified host/table/period/component, arbitrary OData filter/select/top, pagination, feed, redirects, credentials or retries. Validate 4 fixed JSON bodies and observed one-row numerical crosswalk; a source revision failing the frozen format/first-row invariants fails closed. The CBS standard OData API is for limited direct access, capped at 10,000 cells per request; this contract uses at most three records at once.

## Response contract

### Expected media types

- application/json

**Format:** Four original CBS OData 3 JSON responses: one TableInfos row with Identifier=85728NED and 2021=100 title; three native Componenten entries (T001363 total, A043942 wages, A043943 materials); one Perioden row (2018MM01 definitive); one TypedDataSet row (2018MM01, T001363, input index 90.1, 2021=100). Each HTTPS body &lt;=16KiB, strict UTF-8, no duplicate keys or NaN, expected value count and original byte SHA-256. No source bytes retained; output contains only safe typed metadata and original response digests.

**Scientific semantics:** This national monthly input price index measures changes in new Dutch residential construction wages and materials. It excludes machinery, general costs, profit and risk, land, and other items such as energy and transport; it is not an output price index, unit cost per square metre, property appraisal, insured replacement cost, TIV, individual building location, climate hazard, stochastic loss, or insurer market-share observation. 2021=100 index is dimensionless; 2018 January 90.1 is a source table observation. Index series can be revised and non-final periods must not be treated as final. Do not substitute separate CBS 85772NED output-price index.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `16384`

**Max sample bytes:** `16384`

**Retry policy:** none

**Rate limit notes:** CBS official StatLine standard OData service supports programmatic use and limits data retrieval to 10,000 cells per request. Exactly four small manually initiated public GET requests, no retry or scheduled polling, no catalog crawl, no entire table download, no large Feed requests, no arbitrary OData query selection; preserve CBS fair-use guidance. Four responses together at most 64KiB.

**Mutability notes:** CBS source metadata observed 2026-11-13 names 85728NED with official published Modified 2026-10-30T02:00:00 and period Jan 2018-Sep 2026. Rolling updated monthly; this pin is an observed date, not a perpetually immutable snapshot. Each later live request must record UTC, exact URL, response byte length and SHA-256, status/redirect and table revision before updating any estimate. Historical 2018 first row may be revised, in which case fail closed pending renewed schema/value review.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Official Dutch government catalogue lists CBS StatLine table 85728NED and its OData API under CC BY 4.0; CBS official website says StatLine standard API is designed for automated limited data requests and capped at 10,000 cells/request. Commercial research/derived use is permitted with explicit CBS attribution, change notice and no implied CBS endorsement; actual original-body retention and source publication remain separately reviewable. CBS copyright exceptions for photographs/logos and third-party rights do not cover this approved statistical table; no person-level microdata or proprietary insurer values are retrieved. Approval does not include bulk API mirroring, unbounded polling, general OData v4 website API or other Dutch property/claims sources. This 2018 first-row one-record research observation alone does not grant CAT model scientific admission.

## Probe contract

**Mode:** provider_specific

**Operation:** four_fixed_odata_rows

**Requires credentials:** `false`

### Expected evidence

- Four exact 85728NED anonymous direct HTTPS 200 responses, matching final requested URL with no redirect or content encoding, application/json and &lt;=16384 bytes each
- Strictly one TableInfos row, exactly three component identity rows, one definitive 2018MM01 period, and one original data row with 2018MM01/T001363 and 90.1 input-index value
- All four original body SHA256 and byte lengths plus UTC, no original provider response body retained, no data beyond one numeric index cell
- Independent CBS CC BY 4.0, product definition, 10000-cell API cap, revision, no endorsement and attribution preserved
- Explicit research_only, model_input_approved=false, no insured TIV or other financial exposure admitted

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://data.overheid.nl/en/dataset/5c716c45-b7fd-4fef-b3fc-d143a465646f>
- <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>
- <https://www.cbs.nl/en-gb/our-services/open-data>
- <https://www.cbs.nl/en-gb/about-us/website/copyright>
- <https://www.cbs.nl/en-gb/figures/detail/85728ENG>
- <https://opendata.cbs.nl/ODataApi/OData/85728NED>

**Notes:** One fixed public 85728NED first-data-row capability probe only. Original four response bodies were independently observed through an external web-content intermediary on 2026-11-13 and summarized as research Neon samples \#75-\#78 and API receipts \#22-\#25. This observation is NOT strict GitHub Actions runner attestation. This contract proposes an explicit manually opt-in direct provider script with offline synthetic tests; no live request in PR CI or GitHub weekly workflows. No complete 2026 index series, replacement-cost/TIV or model admission.
