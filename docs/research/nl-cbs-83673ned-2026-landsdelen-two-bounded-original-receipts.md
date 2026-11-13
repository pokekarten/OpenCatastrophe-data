<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CBS 83673NED: two original five-row 2026 landsdeel construction-cost receipts (2026-11-13)

## What is newly observable

Official source: [CBS StatLine 83673NED](https://www.cbs.nl/nl-nl/cijfers/detail/83673NED),
an aggregate **new-dwelling granted-building-permit cost** statistical table.
The original [Dutch government register](https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5)
lists source rights **CC BY 4.0** and publication revision **20 August 2026**.
The official [CBS StatLine OData manual](https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data)
allows machine processing, with the standard service limited to **10,000 data cells per request**.

We now have two **additional**, fixed, small original public CBS OData JSON
bodies: one for **rental** (`A028867`) and one for **owner-occupied**
(`A028868`) new dwellings, both restricted to rolling observation
`2026VJ06` (**July 2025 through June 2026**) with `$top=5`.
Each body contains the national `NL01  ` row **plus four
macroregions** `LD01  `–`LD04  ` and no household, property address,
individual building or insurer identifier. In total there are
**ten official aggregate records, eight previously absent
regional records**, in exactly two original provider-response bodies.

All ten source records are explicitly **provisional**, not definitive.
The source is a 12-month rolling-average measure from granted
**pure new-dwelling** permits of at least **€50,000 excluding VAT**,
with mixed-use/recreational combined projects excluded. It does not
measure post-event rebuilding cost, existing building insured
replacement value, claims, TIV or a full stock replacement valuation.

## Exact source-body provenance

The two exact GET endpoints use the fixed URL root
`https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet`.
Percent-encoding, source code spacing, `$top=5`, product ID,
period and fixed tenure are part of the identity.

| Reviewed public fixed-query scope | Complete bounded original JSON bytes | Original body SHA-256 | Neon research sample | Neon external smoke receipt |
| --- | ---: | --- | ---: | ---: |
| `?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5` | 1,457 | `2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0` | #96 | #41 |
| `?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5` | 1,459 | `67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3` | #95 | #42 |

The two original public JSON bodies were obtained on
13 November 2026 through an **external read-only web-content
intermediary** and transiently decoded/hashed in private Neon SQL.
Their original complete bounded-body hashes and byte lengths
were recorded, as were separate SHA-256 hashes of each private
derived JSONB research sample. **The original JSON bodies are
not committed to Git, nor persisted in Neon.** A source-body hash
is different from a digest of the private JSONB summary.
The external intermediary does **not** constitute an independently
attested direct GitHub Actions HTTP 200/no-redirect-chain proof.

The separate private research rights ledger gained **seven narrowly
product-scoped use-case decisions** for this *two-query* acquisition;
this does not expand every CBS API entitlement. Commercial
use of public statistical aggregates is licensed (with CBS attribution
and change notice), while private expanded samples, raw redistribution
and published transformations remain bounded by purpose.
Every sample and rights record keeps
`model_input_approved=false`,
`scientific_model_admission=false` and
`original_asset_admitted=false`.

## Quality and scientific safeguards

The two original JSON bodies were each limited to **five records**.
Independent existing CBS official metadata identifies the source
`RegioS` values, two native ownership codes, the publisher
revision and preliminary status.

**Critical native source unit mapping:** CBS's misleading field
`GemiddeldeBouwkostenPerM_2` is **EUR per m³**, whereas
`GemiddeldeBouwkostenPerM_3` is **EUR per m²**.
This map is checked in the private research query; ordinary
variable-name suffixes are NOT accepted as proof of meaning.

The new standalone, **SELECT-only** SQL
[`sql/research_cbs_83673ned_2026_landsdelen_receipts_v0.sql`](../../sql/research_cbs_83673ned_2026_landsdelen_receipts_v0.sql)
reads only exact original URL+SHA-matched
**private derived summaries**, checks the canonical JSONB receipt
hash, source vintage, provisional status and the explicit mapping,
and expands into exactly **5 region IDs × 2 tenure IDs**.
It refuses to mark the research comparison as complete if a
source receipt is missing, a region is duplicated, or dimension
consistency with published mean dwelling area/volume exceeds
**€2,000** in the rounded average statistics. This €2,000 is
a **research sanity tolerance**, not a pricing/model error budget.

A live private Neon SELECT against this exact query produced **10
rows, 10 distinct region-tenure pairs, 10 research-valid comparisons
and 0 research blockers**. This verifies the *two private receipt
summaries*, not the wider CBS time series or provider HTTP transport.

**Important interpretation:** `NL01` is the national aggregate
and must **not** be summed with the four landsdelen. The rent/owner
means should not be averaged together or projected to insured
buildings without source counts/exposures and independent stock
representation. A West-vs-South construction-permit average
difference is not a CAT vulnerability parameter.

## Repository/runner boundaries and next gate

No original source-response bytes, API tokens, insurer exposures, raw
property data, copied large CBS tables or full regional downloads
are added here. The protected query accesses the separately operated
private insurance research Neon DB only when explicitly run by an
authorized reviewer, and makes **zero provider requests**.

```sh
# Offline static guard, no Neon or CBS network during GitHub CI:
python -m unittest tests.test_cbs_83673ned_2026_landsdelen_receipts_sql_v0 -v

# Only on an already configured private insurance research DB connection:
psql -X -v ON_ERROR_STOP=1 \
  -f sql/research_cbs_83673ned_2026_landsdelen_receipts_v0.sql
```

The separate existing [CBS nine-request direct-runner draft
PR #1542](https://github.com/pokekarten/OpenCatastrophe-data/pull/1542)
remains scoped to **nine different fixed URLs**; it is
**not** altered or silently expanded to include these two
new five-row regional GETs. A separate explicit review of
these two exact direct-provider requests, HTTP status/redirect
attestation, changing table vintage and access scope is needed
before adding them to any trusted GitHub source-API workflow.
The existing **18 fixed reviewed live probes** have not been
executed by this work, and this PR cannot grant CAT scientific
admission.

**Next:** align these independently observed regional permit-cost
proxies with the original EU building stock, GIS footprints and
typology/age sources; quantify new-build permitting selection
bias and explicitly validate replacement-cost targets before any
insurance model consumes them.
