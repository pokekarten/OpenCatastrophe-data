<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara 2020 DWD FX_911 and ERA5 10fg nominal hourly pairs

**Status:** original-source replay completed in GitHub Actions; descriptive
diagnostic only. No model-skill or loss admission.

The repository already pins the original DWD FX_911 station archives and
historical February 2020 site, device and parameter records for stations
02667, 15200 and 00603. It also pins a live-verified replay of 96 original
hourly Google Research ARCO ERA5 10fg fields at their historically nearest
native grid cells. This follow-on pairs the 96 UTC hour-ending labels in
memory and reports only aggregate error metrics by station, both for all
valid DWD hours and for the strict QN_8=3 subset. It writes no source hourly
values or pair-level rows.

Run in the repository's source-enabled environment:

```sh
python research_runners/ciara2020_dwd_historic_sites_era5_utc_peak_v1.py \
  --live-nominal-hour-pairs
```

The hourly label convention is nominally compatible: DWD FX_911 describes the
highest gust during the previous hour and labels the hour in UTC; ERA5 10fg is
indexed by its UTC validity hour. This does not establish identical sensor and
model sampling, postprocessing, spatial support, exposure or independence.
The 10–12 m DWD sensor is a point measurement while ERA5 is a 0.25-degree
grid-cell reanalysis. No height, terrain, exposure or representativeness
adjustment is made. Treat the paired metrics as descriptive diagnostics only,
not as model bias, calibrated skill, or a correction factor.

## Original-source replay result

The live replay succeeded in GitHub Actions run
[`43618572466`, job `132518942937`](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43618572466/job/132518942937).
It re-read the pinned DWD archives and historical metadata, plus all 96
original public ERA5 hourly fields. Each DWD station had 96 valid observations;
all 96 carried QN_8=3, so the strict and all-valid metrics coincide.

| DWD station | Historical site | 2020 ERA5 node | Paired hours | Mean ERA5−DWD (m/s) | MAE (m/s) | RMSE (m/s) |
|---|---|---|---:|---:|---:|---:|
| 02667 Köln/Bonn | 50.8645 N, 7.1575 E | 50.75 N, 7.25 E | 96 | 2.787 | 2.952 | 3.805 |
| 15200 Wuppertal | 51.2531 N, 7.2157 E | 51.25 N, 7.25 E | 96 | 1.258 | 2.396 | 3.316 |
| 00603 Königswinter-Heiderhof | 50.7350 N, 7.1931 E | 50.75 N, 7.25 E | 96 | 2.270 | 2.718 | 3.426 |

The aggregate-only source receipt is
[`ciara2020_dwd_era5_nominal_hourly_pair_v0.toml`](../../research/observations/ciara2020_dwd_era5_nominal_hourly_pair_v0.toml).
The unit tests separately exercise pairing and fail-closed aggregation using
synthetic fixtures. This workspace itself still lacks `xarray`, `zarr` and
`gcsfs`; its attempted local installation stopped because only 115 MB were
available. The successful CI replay supplies the live source evidence.

The original 72-hour CLIMK-WINDS footprint audit remains separate: its
multi-day 3-second gust footprint cannot be transformed into same-hour pairs
from the available published source field. This hourly diagnostic instead
uses the separately pinned Ciara 2020 ERA5 10fg series.
