<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original DWD Berlin-Tempelhof Kyrill-window FX_10 provider-byte research receipt

**Status: research source-read proof, NOT science-admitted calibration, observed insurance loss, annual CAT frequency or native NextGen run.** Original provider ZIP was read on exact OpenCatastrophe-data commit `c04e68fee741b1aeb7813e64a17a5bb102adb293`, in successful [Actions #42185974162](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42185974162), job `127786278269` (2026-11-06). The original 2,292,326-byte DWD ZIP was temporary, excluded from Git and automatically deleted. Original source SHA-256: `56d4e4d64958ca1dc926af58dabed796c550e2ff4969f81868cfb797b1ed891e`.

Original URL: [DWD 10min FX_10 station 00433, 2000–2009](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/10minutenwerte_extrema_wind_00433_20000101_20091231_hist.zip).

The original auditor checked all **525,602** source product records. Its first original clock label is **1999-12-31 23:00** with **six MEZ, pre-2000 source rows excluded**. The Jan 17–20, 2007 **UTC** window has 144 observations per day, zero missing values and zero absent ten-minute slots. The daily measured maximum three-second gusts are **12.5, 33.5, 19.3, 20.9 m/s** on Jan 17, 18, 19, 20 respectively. **Every single observation carries original DWD quality flag QN1; NO QN2/3 gust peak exists in this window.** Such evidence is not automatically high-quality validation; review the historical QN1 meaning, station 2007 device/coordinates and relevant wind-statistic temporal support before source admission.

For context, CLIMK-WINDS v2 ERA5's original research footprint has **31.090 m/s** at the separate *fictional* Berlin marker (x142/y78), but the DWD station is not identical to the modelled site/grid centre, the measurement operators have not been normalized to a common interval, and a storm label/day does not establish cross-source event attribution. The 2.410 m/s difference is **descriptive only**, not a signed model bias, calibration target, observation-based building loss or uncertainty distribution. HANZE contains country-level heterogeneous economic damage reports and cannot provide observed individual building claims.

### Machine-readable exact original GitHub-run aggregate

```json
{
  "annual_AAL": null,
  "annual_AEP": null,
  "annual_OEP": null,
  "annual_event_rate": null,
  "archive_first_clock_is_utc": false,
  "archive_first_original_clock_label": "1999-12-31T23:00:00",
  "archive_last_utc": "2009-12-31T23:50:00Z",
  "climk_berlin_era5_source_max_gust_mps": "31.090",
  "climk_gust_statistic": "MAX_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT_NOT_SAME_OBSERVATION_OPERATOR",
  "climk_source_netcdf_sha256": "92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102",
  "contract": "OC_DWD_2007_KYRILL_BERLIN_TEMPELHOF_ORIGINAL_GUST_PREFLIGHT_V0",
  "daily_10minute_gust_aggregates": [
    {
      "day_utc": "2007-01-17",
      "max_3second_gust_within_10minutes_mps_all_quality": "12.5",
      "max_3second_gust_within_10minutes_mps_qn2_or_qn3": null,
      "missing_value_records": 0,
      "observed_10minute_records": 144,
      "quality_flag_record_counts": {
        "1": 144
      },
      "unobserved_10minute_slots": 0,
      "valid_gust_records": 144
    },
    {
      "day_utc": "2007-01-18",
      "max_3second_gust_within_10minutes_mps_all_quality": "33.5",
      "max_3second_gust_within_10minutes_mps_qn2_or_qn3": null,
      "missing_value_records": 0,
      "observed_10minute_records": 144,
      "quality_flag_record_counts": {
        "1": 144
      },
      "unobserved_10minute_slots": 0,
      "valid_gust_records": 144
    },
    {
      "day_utc": "2007-01-19",
      "max_3second_gust_within_10minutes_mps_all_quality": "19.3",
      "max_3second_gust_within_10minutes_mps_qn2_or_qn3": null,
      "missing_value_records": 0,
      "observed_10minute_records": 144,
      "quality_flag_record_counts": {
        "1": 144
      },
      "unobserved_10minute_slots": 0,
      "valid_gust_records": 144
    },
    {
      "day_utc": "2007-01-20",
      "max_3second_gust_within_10minutes_mps_all_quality": "20.9",
      "max_3second_gust_within_10minutes_mps_qn2_or_qn3": null,
      "missing_value_records": 0,
      "observed_10minute_records": 144,
      "quality_flag_record_counts": {
        "1": 144
      },
      "unobserved_10minute_slots": 0,
      "valid_gust_records": 144
    }
  ],
  "dwd_gust_statistic": "MAX_3S_WITHIN_EACH_10MIN; TIMESTAMP_END_OF_INTERVAL_UTC",
  "dwd_original_archive_filename": "10minutenwerte_extrema_wind_00433_20000101_20091231_hist.zip",
  "dwd_station_id": "00433",
  "dwd_station_identical_to_climk_synthetic_site": false,
  "full_source_product_rows": 525602,
  "historical_kyrill_label_day_utc_exact_identity_confirmed": false,
  "observed_insured_claims": false,
  "one_reported_storm_attribution_proven": false,
  "original_archive_byte_count": 2292326,
  "original_archive_sha256": "56d4e4d64958ca1dc926af58dabed796c550e2ff4969f81868cfb797b1ed891e",
  "original_observations_day_count": 4,
  "pre_2000_december_source_clock_rows_excluded": 6,
  "pre_2000_non_utc_measurements_not_used_for_kyrill": true,
  "scientific_admission": false,
  "source_original_raw_gust_rows_persisted": false,
  "source_station_coordinates_at_2007_original_metadata_verified": false,
  "station_label_candidate": "Berlin-Tempelhof",
  "status": "ORIGINAL_DWD_GUST_PRELIMINARY_HAZARD_HOLDOUT_NOT_CALIBRATED",
  "vulnerability_fitted": false,
  "window_utc_end": "2007-01-20T23:50:00Z",
  "window_utc_start": "2007-01-17T00:00:00Z"
}
```

Do not use `annual_AAL`, `annual_AEP`, `annual_OEP`, insured losses, spatial damage dependence or source licensing as admitted unless separately supported. The full original DWD observation rows, source ZIP and instruments metadata are not republished here. All scientific admission flags remain false.
