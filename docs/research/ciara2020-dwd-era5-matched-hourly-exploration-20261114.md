<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara 2020: DWD and ERA5 matched-hour exploratory comparison

## Result

We decoded the original 96 hourly Google Research ARCO ERA5 10fg fields again and paired the nearest grid-cell value with each original DWD FX_911 hourly value for the three stations. All three DWD archives contain 96 valid observations with QN_8=3. Historical February 2020 station geometry, instrument and time-reference metadata were checked against the original DWD ZIP metadata members. The comparison uses two distinct ERA5 cells: (50.75°N, 7.25°E) for Köln/Bonn and Königswinter-Heiderhof, and (51.25°N, 7.25°E) for Wuppertal.

DWD describes FX_911 as the highest gust of the last hour and its source metadata says UTC. The ERA5 product is an hourly post-processed gust field. The source evidence does **not** prove identical interval boundaries or gust aggregation, so the 0-hour pairing is a documented-label comparison, not a certified like-for-like observation. We make no 10m height adjustment (Wuppertal's verified sensor is at 12m), and the two stations sharing one ERA5 cell are not independent weather-model validation points.

At the same UTC hour labels, ERA5 minus DWD mean differences are positive at all three sites, between 1.26 and 2.79 m/s. Pearson correlations range 0.889–0.935. These describe one storm at three stations and two cells; they are **not** bias corrections, model-skill estimates, or calibration. Every station's -1h, 0h and +1h metrics are reported; no best lag is selected.

| Station | ERA5 cell | DWD sensor height | 0h mean error (m/s) | 0h MAE (m/s) | 0h RMSE (m/s) | 0h correlation | -1h / 0h / +1h RMSE (m/s) |
|---|---|---:|---:|---:|---:|---:|---|
| Köln/Bonn (02667) | 50.75N, 7.25E | 10m | 2.787 | 2.952 | 3.805 | 0.935 | 3.818 / 3.805 / 4.155 |
| Wuppertal (15200) | 51.25N, 7.25E | 12m | 1.258 | 2.396 | 3.316 | 0.889 | 3.400 / 3.316 / 3.304 |
| Königswinter-Heiderhof (00603) | 50.75N, 7.25E | 10m | 2.270 | 2.718 | 3.426 | 0.934 | 3.331 / 3.426 / 3.667 |

The full aggregate metrics for all three offsets, including pair counts, MAE, signed mean error, RMSE, correlation and event peaks, are in `research/observations/ciara2020_dwd_era5_matched_hourly_exploration_20261114.toml`. Raw hourly series are not published.

## Reproduction

The runner reads only the three allowlisted DWD historical ZIPs and the pinned public ERA5 source. Its internal hourly buffers are opt-in; normal CLIs and receipts do not return raw time series. The source reader verifies the frozen normalized ERA5 decoded-value SHA before returning paired aggregates. Run focused offline tests with:

```sh
python -m unittest discover -s tests -p 'test_ciara2020_dwd_era5_matched_hourly_exploration_v0.py'
python -m unittest discover -s tests -p 'test_ciara2020_dwd_hourly_fx_original_station_observations_v0.py'
python -m unittest discover -s tests -p 'test_ciara2020_google_arco_real_96h_nrw_area_v0.py'
python -m unittest discover -s tests -p 'test_ciara2020_dwd_historical_feb2020_station_attestation_v0.py'
```

A live replay additionally needs the isolated dependencies in `requirements-google-arco-2020-original-smoke.txt` and anonymous public Google bucket access. The 96-hour source re-read and the aggregate result are reproducible from the original providers; the exact historical blobs are SHA pinned in the receipt and the prior DWD source evidence.

## Limits and next work

This event comparison cannot establish Germany-wide hazard skill or support a vulnerability curve. Main remaining blockers are: exact DWD versus ERA5 gust interval equivalence; the product-specific 12m versus 10m exposure difference; spatial representativeness and terrain/roughness; more independent stations and multiple storms (including historical severe events); and a separately sourced, licensed damage/claims dataset before fitting vulnerability. Future validation should freeze a station/event holdout plan before fitting any correction and score multiple seasons/storms, rather than choose a lag or correction from this single event.

## Sources and attribution

- Deutscher Wetterdienst (DWD), CDC hourly extreme-wind FX_911 historical observations and original station metadata. DWD data CC BY 4.0; attribute Deutscher Wetterdienst (DWD).
- Google Research ARCO ERA5, variable `10m_wind_gust_since_previous_post_processing`, underlying ECMWF/Copernicus ERA5. Copernicus Licence; acknowledge Copernicus Climate Change Service (C3S) and Google Research ARCO-ERA5.
- Historical sensor/location and UTC evidence is recorded in [`ciara2020_dwd_original_historical_station_metadata_attestation_20261114.toml`](../../research/observations/ciara2020_dwd_original_historical_station_metadata_attestation_20261114.toml).
