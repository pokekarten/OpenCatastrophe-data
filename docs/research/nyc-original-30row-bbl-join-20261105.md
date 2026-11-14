<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NYC LL84 2024 ↔ PLUTO 26v2: actual original-source 30-row smoke

**Date:** 2026-11-05. **Scope:** research-only, bounded, public original-provider read access; no source admission or insured exposure.

## Why another pilot?

The merged [source and canary research PR #1228](https://github.com/pokekarten/OpenCatastrophe-data/pull/1228) established that NYC source metadata/count endpoints work. This pilot verifies **real row-schema compatibility and candidate joins** rather than extrapolating from two incompatible whole-city counts.

## Real official provider measurements

- Original [NYC DOB LL84 dataset 5zyy-y8am](https://data.cityofnewyork.us/d/5zyy-y8am): report year 2024, filter `nyc_borough_block_and_lot like '1000%'`, select only `property_id`, BBL, BIN, parent property ID, reported building count and report year, ordered by `property_id ASC`, limit 30.
- Original [NYC DCP PLUTO 64uk-42ks](https://data.cityofnewyork.us/d/64uk-42ks), current source identity **26v2**: select only `bbl` and `numbldgs`, restrict by the 30 LL84 BBLs. No addresses, owner names, geometries, assessor dollar values or energy readings were requested.
- Independent read-only queries on 2026-11-05 resolved all **30** original BBLs to exactly 30 PLUTO tax-lot rows. **28** of the PLUTO tax lots report `numbldgs=1`; **2** report `numbldgs=2`. For these 30 LL84 submissions, the observed parent state was `Not Applicable: Standalone Property`, one BIN each and `number_of_buildings=1`.
- **Critical real-world adapter finding:** The PLUTO JSON represents numeric `bbl` as strings such as `1000000001.00000000`, whereas LL84 publishes the canonical 10-digit identifier as text. The adapter must remove **only** an all-zero decimal suffix. A real nonzero fractional part, scientific notation, malformed BBL, mixed base/billing condominium identity or rounding is a hard rejection. Example numbers here are invented; no actual BBL IDs are published in this document.
- The initial five-BBL group that timed out was retrieved by **five independent single-BBL queries**, all returning `numbldgs=1`. This is why an interrupted batch is a **request failure**, not an observed missing property. Never silently produce a partial candidate total.

### Precisely what the observed 28 / 2 means

| Observed condition | Count | Interpretation |
| --- | ---: | --- |
| LL84 2024 selected rows | 30 | Nonrepresentative deterministic BBL-prefix / first-property-ID cohort |
| BBLs found in current PLUTO | 30 | Tax-lot-level ID intersection for this cohort |
| Current PLUTO lot reports one building | 28 | **Unverified one-lot/one-BIN candidate only** |
| Current PLUTO lot reports multiple buildings | 2 | Cannot assert building-level identity or allocate energy/TIV automatically |

**Not a statistical match-rate, prevalence or full-stock assessment.** Selection was deliberately concentrated in a narrow Manhattan BBL prefix; report and snapshot dates differ (LL84 year 2024 vs current PLUTO 26v2 in August 2026). A one-to-one BBL and BIN does not prove geometry, building vintage, ownership or insurance coverage. It is not an observed building-insured replacement-cost basis.

## Executable research preflight

New script: `research_runners/nyc_pluto_ll84_original_sample_v0.py`.

    python research_runners/nyc_pluto_ll84_original_sample_v0.py --live

The default invocation refuses network access. With `--live`, the code uses a fixed HTTPS host, fixed 2024/BBL-prefix/30-record query, and batches at most five numeric PLUTO BBLs per request; if a batch fails, every BBL must succeed individually or the entire run fails. It limits response bytes to 32 KiB per response; rejects redirects, non-JSON/malformed rows, duplicate keys, noninteger building counts and nonzero fractional BBLs. It outputs **aggregate counts and fail-closed status only**, with no original IDs or source rows. All tests are synthetic/offline and do not use the network.

Source schemas and expected PLUTO release must be reverified when the provider refreshes the dataset. The script intentionally labels the 26v2 identity as **expected, not independently snapshotted by the runner**. This bounded preflight is not a production data ingestion connector and does not write into Neon, a repository table or OED/NextGen.

## Official NYC Open Data reuse-policy context (reviewed 2026-11-05)

NYC's [official Open Data FAQ](https://www.nyc.gov/opendata/get-started/FAQs)
states no general use restrictions on its open data; its
[public policies and terms](https://cityofnewyork.github.io/opendatatsm/publicpolicies.html)
also describe source/version/modification attribution expectations and
**additional terms imposed by data-providing agencies**, while disclaiming
completeness, accuracy and suitability. This is stronger original-provider
evidence for bounded research access than mere public reachability.
It is **not** a sign-off on redistributing provider bytes, cross-source
license compatibility, sensitive/confidential records or model-grade
scientific admission. Exact dataset-specific attribution and commercial
integration must still be reviewed before real-data promotion.

## Scientific and legal gates before model use

1. Original NYC source rights and any limitations on onward redistribution and commercial derivative combinations require exact-scope review. This pilot did not authorize source data redistribution, model admission or real insurance portfolio inference.
2. Independently compare DOB BIN building footprints and **condominium billing-vs-base tax lots**, plus parent-child campus consistency, on an adjudicated micro-area with aligned historical vintages.
3. Determine geospatial collision and omission rates, stratified by single-vs-multi-building lot, occupancy and census-block geography; only then expand beyond this convenience cohort.
4. Any estimate of insured value, contents, business interruption exposure or insurer membership must be **separate**, calibrated from appropriate evidence, uncertainty-labeled and subject to its own legal/model approval.

**Outcome:** first actual original-row join is technically feasible for the selected 30 cases, but building-level identity and real insurance exposure remain unproven.
