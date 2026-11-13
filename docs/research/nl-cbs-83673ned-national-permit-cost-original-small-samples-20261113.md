<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CBS 83673NED: original public permit-cost samples in €/m³ and €/m² (2026-11-13)

## Source, rights and actual scope

**Canonical source:** `nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned`
([CBS original publication](https://www.cbs.nl/nl-nl/cijfers/detail/83673NED)).
The [Dutch national catalogue](https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5)
publishes table **83673NED** with **CC BY 4.0** rights.
CBS's [official StatLine API manual](https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data)
permits automated public OData processing, with a **10,000-cell per
request** ceiling for the standard direct API. Nine limited public
aggregated original-source rows/metadata sets were investigated.

This CBS source publishes a *12-month moving annual average* of
**construction sums on granted permits** for pure new rental or
owner-occupied dwellings, split by four Dutch macroregions and the
national aggregate. Permit sums are **excluding VAT**, in projects
where the reported building cost is **at least €50,000**. Mixed-purpose
developments and certain combined housing/recreation/commercial
projects are excluded. It is **not** the actual reconstruction cost
of an existing damaged building, net insured sum/TIV, an insurance
claim, a national property-price survey, or an insurer market share.

**Original CBS publication revision:** `2026-08-20T02:00:00`.
The latest published moving annual observation
`2026VJ06` covers **July 2025–June 2026** and is **provisional**
(`Voorlopig`); the earliest checked `2012VJ12` is definitive.
CBS may revise provisional values and rolling periods; neither
should be silently labeled a final insured loss input.

## Verified actual original source responses — exact bounded GETs

Each response was acquired via an external read-only intermediary as
a **small complete source JSON body**, encoded as base64 and
transiently decoded inside the research SQL environment to verify
original byte length, strict JSON shape and original-body SHA-256.
These receipts **do not establish independent original HTTP
200/redirect-chain attestation** and are NOT executions of
the repository's strict direct GitHub runner.
No original provider response bodies, secret keys, cadastral
geometries, building addresses, portfolios, insurer claims, bulk
CBS tables or whole-body originals were persisted in Neon or public
Git.

**Exact public source prefix:**
`https://opendata.cbs.nl/ODataApi/OData/83673NED/`

| Original GET path | Bytes | Original response SHA-256 | Neon derived sample | API receipt |
| --- | ---: | --- | ---: | ---: |
| `TableInfos?$top=1` | 9,623 | `d07e770db896baff8ff9b910d7b11413701921ca422590d99a555fbbecd6a16f` | #90 | #40 |
| `TypedDataSet?$top=1` | 395 | `92115f31bbebf8d3300205cbaccb9fb1f553bbdc4240731405638540ef343bb2` | #87 | #35 |
| `DataProperties?$top=10` | 5,249 | `8bb0cd9f957b1f064d21deb1de16c59c0de6d024d8b3d9c0de464295a32b0353` | #86 | #38 |
| `Eigendom?$top=3` | 636 | `de457be8ce7458dbde9a1407641c780d2fff7f7f8084539c1fcdb3a3de64dabb` | #91 | #36 |
| `RegioS?$top=5` | 1,202 | `8d9ea835880a4b23518490dbdbcdb12aab5c2a52df3ed17c73201a4f9e49fbd9` | #85 | #33 |
| `Perioden?$top=1` | 243 | `f6c4a1ff5800e4e426f5245d9a940f9e018359fb7da435d4183bce68f347b0e1` | #88 | #34 |
| `TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27&$top=1` | 398 | `efbc0adc179275dc12a0a6ffbfe3d581c11c4f41c5e8ca0a0f876116b165fb03` | #89 | #32 |
| `Perioden?$filter=Key%20eq%20%272026VJ06%27&$top=1` | 251 | `ebe2b837bc17b3b48b14df38c2abc078ea2da4056ff37f32b77653c3a85e6fe0` | #92 | #39 |
| `TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27%20and%20RegioS%20eq%20%27NL01%20%20%27&$top=1` | 399 | `ce939d57457bc13e96fb9e69a4f34c17ffac073b348e95d40e414efe7d00ee5f` | #93 | #37 |

The JSONB summary of each of the nine stored sample records has a
**distinctly computed** canonical SHA-256 in private Neon; it is NOT
the same as the corresponding source-original body digest. Each
sample is tagged `model_input_approved=false` and
`source_byte_persistence_authorized=false`. The nine direct
intermediary probe receipts set
`strict_repository_runner_executed=false`.

## Native provider schema: important suffix/units trap

The source's `DataProperties` metadata resolves the misleading
field-name suffixes: these **MUST NOT BE SWAPPED**.

| Original field | Actual native CBS measurement |
| --- | --- |
| `GemiddeldeBouwkostenPerWoning_1` | Average permit cost per new dwelling, **thousand EUR** |
| `GemiddeldeBouwkostenPerM_2` | Average permit cost per **m³**, EUR |
| `GemiddeldeBouwkostenPerM_3` | Average permit cost per **m²**, EUR |
| `GemiddeldeInhoudWoningen_4` | Mean new dwelling volume, m³ |
| `GemiddeldeOppervlakteVanWoningen_5` | Mean new dwelling floor area, m² |

The separate `Eigendom` native codebook proves
`A028867` = **Huurwoningen** (rental)
and `A028868` = **Koopwoningen** (owner-occupied).
The separate `RegioS` codebook preserves exact source code
`NL01  ` (two significant trailing spaces) as **Nederland**,
plus four `LD01  ` through `LD04  ` macroregions. **Never
trim native CBS source keys before exact matching**.

## Three actual original provider numeric rows

| Original native and independently cross-checked meaning | Historic rental NL 2012 | Latest rental NL 2025 Jul–2026 Jun | Latest owned NL 2025 Jul–2026 Jun |
| --- | ---: | ---: | ---: |
| `Perioden` | `2012VJ12` | `2026VJ06` | `2026VJ06` |
| Original row `ID` | 0 | 54 | 329 |
| Original `Eigendom` | `A028867` | `A028867` | `A028868` |
| Original `RegioS` | `NL01  ` | `NL01  ` | `NL01  ` |
| Status | **Definitief** | **Voorlopig** | **Voorlopig** |
| Average permit cost per dwelling | €95k | **€149k** | **€215k** |
| Average permit cost per m³ | €258 | **€488** | **€438** |
| Average permit cost per m² | €748 | **€1,473** | **€1,297** |
| Mean dwelling volume | 370 m³ | 306 m³ | 490 m³ |
| Mean dwelling floor area | 127 m² | 101 m² | 165 m² |

The two latter observations independently agree with the publisher's
current public CBS table. They are **sample national permit averages
for selected projects**, not automatically representative of every
existing insured building or rebuilding after catastrophe.
Do not blindly multiply the per-dwelling mean by building count to
obtain actual insurer TIV, or reverse engineer individual building
records. Source selection, era, region, dwelling type, floor area/
volume, construction standards, demand surge and independent claims
calibration must be assessed separately. Do not sum the already
averaged moving-year periods as independent annual observations.

## Legal-use-case and execution gates

Seven product-/use-case-scoped rights entries have been stored
in private research Neon for this exact 83673NED product:
commercial product use and limited OData automated use **allowed**
with CBS CC BY attribution; internal research/metadata **allowed**;
raw publication, extended research samples and derived publication
**conditional**; all `scientific_model_admission=false`,
`original_asset_admitted=false`.
These rights **do not generalize** to personal data, insurer data
or other unrelated CBS products.

New `access/nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned.json`
is deliberately **`documented_only`**. It lists the exact original
host, table, nine fixed URL choices, native codes and rights; it
**does not authorize live network execution in GitHub yet** and
is not added to the existing 18 strict provider allowlist.
The associated synthetic tests protect this fail-closed status and
the exact column/units crosswalk. A subsequent approved
source-specific provider script must verify HTTP 200/no redirects,
exact original source-body hashes and a frozen source revision before
any `probe_ready` classification.

```sh
python -m unittest tests.test_cbs_83673ned_permit_cost_original_access_v0 -v
python -m scripts.validate_source_access \
  access/nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned.json
```

**Next for CAT/insurance research:** Once source-scoped
rights and a trusted original direct runner are approved,
map the national and four regional rental/owner averages to
a **clearly labelled synthetic estimate only**; measure coverage
bias and compare to independent cadastral building measurements,
historic building stock, construction typology and replacement-cost
benchmarks before considering actual insurer exposure estimation.
