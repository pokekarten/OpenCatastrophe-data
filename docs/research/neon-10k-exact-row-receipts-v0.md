<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Four exact 10,000-year synthetic Neon row-series receipts

**2026-11-01. Read-only software parity. No actual CAT simulation, loss admission, insured/ceded payout, source rights or model approval.**

## Independent evidence

Executed `research_runners/sql/neon_synthetic_gul_10k_row_receipts_v0.sql` in connected Neon `insurance-risk-core`, database `insurance`, **validation branch only** `br-summer-sky-bawujqu8`, never `main`. The SQL is derived from the 10k ground-up toy pilot and now uses the *stricter exact synthetic Oasis OED v0* source/version/currency/value-basis/geometry/asset-count gate proposed by **stacked draft PR #1089**. Importantly, it does not assume that an aggregate EUR 3.15m sum proves 12 exact exposures.

The PostgreSQL result matches an **independent local Python standard-library implementation** on all four ordered row streams:

| Series | Count | MD5 byte-parity receipt |
| --- | ---: | --- |
| `year:gross_loss:max_event_loss:event_count` | 10,000 | `6aebdda0c542f06a882ec16a4fcaa667` |
| `year:peril:event_loss` | 1,541 | `e0b6b2414c0a12459c47785a7de53777` |
| `year:peril:asset_id:asset_loss` | 18,492 | `8cba885a6e1aab7d43e2fe1087fe0d95` |
| `year:peril:invented_intensity` | 1,541 | `2f11da6a6e1fb752cc410f50bfeffbc6` |

Ordering is explicit; source years 0–9,999, one possible Bernoulli event per peril/year, windstorm threshold 26/256, flood 13/256, invented damage multipliers. There is **no physical hazard calibration**, no stochastic ensemble fit to historical events, no real location-specific fragility and no insurance financial basis. All 12 exposures and values were fabricated.

`tests/independent_neon_10k_row_receipts_v0.py` is the independent Python implementation. `tests/test_neon_row_receipts_v0.py` has **4/4 tests passed locally**, including changed-asset/same-total rejection, rejection of real inputs and truncated worlds. Fetched GitHub blobs agree exactly with local tested git blobs: `90bd7c00218865873c5cf1db376e6e9bacc68c3b` and `e4ae832ee441dec7c9aa16bff2cd2b7051c6e500`, respectively. The public repo's latest `CI` workflow also passed on the new receipt commit.

**MD5 is an equality checksum, not an adversarial authenticity signature.** Exact database branch/source snapshot is not dynamically bound to future native runs; if the source version changes, rerun read-only SQL and independently confirm a new receipt. Neither PR #1081 nor stacked #1089 may merge based on synthetic parity alone.

## Relationship to native OpenCatastrophe/NextGen

Private OpenCatastrophe **draft PR #14** adds `verify_neon_sql_row_receipts(full)` so the later actual OpenCat producer output must match all four Neon row receipts *before* a synthetic native NextGen insured-loss success receipt can be emitted. This new private native test **has not been executed**: there is no accessible paired clean private checkouts and the MacBook remote worker is offline. No CAT-XL/reinstatement/retro is computed.

**GitHub coordination:** OpenCatastrophe-data #1089 intentionally targets the branch of #1081 and overlaps three files; the repo's `PR Collision` check currently fails on this stacked configuration. The ordinary Python/REUSE/data CI for the new receipt branch passed; do not conflate that with all required checks being green. Coordinate the dependent PRs before merge; do not disable collision safety or approve real model inputs.
