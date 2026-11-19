<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CBS StatLine 85772NED: native output-price index evidence, six bounded source receipts (2026-11-13)

## Scope and licensing

Canonical candidate `nl.cbs.new-build-output-cost-index.85772ned`.
Official publisher:
[CBS output price index for new dwellings](https://www.cbs.nl/nl-nl/cijfers/detail/85772NED).
The [Dutch government publication register](https://data.overheid.nl/dataset/48393-nieuwbouwwoningen--outputprijsindex-bouwkosten-2021-100)
licenses this public table **CC BY 4.0**.
The [CBS StatLine API guidance](https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data)
explicitly permits automated OData consumption of published
statistics and states that the *standard* direct API is limited
to **10,000 cells/request**. Source/producer acknowledgement to CBS and
change notice are required; publication or application to insured buildings
does not make CBS an endorsing party.

This receipt is the **85772NED quarterly output-price index**, *not*
85728NED (monthly labour/material **input** index), not the unrelated
CBS quarterly 83673NED regional permitted cost/m3 statistics, and not
direct replacement-cost data for insured buildings.

The output index includes contractor general costs, profit and risk,
and excludes land, developer and broker costs. It is dimensionless
(2021=100), and **VAT-inclusive/exclusive are separately defined
source dimensions** rather than a monetary VAT adjustment to estimated
insured TIV.

Important original publisher history:
- Official revision: **2026-09-30T02:00:00**, available 2018 Q1–2026 Q2.
- In **December 2025**, CBS corrected an error in the output price
  calculation; the post-2022 correction reached **up to 7.6 index
  points**. Do not silently mix older price-index releases.
- Most recent observed quarter Q2 2026 is **provisional**; the
  2018 first quarter is definitive. Definitive/provisional status
  cannot be treated identically in a price-inflation backtest.

## Six actual original public provider responses

On 2026-11-13 the original public OData 3 endpoints were read via a
read-only intermediary and original JSON body bytes encoded and
transiently decoded for independent SHA-256 and schema validation.
**This is not yet a trusted direct GitHub-runner HTTP/redirect proof.**
Only research summary JSON and per-body digests, not original provider
responses, are retained in the separate insurance Neon research DB.
All network requests were single-digit public aggregate records; the
full CBS table, source archives, personal records and insurer data were
not downloaded.

**Exact source URL prefix:** `https://opendata.cbs.nl/ODataApi/OData/85772NED/`

| Exact original OData path and fixed query | Original body B | Response SHA-256 | Neon sample | API receipt |
| --- | ---: | --- | ---: | ---: |
| `TableInfos?$top=1` | 6,273 | `f2c07dd01d01519cf3a67788c776b647d7171bebf45891ae6023d4890f6f69f3` | #84 | #27 |
| `TypedDataSet?$top=1` | 295 | `a59eecc7255a4b4cde5041731b21085d12655e5332dfbdf8398afb3983b6150f` | #79 | #29 |
| `Perioden?$top=1` | 229 | `a0134b3268ff7e3dcc26aaa32170661c7b22884d1aebf5909f978329e5d9d87f` | #83 | #31 |
| `DataProperties?$top=6` | 2,899 | `b809c031ff53bdfe6c6788baaf23954de2c8ab32352fc6dd22309ff552566139` | #82 | #26 |
| `TypedDataSet?$filter=Perioden%20eq%20%272026KW02%27&$top=1` | 296 | `d3ea69b8971a8c1e8cfe5027a188073c07e8310a2f332919f3e2abbf125959f2` | #80 | #28 |
| `Perioden?$filter=Key%20eq%20%272026KW02%27&$top=1` | 246 | `6368b06c36134a2b550be0c5b2a764d48a0ff938e61b3897362cb14d848f92d8` | #81 | #30 |

All **six** original body hashes are on the **complete small
intermediary-returned JSON body**, not the full table. The six separate
Neon `sample_sha256` fields refer instead to the canonical private JSONB
derived summaries; the original response body was never persisted.
There is no implied original HTTP status/redirect-chain attestation
until the new trusted provider-runner is separately dispatched.

## Native original numbers and exact source interpretation

| CBS original OData field | 2018 Q1 | 2026 Q2 |
| --- | --- | --- |
| Original `Perioden` | `2018KW01` | `2026KW02` |
| Native `ID` | 0 | 41 |
| Separate `Perioden.Status` | **Definitief** | **Voorlopig** |
| `Prijsindex_1` / **incl. btw** | **87.7** | **133.4** |
| `Prijsindex_3` / **excl. btw** | **87.7** | **133.4** |
| `OntwikkelingTOVEenJaarEerder_2` / incl. btw | `null` | **4.4%** |
| `OntwikkelingTOVEenJaarEerder_4` / excl. btw | `null` | **4.4%** |
| Reference base | 2021=100 | 2021=100 |

The original `DataProperties` response **independently** connects the
VAT-inclusive topic group to `Prijsindex_1` and the VAT-exclusive
topic group to `Prijsindex_3` and validates the exact index units.
The independent `Perioden` responses prove the *finality state*
of each observation. A missing first-year YoY value is **unknown / null**,
not zero.

These are national **statistical price-index points**, not per-m3
construction costs, individual building TIV, property-market sale values,
CAD building replacement-cost estimates, claim inflation, peril hazards
or any stochastic annual exceedance probability. Both 2018/2026 points
are source values; interpolation, annualization and portfolio mapping
require separate scientific consumer design and a vintage-appropriate
benchmark.

## Rights and model-admission split

Seven exact source/product/use-case decisions are held separately in
Neon `research.source_usage_rights_v0`, not overwritten in the
historical candidate snapshot: automated *bounded* OData and
commercial reuse permitted; raw redistribution, research sample
extensions and derived publication conditional; internal
research/metadata permitted. Each has
`scientific_model_admission=false`,
`original_asset_admitted=false`.

Neon `research.source_sample_v0` #79–84 are each
`model_input_approved=false` and
`source_byte_persistence_authorized=false`. The repository stores
no original JSON, raw CBS values beyond the two disclosed tiny
published index points, insurer portfolio, secret or API key.

## Direct-provider verification gate (not yet executed)

New script `scripts/probe_nl_cbs_85772ned_v0.py` requires explicit
`--live` and the exact frozen contract
`access/nl.cbs.new-build-output-cost-index.85772ned.json`.
It has no provider network access during normal CI, is **not** added
to the existing immutable `reviewed_18` runner, and does not
change source/manifests. The six exact real GETs must return HTTP 200
with no redirects, original JSON (<=16KiB each), source revision
2026-09-30, exact legal/scope and the first and Q2 2026
VAT/index/finality fields above. Then it emits only SHA-256 digests,
original response byte sizes, UTC and typed safe metadata; no provider
body is written.

```sh
python -m unittest tests.test_probe_nl_cbs_85772ned_v0 -v
python -m scripts.validate_source_access \
  access/nl.cbs.new-build-output-cost-index.85772ned.json

# Only by a reviewer in a separately approved direct-provider environment:
python -m scripts.probe_nl_cbs_85772ned_v0 --live
```

**Next:** independent direct-probe and published vintage checks, then a
separate index-year alignment to the CBS 85728NED *input* index
and 83673NED permitted €/m³ *absolute-cost* table.
None of these steps may alone create insured building values or CAT
model scientific admission.
