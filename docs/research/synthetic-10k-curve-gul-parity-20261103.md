<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Offline synthetic 10,000-year hazard -> vulnerability -> gross-loss parity (v0)

**Classification: independently synthetic research only.** No database access, source download, provider data, real insurer, calibrated physical event, insurance policy or treaty loss, Solvency II result, model admission or actual commercial use.

## What this proves

The already merged synthetic `research_runners/synthetic_ci_curve_catxl_bridge_v0.py` has a strict intensity/curve-to-loss function. This isolated extension reuses that function across 10,000 **invented year-worlds**, rather than invoking a real CAT producer or a vendor model.

For scientific separation, the annual Bernoulli hash event recipe here exactly matches the existing public **[draft #1081](https://github.com/pokekarten/OpenCatastrophe-data/pull/1081)**, including these fictional conventions: 12 SYNTH-asset positions, 26/256 windstorm and 13/256 flood event thresholds, 10,000 worlds 0..9999, a 1..5 artificial hazard score and 1..3 artificial susceptibility factors per asset/year/event.

The new route encodes that invented multiplier as a literal synthetic **linear fractional-damage curve**, `damage_ratio = synthetic_score * local_factor / 100`, on the bounded support 0..5, using the merged `fictional_event_loss_cells` and `validate_curve_semantics` guards. `synthetic_score` is a **dimensionless fake index**, not mm, flood depth, wind velocity or PGA. This equivalence is purely algebraic: it is not independent catastrophe validation or a statistically established peril correlation model.

The function independently computes all four row-receipt families from its own generated loss cells, then compares them against **fixed documented read-only SQL parity receipts** from the independent draft #1081. MD5 is used **only for deterministic equality**, never source authentication. No direct reference to draft-branch code is imported, and the draft can remain open.

## Exact expected fictional results

| Statistic | Value |
| --- | ---: |
| Worlds | 10,000 |
| Invented assets | 12 |
| Invented portfolio value | EUR 3,150,000 |
| Total events | 1,541 (windstorm 1,008; flood 533) |
| Zero-event years | 8,509 |
| Invented aggregate GUL | EUR 285,494,000 |
| Toy AAL | EUR 28,549.40 |
| 99% / 99.5% AEP loss | EUR 342,500 / EUR 366,250 |
| 99% / 99.5% OEP loss | EUR 333,750 / EUR 351,250 |
| Annual maximum | EUR 638,750 |

Exact expected MD5 series receipts: `annual=6aebdda0c542f06a882ec16a4fcaa667`, `event=e0b6b2414c0a12459c47785a7de53777`, `event_asset=8cba885a6e1aab7d43e2fe1087fe0d95`, `event_intensity=2f11da6a6e1fb752cc410f50bfeffbc6`. These receipts are not cryptographic proof of the Neon branch state.

The `years_with_both_perils` count must be nonzero; the two events in such a year are **not** merged into a fake single event. AEP is based on the *sum of event losses in a year*, OEP on the *largest event loss in that year*. This is fundamental for future occurrence-vs-aggregate reinsurance ordering.

## Exact source/rights and model boundaries

1. The primary hazard/event probabilities, local factors and damage curves are made up; no vendor-model licensing or scientific event frequency is inferred.
2. The `landscape` research register never auto-admits third-party vulnerability curves, insured TIV, empirical damage observations or claims into this route.
3. The code computes **ground-up toy GUL only**. Even though a separate prior toy bridge produces ceded/net on two events, **these 10,000 worlds have no policy terms, CAT-XL, reinstatement premium, hours clause, retrocession, insurer allocation or financial module**.
4. Cross-year event IDs and cross-peril component relations are not fully defined for actual annual stochastic simulation. The hash-peril construction is deterministic pseudo-independent selection, not calibrated multiperil dependence or a Poisson event-count process.
5. SQL receipts can be reverified only by separately executing the original read-only queries on the pinned **isolated Neon validation branch**, followed by source/asset-vintage and schema checks. This PR does not access Neon.

## Reproduction

```bash
python -m unittest discover -s tests -p 'test_synthetic_neon_10k_curve_gul_bridge_v0.py' -v
python research_runners/synthetic_neon_10k_curve_gul_bridge_v0.py
python scripts/check_all.py
```

Both the tests and script are Python standard-library only. They do not save 10,000 actual loss rows as files or emit any model-approved run. The existing upstream draft can retain its isolated source/version checks without creating PR file collisions.

**Next scientific engineering milestone:** Design a proper per-world event identity/occurrence and YLT/OEP/AEP transfer contract, then implement separately approved policy and treaty terms in the downstream model. Real data ingestion and financial deployment remain blocked.
