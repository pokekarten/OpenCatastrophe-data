<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Strict synthetic CAT-XL loss-ledger handoff (research v0.1)

This additive code extends the fictional three-layer arithmetic in draft PR #943. It **does not** execute NextGen, transform the data into Oasis ORD, admit hazard/exposure sources, populate a model run table, or infer true insurer, physical event, contractual occurrence or portfolio identity. No provider bytes, live API, GitHub secrets, Neon writes or customer data are used.

## What is machine-readable

The implementation at `research_runners/synthetic_catxl_nextgen_handoff_v0.py` exposes:

- `build_handoff(positions, events, treaty, result)`: independently recomputes the original synthetic three-layer calculation and refuses a mismatched caller result before producing a handoff receipt.
- `validate_handoff(receipt)`: rejects unknown/missing fields, noncanonical SHA-256, modified payloads, fabricated physical/contractual IDs, event ordering or duplicated labels, mixed EUR and cent units, incorrect gross = ceded + net, missing/duplicate/reordered layers, and any unreconciled event/year or layer/event cession and reinstatement premiums.
- Both `nextgen_execution_authorized` and `ord_compatibility_attested` must be exactly `false`. No receipt produced here can self-authorize its own promotion.

The JSON handoff has a frozen profile ID `OC-SYNTHETIC-CATXL-LEDGER-0.1`, two distinct amount units (**whole EUR insured-gross, ceded and net losses** versus **EUR cents for original and reinstatement premiums**), ordered fictional event rows and per-event layer rows, yearly totals and a canonical-content SHA-256. The input fixture digest is a deterministic checksum for **invented input**, not an externally signed receipt or provider provenance proof.

## Critical semantics

The example's labels like `FICTIONAL-WIND-001` **are neither validated physical-event IDs nor legal contractual-occurrence IDs**. Both fields are fixed to `null`. A NextGen native hours-clause application may group multiple original physical events into one contractual occurrence, or need stronger causality/event clocks. This interface therefore does not turn the synthetic label or same-day order into an authoritative event identity.

The sample premium convention is still the explicitly invented “reinstated capacity *consumed*” rule, not real activation/pricing wording. The handoff keeps reinstatement premiums as a separate line item, never netted into `net_insured_loss_eur`. It preserves only a **single fictional annual test world**: no 10,000-year simulation, common peril/insurer seed, annual weights, zero years, AEP/OEP or financial capital claim is implied.

## Reproduce

From a full checkout of the PR branch:

```bash
python -m unittest discover -s tests -p 'test_synthetic_catxl_nextgen_handoff_v0.py' -v
python scripts/check_all.py
```

The test file includes 23 self-contained validator tests and a twenty-fourth integration test that **must import the real synthetic tower implementation in the same repository**. A deliberately isolated validator-only test execution (without that tower) covered the 23 cases; exact-head GitHub CI is the authoritative full-integration check.

An illustrative Python caller in this branch can use:

```python
from research_runners.synthetic_catxl_tower_v0 import fictional_example, calculate_toy_tower
from research_runners.synthetic_catxl_nextgen_handoff_v0 import build_handoff, validate_handoff

positions, events, treaty = fictional_example()
result = calculate_toy_tower(positions, events, treaty)
receipt = build_handoff(positions, events, treaty, result)
validate_handoff(receipt)
assert receipt["payload"]["nextgen_execution_authorized"] is False
```

## Before any real NextGen consumer

A **separate independent adapter/admission gate** must establish original physical/cause/event/occurrence identity, hours-clause grouping, genuine treaty terms and legal ownership, insured loss stage, model version, provider/hash/rights provenance, exact valuation and currency, zero-year/annual world completeness, shared simulation and global ordering. No invented ledger row may bypass those gates.

**Status:** synthetic integration plumbing, not production model science.
