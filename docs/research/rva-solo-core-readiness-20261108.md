<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V solo 2025: source-bound Neon main readiness and cross-Kreis identity gate

**Checkpoint 2026-11-08; research-only, not source admission, legal-entity registration, an insurer customer database, scientific model calibration or a CAT loss calculation.**

This narrowly integrates the **read-only SQL** and its original source-contract unit tests from [original research Draft #1372](https://github.com/pokekarten/OpenCatastrophe-data/pull/1372), without importing that PR's original-source receipts, research portfolios, external PDFs or other unpublished work. Canonical R+V 2025 HGB/SFCR and Berlin insurer LEI research TOML records already exist on `main`.

The SQL is `research_runners/sql/rva_solo_2025_neon_readiness_v0.sql`; tests are `tests/test_rva_solo_neon_readiness_v0.py`. **Source:** original Draft SQL blob `542093bbe56e1e2af9a41ae32b7812f857715c49`, which was executed against main before this change. The code now adds **three version-global gates** beyond the 53 local-Kreis counts and TIV sums: exactly 10,000 exposure rows, 10,000 distinct `external_unit_id` values across all counties, and 10,000 distinct PostGIS binary point geometries across all counties, keyed to the same `portfolio_version_id`. Repeated IDs or coordinates in different Kreise must not be accepted just because each Kreis count and local distinct count passes. This remains deliberately strict for the original-source **10k unique fictional building point** experiment, not a universal rule for multiple policies at one real building.

## Executed original and revised code against Neon main

Explicit read-only live query target: `insurance-risk-core`, database `insurance`, branch **`br-late-recipe-ba1cr8hc` (main)**. Both original and tightened SQL completed as a single SELECT on 2026-11-08.

| Measured check | Main result |
| --- | ---: |
| `verified_solo_entities` | 0 |
| `solo_directory_candidates` | 1 |
| `source_bound_exact_sfcr_property_gwp_rows` | 0 |
| `source_bound_exact_hgb_building_contract_rows` | 0 |
| `company_linked_portfolios` | 0 |
| `source_admitted_synthetic_nrw_wgs84_units` | 0 |
| `complete_source_admitted_10k_nrw_oed_versions` | 0 |
| `next_gate` | `BLOCKED_UNVERIFIED_OR_AMBIGUOUS_SOLO_LEGAL_ENTITY` |

The issuer-published 2025 scope anchors embedded in the SQL are **1,060,546 year-end connected-building contracts**, **EUR 997,710,000 HGB direct connected-building gross premium**, and **EUR 2,223,182,000 SFCR gross property premium**; these are separate accounting/coverage observations. None proves actual insured locations, TIV, loss, annual event frequency or RI treaty. A zero in **this research database** is not a claim that R+V lacks policyholders.

The separate research/validation branch can contain metadata-only or fictional source experiments. This SQL being accepted on `main` does **not** promote any of those experiments, source rights, original NRW 2022 HU archived data, PiWind or Kyrill event trials into a calibrated R+V model.

## Reproduction and limitations

```sh
python -m unittest discover -s tests -p 'test_rva_solo_neon_readiness_v0.py' -v
python scripts/check_all.py
```

For live readiness, use the exact SQL file **read-only** against the explicitly selected Neon `insurance` database and main branch; do not confuse the test branch with main or mutate any source/organization/portfolio tables. The original source/rights approval, official 53-Kreis GFK semantics, full 10k OED artifact custody, portfolio-to-carrier legal binding, German vulnerability calibration, actual annual stochastic catalogue and treaty terms remain independent **no-go** gates. The correct final green state of this report is still **RESEARCH_ONLY_NEEDS_HAZARD_VULNERABILITY_RIGHTS_AND_TREATY_REVIEW**, never production certification.
