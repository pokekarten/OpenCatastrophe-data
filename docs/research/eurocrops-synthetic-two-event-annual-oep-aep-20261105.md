<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synthetic crop annual OEP/AEP arithmetic pilot (2026-11-05)

**RESEARCH-ONLY / NOT_ADMITTED.** The terms OEP/AEP below refer to mathematical exceedance arithmetic on entirely fabricated **direct crop-value impacts**, NOT insurer gross/net losses, actuarial pricing, Solvency II results, or a scientifically calibrated event model.

## Two exact invented event types

The executable research_runners/synthetic_crop_two_event_annual_ep_v0.py reuses the earlier bounded, exclusively fictional agricultural spatial overlay and direct-value impact model.

| Invented event identity | Imaginary annual presence | Direct value impact lower | Direct value impact upper |
| --- | ---: | ---: | ---: |
| SYNTH-EVENT-001, flood | 26/256 = 10.15625% | EUR 4,900 | EUR 11,900 |
| SYNTH-EVENT-002, hail | 13/256 = 5.078125% | EUR 2,250 | EUR 2,250 |

All agricultural fields, geographic supports, crop €/ha values, damage fractions, flood depths, hail diameters, event frequencies and their independence are invented. The flood upper bound assumes the highest conceivable crop-value impairment on unknown-coverage area; it is neither an empirical confidence interval nor an insurance policy limit.

## Exact four-state annual reference

The model explicitly assumes **two independent Bernoulli event-presence variables**, at most one event of each type per fictional year. It enumerates the four combinations: neither, flood only, hail only and both. The exact rational world probabilities sum to 1.

- Occurrence arithmetic (OEP): annual **maximum** of individual invented direct event impacts.
- Aggregate arithmetic (AEP): annual **sum** of direct event impacts.
- Exceedance is strict P(metric > X), not greater-than-or-equal.
- Four analytical exact distributions are calculated separately: OEP lower, OEP upper, AEP lower and AEP upper.

At the threshold EUR 5,000:

| Mathematical quantity on toy direct crop impacts | Lower uncertainty assumption | Upper uncertainty assumption |
| --- | ---: | ---: |
| OEP (maximum event exceeds threshold) | 0% | 10.15625% |
| AEP (year total exceeds threshold) | 169/32768 = approximately 0.51575% | 10.15625% |

Both lower event impacts together are EUR 7,150, even though their maximum is only EUR 4,900: therefore the lower AEP can exceed the threshold while lower OEP cannot. This is a unit test for correct aggregation and must not be interpreted as a real risk probability.

The *exact mathematical expected annual direct impact* under **only these invented event probabilities** is EUR **611.91** (lower) or EUR **1,322.85** (upper). These values are NOT a real insurer average annual loss, GUL, IL, CAT XL or premium.

## Reproducible 10,000-year parity check

In addition to the exact reference, 10,000 invented annual year-worlds are produced with fixed seed 20261105, year IDs 0..9999 and SHA256-based toy Bernoulli event draws. This is a deterministic test of numerical convergence/ordering, not a physical event process or proof of independent weather events. The executable produces:
- four exact rational exceedance curves at predefined EUR thresholds;
- sampled annual exceedance counts, sample probabilities, and fictional event-presence counts;
- a SHA256 receipt of the internally generated 10,000-year event-loss representation for reproducibility (not original data authentication).

It neither downloads EuroCropsV2 originals nor writes any yearly rows to Git, Neon or insurance databases. Reproduction from repository root:

    python research_runners/synthetic_crop_two_event_annual_ep_v0.py
    python -m unittest discover -s tests -p test_synthetic_crop_two_event_annual_ep_v0.py -v

The 11 synthetic tests challenge: exact world probabilities, simultaneous events, strict equality vs threshold, an AEP-only threshold crossing, monotonic ordering, expected annual arithmetic, deterministic replay, empirical-vs-analytic tolerance, invalid probabilities and source/insurer admission guards.

## Hard scientific constraints

The corrected JRC original gpqtv202/de4_2023.parquet remains not downloaded/tested; no original field/parcel exposure, crop-season or HCAT4-derived value is used. Original source rights, source checksums and actual crop classification must be independently validated. Any true event frequency, seasonality, spatial hazard support, climate trend or cross-peril dependence must be established from admissible data; one event max per type per year is a deliberate toy simplification.

Calibrated crop vulnerability, agricultural valuation/coverage, per-event and aggregate terms, deductible/limit/reinstatement, RI/retro and an OED agricultural-asset contract are **not** present. OED BuildingTIV from an unrelated synthetic building test must not be relabelled as crop insurance. Thus there is NO actual ELT, insured OEP/AEP, gross/net loss, risk premium or CAT-ready model here.

Keep the PR Draft and sources NOT_ADMITTED until exact-source, rights and scientific admission gates are met.
