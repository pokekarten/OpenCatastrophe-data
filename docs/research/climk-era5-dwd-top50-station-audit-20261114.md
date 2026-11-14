<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# CLIMK ERA5 versus DWD station gusts: 50-event exploratory audit

**Status:** source-replayed descriptive comparison; no model-skill admission.

On 14 November 2026, the runner replayed the original CLIMK-WINDS v2 ERA5
NetCDF and the original DWD hourly FX_911 station archives for stations 02667
and 00603. It compared each CLIMK event's 72-hour `absolute_maxwindgusts`
grid-cell value with the maximum observed DWD hourly gust over the 72 UTC hour
labels centered on the published `Storm_Dates` midpoint. The dates are the
source's selected top 50 European winter storms ranked by LI3D severity; they
are not a complete event set. Source rank fields were not used.

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

## Complete-window results

Only event windows with all 72 DWD hourly observations enter the primary
metrics. The stricter sensitivity subset additionally requires QN_8=3 on all
72 observations. No partial window is imputed. Sensor heights and source
metadata coverage are shown because they differ between stations.

| DWD station | Windows with DWD observations (of 50) | Windows with verified metadata (of 50) | Complete 72h | Complete 72h, all QN_8=3 | Sensor height in observed windows | CLIMK grid cells |
|---|---:|---:|---:|---:|---|---:|
| 02667 | 50 | 50 | 29 | 23 | 10 m: 50 | 1 |
| 00603 | 36 | 36 | 25 | 21 | 10 m: 5; 12 m: 31 | 1 |

| Station / subset | n | Mean CLIMK − DWD (m/s) | MAE (m/s) | RMSE (m/s) | Pearson r |
|---|---:|---:|---:|---:|---:|
| 02667 / complete 72h | 29 | −2.03 | 6.07 | 8.87 | 0.626 |
| 02667 / all QN_8=3 | 23 | −2.63 | 7.35 | 9.93 | 0.610 |
| 00603 / complete 72h | 25 | −0.75 | 6.80 | 9.09 | 0.572 |
| 00603 / all QN_8=3 | 21 | −1.60 | 7.39 | 9.75 | 0.599 |

The CLIMK and DWD series map to the same nearest ERA5 grid cell for both
stations. Thus the two station comparisons are not independent spatial
validations; the combined support is one ERA5 grid node. Three pairs of the
selected CLIMK 72-hour event windows overlap in time.

## Interpretation and limits

The selected complete windows show negative mean ERA5-minus-DWD differences
at both stations, but these descriptive results do **not** establish a
correctable model bias or predictive skill. CLIMK's field is a postprocessed
maximum 3-second gust associated with an ERA5 storm footprint; DWD FX_911 is
the maximum gust during the previous hour. Exact aggregation-time support and
input independence have not been proven. The point stations and nearest grid
cell also have different spatial support; no interpolation or sensor-height
adjustment was applied. The stations and storm rows are not a representative
or independent validation sample.

The CLIMK top-50 selection is unsuitable for annual frequency, OEP/AEP or
loss calibration. This audit contains no German vulnerability curve, insured
loss, exposure, return-period inference or bias correction. The result is
evidence about source behavior and coverage, not proof that the catastrophe
model is calibrated or complete.

## Source identity

- CLIMK-WINDS v2 ERA5, Flynn et al. (2025), Zenodo record 15305753, CC BY 4.0;
  original SHA-256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.
- DWD CDC hourly extreme wind FX_911 archives, CC BY 4.0 with DWD attribution;
  station archive hashes and original metadata member hashes are in the JSON
  receipt. Archive hashes match the previously accepted source receipt.

The local test suite verifies complete-window gating, the QN_8 sensitivity,
historical-metadata coverage, source parsing, status-only stdout, and
exclusive receipt writing. It does not substitute for independent validation.
