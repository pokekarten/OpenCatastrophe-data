<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Worldwide synthetic insurer regional cohort allocator v0

**Research-only, non-admitted arithmetic bridge; not real insurance exposure.** The goal is a reusable first step for any national insurer or public programme with an independently sourced, *carrier-reported policy count* and a separate physical building-stock denominator. This is not a worldwide completed insurer portfolio inventory.

`research_runners/worldwide_synthetic_carrier_allocation_v0.py` takes **one explicitly scoped insurer per input** (solo/group/programme; country; coverage; as-of; reported *policy count*; HTTPS product and declared source SHA-256), one **independent non-insurer regional physical building stock** (different as-of allowed, explicitly exposed), and one or more *invented* per-region selection multipliers per scenario.

It uses exact `fractions.Fraction` and deterministic largest remainders (alphabetical region-ID tie break) to conserve the company's national reported policy count for each scenario. The output is **aggregate fictional policies by region only**; no building/site/account identities, coordinates, TIV, loss, treaties or market shares. Each cohort retains legal scope, policy scope, source identity and separate carrier/physical vintages. Strict input keys reject accidentally passed customer or site fields. No provider bytes, private insurer data or Neon writes.

The result always says `FICTIONAL_REGION_ALLOCATION_NOT_INSURER_GEOGRAPHY`, `model_ready=false`, `insured_tiv_known=false`, `source_rights_reviewed=false` and `source_bytes_verified=false`. A caller-supplied SHA only identifies what the caller says it used: it is **not a source-byte check** and does not confer scientific or rights admission. Reported *premiums*, company gross written premium, programme exposure and physical-building counts may **never** substitute for reported insurance policy counts. A group-wide count is not a solo-entity observation. One policy need not equal one building; insurer penetration is a scenario assumption, not a measured fact.

## Local inputs and test

The CLI takes a **locally prepared JSON file of aggregate metadata**, not a downloaded provider export. Its shape and sample values are exercised in `tests/test_worldwide_synthetic_carrier_allocation_v0.py`; its two fictitious scenarios intentionally allocate different regional policy totals while preserving the same 11 invented company policies. No input or output file is committed.

```bash
python -m unittest discover -s tests -p 'test_worldwide_synthetic_carrier_allocation_v0.py' -v
python research_runners/worldwide_synthetic_carrier_allocation_v0.py /private/aggregate-fictional-input.json
python scripts/check_all.py
```

## Steps needed before model use

1. Bind a **real exact insurer legal-entity source**, reporting scope/date/line and source-byte SHA to independently checked original data and reviewed rights. Original country-wide policy counts are not enough to calibrate the geographic selection model.
2. Source geography/CRS/vintage and physical-building counts independently; account for unknown/suppressed cells and multiple policies on buildings. The tool deliberately demands non-overlapping region IDs and rejects duplicate or missing factor keys.
3. Fit and test insurer-specific regional share hypotheses against **independent observed regional carrier controls** where permitted. Hold out the observed controls not used for fitting, quantify uncertainty across multiple scenarios; do not score this toy allocator as calibrated.
4. Only after separate exposure/valuation, coverage/peril, geolocation, insurer perimeter, hazard/vulnerability, treaties, loss and annual-frequency gates can a consumer create synthetic OED and Gross/Net AEP/OEP. Existing R+V/TWIA/Florida pilot source audits remain authoritative and are not modified here.
