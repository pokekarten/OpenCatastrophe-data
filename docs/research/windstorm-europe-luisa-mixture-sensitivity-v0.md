<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# LUISA wind curve mixture: full mapping sensitivity

Stand: 14 November 2026. This report compares the two plausible
interpretations of the CLIMAAX middle-curve order across the complete pinned
LUISA workbook. It corrects an earlier audit error: 0.40% and 2.75% described
only the disputed regular-outbuilding component, not the total class curve.

## Reproducible comparison

The runner reads all six construction shares for 46 LUISA classes and all 141
wind-speed knots in the pinned Feuerstein/Koks CSV. It computes two explicit
variants for each class and knot:

- **Name-resolved:** match the workbook share labels to the CSV labels by
  construction meaning. `strong outbuilding` maps to the CSV header
  `outbuilding strong`.
- **Legacy positional:** reproduce the original CLIMAAX notebook exactly,
  multiplying the workbook's standard share order by CSV columns 0–5.

No curve is selected as correct. The complete machine-readable 46-class
summary, source hashes and runner hash are in
`research/observations/windstorm_europe_luisa_curve_mixture_sensitivity_v0.toml`.
The runner is
[windstorm_europe_luisa_curve_mixture_sensitivity_v0.py](../../research_runners/windstorm_europe_luisa_curve_mixture_sensitivity_v0.py).

| Finding | Result |
|---|---:|
| LUISA classes compared | 46 |
| CSV wind-speed knots compared | 141 (0–140 m/s) |
| Classes with any difference between variants | 29 |
| Largest absolute difference | 32.5 percentage points |
| Class / wind speed at largest difference | 2110 / 63 m/s |
| Full class-2110 curve at 40 m/s, name-resolved | 29.40% |
| Full class-2110 curve at 40 m/s, legacy positional | 31.75% |

Class 2110 has 50% `weakest outbuilding`, 50% regular `outbuilding`, and 0%
`strong outbuilding`. At 40 m/s, the `weakest outbuilding` component is
`0.5 × 58% = 29.0%` under both interpretations. The regular-outbuilding
component is `0.5 × 0.8% = 0.40%` under name resolution and
`0.5 × 5.5% = 2.75%` under positional reproduction. Therefore the complete
curves are 29.40% and 31.75%, respectively. The old 6.875 ratio applies only
to the disputed component; the actual total-curve difference is 2.35
percentage points at that knot.

The maximum 32.5 percentage-point difference for class 2110 occurs at 63 m/s:
60.5% name-resolved versus 93.0% legacy positional. This confirms the
ordering has material sensitivity in some classes and wind ranges. These are
still deterministic mixtures of estimated damage curves, not observed loss,
fragility probabilities, or a calibrated Europe-wide vulnerability model.

## Upstream history checked

The [2 August 2023 upstream commit that introduced the curve file and original
LUISA notebook](https://github.com/CLIMAAX/STORMS/commit/7c49e1f3939cd4b6509112c5c6fde43d12a82461)
already contains this ordering: the CSV labels its middle columns
`outbuilding strong`, then `outbuilding`; the notebook lists workbook shares
as `outbuilding`, then `strong outbuilding` and multiplies by column position.
The original 2023 CSV SHA-256 is identical to the current pinned source
(`d960e67ab726815974feb08e5850054d7fac2873ea5bb3b02956e6262da7fd81`). The
pinned 2026 notebook retains the same mixing expression. No later correction
or author intent decision appears in the inspected file history. Thus the
ambiguity predates the 2026 LUISA update and has persisted since the earliest
available source history; that alone does not establish which artifact is
wrong.

## Reproduction

```sh
python -m unittest tests.test_windstorm_europe_luisa_curve_mixture_sensitivity_v0
python research_runners/windstorm_europe_luisa_curve_mixture_sensitivity_v0.py \
  --workbook /data/windstorm-europe/LUISA_damage_info_curves.xlsx \
  --curves /data/windstorm-europe/CURVES_feuerstein_koks.csv \
  --output /tmp/luisa-mixture-sensitivity.json
```

The runner rejects workbook and curve files whose SHA-256 differs from the
pinned sources. It compares knots as supplied and does not extrapolate or
interpolate.

## Model decision

Keep the two mappings separately named and versioned. The existing point
prototype evaluates the six original curves separately and does not use a
mixed class curve. Do not merge the variants, average them, or label either
one as the corrected historical implementation until an authoritative source
or decision resolves the discrepancy. If we develop a chosen interpretation
for our own model, record that as a new model version while preserving the
legacy positional reproduction for historical comparison.
