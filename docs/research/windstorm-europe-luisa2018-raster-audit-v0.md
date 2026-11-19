<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# LUISA 2018 50 m raster and CLIMAAX curve audit

Stand: 14. November 2026. This records an acquired source and a specific
cross-source ambiguity for the Windstorm Europe model. Full byte-level
metadata is in `research/windstorm_europe_luisa2018_raster_audit_v0.toml`.

## JRC LUISA source

The [JRC LUISA Base Map 2018 catalogue](https://data.jrc.ec.europa.eu/dataset/51858b51-8f27-4006-bf82-53eba35a142c)
provides a 50 m raster covering EU27 and additional European countries. The
audited file is `LUISA_Basemap_2018_50m_rev0726.tif` from revision
`VER2026-07-15`.

| Property | Audited value |
|---|---|
| Bytes | 1,019,186,382 |
| SHA-256 | `6693db65a8bb4d7f152e11533d121130c716037e82f67a55b67e8e82ef467c8a` |
| Grid | 130,000 × 92,000; 50 m; 1 int32 band |
| CRS / transform | EPSG:3035; origin (900000, 5500000), 50 m x, −50 m y |
| NoData / compression | 0 / LZW |
| Reuse | JRC `copyright.txt` declares CC BY 4.0; attribute the European Commission JRC and identify changes. |

The original TIFF was downloaded and its full size/hash checked. It is too
large for Git and remains a locally reproducible source. The query method
transformed fixture point coordinates from WGS84 into EPSG:3035 and read the
containing cell:

| Fixture point | LUISA class | Description from the CLIMAAX workbook |
|---|---:|---|
| London (−0.12, 51.50) | 1210 | Industrial or commercial units |
| Paris (2.35, 48.86) | 1111 | High density urban fabric |
| Cologne (6.96, 50.94) | 1210 | Industrial or commercial units |

These are point-pixel lookups only. They do not classify the footprint or
resistance of a particular building.

## CLIMAAX mixture order discrepancy

Pinned sources:

- `CURVES_feuerstein_koks.csv`, SHA-256
  `d960e67ab726815974feb08e5850054d7fac2873ea5bb3b02956e6262da7fd81`.
- `LUISA_damage_info_curves.xlsx`, SHA-256
  `a4ddff2c35bbc3536330389334c0fcae378799a49c6b7f3c643276065bbb8276`.
- [Published CLIMAAX STORMS wind workflow](https://handbook.climaax.eu/notebooks/workflows/STORMS/01_windstorm/Risk_assessment_STORMS.html).

The workbook orders material shares as `outbuilding`, then `strong
outbuilding`. The downloaded CSV labels its second and third response columns
`outbuilding strong`, then `outbuilding`. The published notebook's
`building_types` list instead says `outbuilding`, then `strong outbuilding`,
and multiplies those weights by curve columns positionally. This means the
notebook positionally reverses the two weights relative to the CSV labels.

At 40 m/s, the source CSV gives 0.8% for the named `outbuilding` curve and
5.5% for `outbuilding strong`. LUISA class 2110 has a 50% `weakest
outbuilding` share, a 50% regular `outbuilding` share, and no `strong
outbuilding` share. The often-quoted `0.40%` and `2.75%` are only the regular-
outbuilding component under the two mappings. They omit the other 50% of the
class. Including all six workbook shares gives total damage percentages of
29.40% under name-resolved mapping and 31.75% under the notebook's positional
mapping, a difference of 2.35 percentage points. The 6.875-fold ratio applies
only to that one disputed component, not to the complete class curve.

A full source-pinned comparison of all 46 LUISA classes at all 141 CSV wind
speed knots finds different curves for 29 classes. The largest absolute
difference is 32.5 percentage points for class 2110 at 63 m/s. Per-class
40 m/s values, maximum difference points, all input hashes, and the executable
comparison are in the [mixture sensitivity report](windstorm-europe-luisa-mixture-sensitivity-v0.md)
and its TOML receipt.

Upstream history shows that this is an original-workflow ambiguity, not a
consequence of the 2026 LUISA revision. The CSV was first added in the
[2 August 2023 source commit](https://github.com/CLIMAAX/STORMS/commit/7c49e1f3939cd4b6509112c5c6fde43d12a82461)
with the same byte-level SHA-256 as the pinned current CSV. The notebook at
that commit already had the category list in workbook order and multiplied
the CSV columns positionally. The current pinned notebook retains that mixing
cell. No upstream correction or mapping decision appears in the inspected
file history. This establishes the historical presence and persistence of
the discrepancy, but still does not tell us which artifact the authors meant
to change.

Until source semantics are clarified, the integrated model does not generate
LUISA-mixed vulnerability curves. Its explicit single-response path is
unaffected. The LUISA workbook values are also 2010-euro per-area structural
damage proxies, not current building-level replacement sums. Their use needs
area, country GDP/price-year updates, spatial matching and building-level
valuation assumptions, as detailed in the main rebuild report.

### Independent category-order cross-check

The [ECMWF/Copernicus Loss Indicators product guide](https://confluence.ecmwf.int/display/CKB/Loss+indicators+%28Tier+3%29%3A+Product+User+Guide)
independently names the six Feuerstein classes in this order: weakest
outbuildings, outbuilding, strong outbuilding, weak brick, strong brick,
concrete. This agrees with the CLIMAAX notebook's `building_types` list and
the LUISA workbook's share-column order. It makes a swapped pair of CSV labels
or curve columns a plausible explanation, but does not prove which artifact is
wrong: the curve source is still the pinned CSV, and its middle headers read
`outbuilding strong`, then `outbuilding`.

Accordingly, two different computations must remain distinguishable:

- **Name-resolved class interpretation:** map workbook `outbuilding` share to
  the exact CSV `outbuilding` column, and `strong outbuilding` share to
  `outbuilding strong`. For the disputed component in LUISA class 2110 at
  40 m/s this contributes 0.40%; including the 50% weakest-outbuilding share,
  the complete class curve is 29.40%.
- **Published notebook positional reproduction:** preserve the notebook's
  list and column positions exactly. The disputed component contributes
  2.75%; including the 50% weakest-outbuilding share, the complete class
  curve is 31.75%.

The independent taxonomy supports the semantic category order, but cannot
establish whether the CSV labels are transposed or the published computation
intended the positional result. The implementation therefore continues to
report the six source curves independently and does not admit either mixture
as the resolved model curve. Resolving this requires an authoritative erratum,
source-data clarification, or a byte-pinned upstream version whose mapping
can be reconciled to the cited category definitions.
