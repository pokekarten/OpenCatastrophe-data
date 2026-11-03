<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synthetic hazard -> curve -> gross loss -> CAT-XL bridge (2026-11-03)

**Boundary:** This is **not** a CAT model, real insurer exposure, real portfolio, validated vulnerability curve, vendor model, ILT/YLT, or operational reinsurance estimate. It proves that a fictional hazard intensity can be translated into an equally fictional money loss **only** via an explicitly dimensionless `fractional_damage_ratio`, then sent to the existing fictional CAT-XL arithmetic without altering treaty conventions. It fetches no third-party bytes, accesses no database, and clears no source rights.

## Reproducible toy case

- Two invented asset values: `SYNTH-01 = EUR 500,000` and `SYNTH-02 = EUR 300,000`.
- One invented flood curve in **mm**: depth `0 -> 0%`, `100 -> 50%`, `200 -> 100%`. This is a toy function, **not** a Nirandjan, GEM, SimCenter, FEMA or observed flood curve.
- Fictional event 1: 100 mm at SYNTH-01 produces gross EUR 250,000; treaty attachment EUR 200,000 gives ceded EUR 50,000.
- Fictional event 2: 200 mm at SYNTH-01 and 100 mm at SYNTH-02 produces gross EUR 650,000; ceded EUR 450,000.
- With a toy EUR 500,000 occurrence limit, one free reinstatement and annual cumulative capacity EUR 1 million: **gross EUR 900,000, ceded EUR 500,000, net EUR 400,000**. This does not establish an actual contract, event occurrence aggregation, deductible, secondary uncertainty, policy allocation or real claim.

The code `research_runners/synthetic_ci_curve_catxl_bridge_v0.py` imports the existing `ci_curve_semantics_v0` preflight and `synthetic_catxl_loss_math_v0.allocate` without weakening either. It accepts only `SYNTH-` curve/asset identities and the existing fictional `FICTIONAL-` event/treaty vocabulary. Original source products remain in `landscape/` as **not admitted** research candidates.

## Critical scientific exclusions

1. **No automatic interpolation outside the curve's measured/synthetic support:** an out-of-range intensity fails. Inside the domain it uses a *declared bounded linear interpolation*. It does not estimate credible uncertainty bands or a calibrated smooth physical response.
2. **No implicit intensity conversion:** mm, m, PGA, wind speed and other measures are never swapped or converted. Curve unit must equal the event unit exactly.
3. **No monetary conversion for non-fractional outputs:** repair rate, pipe failures per km, fragility-state probabilities, repair time and all other non-damage-ratio metrics fail. Repair rates need an independent repair-cost model and explicit asset quantity before money can be estimated.
4. **No external/real sources or claims:** identities of all assets, curves and events are visibly fictional. No original provider data, geometries, real building TIV, insured contract, third-party loss, licensed model input, Neon rows or vendor ILT/YLT are used.
5. **Whole-EUR toy rounding:** `ROUND_HALF_UP` is explicit; it is not a model of policy-level accounting conventions, currency exchange or inflation.

## Execution and acceptance evidence

Run from repository root:

```bash
python -m unittest discover -s tests -p 'test_synthetic_ci_curve_catxl_bridge_v0.py' -v
python scripts/check_all.py
```

The focused test suite checks exact synthetic gross, ceded and net outcomes, loss conservation, deterministic repeatability, unit rejection, no extrapolation, fractional-vs-repair mismatch, fictional identity, amount type bounds, and bypass-resistant downstream treaty semantics.

## Checked upstream rights metadata (separate from the synthetic test)

The [original Nirandjan et al. v1.1.0 Zenodo record](https://zenodo.org/records/13889558) identifies the three D1/D2/D3 Excel workbooks and explicitly lists a **CC BY 4.0** dataset licence. This is stronger provider-record evidence than an unspecified licence, but does not finish the source-specific rights, original-byte hash and scientific-usage review required by OpenCatastrophe. Each constituent function's upstream attribution, correction history and any third-party restrictions still need review; the later [SebKrantz CSV repository](https://github.com/SebKrantz/VulnerabilityCurves) advertises CC0, which must not be silently treated as removing upstream credit/provenance. Neither original provider data nor derived CSVs were fetched or passed into this test. Its vulnerability curve remains wholly invented.

**Remaining gates for a genuine source-backed model:** original dataset version/sha256/license, admitted model-input manifest, exposure geometry/TIV and taxonomy, event footprint and intensity uncertainty, vulnerability applicability and deductible, contractual occurrence/reinstatement logic, plus independent validation. The path to NextGen/FFBK must not label toy gross loss as genuine CAT ILTs or insured results.
