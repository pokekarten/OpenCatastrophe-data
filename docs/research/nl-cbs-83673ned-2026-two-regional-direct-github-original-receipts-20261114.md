<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Actual trusted GitHub direct proof: CBS 83673NED 2026VJ06 2 x 5 macroregional values (14 November 2026)

## Completed original provider validation

Official CBS source: https://www.cbs.nl/nl-nl/cijfers/detail/83673NED
Standard public OData API: https://www.cbs.nl/en-gb/our-services/open-data/statline-as-open-data
Dataset rights: https://data.overheid.nl/dataset/4a90058c-8b48-4ad0-9f9f-6475dea718a5 — CC BY 4.0, cite CBS and state changes.

After earlier external-intermediary-only samples #95/#96 and external smoke API receipts #41/#42, actual trusted same-repository GitHub Actions original source run [43580334849](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43580334849), source-specific job 132403533534, directly contacted the public original CBS OData 3 table 83673NED at 2026-11-14T09:23:53.657761+00:00.

Source-specific GitHub job **SUCCESS** after 10 offline synthetic/negative security tests. Each source provider request was strictly anonymous exact-URL public HTTPS GET with no proxy, no redirects, no retries, original HTTP 200, application/json and identity body; maximum 8,192 bytes, 25 seconds. **Both original complete byte SHA-256 digests and body lengths match the previous independently intermediated source originals.**

| Original direct CBS source | Native source rows | Full source original HTTP bytes | SHA-256 original complete JSON |
| --- | ---: | ---: | --- |
| Rental A028867 / period 2026VJ06, fixed top=5 | NL01 and LD01–LD04 | 1,457 | 2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0 |
| Owner A028868 / period 2026VJ06, fixed top=5 | NL01 and LD01–LD04 | 1,459 | 67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3 |

**Private Neon append-only research metadata:** source_sample_v0 **#127 rental** and **#128 owner** now refer to original prior samples #96/#95, exact original public request URI, source response bytes+SHA256, this actual GitHub source run and job ID, a successful separate job status, and the source vintage/research scope. They are **not new independent source candidates** nor provider JSON duplicates. Old external smoke entries #41/#42 still accurately describe **intermediary-only** fetches; their strict direct-runner flag was never altered. The original source responses were not saved to GitHub files, workflow artifacts, Neon, or public source-repository files. The private derived receipt JSONB also has a separate independent canonical SHA-256 for each row.

## Source-native meaning and source-age caveats

The official CBS publication revision is 2026-08-20T02:00:00. The independent previously executed nine-GET original metadata proof in [PR #1542](https://github.com/pokekarten/OpenCatastrophe-data/pull/1542) confirmed the source period 2026VJ06 is **Voorlopig (preliminary)**: **July 2025 through June 2026**, twelve-month rolling mean.

Only **pure newly permitted dwellings from at least €50,000 excluding VAT** contribute to this source aggregate. Exactly five original source-native region codes exist per tenure (NL01 national aggregate and four macroregions LD01–LD04). The national aggregate **overlaps** and cannot be summed with the four regional averages.

Critical source field suffix mapping:
- GemiddeldeBouwkostenPerM_2 = **EUR per cubic metre**, despite suffix _2.
- GemiddeldeBouwkostenPerM_3 = **EUR per square metre**, despite suffix _3.
- GemiddeldeBouwkostenPerWoning_1 = **thousand EUR per granted pure-new-dwelling permit**.

These 2026 figures are **not** an insured portfolio value, geocoded house stock, repair/rebuilding cost, 2020 cadastral ground truth, actual CAT claims, or constant-quality price change from the definitive 2025 period. CC BY 4.0 legally permits commercial data reuse with CBS attribution but does **not** grant scientific model-input admission.

## Enforced research-provenance SQL gate

This PR hardens the existing private read-only SELECT at sql/research_cbs_83673ned_2026_landsdelen_receipts_v0.sql. It now explicitly joins the two externally obtained 2026 native-values summaries (#95/#96) with the two **separately recorded actual GitHub 200/original-byte source receipts** (#127/#128), pinned by original exact URL, SHA, byte counts, fresh canonical private JSONB hashes, Github run and job identity, version, provisional status, original-native-unit validation, and no raw/provider/model flags.

Successful replay against private Neon: **10 source-native region/tenure rows, all 10 with verified direct original GitHub SHA/HTTP provenance, zero blockers**. The query is **read-only**, does not call CBS, and creates no database records.

Four actual read-only Neon negative-control replays, each changing just one validation expectation in memory (no source/DB changes), returned **exactly one BLOCKED sentinel and zero source values**:
1. Wrong GitHub run identity.
2. Misleading native m³ vs m² unit crosswalk reversed.
3. Official period status incorrectly changed from preliminary to definitive.
4. Missing/false strict direct GitHub runner flag.

These direct research receipts can be used for **audited public-source statistical comparisons**. All samples, legal decisions and metadata still have model_input_approved=false and no raw source byte persistence. There is no implied calibration or scientific approval for insurer CAT models. The larger previously reviewed fixed 18-source provider allowlist remains untouched.

## Reproducibility and next boundary

Offline Python regression: python -m unittest tests.test_probe_nl_cbs_83673ned_2026_regional_two_v0 tests.test_cbs_83673ned_2026_landsdelen_receipts_sql_v0 -v

Source network must be explicitly opted into through the source-specific runner with --live-two, only two tiny exact original URLs; the PR-specific GitHub job is gated to this same-repository research branch.

The existing 2025 definitive-vs-2026 preliminary comparisons under [PR #1560](https://github.com/pokekarten/OpenCatastrophe-data/pull/1560) should next be gated with **independent direct original-source receipts for all six comparison URLs**; this is a separate review step. Compare public averages only and never infer a fixed-quality insurer replacement-cost inflation factor from the region/tenure changes.
