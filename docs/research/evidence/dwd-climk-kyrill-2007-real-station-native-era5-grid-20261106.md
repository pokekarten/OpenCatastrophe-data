<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Real DWD station coordinates × original CLIMK Kyrill ERA5 native grid (research proof)

Original SHA-pinned NetCDF, 3 original DWD station/height/source receipts and two *fictional* CLIMK comparison markers. Exact successful [GitHub Actions run #42251191294](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42251191294), job 128006409563, checked-out source commit `cbd95cd7825f3588ac3d450e1c0923b1de7f51a0` (2026-11-06).

**No original NetCDF bytes, DWD weather observation rows or insurer exposures are committed.** This result reports CLIMK's *modelled storm-footprint maximum gust* at the precise time-valid meteorological station locations, not a DWD 10-minute FX_10 model-equivalent measure. Station 00433 and 01262 historical QN1 are only formally checked; station 03379 QN3 is 29.28 m above ground. There is no roughness/height adjustment, event-time operator alignment, inferred model bias, fitted vulnerability, annual frequency or annual AAL/AEP/OEP. All source admissions remain false.

Berlin (00433) maps to CLIMK (142,78), model 31.090 m/s; Munich Airport (01262) maps to (135,95), model **34.324 m/s**, a *different cell* from the fictional Munich reference marker; Munich City (03379) maps to (134,95), model 33.976 m/s. Any reported DWD minus CLIMK numerical differences are **descriptive only**.

## Strict original-source GitHub-run aggregate

```json
{
  "annual_AAL": null,
  "annual_AEP": null,
  "annual_OEP": null,
  "annual_event_rate": null,
  "contract": "OC_CLIMK_KYRILL_2007_DWD_STATION_NATIVE_GRID_HOLDOUT_V0",
  "era5_sample_original_bytes_verified_in_this_pure_function": true,
  "fictional_comparison_markers": 2,
  "original_dwd_measurement_and_metadata_receipts_git_blob_authenticated": true,
  "real_dwd_stations": 3,
  "same_physical_wind_operator_established": false,
  "source_dwd_metadata_proofs_git_blobs": {
    "berlin": "20ac79115e60beb6a8124789cf02956992b39e86",
    "history": "7e87179d21a217d7a9d6f14e998c484865d05321",
    "munich": "dace35c11ac5272797662ea2860bdb768e080462"
  },
  "source_era5_sha256": "92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102",
  "station_to_grid_results": [
    {
      "descriptive_DWD_minus_ERA5_mps_not_validated_bias": "2.410",
      "dwd_station_id": "00433",
      "era5_grid_cell_center_distance_km": 7.55,
      "era5_native_cell_x": 142,
      "era5_native_cell_y": 78,
      "era5_original_kyrill_storm_footprint_max_gust_mps": "31.090",
      "fictional_marker_gust_mps": "31.090",
      "height_or_roughness_normalized": false,
      "in_same_era5_cell_as_fictional_city_marker": true,
      "observed_DWD_2007_01_18_max_3s_10min_gust_mps": "33.5",
      "observed_building_claims": false,
      "original_sensor_height_m": "10",
      "same_wind_measurement_operator_validated": false,
      "science_admitted_for_wind_model_calibration": false,
      "source_observation_quality_level": "1",
      "source_station_lat_deg": 52.4675,
      "source_station_lon_deg": 13.4021
    },
    {
      "descriptive_DWD_minus_ERA5_mps_not_validated_bias": "-1.324",
      "dwd_station_id": "01262",
      "era5_grid_cell_center_distance_km": 12.685,
      "era5_native_cell_x": 135,
      "era5_native_cell_y": 95,
      "era5_original_kyrill_storm_footprint_max_gust_mps": "34.324",
      "fictional_marker_gust_mps": "33.976",
      "height_or_roughness_normalized": false,
      "in_same_era5_cell_as_fictional_city_marker": false,
      "observed_DWD_2007_01_18_max_3s_10min_gust_mps": "33.0",
      "observed_building_claims": false,
      "original_sensor_height_m": "10",
      "same_wind_measurement_operator_validated": false,
      "science_admitted_for_wind_model_calibration": false,
      "source_observation_quality_level": "1",
      "source_station_lat_deg": 48.3574,
      "source_station_lon_deg": 11.8078
    },
    {
      "descriptive_DWD_minus_ERA5_mps_not_validated_bias": "-4.976",
      "dwd_station_id": "03379",
      "era5_grid_cell_center_distance_km": 10.162,
      "era5_native_cell_x": 134,
      "era5_native_cell_y": 95,
      "era5_original_kyrill_storm_footprint_max_gust_mps": "33.976",
      "fictional_marker_gust_mps": "33.976",
      "height_or_roughness_normalized": false,
      "in_same_era5_cell_as_fictional_city_marker": true,
      "observed_DWD_2007_01_18_max_3s_10min_gust_mps": "29.0",
      "observed_building_claims": false,
      "original_sensor_height_m": "29.28",
      "same_wind_measurement_operator_validated": false,
      "science_admitted_for_wind_model_calibration": false,
      "source_observation_quality_level": "3",
      "source_station_lat_deg": 48.1632,
      "source_station_lon_deg": 11.5429
    }
  ],
  "status": "REAL_DWD_STATION_COORDINATES_SAMPLED_IN_CLIMK_ERA5_KYRILL_NOT_CALIBRATION",
  "vulnerability_calibrated": false,
  "wind_model_bias_calibrated": false
}
```

Source replay workflow `.github/workflows/dwd-climk-kyrill-2007-station-grid-holdout.yml` must re-read the original NetCDF and compare the entire strict JSON evidence block against the output. No silent source digest or statistic refresh.
