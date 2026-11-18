<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CBS Netherlands 85728NED: first original construction-input index row (2026-11-13)

## Research result — source and original-response boundaries

**Candidate ID:** `nl.cbs.new-build-input-cost-index.85728ned`.
The original national Dutch statistics table is
[CBS StatLine 85728NED](https://www.cbs.nl/nl-nl/cijfers/detail/85728NED)
(input price index for *new dwellings*, base **2021=100**).
The [Dutch government catalog entry](https://data.overheid.nl/en/dataset/5c716c45-b7fd-4fef-b3fc-d143a465646f)
assigns **CC BY 4.0** to the exact Dutch table and lists its
[official original standard OData API](https://opendata.cbs.nl/ODataApi/OData/85728NED).
CBS's own [StatLine API documentation](https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data)
allows automated processing of published data using OData; its **standard
API has a 10,000-cell per-request limit**, and its general service
use is subject to fair-use guidance. This review permits **only the
four explicitly fixed small requests** in the contract, not unlimited
polling, bulk OData crawling or use of other unrelated datasets.

An external read-only web-content intermediary was used to retrieve
exactly four public original JSON response bodies (each with OData
`$top=1` or `$top=3`) on 13 November 2026. The original-body
SHA-256 was computed from the returned base64-decoded bytes in
isolated research Neon SQL. Each response had the expected JSON shape.
**Limitation:** this is not a direct trusted GitHub-runner HTTP status,
content-range or redirect-chain attestation. No full CBS data table,
private personal microdata, original response body, credential or
insurer record was copied into Git or Neon.

| Original table-scoped HTTPS GET path | Original JSON body bytes | Original body SHA-256 | Research Neon sample | Neon API smoke receipt |
| --- | ---: | --- | --- | --- |
| `TableInfos?$top=1` | 7,166 | `372b89cb7d0ff974059b34c9b795fcbef6dfd7b51f8221c77dfc8c78afe0b9c8` | #75 public metadata | #22 |
| `Componenten?$top=3` | 1,935 | `dc4a8f2e924b6f1ba585bdf1dc42624c9a1d5cd57f2117398a1b52672ea2d018` | #78 public metadata | #23 |
| `Perioden?$top=1` | 227 | `14231aea87399143ceee8890710d38dcf5e9fbfd93aa74aa1756c1b0d5eba4fc` | #76 public metadata | #24 |
| `TypedDataSet?$top=1` | 276 | `59b9d7bb2e40ac61aaa9b4776666d07e923e55900d127940ca4d7f755b17d455` | #77 one original numeric input-index row | #25 |

The exact query prefix is
`https://opendata.cbs.nl/ODataApi/OData/85728NED/`.
These hashes are **per complete bounded response body**, not full
table/release hashes. The four Neon JSONB-derived summaries each have
a **separate** canonical JSONB SHA-256; their hash verification is not
proof of long-term historical data immutability. All four were saved
with `model_input_approved=false` and
`source_byte_persistence_authorized=false`.
All four API entries set `strict_repository_runner_executed=false`.

## First native numerical observation and independent metadata crosswalk

The first original `TypedDataSet` OData row has:

| Field | Official observed value |
| --- | --- |
| `ID` | `0` |
| `Perioden` | `2018MM01` |
| `Componenten` | `T001363` |
| `InputprijsindexBouwkosten_1` | **90.1** |
| `OntwikkelingTOVEenJaarEerder_2` | `null` |
| Base year | **2021 = 100** |

The independent `Perioden` metadata resolves `2018MM01` to
**January 2018** and classifies it as **definitive**
(`Definitief`). The separate `Componenten` metadata identifies
`T001363` as **total new-dwelling input construction costs**
(`Bouwkosten totaal`); two additional source-defined cost components
are wages (`A043942`) and building materials (`A043943`).
The original `TableInfos` record identifies `85728NED`,
modified **2026-10-30 02:00**, and available published months
January 2018 through September 2026. **Do not interpret missing
year-over-year percentage as zero**.

## Legal and scientific interpretation

- **Dataset licence:** official CBS data.gov listing CC BY 4.0.
  CBS source citation and change notice are required; do not imply
  CBS endorses OpenCatastrophe.
- **API terms:** CBS explicitly permits automatic StatLine OData processing,
  standard API maximum **10,000 cells/request**, fair use. The new
  access contract is `probe_ready` only for four exact GETs, no
  asynchronous schedule, arbitrary OData filters, bulk feed or retries.
- **Insurance use:** the value is a **dimensionless national price index**
  for labour/materials. It excludes machinery, overhead, profit and risk,
  land, energy and transport. It is **not** an estimated full rebuilding
  cost, insurer exposure, insured value/TIV, cadastral building age,
  hazard probability, catastrophe loss, commercial insurer pricing or
  policy-level statistical observation. For a complete construction-cost
  planning context, CBS itself distinguishes input from **output** indices;
  dataset `85772NED` is a different product and not a substitute.
- **Revision:** this is a rolling published index with both definitive
  and provisional periods. The one 2018 row was checked, **not the
  completeness of the 2018–2026 series**. Future observations require
  current release identity and original response digests.
- **CAT admission:** zero. Independent loss/replacement-cost validation
  and an actual intended consumer are required.

The separate private research rights ledger has seven
product/use-case-scoped entries for this exact table: commercial
product-use permission, small automated API access, internal research
and metadata recording as allowed, plus conditional source-sample,
redistribution and derived-publication controls. These do not
automatically apply to other CBS datasets or to a building-level
replacement cost.

## Exact direct-provider runner and offline tests

This PR provides the fixed-program script
[`scripts/probe_nl_cbs_85728ned_v0.py`](../../scripts/probe_nl_cbs_85728ned_v0.py).
The direct original HTTP job has **not yet run**; historical external
web-intermediary receipts are not counted as that stronger proof.
No network call occurs in ordinary CI or without explicit opt-in.

```sh
# Offline only: fail-closed contract + synthetic provider responses
python -m unittest tests.test_probe_nl_cbs_85728ned_v0 -v
python -m scripts.validate_source_access \
  access/nl.cbs.new-build-input-cost-index.85728ned.json

# Explicit, authorized, single manual original-provider verification:
python -m scripts.probe_nl_cbs_85728ned_v0 --live
```

The script allows exactly four CBS HTTPS URLs, requires direct
HTTP 200 without redirects, identity transfer, strict UTF-8
`application/json`, at most 16KiB per body, exact table/component/
period/index shape, and outputs only four original-body SHA-256 digests
with typed safe metadata. Original provider body contents are never
logged or persisted. Any changed CBS first row or service shape
fails closed until review.

**Next gate:** run the direct trusted probe with explicit permission;
then separately review full published index history and scientific
suitability for updating *national construction price indices* rather
than claiming individual insured building replacement costs.
