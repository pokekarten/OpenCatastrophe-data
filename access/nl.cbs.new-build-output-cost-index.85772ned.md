<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nl.cbs.new-build-output-cost-index.85772ned.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nl.cbs.new-build-output-cost-index.85772ned.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nl.cbs.new-build-output-cost-index.85772ned

## Source ids

- nl.cbs.new-build-output-cost-index.85772ned

**Provider:** Statistics Netherlands / Centraal Bureau voor de Statistiek (CBS)

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Service root:** <https://opendata.cbs.nl>

**Api version:** CBS StatLine OData 3 exact Dutch table 85772NED; output-price index for new dwellings 2021=100; official Modified 2026-09-30

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

- six_fixed_original_odata_rows

### Path templates

- /ODataApi/OData/85772NED/TableInfos
- /ODataApi/OData/85772NED/TypedDataSet
- /ODataApi/OData/85772NED/Perioden
- /ODataApi/OData/85772NED/DataProperties

**Parameter rules:** Six EXACT manually opt-in anonymous HTTPS GET URLs, not arbitrary OData queries. TableInfos?$top=1; TypedDataSet?$top=1; Perioden?$top=1; DataProperties?$top=6; TypedDataSet?$filter=Perioden%20eq%20%272026KW02%27&amp;$top=1; Perioden?$filter=Key%20eq%20%272026KW02%27&amp;$top=1. No caller inputs, pagination, path/host/query substitution, redirects, retries, credentials, bulk mirrors, schedule, feed endpoints or other CBS tables. Each request &lt;=16384 bytes and at most six aggregate public records, far below CBS standard 10000-cell limit.

## Response contract

### Expected media types

- application/json

**Format:** Six strict UTF-8 CBS OData 3 JSON bodies, one TableInfos, six DataProperties, one definitive 2018KW01 Perioden, one preliminary 2026KW02 Perioden, one source first numeric row and one fixed latest-quarter numeric row; only typed summaries and per ORIGINAL response SHA-256 receipts can leave memory. No provider original body persisted or logged.

**Scientific semantics:** CBS new dwelling OUTPUT construction price index base 2021=100, distinct from the 85728NED monthly INPUT-price index. This index includes contractor overhead and profit/risk but excludes land and developer/broker costs. VAT-inclusive and VAT-exclusive 2021=100 indices are explicitly separate CBS topic dimensions. Source 2018KW01 first official index=87.7 both variants (definitive); 2026KW02=133.4 both, 4.4% year-on-year, explicitly provisional. December 2025 publisher methodology correction revised 2022+ output indices up to 7.6 index points; no conflation of historical vintages. Index points are dimensionless, NOT full replacement cost in euros, insured building TIV, individual property values, hazards, stochastic losses or premiums.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `16384`

**Max sample bytes:** `16384`

**Retry policy:** none

**Rate limit notes:** CBS StatLine OData standard direct-use service permits automated limited public data use (max 10000 cells per request). This single explicitly manually opted-in test makes only six &lt;=6-row requests; no recurring polling, bulk download, unattended crawl or API rate/usage expansion.

**Mutability notes:** CBS table source metadata last Modified 2026-09-30T02:00:00 and original first/2026Q2 rows were observed on 2026-11-13. The CBS current-version dataset can be revised; freeze original response SHA256 and bytes per request, exact final URL, UTC, direct HTTP 200, no redirect; fail closed on schema, historical numeric, latest quarter or definitive-vs-preliminary status changes. December 2025 methodology correction makes earlier releases non-comparable without vintage reconciliation. Never assert all 2018-2026 quarters or entire asset hashes from six rows.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Official Dutch government CBS 85772NED catalogue explicitly CC BY 4.0, public API; CBS permits automated processing with 10000 cells/request standard API. Commercial derivative analysis with CBS attribution, change disclosure and no CBS endorsement is permitted for this exact public aggregated table. No rights for unrelated content, raw source-byte publication, insurer portfolio data or all CBS datasets are assumed. This legal product-use allowance is not scientific model admission or blanket bulk automation authorization.

## Probe contract

**Mode:** provider_specific

**Operation:** six_fixed_original_odata_rows

**Requires credentials:** `false`

### Expected evidence

- Exactly six immutable CBS table-85772NED HTTPS GETs, anonymous no-redirect 200 application/json identity encoding, strict original response size &lt;=16384 each
- Table ID/title/Modified 2026-09-30-or-later and exact six DataProperties with VAT index topics in 2021=100 units
- Definitive 2018KW01 first data row index 87.7; provisional 2026KW02 index 133.4 both VAT variants and 4.4 percent year-on-year
- Six distinct original source body byte lengths, SHA256 digests and retrieval UTC, never whole data table SHA or an inferred HTTP attestation from intermediary
- Source-licensed CC BY 4.0 with CBS attribution, Dec 2025 corrected methodology and provisional date, model_input_approved=false, original provider bytes not persisted

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://data.overheid.nl/dataset/48393-nieuwbouwwoningen--outputprijsindex-bouwkosten-2021-100>
- <https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data>
- <https://www.cbs.nl/nl-nl/cijfers/detail/85772NED>
- <https://opendata.cbs.nl/ODataApi/OData/85772NED>

**Notes:** Six original CBS output index metadata+actual-value responses were retrieved via an external web-content intermediary 2026-11-13 (Neon samples \#79-84, API receipts \#26-31). That is not a strict GitHub-runner proof. The new self-contained provider-specific script requires --live and runs no requests in PR CI; it is NOT added to the immutable reviewed_18 allowlist. No entire table, insurer data, source payload or model approval.
