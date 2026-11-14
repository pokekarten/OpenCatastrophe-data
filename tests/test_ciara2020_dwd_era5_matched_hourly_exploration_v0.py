# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import timedelta
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import tomllib
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import ciara2020_dwd_era5_matched_hourly_exploration_v0 as m


def synthetic_inputs():
    observations={}
    modeled={}
    for station in m.STATIONS:
        observations[station]={}
        modeled[station]=[]
        for i in range(96):
            timestamp=(m.START+timedelta(hours=i)).strftime("%Y%m%d%H")
            v=20.0+(i%13)*0.6
            observations[station][timestamp]=v
            modeled[station].append(v+1.0)
    attestation={
        "DWD_original_site_geography_Feb2020_verified":True,
        "DWD_original_sensor_height_type_Feb2020_verified":True,
        "DWD_original_FX911_hour_reference_declared_UTC":True,
        "DWD_FX911_and_ERA5_10fg_exact_gust_aggregation_same":False,
        "stations":[
            {"station_id":"02667","nearest_2020_ERA5_grid_lat":50.75,
             "nearest_2020_ERA5_grid_lon":7.25,"original_DWD_station_latitude_as_of_Feb2020":50.8645,
             "original_DWD_station_longitude_as_of_Feb2020":7.1575,
             "original_FX911_anemometer_height_above_ground_m_as_of_Feb2020":10.0,
             "historical_station_to_ERA5_grid_centre_km":14.295},
            {"station_id":"15200","nearest_2020_ERA5_grid_lat":51.25,
             "nearest_2020_ERA5_grid_lon":7.25,"original_DWD_station_latitude_as_of_Feb2020":51.2531,
             "original_DWD_station_longitude_as_of_Feb2020":7.2157,
             "original_FX911_anemometer_height_above_ground_m_as_of_Feb2020":12.0,
             "historical_station_to_ERA5_grid_centre_km":2.412},
            {"station_id":"00603","nearest_2020_ERA5_grid_lat":50.75,
             "nearest_2020_ERA5_grid_lon":7.25,"original_DWD_station_latitude_as_of_Feb2020":50.735,
             "original_DWD_station_longitude_as_of_Feb2020":7.1931,
             "original_FX911_anemometer_height_above_ground_m_as_of_Feb2020":10.0,
             "historical_station_to_ERA5_grid_centre_km":4.337},
        ],
    }
    return observations,modeled,attestation


class MatchedHourExplorationTests(unittest.TestCase):
    def test_aggregate_receipt_matches_runner_schema_and_no_go_gates(self):
        path=ROOT/"research"/"observations"/"ciara2020_dwd_era5_matched_hourly_exploration_20261114.toml"
        with path.open("rb") as f:
            receipt=tomllib.load(f)
        self.assertEqual(receipt["schema"],m.SCHEMA)
        self.assertEqual(receipt["stations"],3)
        self.assertEqual(receipt["unique_ERA5_grid_nodes"],2)
        self.assertFalse(receipt["DWD_and_ERA5_exact_interval_boundaries_proven_equal"])
        self.assertFalse(receipt["bias_or_model_skill_admitted"])
        self.assertFalse(receipt["wind_vulnerability_or_insured_loss_calibrated"])
        self.assertEqual([x["station_id"] for x in receipt["station_results"]],list(m.STATIONS))
        self.assertEqual(receipt["station_results"][0]["lag_zero"]["paired_hour_count"],96)

    def test_live_cli_prints_status_only_not_source_derived_metrics(self):
        sink=StringIO()
        with patch.object(m,"live_report",return_value={"station_id":"private-row","gust":123.4}), \
             patch("sys.argv",["runner.py","--live-event"]), redirect_stdout(sink):
            self.assertEqual(m.main(),0)
        output=sink.getvalue()
        self.assertIn("LIVE_SOURCE_COMPARISON_COMPLETED",output)
        self.assertNotIn("private-row",output)
        self.assertNotIn("123.4",output)

    def test_exact_constant_difference_and_all_lags_reported(self):
        obs,mod,att=synthetic_inputs()
        result=m.matched_hour_report(obs,mod,att)
        self.assertEqual(result["unique_ERA5_grid_nodes"],2)
        self.assertFalse(result["DWD_and_ERA5_exact_interval_boundaries_proven_equal"])
        self.assertFalse(result["bias_or_model_skill_admitted"])
        self.assertFalse(result["raw_hourly_source_values_in_receipt"])
        by_station={x["DWD_station_id"]:x for x in result["stations_results"]}
        center=by_station["02667"]["lag_sensitivity_all_offsets_reported_no_best_lag_selected"]["0"]["metrics"]
        self.assertEqual(center["paired_hour_count"],96)
        self.assertAlmostEqual(center["mean_error_era5_minus_dwd_mps"],1.0)
        self.assertAlmostEqual(center["mean_absolute_error_mps"],1.0)
        self.assertAlmostEqual(center["root_mean_square_error_mps"],1.0)
        self.assertAlmostEqual(center["pearson_correlation"],1.0)
        self.assertEqual(by_station["02667"]["lag_sensitivity_all_offsets_reported_no_best_lag_selected"]["-1"]["metrics"]["paired_hour_count"],95)
        self.assertEqual(by_station["02667"]["lag_sensitivity_all_offsets_reported_no_best_lag_selected"]["1"]["metrics"]["paired_hour_count"],95)

    def test_missing_hour_malformed_values_wrong_grid_or_missing_attestation_rejected(self):
        obs,mod,att=synthetic_inputs()
        del obs["02667"]["2020020800"]
        with self.assertRaises(m.MatchedHourBlocked):
            m.matched_hour_report(obs,mod,att)
        obs,mod,att=synthetic_inputs()
        mod["15200"][3]=float("nan")
        with self.assertRaises(m.MatchedHourBlocked):
            m.matched_hour_report(obs,mod,att)
        obs,mod,att=synthetic_inputs()
        att["stations"][0]["nearest_2020_ERA5_grid_lon"]=7.0
        with self.assertRaises(m.MatchedHourBlocked):
            m.matched_hour_report(obs,mod,att)
        obs,mod,att=synthetic_inputs()
        att["DWD_FX911_and_ERA5_10fg_exact_gust_aggregation_same"]=True
        with self.assertRaises(m.MatchedHourBlocked):
            m.matched_hour_report(obs,mod,att)


if __name__=="__main__":
    unittest.main()
