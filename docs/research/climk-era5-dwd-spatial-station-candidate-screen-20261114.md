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
of the CLIMK top-50 72-hour windows. This was a purposive spatial screen, not a
random sample.

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

## Coverage and results

Fourteen of the 15 downloaded candidate archives could be checked against
historical station, instrument and UTC parameter metadata. Station 01832 is
blocked because its historical metadata cannot uniquely support the sampled
event windows. The 14 auditable stations map to 14 distinct nearest ERA5 grid
cells. Combined with the two cells from the earlier comparison, the current
German station screen touches 16 cells. This count is spatial coverage, not 16
independent validations.

Only windows with all 72 valid DWD hourly observations enter the paired
metrics. The QN_8=3 column is a stricter subset requiring every hour in the
window to have that quality code. Heights and elevations below are from
original DWD event-era metadata, counted only for windows with DWD readings.
No sensor-height or terrain adjustment was made.

| Station | Archive-supported windows | DWD windows with readings | Complete 72h | Complete 72h, all QN_8=3 | DWD sensor height (m AGL) | DWD station elevation (m) | Mean ERA5−DWD (m/s) | MAE (m/s) | RMSE (m/s) | Pearson r |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|
| 00183 Arkona | 50 | 50 | 28 | 23 | 24 | 42 | −11.10 | 11.41 | 14.88 | 0.832 |
| 00222 Aue | 37 | 36 | 12 | 9 | 13 | 391 | −7.52 | 13.82 | 15.06 | 0.577 |
| 00460 Berus | 50 | 50 | 27 | 23 | 12 | 362.33–363 | −7.84 | 9.31 | 13.95 | 0.510 |
| 01228 UFS TW Ems | 50 | 41 | 8 | 6 | 15 | 0 | −12.35 | 12.45 | 16.97 | 0.788 |
| 01346 Feldberg/Schwarzwald | 50 | 50 | 27 | 21 | 18.4 | 1486.07 | −25.07 | 25.07 | 27.46 | 0.659 |
| 01684 Görlitz | 50 | 50 | 29 | 23 | 12–13 | 238–238.48 | −10.11 | 11.28 | 14.90 | 0.655 |
| 01832 Großer Arber | 50 | — | — | — | — | — | blocked | — | — | — |
| 01975 Hamburg-Fuhlsbüttel | 50 | 50 | 29 | 23 | 10 | 10.65–13 | −2.50 | 6.38 | 8.82 | 0.785 |
| 02494 Kalkar | 43 | 20 | 0 | 0 | 10 | 31.33 | — | — | — | — |
| 02925 Leinefelde | 50 | 50 | 28 | 22 | 11.6–12 | 355.87–356 | −3.56 | 6.83 | 10.10 | 0.738 |
| 03032 List auf Sylt | 50 | 50 | 29 | 23 | 10–12 | 24.7 | −10.11 | 10.51 | 14.28 | 0.763 |
| 03167 Bad Marienberg | 50 | 50 | 26 | 20 | 10–12 | 545.37–546.66 | −0.82 | 7.24 | 9.85 | 0.414 |
| 03552 Neuruppin | 50 | 49 | 27 | 22 | 18 | 38.44 | −7.56 | 8.49 | 11.42 | 0.815 |
| 03603 Niederstetten | 50 | 21 | 0 | 0 | 10 | 463 | — | — | — | — |
| 03730 Oberstdorf | 50 | 44 | 24 | 22 | 10 | 805.76–806 | −0.55 | 11.62 | 12.17 | 0.686 |

Among the 14 stations with verified event-era metadata, 11 have at least 10
complete 72-hour windows; three have fewer than 10 or none. An archive filename
covering a storm date does not guarantee actual hourly readings: 02494 had 20
partial windows but none complete, and 03603 had 21 partial windows but no
complete window. Station 01228 had only eight complete windows.

## What the discrepancies do and do not say

The complete-window mean ERA5-minus-DWD differences are negative at all 12
stations with at least one complete pair, but their magnitudes vary widely.
For example, Feldberg/Schwarzwald has a sensor at 18.4 m above ground and a
reported station elevation near 1,486 m; its 27-window mean difference is
−25.07 m/s. Arkona's 24 m sensor has a −11.10 m/s mean difference, while
10–12 m sensors at Hamburg and Bad Marienberg show −2.50 and −0.82 m/s. These
are not grounds for a common multiplicative or additive correction. They
highlight the unresolved role of sensor height, local terrain, exposure,
offshore setting, historical siting and different model/observation support.

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
