<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Real DWD gust observations around Kyrill 2007 – Berlin station preflight

**Research-only, not a fitted model, independent insurer claims, or native NextGen acceptance.** Companion to OpenCatastrophe-data PR #1361 and NextGen PR #280. Earlier source-authenticated paired DWD station runs use 2010–2011, so they cannot validate the **2007-01-18** historical Kyrill case used in the CLIMK research. This preflight fixes the calendar mismatch rather than recycling the 2010–2011 gust statistics.

## Exact original source targeted

- Original DWD dataset: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/ (DWD CDC version v24.03).
- **Original historical ZIP, Berlin-Tempelhof station ID 00433, 2000–2009**: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00433_20000101_20091231_hist.zip. Historical directory publicly lists **2,292,326 compressed bytes**, but ZIP source SHA-256 and original observation completeness must be established by the actual native source run, not guessed from the filename.
- DWD 10-minute `FX_10` is the **maximum 3-second gust in each preceding 10-minute interval**, timestamped at interval end in **UTC** from 2000 onward. It is *not* ten-minute **mean** wind, nor guaranteed to be the same gust accumulation operator, grid alignment, or event-specific temporal support as CLIMK. DWD instrument changes, relocations and historical station coordinates remain separate admission gates.
- Existing original CLIMK-WINDS v2 Kyrill ERA5 x142/y78 synthetic Berlin marker is **31.090 m/s**, from original SHA-256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102` and successful source workflow 42095141447. The marker at 13.4050/52.5200 is imaginary, not identical to Berlin-Tempelhof.

## Scientific method and exclusion rules

Run standard-library-only `scripts/dwd_kyrill_2007_berlin_original_v0.py` **on the entire original ZIP bytes**. Validate archive limits, CRCs, one correct product member and required raw header names, numeric bounds, station identity 00433, UTC 10-minute grid, monotone records, DWD quality flags, and proper missing `-999` handling. Archive digest and original extent are printed only after real byte verification. The report contains four UTC-day aggregates for 17, 18, 19 and 20 January 2007, each with observed/missing/absent counts, separated quality categories, and maximum FX_10 gust with **all** versus quality-flag 2/3 readings. Missing values and absent intervals must not be silently converted to zeros; QN1 must not silently become QN2/3.

Workflow: `.github/workflows/dwd-kyrill-2007-original-berlin-holdout.yml` performs synthetic-only negative testing first and then ephemeral original DWD ZIP acquisition, actual original-byte parsing, and output of **aggregates only**. The native DWD output is not committed, and no original station rows are published. The full source SHA, historical station metadata and observed Jan 2007 quality counts must be reviewed before using those data beyond preliminary hazard holdout.

**Important scientific limits:** Source storm name/date matching from HANZE/CLIMK and a DWD measurement interval alone does **not** prove event attribution or meteorological operator equivalence. There is no original DWD 2007 geometry/instrument chain proven here, no Munich DWD 2007 site identified and verified on the same product, no observed insured losses, no fitted windstorm vulnerability, no built spatial damage copula, and **no annual AAL/AEP/OEP**. Do not change existing FFBK/RIM tolerances/seeds or promote these sources into production without separate rights/physical-validation review. Keep PR Draft.

## Run

```bash
python -m unittest tests.test_dwd_kyrill_2007_berlin_original_v0 -v
# Actual original archive must already be acquired and preserved outside Git:
python -m scripts.dwd_kyrill_2007_berlin_original_v0 \
  --original-zip /private/dwd-original/10minutenwerte_extrema_wind_00433_20000101_20091231_hist.zip \
  --output /private/dwd-reports/berlin-kyrill-2007-gust-research.json
```

The offline unit tests use a **constructed toy ZIP**; they are not real January 2007 wind observations. Only a successful original-provider source execution may be reported as an observed-data preflight.
