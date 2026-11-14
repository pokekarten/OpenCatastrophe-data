<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CBS 83673NED: 2025 definitive vs 2026 preliminary regional permit-average research comparison (2026-11-13)

## Research question and original official publisher scope

Can we compare exactly the **July 2024–June 2025** (`2025VJ06`, **Definitief**) and **July 2025–June 2026** (`2026VJ06`, **Voorlopig**) **rolling twelve-month annual means** of permitted pure-new-dwelling construction costs per m² and per m³ in the Netherlands and four landsdelen, separated into rental and owner-occupied permits, without implying actual **insured replacement costs**?

**Yes as descriptive research on official published averages, not as a building-cost inflation or insurer TIV model.** The distinction between fixed-source, revised definite 2025 observations and provisional 2026 observations is source-native and independently checked through two separate `Perioden` body receipts.

Primary sources:
- [Official CBS 83673NED source and publication status](https://www.cbs.nl/nl-nl/cijfers/detail/83673NED) — publisher modification **20 August 2026, 02:00**.
- [Official Dutch government CBS open-data licence](https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5) — **CC BY 4.0** including commercial licensed data reuse with attribution, change notice and no implied endorsement.
- [CBS standard StatLine OData API](https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data) — public automated use subject to **10,000 cells per request** on the standard API.

These statistics apply only to **granted pure new-dwelling permits of at least €50,000 total construction sum excluding VAT**; combined residential-commercial, mixed housing-unit, recreational and other mixed permit cases are excluded. The **national** code `NL01  ` includes the four **macroregions** `LD01  ` to `LD04  `; **do not add the national row to the regions**. CBS national figures and region-wide averages have different reporting composition and weights.

The official native `DataProperties` field mapping is counterintuitive:
- `GemiddeldeBouwkostenPerM_2` is **euros per m³** (cubic metre);
- `GemiddeldeBouwkostenPerM_3` is **euros per m²** (square metre);
- `GemiddeldeBouwkostenPerWoning_1` is **thousands of euros per permitted dwelling**.

Do **not** interpret either a change in original mean €/m² or mean €/m³ as a constant-quality price index for identical buildings. Project/area/volume composition and revision status vary between periods. These are **not** claims, premiums, actual rebuilding quotes, 2020 cadastral valuation, insured exposure or stochastic CAT losses.

## Six exact original public CBS source response receipts

All **six original complete small JSON response bodies** were obtained via read-only intermediary, with original-body byte lengths and SHA-256 digests transiently computed; no original provider JSON was retained in Git or Neon. **These receipts do not attest direct HTTP transport status or no redirects by a trusted GitHub runner.**

Exact source prefix: `https://opendata.cbs.nl/ODataApi/OData/83673NED/`.

| Provider original bounded response | Bytes | Original body SHA-256 | Research Neon sample | External API log |
| --- | ---: | --- | ---: | ---: |
| `TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5` — definite rental | 1,457 | `70731cf7be6e73813059c250db9f1f21ad4024f0fb7cba5075ad8af666d90a5e` | #98 | #44 |
| `TypedDataSet?$filter=Perioden%20eq%20%272025VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5` — definite owner | 1,459 | `7c9b9e307fd7fbf4ef8d5e9e26eaf3d9b9a991dd54a6b95c01409d22663c5908` | #99 | #45 |
| `Perioden?$filter=Key%20eq%20%272025VJ06%27&$top=1` — **Definitief** | 234 | `626dac3ab357839e615bcf0260237651d4a3983a88a0f18f6c8e3bfc24272c4d` | #97 | #43 |
| `TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028867%27&$top=5` — preliminary rental | 1,457 | `2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0` | #96 | #41 |
| `TypedDataSet?$filter=Perioden%20eq%20%272026VJ06%27%20and%20Eigendom%20eq%20%27A028868%27&$top=5` — preliminary owner | 1,459 | `67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3` | #95 | #42 |
| `Perioden?$filter=Key%20eq%20%272026VJ06%27&$top=1` — **Voorlopig** | 251 | `ebe2b837bc17b3b48b14df38c2abc078ea2da4056ff37f32b77653c3a85e6fe0` | #92 | #39 |

The original response SHA-256 is **not** the canonical JSONB research summary `sample_sha256`. The latter is verified separately for each private Neon source summary. All six are `research_only`, `model_input_approved=false`, `source_byte_persistence_authorized=false`; the external API receipts also set `strict_repository_runner_executed=false`.

The three **new** older-period receipts are #97–99, #43–45; the three 2026 receipts are reused original data from earlier research. Seven additional 2025VJ06 product-/use-case-scoped rights decisions were added to Neon, with all `scientific_model_admission=false` and `original_asset_admitted=false`. There is no claim of six newly discovered sources or of 20 independent raw files.

## Direct native descriptive comparisons per m²

| Region (CBS macroregion) | Rental 2025 definitive €/m² | Rental 2026 preliminary €/m² | Change in average | Owner 2025 definitive €/m² | Owner 2026 preliminary €/m² | Change in average |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Netherlands (national aggregate)** | 1,417 | 1,473 | **+3.95%** | 1,221 | 1,297 | **+6.22%** |
| North Netherlands | 1,371 | 1,223 | **−10.80%** | 1,258 | 1,308 | +3.97% |
| East Netherlands | 1,337 | 1,356 | +1.42% | 1,159 | 1,234 | +6.47% |
| West Netherlands | 1,577 | 1,647 | +4.44% | 1,328 | 1,425 | **+7.30%** |
| South Netherlands | 1,258 | 1,280 | +1.75% | 1,114 | 1,171 | +5.12% |

Calculated as exactly **(2026 mean ÷ 2025 mean − 1) × 100**, rounded to two decimals. The SQL additionally returns €/m³ changes and **changes in mean permitted cost per dwelling**. Those can diverge because new dwelling area/volume and the composition of applications differ; it would be a statistical error to treat them all as a single constant-quality construction price change.

For example the observed **northern rental −10.80% €/m²** is a change in permit-application mean for the selected new-construction projects, *not* evidence that insurers in northern Netherlands can reduce rebuilding cost inflation by 10.8%. Historical source vintages, construction quality, labor/material split, demolition, post-CAT demand surge and individual building use/age remain separately unresolved.

## Fail-closed read-only research query

The new [SQL](../../sql/research_cbs_83673ned_2025_definitive_2026_preliminary_v0.sql)
requires **four fixed, exact original-response URI+SHA+byte-identity pairs** for the two selected years × two tenures, plus **both fixed original period-status receipts**. Source metadata must match the **CBS publisher 2026-08-20 revision**, corrected native m²/m³ crosswalk, official two-trailing-space region keys and required period finality. Both the original bounded-body SHA and canonical private JSONB sample SHA are checked; research Neon also must contain separate scoped API receipts without any false trusted direct-runner indication.

The query enforces **20 regional/tenure/period observations** with no duplicates and exactly **10 valid inter-year region/tenure pairs**; rounds cost × mean area/volume sanity checks within €3,000 to account for independently rounded published means. That tolerance is a **research sanity check, not an insurance valuation model error tolerance**.

The SQL is **one SELECT-only statement**. It emits **one explicit BLOCKED sentinel** instead of any comparison if the six source proofs/statuses, sample hashes or official semantics do not pass, and never approves CAT model input or runs an API request. Replay against research Neon returned **10 validated comparisons and 0 BLOCKED rows** as of 2026-11-13. All CI tests are offline.

```sh
python -m unittest tests.test_cbs_83673ned_2025_2026_original_pair_sql_v0 -v

# Only with authorized private research Neon credentials (never in GitHub CI):
psql -X -v ON_ERROR_STOP=1 \
  -f sql/research_cbs_83673ned_2025_definitive_2026_preliminary_v0.sql
```

## Next admission boundaries

The existing [CBS 83673NED direct nine-request source runner draft PR #1542](https://github.com/pokekarten/OpenCatastrophe-data/pull/1542)
does **not** cover these 2025VJ06 URLs; this PR leaves that contract unchanged. The separate [2026 regional five-row research PR #1553](https://github.com/pokekarten/OpenCatastrophe-data/pull/1553) stays unchanged too. No GitHub Actions dispatch for these three new requests is implied, and no new full CBS table, raw provider body, property-level geometry or insurer portfolio is written.

Before linking to synthetic insurer portfolios, one must review independent exposure stock age/use, postcode-to-landsdeel mapping with correct regional crosswalk, dwelling-type calibration, construction mix bias, time revisions, VAT and coverage assumptions, loss demand surge and insured TIV contract definitions. Only after a separately approved source/science/legal review should an insurer-model consumer be built.

## 2026-11-14 update — all six comparison URLs directly provider-verified

The six exact original public OData response URIs used in this descriptive inter-year comparison **are now independently direct GitHub-verified**, in addition to the older external-intermediary complete original JSON byte evidence. This closes a previously missing **technical original-provider HTTP transport attestation** for these particular six URLs, not source-wide scientific or insurance-model admission.

| 2025/2026 exact source scope | Original direct GitHub run | Job | Durable private research-only direct-proof sample |
| --- | --- | --- | --- |
| 2025VJ06 rental five regional rows | [43500093202](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43500093202) | 132143531309 | #102 |
| 2025VJ06 owner five regional rows | same 2025 direct run | same | #103 |
| 2025VJ06 definitive Perioden status | same 2025 direct run | same | #104 |
| 2026VJ06 rental five regional rows | [43580334849](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43580334849) | 132403533534 | #127 |
| 2026VJ06 owner five regional rows | same 2026 regional run | same | #128 |
| 2026VJ06 provisional Perioden status | [43501313224](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43501313224) | 132147517168 | #119 |

These metadata-only source-proof samples contain actual provider HTTP/whole response SHA-256/byte counts plus GitHub run/job and provenance. The previous intermediary source data samples #95–99, external smoke entries #39 and #41–45 and the older original 2026 Perioden source sample remain **unchanged**. No original CBS raw JSON bodies were persisted in Git, Actions artifacts or Neon, and no CAT model/TIV approval was granted.

The read-only canonical research SQL at sql/research_cbs_83673ned_2025_definitive_2026_preliminary_v0.sql is upgraded to require all **six** direct GitHub receipt identities (exact source URL+original provider body SHA256+byte count, canonical private JSONB SHA256, fixed trusted job IDs and successful original-source 200/no-redirect attestations), in addition to earlier independently intermediary-observed original source bytes, source publication/vintage flags and source-native value/metric checks. With the private research database, the updated query returned exactly **10 research-only comparisons, zero blockers**.

Five live database **read-only negative-control replays** each returned exactly **one BLOCKED_INCOMPLETE_OR_UNVERIFIED_SOURCE_EVIDENCE sentinel and zero comparison values**: absent original 2025 GitHub run; absent 2026 regional GitHub run; absent 2026 period GitHub run; wrong native €/m³ unit; and a mismatched original-body SHA join.

**Interpretation remains unchanged:** The CBS 2025VJ06 figures are definitive, 2026VJ06 provisional; the native series consists of rolling averages of **new pure-dwelling granted permit projects**, not constant-quality same-building reconstruction inflation, existing property TIV, insured claims or an insurer portfolio model. Publishing or commercially using the official aggregate data is permitted with CBS attribution under CC BY 4.0, but all 10 comparison rows remain strictly **research-only, model_input_approved=false**.
