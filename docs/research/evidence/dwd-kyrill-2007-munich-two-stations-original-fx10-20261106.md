<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original DWD Kyrill 2007: München-Flughafen and München-Stadt provider-byte gust research receipt

**As replayed 2026-11-06** on GitHub commit `ad3407075f9b860fdc0a11f78a1d024edd0d691a`, successful [original source run 42231216104](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42231216104), job 127937281883. The two original DWD archives were downloaded via HTTPS into ephemeral runner-local storage, checked as source ZIPs, SHA-256 hashed, completely parsed and deleted. Only the bounded station/day aggregates below are committed.

Original DWD files: station **01262 München-Flughafen**, 2,293,243 bytes, SHA-256 `ca273211d92b48449c1e92e140a3b6c5b4c99999307aa1ef2fad4fcb6c486fca`; station **03379 München-Stadt**, 2,643,542 bytes, SHA-256 `4a5abf0fdfbf073cee91179f018863e871a496e23199d8c9476d96ff934f0ff7`. They contain 523,154 and 525,519 original measurement rows respectively. Each has 144 original 10-minute values on each of 17, 18, 19 and 20 January 2007, no missing values; six pre-2000 source local-clock labels are excluded per archive.

The observed **18 January 2007** maxima from each archive are **33.0 m/s at station 01262 (QN1 only)** and **29.0 m/s at 03379 (QN3 only)**. QN1 must not be labelled equivalent to QN3; measurement height, devices, site metadata at 2007 and any wind-operator equivalence to modelled CLIMK ERA5 still need independent review. The **33.976 m/s** original CLIMK wind value comes from a different, invented *Munich* marker and different physical measurement operator. No modelled damage calibration, annual storm rate, annual AAL/AEP/OEP, insurer claims or licensed production-data admission has been established.

## Exact original GitHub-run aggregates (research-only)

```json
{
  "all_original_sources_independently_prior_pinned": false,
  "annual_AAL": null,
  "annual_AEP": null,
  "annual_OEP": null,
  "annual_event_rate": null,
  "both_2007_instrument_histories_verified": false,
  "contract": "OC_DWD_KYRILL_2007_TWO_MUNICH_STATION_GUST_HOLDOUT_V0",
  "dwd_vs_climk_spatial_scale_normalized": false,
  "fitted_spatial_damage_dependence": false,
  "fitted_vulnerability": false,
  "reported_2007_munich_maxima_are_insurer_claims": false,
  "same_historical_storm_attribution_proven": false,
  "same_measurement_height_verified": false,
  "source_archive_sha256_runtime_computed": true,
  "source_directory": "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/historical/",
  "stations": [
    {
      "dwd_station_id": "01262",
      "event_attribution_independently_verified": false,
      "first_original_clock": "1999-12-31T23:00:00",
      "first_source_clock_is_utc": false,
      "four_day_window_utc": [
        {
          "day_utc": "2007-01-17",
          "max_3second_gust_mps_all_quality": "12.2",
          "max_3second_gust_mps_qn2_or_qn3": null,
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
          "max_3second_gust_mps_all_quality": "33.0",
          "max_3second_gust_mps_qn2_or_qn3": null,
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
          "max_3second_gust_mps_all_quality": "28.1",
          "max_3second_gust_mps_qn2_or_qn3": null,
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
          "max_3second_gust_mps_all_quality": "16.5",
          "max_3second_gust_mps_qn2_or_qn3": null,
          "missing_value_records": 0,
          "observed_10minute_records": 144,
          "quality_flag_record_counts": {
            "1": 144
          },
          "unobserved_10minute_slots": 0,
          "valid_gust_records": 144
        }
      ],
      "full_product_rows": 523154,
      "fx10_statistic": "MAX_3SECOND_GUST_IN_LAST_10MIN; ORIGINAL_UTC_ENDSTAMP",
      "last_source_clock_utc": "2009-12-31T23:50:00Z",
      "measuring_height_and_location_in_2007_source_metadata_verified": false,
      "observed_building_damage": false,
      "original_archive_bytes": 2293243,
      "original_archive_filename": "10minutenwerte_extrema_wind_01262_20000101_20091231_hist.zip",
      "original_archive_sha256": "ca273211d92b48449c1e92e140a3b6c5b4c99999307aa1ef2fad4fcb6c486fca",
      "pre_2000_local_clock_prelude_excluded": 6,
      "station_label_candidate": "Muenchen-Flughafen"
    },
    {
      "dwd_station_id": "03379",
      "event_attribution_independently_verified": false,
      "first_original_clock": "1999-12-31T23:00:00",
      "first_source_clock_is_utc": false,
      "four_day_window_utc": [
        {
          "day_utc": "2007-01-17",
          "max_3second_gust_mps_all_quality": "12.3",
          "max_3second_gust_mps_qn2_or_qn3": "12.3",
          "missing_value_records": 0,
          "observed_10minute_records": 144,
          "quality_flag_record_counts": {
            "3": 144
          },
          "unobserved_10minute_slots": 0,
          "valid_gust_records": 144
        },
        {
          "day_utc": "2007-01-18",
          "max_3second_gust_mps_all_quality": "29.0",
          "max_3second_gust_mps_qn2_or_qn3": "29.0",
          "missing_value_records": 0,
          "observed_10minute_records": 144,
          "quality_flag_record_counts": {
            "3": 144
          },
          "unobserved_10minute_slots": 0,
          "valid_gust_records": 144
        },
        {
          "day_utc": "2007-01-19",
          "max_3second_gust_mps_all_quality": "27.8",
          "max_3second_gust_mps_qn2_or_qn3": "27.8",
          "missing_value_records": 0,
          "observed_10minute_records": 144,
          "quality_flag_record_counts": {
            "3": 144
          },
          "unobserved_10minute_slots": 0,
          "valid_gust_records": 144
        },
        {
          "day_utc": "2007-01-20",
          "max_3second_gust_mps_all_quality": "17.9",
          "max_3second_gust_mps_qn2_or_qn3": "17.9",
          "missing_value_records": 0,
          "observed_10minute_records": 144,
          "quality_flag_record_counts": {
            "3": 144
          },
          "unobserved_10minute_slots": 0,
          "valid_gust_records": 144
        }
      ],
      "full_product_rows": 525519,
      "fx10_statistic": "MAX_3SECOND_GUST_IN_LAST_10MIN; ORIGINAL_UTC_ENDSTAMP",
      "last_source_clock_utc": "2009-12-31T23:50:00Z",
      "measuring_height_and_location_in_2007_source_metadata_verified": false,
      "observed_building_damage": false,
      "original_archive_bytes": 2643542,
      "original_archive_filename": "10minutenwerte_extrema_wind_03379_20000101_20091231_hist.zip",
      "original_archive_sha256": "4a5abf0fdfbf073cee91179f018863e871a496e23199d8c9476d96ff934f0ff7",
      "pre_2000_local_clock_prelude_excluded": 6,
      "station_label_candidate": "Muenchen-Stadt"
    }
  ],
  "status": "TWO_REAL_DWD_STATION_ARCHIVES_WINDOW_RESEARCH_NOT_CALIBRATED"
}
```

Raw observation rows, source ZIP files, fine timing and any person-associated records are not in this repository. This research evidence reports what the original reader observed, not a physically identical spatial cross-model holdout or a fitted wind-vulnerability relationship.
