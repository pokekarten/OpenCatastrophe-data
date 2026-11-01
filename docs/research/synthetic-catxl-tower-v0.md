<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synthetic CAT-XL multi-layer accounting prototype (v0)

## Boundaries

This is a small reproducible **independently fictional** accounting experiment, NOT a catastrophe model or a real reinsurance contract interpreter. It uses twelve invented property positions, four invented post-snapshot future losses, and three invented non-overlapping occurrence layers. There are no source bytes, real insured records, external insurer identities, provider losses, hazard footprints, vulnerability curves, portfolio valuations, or confidential data. Nothing is model-admitted. The code does not connect to Neon or write any database.

This prototype is intentionally independent of the existing single-layer PR #935, whose free-reinstatement arithmetic is a distinct exercise. The synthetic Neon demonstration in merged #921 is read-only context; the additional **three-layer** treaty and its paid premium conventions exist **only** inside this example, not as Neon treaty rows.

## Exact toy wording, not actual reinsurance wording

- **Original gross occurrence basis:** each layer's attachment and limit are calculated on the same original gross insured event loss; no downstream net-of-prior inuring. Layer monetary bands are strictly ordered and non-overlapping; touching bands are permitted.
- **Ordering:** all events are date-ordered, strictly after the fictional 2026-11-01 exposure vintage and in 2026. Two events on one day are rejected rather than silently selecting an event order. Real multi-event attribution and hours clauses remain unimplemented.
- **Covered perils:** each layer has explicit sorted flood/windstorm coverage; losses outside a layer's covered perils do not erode its annual recovery limit.
- **Annual recovery capacity:** occurrence limit times (1 + number of reinstatements); each event is separately capped by occurrence limit and by remaining annual capacity, with no cross-layer inuring or retrocession.
- **Toy paid reinstatement convention:** *only reinstated capacity actually used* earns an incremental premium, proportional to used reinstated limit and to an invented full-layer premium times the explicitly declared reinstatement rate in basis points. Rounded half-up at the **cumulative** premium in cents, then difference per event; no time adjustment. This is **not** the usual contract-specific activation/pricing formula and cannot price a real treaty. Base layer premiums are displayed separately, not subtracted from ceded loss.
- **Money:** gross/ceded/net loss amounts are exact whole EUR integers; premiums are integer EUR cents. Negative, boolean, floating-point, missing and unknown inputs are rejected.

## Example layers (all EUR, fictional)

| Layer | Attachment | Occurrence limit | Reinstatements | Perils | Base premium | RI rate |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| FICTIONAL-L1 | 200,000 | 200,000 | 1 | Flood, wind | 25,000 | 100% |
| FICTIONAL-L2 | 400,000 | 300,000 | 1 | Wind only | 30,000 | 50% |
| FICTIONAL-L3 | 700,000 | 500,000 | 0 | Flood, wind | 40,000 | 0% |

## Calculated synthetic output

| Invented event | Gross EUR | Layer 1 ceded | Layer 2 ceded | Layer 3 ceded | Net EUR |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-11-02 wind | 100,000 | 0 | 0 | 0 | 100,000 |
| 2026-11-08 flood | 400,000 | 200,000 | 0 | 0 | 200,000 |
| 2026-11-15 wind | 900,000 | 200,000 | 300,000 | 200,000 | 200,000 |
| 2026-11-22 wind | 600,000 | 0 | 200,000 | 0 | 400,000 |
| **Total** | **2,000,000** | **400,000** | **500,000** | **200,000** | **900,000** |

Invented additional reinstatement premiums: **EUR 25,000 (L1) + EUR 10,000 (L2) + zero (L3) = EUR 35,000**. Fictional base reinsurance premiums total **EUR 95,000**. For illustration, the insurer's toy **net loss + reinstatement premium** is EUR 935,000; including the fictional base premiums, EUR 1,030,000. These accounting presentations **do not** represent actual insurer or reinsurer profitability, liabilities or cash flows.

## Run locally without provider access

From repository root:

```bash
python -m unittest discover -s tests -p test_synthetic_catxl_tower_v0.py -v
python research_runners/synthetic_catxl_tower_v0.py
```

The code and tests require Python's standard library only. The local focused suite contains **29 test methods** covering exact conservation, limits, RI premiums, coverage differences, chronology, rounding, deterministic results, and rejecting unexpected, non-synthetic, overlapping or invalid input. GitHub CI remains authoritative for the exact repository commit. No source rights/admission or production Neon changes were made.

## Not implemented

Real reinstatement activation clauses/pricing and time pro-rata, annual aggregate/event grouping, exact reinstatement purchase logic, multi-year treaties, reinstatement subject premiums, insurer deductibles/coinsurance, proportional treaties, retrocession, global cross-company/peril loss ordering, expense/recovery credit risk, secondary uncertainty, peril hazard intensities, real exposure valuation or event/period loss tables. These are next scoped modules, not capabilities inferred from a successful arithmetic smoke test.

A downstream NextGen adapter must preserve all loss stages, units, ordered event identities, treaty terms, source/fixture provenance, and must **not** treat these fictional numbers as external CAT data or as production simulation evidence.
