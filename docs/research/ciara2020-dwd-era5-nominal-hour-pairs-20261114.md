<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara 2020 DWD FX_911 and ERA5 10fg nominal hourly pairs

**Status:** reproducible aggregate diagnostic implemented; this workspace could
not complete the live source replay. No model-skill or loss admission.

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

## Execution status in this workspace

The live replay was attempted but stopped before source values were read:
`xarray`, `zarr` and `gcsfs` were absent. The repository's pinned requirements
are in `requirements-google-arco-2020-original-smoke.txt`; installing them was
blocked by the workspace filesystem being full (115 MB available at the time
of the attempt). Therefore no live hourly-pair result is claimed here. The
unit tests exercise the pairing and fail-closed aggregation logic using
synthetic fixtures. Run the live command in CI or another environment with the
pinned dependencies to produce actual aggregate metrics.

The original 72-hour CLIMK-WINDS footprint audit remains separate: its
multi-day 3-second gust footprint cannot be transformed into same-hour pairs
from the available published source field. This hourly diagnostic instead
uses the separately pinned Ciara 2020 ERA5 10fg series.
