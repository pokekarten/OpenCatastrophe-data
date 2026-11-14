<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# LUISA point-pixel conditional sensitivity on Kyrill

This is a small, deterministic integration run of the JRC 50 m LUISA raster,
the CLIMAAX damage workbook, CLIMAAX's six source response curves and the
source-pinned CLIMK ERA5 Kyrill footprint. It checks that a land-use pixel can
be joined to a storm gust and converted to conditional structural-damage
sensitivity while preserving source curve labels. It is not a building or
insured-portfolio loss model.

## Exact executed result

The machine-readable, one-table-per-site-and-curve receipt is
`research/observations/windstorm_europe_luisa_point_sensitivity_kyrill_v0.toml`;
it includes source, runner and configuration hashes. The
fictional point configuration is the TOML file
`research/fixtures/windstorm_europe_luisa_point_sensitivity_v0.toml`.
The executable is [windstorm_europe_luisa_point_sensitivity_v0.py](../../research_runners/windstorm_europe_luisa_point_sensitivity_v0.py).

| Fictional point | CLIMK gust (m/s) | LUISA code | Structural maximum per pixel (2010 EUR) |
|---|---:|---:|---:|
| London | 34.379973 | 1210 | 450,264.88 |
| Paris | 22.871452 | 1111 | 857,528.26 |
| Cologne | 33.411882 | 1210 | 450,264.88 |

The “pixel maximum” multiplies the workbook's `structural €/m²` by the full
2,500 m² pixel area. The workbook gives this as a land-use damage proxy in
2010 euros; it is not observed value and not an individual-building
replacement sum. Contents are reported by the input workbook but excluded
from the calculation.

Each source curve is evaluated separately, by its exact CSV header, against
the CLIMK gust at the point. Summed across the three sampled pixels, the
conditional structural-loss sensitivities are:

| Exact curve CSV header | Conditional sum (2010 EUR) |
|---|---:|
| `weakest outbuilding` | 93,921.36 |
| `outbuilding strong` | 9,066.31 |
| `outbuilding` | 13.04 |
| `weak brick structure` | 0.00 |
| `strong brick structure` | 0.00 |
| `concrete buidling` | 0.00 |

These alternatives are deliberately not averaged or mapped from a land-use
code to a mix. The 0.40% versus 2.75% workbook/notebook column-order conflict
remains unresolved. The output is deterministic damage-percentage arithmetic;
it does not model the probability distribution of individual building
damage. Paris's zero here means only that every selected source curve is zero
at its sampled gust knot range; it is not evidence of zero wind risk.

## Reproduction

The exact input hashes and output values are recorded in the TOML receipt. The
full 1 GB JRC raster must be downloaded from the pinned URL in
`research/windstorm_europe_luisa2018_raster_audit_v0.toml`. Python needs
`rasterio` to read it and the repository's NetCDF4/NumPy environment for the
CLIMK hazard export. Run:

```sh
python -m unittest tests.test_windstorm_europe_luisa_point_sensitivity_v0
python research_runners/windstorm_europe_luisa_point_sensitivity_v0.py \
  --raster /data/windstorm-europe/LUISA_Basemap_2018_50m_rev0726.tif \
  --workbook /data/windstorm-europe/LUISA_damage_info_curves.xlsx \
  --curves /data/windstorm-europe/CURVES_feuerstein_koks.csv \
  --hazard /data/windstorm-europe/ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc \
  --sites research/fixtures/windstorm_europe_luisa_point_sensitivity_v0.toml \
  --output /tmp/luisa-kyrill-point-sensitivity.json
```

The run used CLIMK storm index 0 (Kyrill), bounds WGS84 `[-5,45,16,56]`,
three public city-centre coordinates, and 50 m LUISA pixels. The source map
is not spatially clipped to building footprints. Weather is the source's
72-hour maximum 3-second gust field. This run establishes neither annual
event frequency nor broad geographic coverage, and has no policy, contents,
or reinsurance terms.

Attribution for the derived inputs: European Commission Joint Research Centre,
LUISA Base Map 2018, Batista and Pigaiani (2021),
[doi:10.2905/JRC.NBGPQJ8](https://data.jrc.ec.europa.eu/dataset/51858b51-8f27-4006-bf82-53eba35a142c),
CC BY 4.0; CLIMAAX STORMS workflow and supplied curve source, attributed there
to Feuerstein et al. (2011), [doi:10.1016/j.atmosres.2010.12.026](https://doi.org/10.1016/j.atmosres.2010.12.026).
The CLIMK hazard is source-pinned in the result receipt and its separate
source report.

## Remaining model step

To use LUISA as the CLIMAAX workflow intends, resolve the two outbuilding
curve labels from an authoritative source, then implement and validate the
land-use-class-to-combined-curve mapping. For an asset-based loss model,
replace the one-pixel illustration with a versioned spatial aggregation and
validate asset area and value assumptions. This point-pixel sensitivity is a
reproducible bridge and a set of competing vulnerability outcomes, not a
promoted European calibration.
