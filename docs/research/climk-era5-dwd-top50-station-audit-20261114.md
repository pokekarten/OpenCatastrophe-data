<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# CLIMK ERA5 and DWD station gusts: 50-event unmatched-support audit

**Status:** source-replayed descriptive comparison; no model-skill admission.

On 14 November 2026, the runner replayed the original CLIMK-WINDS v2 ERA5
NetCDF and original DWD hourly FX_911 station archives for stations 02667,
00603 and 15200. For each event it paired the CLIMK `absolute_maxwindgusts`
per-storm field with the maximum DWD hourly gust in the 72 UTC hour labels
centered on the published `Storm_Dates` midpoint. CLIMK–WINDS describes its
absolute field as a daily maximum derived from hourly gust data; the source
variable metadata does not define its exact temporal aggregation bounds. The
two paired values therefore do **not** have proven identical time support.
The dates are the source's selected top 50 European winter storms ranked by
LI3D severity, not a complete event set. Source rank fields were not used.

The aggregate results below were produced by the reproducible runner
[`climk_era5_dwd_50event_station_audit_v0.py`](../../research_runners/climk_era5_dwd_50event_station_audit_v0.py).
Run it with the repository's pinned acquisition dependencies:

```sh
python research_runners/climk_era5_dwd_50event_station_audit_v0.py \
  --live-original-sources \
  --output research/observations/climk_era5_dwd_top50_station_audit_20261114.json
```

The output option refuses to overwrite a receipt. It writes an aggregate-only
JSON receipt at the chosen local path. Original hourly DWD and gridded CLIMK
observations are held in memory only and are not written into the repository.

## Complete-window descriptive contrasts

Only event windows with all 72 DWD hourly observations enter these descriptive
contrasts. The stricter sensitivity subset additionally requires QN_8=3 on
all 72 observations. No partial window is imputed. Sensor heights and source
metadata coverage are shown because they differ between stations.

| DWD station | Windows with DWD observations (of 50) | Windows with verified metadata (of 50) | Complete 72h | Complete 72h, all QN_8=3 | Sensor height in observed windows | CLIMK grid cells |
|---|---:|---:|---:|---:|---|---:|
| 02667 | 50 | 50 | 29 | 23 | 10 m: 50 | 1 |
| 00603 | 36 | 36 | 25 | 21 | 10 m: 5; 12 m: 31 | 1 |
| 15200 | 7 | 7 | 7 | 7 | 12 m: 7 | 1 |

| Station / subset | n | Mean paired difference CLIMK − DWD (m/s) | Mean absolute paired difference (m/s) | Root mean square paired difference (m/s) | Pearson r |
|---|---:|---:|---:|---:|---:|
| 02667 / complete 72h | 29 | −2.03 | 6.07 | 8.87 | 0.626 |
| 02667 / all QN_8=3 | 23 | −2.63 | 7.35 | 9.93 | 0.610 |
| 00603 / complete 72h | 25 | −0.75 | 6.80 | 9.09 | 0.572 |
| 00603 / all QN_8=3 | 21 | −1.60 | 7.39 | 9.75 | 0.599 |
| 15200 / complete 72h | 7 | −4.90 | 7.74 | 12.15 | 0.609 |
| 15200 / all QN_8=3 | 7 | −4.90 | 7.74 | 12.15 | 0.609 |

The two longer DWD series map to the same nearest ERA5 grid cell. Station
15200's archive begins in 2013, leaving 43 of the earlier CLIMK windows without
DWD observations at that station. It maps to one additional cell, so all three
stations cover two distinct ERA5 grid nodes. Station 15200 contributes only
seven of the selected windows;
that small subset does not establish independent spatial validation. Three
pairs of the selected CLIMK 72-hour event windows overlap in time.

## Interpretation and limits

These are arithmetic contrasts of paired source values, **not MAE/RMSE error
metrics, bias estimates, or predictive-skill measures**. CLIMK–WINDS describes
its field as a daily maximum gust derived from hourly data; its variable
metadata says `time:maximum` but does not specify the aggregation bounds or
gust averaging duration. The paper defines `Storm_Dates` as the midpoint of
the 3-day window with maximum LI3D; that event-selection window does not prove
that the per-storm gust field itself is a 72-hour maximum. DWD FX_911 is the
highest gust during the previous hour. Exact temporal equivalence and input
independence are not established.
The point stations and nearest grid cell also have different spatial support;
no interpolation or sensor-height adjustment was applied. The stations and
storm rows are not a representative or independent validation sample.

The CLIMK top-50 selection is unsuitable for annual frequency, OEP/AEP or
loss calibration. This audit contains no German vulnerability curve, insured
loss, exposure, return-period inference or bias correction. The result is
evidence about source behavior and coverage, not proof that the catastrophe
model is calibrated or complete.

## Source identity

- CLIMK-WINDS v2 ERA5, Flynn et al. (2025), Zenodo record 15305753, CC BY 4.0;
  original SHA-256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.
  The paper's [methods](https://essd.copernicus.org/articles/17/4431/2025/)
  describe daily maxima derived from hourly gust data and a separate 3-day
  sliding LI3D event-selection window; it does not specify the field's exact
  time bounds or gust averaging duration.
- DWD CDC hourly extreme wind FX_911 archives, CC BY 4.0 with DWD attribution;
  archives match the previously accepted source receipt. SHA-256: station
  02667 `e88536b7eebb6c7f94de63de56b1af85a0981fdd769e727f45f6d7db7c93ae78`,
  00603 `4a61a6394344bba05a06553794ac1a2d5edb4c4e3ac39ae1f26407e5f4e2f62b`,
  and 15200 `748ffdbc8f6ebf04a014ebf3d8fdc177e9a903349cc5b36e19f4c425998bfaa0`.

The local test suite verifies complete-window gating, the QN_8 sensitivity,
historical-metadata coverage, source parsing, status-only stdout, and
exclusive receipt writing. It does not substitute for independent validation.
