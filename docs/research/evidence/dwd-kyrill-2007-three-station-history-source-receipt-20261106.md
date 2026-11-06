<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original DWD historical Kyrill 2007 three-station instrument-and-geography receipt

**Source-executed 2026-11-06; historical valid-date join, NOT a CLIMK calibration or loss model.** The original 10-minute FX_10 per-station metadata ZIPs were read on exact OpenCatastrophe-data commit `45c0bcd1122ef00596025e91fb734ebac893d639` in successful [GitHub Actions original-provider run #42246305755](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42246305755), job `127989307633`. The three original archive SHA-256 digests and original member digests below were established by the CI job; source ZIPs were ephemeral, no observation rows or wind-gust source archives are included. DWD original metadata source: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/meta_data/ . DWD 10-minute extreme-wind documentation is CC BY 4.0: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/DESCRIPTION_obsgermany_climate_10min_extreme_wind_en.pdf .

**Reviewed time-valid interval:** 2007-01-17 through 2007-01-20 inclusive, same date window as the separately source-verified historical gust summaries. Sensor height, instrument model, FX_10 parameter validity and station longitude/latitude come from the **original DWD station metadata**, not from the fictional CLIMK urban markers.

- Berlin-Tempelhof (00433): 52.4675°N / 13.4021°E, station altitude 47.72 m; Windsensor Classic 4.3303 at **10 m above ground**; original FX_10 QN1 wind readings in this window.
- München-Flughafen (01262): 48.3574°N / 11.8078°E, station altitude 443.60 m; Windsensor Classic 4.3303 (DWDSYN) at **10 m**; original FX_10 QN1 wind readings.
- München-Stadt (03379): 48.1632°N / 11.5429°E, station altitude 515.37 m; Windsensor Classic 4.3303 at **29.28 m**; original FX_10 QN3 wind readings.

**Important physics limitation:** The synthetic source sampling points are Berlin 52.5200°N / 13.4050°E, Munich 48.1351°N / 11.5820°E. Their approximate great-circle separations from these DWD station locations are respectively **5.84 km, 29.84 km (airport), and 4.26 km (city)**. Neither DWD QN3 nor a valid historical device period establishes wind-grid representativeness or normalizes 29.28 m observations to a 10 m reference. QN1 remains formally checked only; no station observed building/insurance losses. Modelled CLIMK gust and measured FX_10 are not implicitly identical spatial/temporal operators. No real-spatial damage dependence, annual AAL/AEP/OEP or SCR is inferred.

## Source-original strictly parseable CI result (reviewed exact head)

```json
{
  "contract": "OC_DWD_KYRILL_2007_THREE_STATION_TIME_VALID_SOURCE_HISTORY_V0",
  "scientific_model_admitted": false,
  "stations": [
    {
      "FX_10_parameter_interval_end": "20081120",
      "FX_10_parameter_interval_start": "19991231",
      "QN1_data_reclassified_as_QN3": false,
      "annual_AAL": null,
      "annual_AEP": null,
      "annual_OEP": null,
      "contract": "OC_DWD_KYRILL_2007_THREE_STATION_TIME_VALID_SOURCE_HISTORY_V0",
      "geography_interval_end": "20220912",
      "geography_interval_start": "19700910",
      "geography_latitude_deg": "52.4675",
      "geography_longitude_deg": "13.4021",
      "geography_station_altitude_m": "47.72",
      "historical_2007_station_sensor_source_join_verified": true,
      "historical_DWD_observation_QN1_or_QN3_independently_rechecked_here": false,
      "maxwind_instrument_interval_end": "20090329",
      "maxwind_instrument_interval_start": "19950531",
      "maxwind_instrument_model": "Windsensor Classic 4.3303",
      "maxwind_instrument_sensor_height_over_ground_m": "10",
      "physical_wind_calibrated": false,
      "source_geography_member_sha256": "6ed493f2261c941c9b4945688c04709d9f9b2ee727432f1f3e286c4a11c9fd5b",
      "source_maxwind_device_member_sha256": "fd2fc6bf3b8f77c6a728ed0d18291135eaac93a2f1d873563b5977936f9a5e23",
      "source_original_metadata_zip_sha256": "8c683f7d01de4461f731bb07837818a1a87ba9c9bbff2f3c4a3774e2730c51f6",
      "source_original_zip_byte_length": 10049,
      "source_parameter_member_sha256": "fbaa4abe5b5baeb56d01f47de01b7ae5e2ff2ea624b8b7c07cd6002169c2d3c6",
      "station_id": "00433",
      "station_point_identical_to_CLIMK_fictional_marker": false,
      "valid_for_complete_2007_01_17_through_2007_01_20": true,
      "vulnerability_calibrated": false
    },
    {
      "FX_10_parameter_interval_end": "20081111",
      "FX_10_parameter_interval_start": "19991231",
      "QN1_data_reclassified_as_QN3": false,
      "annual_AAL": null,
      "annual_AEP": null,
      "annual_OEP": null,
      "contract": "OC_DWD_KYRILL_2007_THREE_STATION_TIME_VALID_SOURCE_HISTORY_V0",
      "geography_interval_end": "20081127",
      "geography_interval_start": "20020517",
      "geography_latitude_deg": "48.3574",
      "geography_longitude_deg": "11.8078",
      "geography_station_altitude_m": "443.60",
      "historical_2007_station_sensor_source_join_verified": true,
      "historical_DWD_observation_QN1_or_QN3_independently_rechecked_here": false,
      "maxwind_instrument_interval_end": "20110920",
      "maxwind_instrument_interval_start": "20020517",
      "maxwind_instrument_model": "Windsensor Classic 4.3303 (DWDSYN)",
      "maxwind_instrument_sensor_height_over_ground_m": "10",
      "physical_wind_calibrated": false,
      "source_geography_member_sha256": "8ab964c4b31be3f808379b266bea7b29eda66202bde78b780a0560af8fc0ddc1",
      "source_maxwind_device_member_sha256": "f7468421ef47c916f0023150406f03e265e8adb47d01c3bb39b9fb195732f555",
      "source_original_metadata_zip_sha256": "a6c3e4bd40b37f26422a6cda5c0be1ebd760d2f1e3343a368953af44dea2684e",
      "source_original_zip_byte_length": 9411,
      "source_parameter_member_sha256": "033bfe43e260cee332aff50891f678e470af7ead920faf4efc019680c2745644",
      "station_id": "01262",
      "station_point_identical_to_CLIMK_fictional_marker": false,
      "valid_for_complete_2007_01_17_through_2007_01_20": true,
      "vulnerability_calibrated": false
    },
    {
      "FX_10_parameter_interval_end": "20261106",
      "FX_10_parameter_interval_start": "20061205",
      "QN1_data_reclassified_as_QN3": false,
      "annual_AAL": null,
      "annual_AEP": null,
      "annual_OEP": null,
      "contract": "OC_DWD_KYRILL_2007_THREE_STATION_TIME_VALID_SOURCE_HISTORY_V0",
      "geography_interval_end": null,
      "geography_interval_start": "19970708",
      "geography_latitude_deg": "48.1632",
      "geography_longitude_deg": "11.5429",
      "geography_station_altitude_m": "515.37",
      "historical_2007_station_sensor_source_join_verified": true,
      "historical_DWD_observation_QN1_or_QN3_independently_rechecked_here": false,
      "maxwind_instrument_interval_end": "20210509",
      "maxwind_instrument_interval_start": "19970710",
      "maxwind_instrument_model": "Windsensor Classic 4.3303",
      "maxwind_instrument_sensor_height_over_ground_m": "29.28",
      "physical_wind_calibrated": false,
      "source_geography_member_sha256": "3a7672cc14a190f51013bdcdfd6a74ba5179364087323b7d91d1451bd948026f",
      "source_maxwind_device_member_sha256": "ff05eeffea268875f325a6e89b81ea3e732cce9a3ecdfdda4ec68b4e93888701",
      "source_original_metadata_zip_sha256": "5525ce5656d1231c5eb0ecbe1b4b482f60b84d41262fa0ff22a1f46643da5da3",
      "source_original_zip_byte_length": 9116,
      "source_parameter_member_sha256": "11f13a031954d765dc68dffff6b09db5177cb4b9b6e6bf23f3264fc517c81b4a",
      "station_id": "03379",
      "station_point_identical_to_CLIMK_fictional_marker": false,
      "valid_for_complete_2007_01_17_through_2007_01_20": true,
      "vulnerability_calibrated": false
    }
  ]
}
```

Future CI replays must compare the three **source-original time-valid station outputs** exactly to this evidence block. On any source drift, stop and review a new immutable receipt; never silently refresh source hashes.
