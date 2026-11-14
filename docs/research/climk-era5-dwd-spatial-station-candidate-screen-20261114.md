<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Spatial DWD station screen against CLIMK-WINDS v2 ERA5

**Status:** exploratory source audit; no model-skill, frequency or loss
admission.

This screen extends the earlier three-station comparison with 15
geographically spread DWD stations selected from the publisher's hourly
extreme-wind directory. The DWD station list and archive index contained 564
station records and 448 historical FX ZIP links when retrieved. Candidate
stations were chosen on distinct nearest CLIMK ERA5 grid cells, excluding the
three stations in the first audit; archive filename date ranges covered 35–50
of the selected event-context windows centered on the CLIMK `Storm_Dates`
labels. The archive screen is a purposive spatial sample, not a random sample.

The runner replays the original CLIMK-WINDS v2 ERA5 NetCDF, the two DWD
directory sources and all 15 original station archives against the exact
SHA-256 pins in the
[`source manifest`](../../research/observations/climk_era5_dwd_spatial_station_candidate_sources_20261114.toml).
It resolves each event window against DWD's historical site, instrument and
parameter metadata. The first three stations' aggregate comparison remains in
the [initial audit report](climk-era5-dwd-top50-station-audit-20261114.md).

Run the live source audit with the repository's pinned acquisition
dependencies:

```sh
python research_runners/climk_era5_dwd_spatial_station_candidate_screen_v0.py \
  --live-original-sources \
  --output /tmp/climk-era5-dwd-spatial-candidate-screen.json
```

The JSON receipt is aggregate-only and written exclusively to the requested
local path. Hourly DWD readings, CLIMK event rows and station-by-event series
are held in memory and are not written to the repository.

## Hour-ending correction

The numerical tables were replayed from the pinned original CLIMK and DWD
files using V3 hour-ending labels 01:00 through 00:00 of the following date.
These represent Storm_Dates 00:00–24:00 UTC in DWD. CLIMK day-boundary and
gust-duration equivalence remain unproven.

## Coverage and results

Fourteen of the 15 downloaded candidate archives could be checked against
historical station, instrument and UTC parameter metadata. Station 01832 is
blocked because its historical metadata cannot uniquely support the sampled
event windows. The 14 auditable stations map to 14 distinct nearest ERA5 grid
cells. Combined with the two cells from the earlier comparison, the current
German station screen touches 16 cells. This count is spatial coverage, not 16
independent validations.

The table compares each CLIMK per-storm daily field with the maximum of DWD's
24 hourly gust observations on the same `Storm_Dates` calendar date. It
requires a complete DWD day; the QN_8=3 subset requires all 24 values to have
that quality code. The 72-hour context columns describe data coverage around
the event label and do not define the daily comparison values. CLIMK's exact
UTC day boundaries and gust averaging duration remain unproven. Heights and
elevations are from original DWD event-era metadata. No sensor-height or
terrain adjustment was made.

| Station | Archive-supported event windows | DWD windows with readings | Complete 72h context | Complete Storm_Dates days | Complete days, all QN_8=3 | Sensor height (m AGL) | Station elevation (m) | Mean paired difference CLIMK−DWD (m/s) | Mean absolute paired difference (m/s) | RMS paired difference (m/s) | Pearson r |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|
| 00183 Arkona | 50 | 50 | 28 | 28 | 23 | 24 | 42 | -8.96 | 11.13 | 13.83 | 0.722 |
| 00222 Aue | 37 | 36 | 12 | 14 | 10 | 13 | 391 | -4.83 | 12.75 | 13.95 | 0.581 |
| 00460 Berus | 50 | 50 | 27 | 27 | 23 | 12 | 362.33–363 | -5.28 | 10.39 | 14.04 | 0.210 |
| 01228 UFS TW Ems | 50 | 41 | 8 | 17 | 12 | 15 | 0 | -2.76 | 7.38 | 11.23 | 0.616 |
| 01346 Feldberg/Schwarzwald | 50 | 50 | 27 | 28 | 22 | 18.4 | 1486.07 | -21.66 | 22.03 | 25.33 | 0.401 |
| 01684 Görlitz | 50 | 50 | 29 | 29 | 23 | 12–13 | 238–238.48 | -8.04 | 11.29 | 14.36 | 0.425 |
| 01832 Großer Arber | 50 | — | — | — | — | — | — | blocked | — | — | — |
| 01975 Hamburg-Fuhlsbüttel | 50 | 50 | 29 | 29 | 23 | 10 | 10.65–13 | -0.43 | 7.30 | 9.15 | 0.668 |
| 02494 Kalkar | 43 | 20 | 0 | 0 | 0 | 10 | 31.33 | — | — | — | — |
| 02925 Leinefelde | 50 | 50 | 28 | 29 | 23 | 11.6–12 | 355.87–356 | -1.40 | 7.89 | 10.38 | 0.502 |
| 03032 List auf Sylt | 50 | 50 | 29 | 29 | 23 | 10–12 | 24.7 | -7.11 | 10.56 | 13.48 | 0.606 |
| 03167 Bad Marienberg | 50 | 50 | 26 | 27 | 21 | 10–12 | 545.37–546.66 | 1.42 | 7.84 | 9.60 | 0.442 |
| 03552 Neuruppin | 50 | 49 | 27 | 28 | 22 | 18 | 38.44 | -5.23 | 8.29 | 10.37 | 0.756 |
| 03603 Niederstetten | 50 | 21 | 0 | 0 | 0 | 10 | 463 | — | — | — | — |
| 03730 Oberstdorf | 50 | 44 | 24 | 28 | 22 | 10 | 805.76–806 | 0.10 | 11.68 | 12.23 | 0.601 |

Among the 14 stations with verified event-era metadata, 12 have at least 10
complete Storm_Dates days; two have none. An archive filename covering an
event window does not guarantee actual hourly readings: 02494 had 20 windows
with partial context data but no complete Storm_Dates day, and 03603 had 21
windows with some readings but no complete Storm_Dates day. Station 01228 had
eight complete 72-hour context windows but 17 complete Storm_Dates days.

## What the discrepancies do and do not say

The mean paired differences are negative at 10 of the 12 stations with at
least one complete Storm_Dates day; two are positive. For example,
Feldberg/Schwarzwald has a sensor at 18.4 m above ground and a reported
station elevation near 1,486 m; its 28-day mean paired difference is −21.59
m/s. Arkona's 24 m sensor has a −9.03 m/s mean paired difference, while
10–12 m sensors at Hamburg and Bad Marienberg show −0.50 and 1.46 m/s. These
arithmetic contrasts are not error metrics or grounds for a common
multiplicative or additive correction. They highlight the unresolved role of
sensor height, local terrain, exposure, offshore setting, historical siting
and measurement definitions.

The station sample is purposive, all windows reuse the same source-selected
CLIMK storms, several station readings share each storm, and two long-record
stations in the earlier comparison share a CLIMK cell. DWD and ERA5 input
independence and exact temporal equivalence are unproven. The largest
discrepancies could reflect exposure or site representativeness as well as
model behavior. Do not call these differences model bias or use them to fit a
correction.

CLIMK's top-50 list is not a complete event catalogue. This screen supports no
annual rate, OEP/AEP, German vulnerability curve, insured loss, calibration or
validated model-skill claim. It is useful for identifying coverage gaps,
metadata blockers and places where a later, pre-registered validation should
control station height and terrain explicitly.

## Source identity and reuse

- CLIMK-WINDS v2 ERA5, Flynn et al. (2025), Zenodo record 15305753, CC BY 4.0;
  original SHA-256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.
- DWD CDC hourly extreme wind FX_911 and station history, CC BY 4.0; attribute
  Deutscher Wetterdienst (DWD). Station-list, directory-index and archive SHA
  pins are in the source manifest. Archive hashes freeze the original bytes
  observed in this audit; they are not separate DWD-published checksum files.
