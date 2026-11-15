<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synthetic OED 5.0.0 CSV export v0 — bounded interoperability experiment

**Status:** synthetic research-only exporter. Validated with pinned ODS Tools **5.0.8** in GitHub Actions on the draft PR; **not** a CAT model, insurer exposure, insured replacement value, financial model or approval for a real portfolio.

## Canonical source and rights boundary

- Source of *existing* 12 completely invented locations/amounts: `research_runners/sql/synthetic_exposure_smoke_v0.sql` and isolated Neon `insurance-risk-core` **validation-schema-20261031** branch (`br-summer-sky-bawujqu8`), database `insurance`. **Never run the source SQL on main.**
- Source for snapshot projection: read-only `research_runners/sql/synthetic_oed_snapshot_v0.sql`. It returns one `synthetic_snapshot` JSON value from the 12-row smoke cohort. It does **not** stage any real data.
- Source for CSV projection: `research_runners/export_synthetic_oed_v0.py`. Projection is intentionally *lossy*: it omits synthetic invalid OED occupancy/construction codes and fabricates ONE explicit hypothetical account/policy, peril groups and TIV component split for CSV formatting proof only. The source value itself stays unchanged; no representation becomes canonical.
- Do **not** commit the resulting snapshot or CSVs: they are disposable test artifacts. No external provider bytes, customer records, actual insured TIV, actual policies, real asset IDs or real insurance companies are admitted or linked.

## Expected mapping and explicit synthetic-only assumptions

| Native field | OED field / value | Interpretation |
| --- | --- | --- |
| `portfolio_key` | `PortNumber` | Stable exact synthetic portfolio ID |
| `external_unit_id` | `LocNumber` | One invented unit per CSV row |
| `country_code`, PostGIS EPSG:4326 | `CountryCode`, `Latitude`, `Longitude` | Arbitrary 12-point grid, **not** real buildings or geocodes |
| `insured_value` | `BuildingTIV` | Deliberately assumes all EUR 3,150,000 invented value belongs to buildings, **not** an insured-value observation |
| no such source components | `OtherTIV`, `ContentsTIV`, `BITIV` = `0` | Artificial zeros, not evidence of no real exposures |
| generic `windstorm`, `flood` scope | `LocPerilsCovered`, `PolPerilsCovered` = `WW2;OO1` | Explicit hypothetical wind **without** storm surge and flood **without** storm surge; not inferred coverage |
| no account/policy source rows | `AccNumber=SYNTH-ACC-01`, `PolNumber=SYNTH-POL-01` | Export-only fictitious one-account, one-policy grouping, not DB contract facts |
| generic synthetic occupancy and construction strings | omitted | `SYNTHETIC_*` codes are not OED vulnerability taxonomies |
| `insured_value_currency` | `LocCurrency`, `AccCurrency` | EUR only |

Only `location.csv` (12 rows) and `account.csv` (1 row) are emitted. There are **no** `ReinsInfo`/`ReinsScope` files: the existing invented CAT-XL row has explicitly **unspecified** loss ordering/reinstatement pricing and must not be misrepresented as an OED reinsurance financial contract. Version is explicitly **OED 5.0.0**.

## Reproduction (after explicitly selecting the validation branch)

1. In a read-only Postgres session for **branch ID `br-summer-sky-bawujqu8`**, DB `insurance`, run `research_runners/sql/synthetic_oed_snapshot_v0.sql` and save the JSON value of **one** returned column `synthetic_snapshot` into a local `snapshot.json` file. Recheck the target branch ID in Neon before executing; the SQL predicate is an additional guard, not independent proof of branch selection. Never run the fixture *creation* SQL again merely for export.
2. From the repository root: `python research_runners/export_synthetic_oed_v0.py snapshot.json /tmp/oc-synthetic-oed-v5` (the output directory must not exist).
3. Run `python -m unittest discover -s tests -p 'test_export_synthetic_oed_v0.py' -v` for offline positive and negative cases. Official compatibility validation uses **pinned** `ods-tools==5.0.8` and `python research_runners/validate_synthetic_oed_ods_tools_v0.py` from the dedicated `Synthetic Oasis OED 5.0 compatibility` GitHub workflow. It also checks that removing a mandatory `CountryCode` is rejected. This is an OED-format validation, **not** an OasisLMF model run.
4. Confirm 12 location rows, exactly 1 fictitious account/policy, consistent account IDs/currency/perils, and sum of all four TIV components **EUR 3,150,000** (entirely invented). Do not read/rewrite any live Neon tables.

## Normalized relational synthetic OED path (implemented on isolated Neon branch)

This is an **additional source of the same deliberately invented values**, not an independent real exposure source. The four validation-only tables are `insurance.account_v1`, `insurance.policy_v1`, `insurance.policy_location_v1` and `insurance.policy_tiv_component_v1`. Their canonical, additive DDL and fixture SQL are under `research_runners/sql/oed_synthetic_relational_{schema,fixture}_v1.sql`. The original exact invented location amounts remain the baseline; the new relational account/policy/perils and coverage components are explicitly fictional.

- Execute `research_runners/sql/oed_synthetic_relational_schema_v1.sql` **only** on the explicit validation branch `br-summer-sky-bawujqu8`. Its fail-closed guard requires validation-only source tables and the 12-row invented smoke portfolio. Never apply to main.
- Execute `research_runners/sql/oed_synthetic_relational_fixture_v1.sql` on that same branch to persist the one invented account, one invented policy, twelve location links and exactly four synthetic components per location. Reruns preserve counts.
- Execute `research_runners/sql/oed_synthetic_relational_invariants_v1.sql` on the validation branch: checks 1/1/12/48, 3,150,000 EUR total and expected *rejection* of invalid cross-version links, non-synthetic accounts and negative TIV.
- Execute read-only `research_runners/sql/oed_synthetic_relational_snapshot_v1.sql` on that branch. It returns one JSON object under `synthetic_relational_snapshot` (12 units plus the fictional persisted account/policy/TIV fields); save **the JSON object value itself** as `relational_snapshot.json` outside Git, not the enclosing SQL result array.
- Run `python research_runners/export_relational_synthetic_oed_v1.py relational_snapshot.json /tmp/synthetic-oed-relational-v1` from the repository root, where the output folder does not already exist. The exporter refuses any drift from the exact invented fixture. The generated files remain disposable.
- Official pinned `ods-tools==5.0.8` CI checks both the original projection and this relational projection; generated synthetic CSV files must match byte-for-byte. This proves the **bounded synthetic mapping only**, not real insurer model/financial correctness.

Live Neon evidence (2026-11-01): 1 invented account, 1 invented policy, 12 cross-version-FK-checked links, 48 nonnegative fictional TIV components, EUR 3,150,000 total. The separate production `main` has no these four new tables; no customer or real property data have been inserted.

## Future real-data path (not implemented)

Real insurance exposure requires source-specific rights, provenance, true/estimated **value basis**, the correct asset-to-account and account-to-policy joins, known geocode uncertainty, valid OED occupancy/construction dictionaries, per-peril cover, a proper TIV breakdown, and separately specified treaty scopes. `landscape/` entries and registered Git blobs are **not** insured assets. METEOR Level 1 offers OED examples but carries **CC BY-NC-SA 4.0** conditions and is not commercially admitted. EIOPA data are primarily admitted as **metadata** and cannot be inferred down to insured building records.

OED reference: https://github.com/OasisLMF/ODS_OpenExposureData (5.0.0 release), peril-code explanation: https://github.com/OasisLMF/ODS_OpenExposureData/blob/main/docs/source/explanation/geography-perils.rst
