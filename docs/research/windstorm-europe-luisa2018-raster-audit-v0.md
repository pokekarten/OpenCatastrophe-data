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
5.5% for `outbuilding strong`. LUISA class 2110 has a 50% `outbuilding` share
and no `strong outbuilding` share. The name-resolved weighted response is
`0.5 × 0.8% = 0.40%`; the published positional order gives
`0.5 × 5.5% = 2.75%`. This 6.875-fold difference diagnoses the mismatch; it
does not select a corrected vulnerability value.

Until source semantics are clarified, the integrated model does not generate
LUISA-mixed vulnerability curves. Its explicit single-response path is
unaffected. The LUISA workbook values are also 2010-euro per-area structural
damage proxies, not current building-level replacement sums. Their use needs
area, country GDP/price-year updates, spatial matching and building-level
valuation assumptions, as detailed in the main rebuild report.
