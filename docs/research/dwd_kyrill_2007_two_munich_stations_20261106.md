<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Kyrill 2007: Two original DWD Munich 10-minute maximum-gust stations

Research preflight only. No realized insurer loss, certified wind validation, fitted building vulnerability, fitted damage dependence or annual AAL/AEP/OEP.

Original provider: DWD CDC 10-minute extreme wind, historical archive [index](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/). Two independent historical source archives *covering* 2007 (actual full source analysis must succeed before confirming completeness and numeric gusts):

- **01262** München-Flughafen: `10minutenwerte_extrema_wind_01262_20000101_20091231_hist.zip`
- **03379** München-Stadt: `10minutenwerte_extrema_wind_03379_20000101_20091231_hist.zip`

Their historic installation, sensor height, moves and measurement basis may differ. **Do not spatially equate these station measurements to the fictitious Munich CLIMK nearest-neighbor source grid 134/95, whose modelled storm maximum is 33.976 m/s**, and do not claim measured asset damages. These station identifiers and period have public support from both the DWD index and independently published station references. Original raw measurements are downloaded ephemerally in GitHub Actions, hashed, parsed and checked, never committed.

The standard-library-only `scripts/dwd_kyrill_2007_munich_original_v0.py` reuses the proven DWD Berlin-Tempelhof timestamp, original ZIP structural, FX_10 missing-value and quality conventions to analyze **four UTC days 17–20 January 2007**. All original source product rows are processed to confirm station identity, time monotonicity, 2007 coverage, historical quality class QN1/2/3, missing values, ZIP CRC and selected daily aggregated maximum 3-second gust in 10-minute intervals. Pre-2000 source local-clock label rows are excluded. The `QN2/3`-only maximum is never filled from QN1 or inferred to be zero when absent.

The planned workflow runs synthetic-source negative tests and **then downloads both real archives**, and prints only four-day daily aggregates, original SHA256 digests and source quality completeness. The first successful original run will establish *candidate* SHA digests for separately pinned immutable source receipts. It does not admit rights, certify an original 2007 instrument height/coordinate crosswalk, prove that each gust is attributable to Kyrill, or fit a spatial damage law. In particular the 24 fictional NextGen assets in only two CLIMK grid cells remain an illustration, not a calibration sample.

Existing verified Berlin-Tempelhof measured 18 January maximum **33.5 m/s, all QN1**, is a preliminary descriptive physical comparison, not a general independent holdout yet. The historical station quality and equipment lineage need separate documented admission.
