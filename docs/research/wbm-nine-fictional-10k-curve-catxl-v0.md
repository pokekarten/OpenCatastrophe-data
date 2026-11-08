<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Nine fictional Berlin-grid OED assets → 10,000 invented hazard years → toy GUL/gross/ceded/net EP curves

**Research-only, 2026-11-05. Not a native OasisLMF/GUL engine run and not an actual WBM, HDI, Helvetia or R+V insurance model.**

## Why this next step

The [validated OED 5.0.0 nine-commercial-site test fixture](../../research_runners/wbm_like_nine_fictional_oed_v0.py) has **9 invented** grid coordinates, one invented account/policy and **EUR 108m arbitrary** building exposure. Its official `ods-tools==5.0.8` schema acceptance was proved in [merged PR #1397](https://github.com/pokekarten/OpenCatastrophe-data/pull/1397). However, **OED format validity is not a catastrophe loss calculation**. Genuine OasisLMF GUL requires model-specific peril/area/vulnerability keys, event intensity/data, loss modelling setup and a real engine execution, and insured/RI losses additionally require correctly populated policy and reinsurance terms. See [OasisLMF core](https://github.com/OasisLMF/OasisLMF) and the [Oasis GUL input pipeline](https://oasislmf.github.io/OasisLMF/_modules/oasislmf/preparation/gul_inputs.html).

This research branch connects the **same nine fake source rows** to a **pre-existing, merged, fully synthetic** damage-ratio interpolator `fictional_event_loss_cells` and its independent 10,000-world discrete annual quantile function. That measures technical continuity of exposure identities → intensity index → response curve → loss sums → toy financial annual output, **not predictive skill**.

## Exact fully invented assumptions

- **Location base:** `research_runners/wbm_like_nine_fictional_oed_v0.py` source, 9 invented identifiers/cells, invented country coordinates and exactly EUR 108,000,000 sum. OED `LocNumber` maps one-to-one in list order to internal `SYNTH-01` ... `SYNTH-09` labels. No user-supplied source data, WBM site address, WBM corporate EUR5.9bn valuation, asset registries or insurer-provided TIV.
- **Years:** exact **10,000 synthetic annual worlds**, numbered 0 to 9,999. Each has zero to two separate fictional perils. Every zero-event year counts in annual distributions.
- **Synthetic event generator:** fixed source label `OC-NINE-UNAFFILIATED-FICTIONAL-10K-V0` plus year and peril hashed by MD5 for deterministic pseudo-random test values (NOT security/provenance). `flood` event if first hash byte is less than **13/256**, and `windstorm` if below **26/256**. These arbitrary thresholds are **not Berlin flood or wind frequencies** and may not be interpreted as historical probability.
- **Synthetic intensity and susceptibility:** 1–5 purely dimensionless hazard index (not mm, m/s, PGA), and separately 1–3 invented location-specific curve factors. Uses merged `synthetic_ci_curve_catxl_bridge_v0.fictional_event_loss_cells`, bounded 0..5 linear fractional-damage curves `loss_ratio = score × factor / 100`, integer EUR half-up rounding and strict asset-TIV cap. Every location is artificially exposed to each generated event. **No physical footprints or correlation calibration.**
- **Financial toy:** Annual insured **gross loss = toy GUL** by an explicitly fictional 100%-of-test-damage, zero-deductible/zero-limit-at-policy convention. One invented CAT-XL per event: **EUR5m xs EUR5m**, 5m per-occurrence limit and 10m annual cession capacity (1 free reinstatement for arithmetic); annual capacity resets each world. Premium/reinstatement price, hours clause, actual legal event identity, shares, co-insurance, treaty inuring and retro **are not modelled**. `net = gross − ceded`, checked at event/world/all-world levels. No actual WBM/R+V contract is applied.
- **EP metrics:** toy GUL/insured-gross and toy retained-net discrete **99% and 99.5% annual aggregate exceedance (AEP)** from the sum of events per year; corresponding **occurrence exceedance (OEP)** from the largest event in each year. For net OEP each event net is measured *after the toy event-layer allocation*, so event ordering matters. Quantiles use existing PostgreSQL-compatible `percentile_disc` rank with 10,000 complete years, **not a calibrated return-period curve**.

No observational source is admitted into the annual engine. The TED September statement of **nine commercial objects** is only used for the count of artificial sites. Different 2026 TED BT-04 procedure IDs must not be joined, and the awarded-company contract business identifier percentages 50/40/10 are **not included** anywhere in this toy loss model.

## Code and reproducibility

```bash
python -m unittest discover -s tests -p 'test_nine_fictional_oed_10k_curve_catxl_v0.py' -v
python -m research_runners.nine_fictional_oed_10k_curve_catxl_v0
```

See [runner](../../research_runners/nine_fictional_oed_10k_curve_catxl_v0.py), [14 synthetic mathematical/invariant tests](../../tests/test_nine_fictional_oed_10k_curve_catxl_v0.py), and the existing [independent 12-site 10k GUL reference](synthetic-10k-curve-gul-parity-20261103.md). All operations are in-memory stdlib except the existing local OED exposure generator and previously merged source-agnostic bridge. No provider access, database writes, stored confidential policies, demand for credentials or intermediate 10k-year loss files. Result JSON reports counts, toy AAL/AEP/OEP and SHA-256 series checksums; row checksums are **replay IDs** of invented sequences, not authenticity of external sources.

The [existing synthetic OED compatibility GitHub workflow](../../.github/workflows/synthetic-oed-compat.yml) first validates the nine-site CSV with pinned official `ods-tools==5.0.8`, and then independently runs these invented annual calculations. **Do not call that an OasisLMF model run.** It is two demonstrators in the same CI, not validated physical hazard/insured loss calibration.

## Independent integer-math toy oracle (synthetic, uncalibrated)

A separate in-memory integer-only check reconstructed the exact fixed MD5 year/event recipe and 1–3 response factors without calling the repo's vulnerability interpolator. The following figures have been added as **expected values for exact-head automated parity testing**, not as observed Berlin or insurer risk metrics:

| Purely invented quantity | Oracle result |
| --- | ---: |
| Annual worlds | 10,000 |
| Fictional storm / flood events | 1,051 / 481 |
| Zero-event years / two-peril years | 8,520 / 52 |
| GUL = assumed policy gross aggregate | EUR 9,869,840,000 across 10,000 toy years |
| Toy CAT-XL ceded aggregate | EUR 2,945,200,000 |
| Toy retained net aggregate | EUR 6,924,640,000 |
| **Toy** gross / net annual average | EUR 986,984 / 692,464 |
| **Toy** gross 99% / 99.5% AEP | EUR 12,000,000 / 13,000,000 |
| **Toy** gross 99% / 99.5% OEP | EUR 11,800,000 / 12,600,000 |
| **Toy** net 99% / 99.5% AEP | EUR 7,280,000 / 8,300,000 |
| **Toy** net 99% / 99.5% OEP | EUR 6,800,000 / 7,600,000 |

The expected **annual-row SHA-256** is `b36e41340ec8428315af8fc59077c2f4d4d8705a244c2c7d3fa2041d5bc7ef04` and **event-row SHA-256** `92b62f63927b2aa8e85a9f25ce24ad2ef71b37ed7152b937bd3997071ab04590`. They are exact byte-recipe consistency checks over *invented internal rows*, never source authenticity receipts. The expected test numbers must pass against the implementation in hosted CI before this code is merged. AEP/OEP values refer solely to 10,000 made-up probability worlds and cannot be interpreted as predictive 1-in-100 or 1-in-200 catastrophe loss estimates.

## Gates before real modelling and OEP/AEP

1. Obtain a Germany-compatible, releasable and calibrated hazard event catalogue and intensity field with defined event IDs / frequency / period weights, storm/flood treatment and correlation assumptions.
2. Obtain a legally usable Germany commercial building vulnerability/damage model, with explicit occupancy, construction, loss type, TIV vintage and peril units; avoid unsupported generic ratio curves.
3. Link nine *actually identified or transparently synthetic* buildings to compatible model-specific `areaperil_id`, `vulnerability_id` etc; use OasisLMF engine or a separately verified equivalent to produce a real, scientifically qualified GUL.
4. Only when policy schedule, limits, deductible, coinsurance parties/actual shares and reinsurance treaty ordering are available, promote GUL to *real* insured gross/net. Until then keep the toy gross/net and annual exceedance charts explicitly labelled synthetic arithmetic.

**Admission:** always `model_input_approved=false`, `oasis_engine_executed=false`, `real_insurer_or_policy_TIV_used=false`, `toy_hash_event_probability_is_calibrated=false` in computed receipt. This step demonstrates *software plumbing*, not scientific proof of a CAT portfolio or 2027 insurance coverage.
