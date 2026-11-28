<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synthetic crop-area × direct-value impact (2026-11-05)

**Non-admission research only. No real insurance loss, original crop or hazard
field, policy, insured TIV, frequency, ELT, AEP, OEP, or CAT model.**

## Causal chain and evidence boundary

The new runner research_runners/synthetic_crop_value_impact_v0.py re-runs
the exact synthetic-only geometry gate in
research_runners/synthetic_crop_hazard_area_overlay_v0.py, rather than trusting
any hand-written loss or area result. The two small local fictional JSON inputs
must have explicit user-pinned SHA-256. They are never read from original JRC
assets, real hazard sources, insurer databases or external network access.

It performs **invented direct crop-value arithmetic**, NOT insured payouts,
production value, independent agricultural damage calibration, claim or PML.
All perils, areas, fields and events are fake test cases.

Fixed fictional values (EUR/ha): SYNTH-WHEAT 10,000; SYNTH-BARLEY 8,000;
SYNTH-MAIZE 14,000. They are illustrative fractions-of-one-hectare constants,
not German harvest prices, crop yield or sums insured.

The invented and intentionally non-calibrated loss fractions are:

| Flood depth (m) | Hypothetical value impaired | Hail diameter (mm) | Hypothetical value impaired |
| ---: | ---: | ---: | ---: |
| 0 | 0% | 0 | 0% |
| 1 | 20% | 20 | 10% |
| 2 | 50% | 40 | 35% |
| 3 | 75% | 60 | 65% |

No interpolation or extrapolation is permitted. Untabulated hazard intensity
blocks rather than being guessed; hailstone diameter is not automatically an
energy, crop-loss, or policy payout model. Crop phenology, local market,
production and seasonality remain unmodelled.

## Value conservation and unknown coverage

The area overlay assigns every square metre to:
1. explicit numeric intensity, including known-zero hazard;
2. explicit nodata, still unknown, or
3. outside the modelled support, also unknown, not dry.

The illustrative **lower** direct-value impact multiplies known intensity bands
by the corresponding invented damage fraction and invented value per hectare.
The **upper** adds at most 100% of the invented field value for all unknown
support, irrespective of why that area is unknown.

These arithmetic bounds are **not confidence intervals**, real
economic/insured risk estimates, annual loss curves or a calibrated impact.
They are a demonstration that we do not silently turn missing hazard data
into zero loss or double-count overlapping hazard polygons.

## Exact invented two-field result

Two invented one-hectare parcels: SYNTH-WHEAT is half covered by 2 m, half
by 1 m; SYNTH-MAIZE is half covered by 1 m and half explicit nodata:

| Quantity | Fictional EUR |
| --- | ---: |
| Total invented field value | 24,000 |
| Wheat (0.5 ha × EUR 10k/ha × 50%) | 2,500 |
| Wheat (0.5 ha × EUR 10k/ha × 20%) | 1,000 |
| Maize (0.5 ha × EUR 14k/ha × 20%) | 1,400 |
| Known-support illustrative direct value impact: lower | **4,900** |
| Unknown-support additional impact upper | 7,000 |
| Illustrative direct value impact upper | **11,900** |

No real original Parquet was downloaded or used. Zero actual insured TIV, zero
actual claims and zero model calibration were inferred. This is not a property
building portfolio, not German farm value, and not an R+V insurer portfolio.

## Reproduction

The two entirely invented inputs are created locally according to the exact
fixture shapes in tests/test_synthetic_crop_value_impact_v0.py. Hash each
serialized JSON file with sha256sum, keep files OUTSIDE the repository and run:

    python research_runners/synthetic_crop_value_impact_v0.py \
      /tmp/invented-parcels.json /tmp/invented-hazard.json \
      --parcels-sha256 <exact-original-synthetic-json-sha256> \
      --hazard-sha256 <exact-original-synthetic-json-sha256>

Synthetic-only regression tests:

    python -m unittest discover -s tests -p test_synthetic_crop_value_impact_v0.py -q

## Next science and engineering gates

1. Obtain the real corrected JRC EuroCrops original de4_2023.parquet from
   gpqtv202, independently record its identity and validate rights, full source
   coverage, seasonal source semantics, exact crop taxonomy and geometries.
2. Verify actual flood/hail event intensity, timing, spatial support, physical
   meaning, data rights and uncertainty independently. Do not pass real JRC
   rows into this synthetic-only module.
3. Research crop- and phenology-specific vulnerability, farm valuation,
   partial harvesting, farm subsidies and weather dependence; independently
   calibrate and validate with admissible original loss evidence.
4. Model genuine or labelled *synthetic* crop-specific insurance coverage,
   deductibles, TIV/limit semantics and OED format (never equate a crop to
   OED BuildingTIV). Only with suitable event occurrence rates, catalogues,
   peril dependencies, treaties and retro may AEP, OEP, gross/net be claimed.

Every result remains research_only, with explicit insured_gross_or_net_loss=false,
event_frequency_calibrated=false, elt_or_aep_oep_calculated=false and
admitted_cat_model_input=false.
