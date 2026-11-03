<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Independently synthetic CAT-XL gross / ceded / net arithmetic (v0)

## Claim boundary

This is a **toy loss-arithmetic smoke test**, not an actual catastrophe model, insured loss estimate, capital model or real treaty payout. All 12 fictitious exposures and four future events were independently invented. No real insurer, claims, policy, third-party source bytes, geographical risk or vulnerability curve is used.

Merged #921 contains one synthetic portfolio and a fictional CAT-XL contract. That contract deliberately has **undefined** loss-ordering and reinstatement-premium terms. This module **does not** interpret those unknown actual contract terms. It instead declares separate assumptions for arithmetic only: strict chronological order, invented losses, occurrence attachment EUR 200,000, occurrence limit EUR 500,000, and a free/immediate single reinstatement represented by a simple **EUR 1,000,000 cumulative recovery cap**.

The calculation excludes reinsurance/reinstatement premiums, event hours clauses, treaty inception exclusions, insurer deductibles, attrition, exhaustion/reinstatement timing, secondary uncertainty, retro and real catastrophe risk.

## Demonstration results

| Synthetic event date | Peril | Gross EUR | Ceded EUR | Net EUR |
| --- | --- | ---: | ---: | ---: |
| 2026-11-02 | Wind | 100,000 | 0 | 100,000 |
| 2026-11-08 | Flood | 400,000 | 200,000 | 200,000 |
| 2026-11-15 | Wind | 900,000 | 500,000 | 400,000 |
| 2026-11-22 | Wind | 600,000 | 300,000 | 300,000 |
| **Total** | | **2,000,000** | **1,000,000** | **1,000,000** |

The final event has EUR 400,000 preliminary per-occurrence recovery but only EUR 300,000 annual capacity remains. Each fictional event preserves gross = ceded + net. These are **not** real damages, predictions or insurer losses.

## Reproduction

In the repository root with Python standard library, run:

- python -m unittest discover -s tests -p test_synthetic_catxl_loss_math_v0.py -v
- python research_runners/synthetic_catxl_loss_math_v0.py

The **read-only** query at research_runners/sql/synthetic_catxl_loss_input_invariants_v0.sql checks the fictional input units and losses against the actual isolated Neon validation branch. It is not executable ingestion and must never be used as a real portfolio admission. Use a Neon connection explicitly pinned to validation-schema-20261031, not the default production main.

## Verification from 2026-11-01

- 18/18 standard-library focused Python tests passed locally, including conservation, determinism, invalid event ordering, loss greater than insured value, unsupported treaty terms and fake-vs-real guards.
- 11/11 read-only Neon SQL checks passed on the isolated insurance validation branch; the 13 invented asset-event loss cells joined to all twelve fictional exposure units.
- No database inserts, migrations, simulation-run rows, real company links or existing source admissions were changed by this work.

## Explicit scientific gaps

Real hazard intensity/footprint, vulnerability curves, insured terms, geocoded and licensed exposures, event identity, premium-bearing reinstatement rules, and a NextGen/Oasis exchange adapter remain unimplemented in this test. The model.simulation_run table is **not** evidence of a completed CAT simulation, and the current experiment does not write to it.

This isolated demonstration does not authorize deployment of unapproved input data or publication of external data.
