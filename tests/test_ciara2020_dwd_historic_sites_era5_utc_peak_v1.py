# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned original Feb2020 DWD historic geography vs ERA5 event peak."""
from __future__ import annotations
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import sys
import tomllib
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import ciara2020_dwd_historic_sites_era5_utc_peak_v1 as m
from tests.test_ciara2020_dwd_original_to_era5_station_peak_comparison_v0 import (
    original_dwd_fixture, original_grid_fixture,
)


def actual_historical_fixture():
    with m.ORIGINAL_DWD_HISTORIC_RECEIPT.open("rb") as f:
        source=tomllib.load(f)
    records=[]
    for s in source["stations"]:
        records.append({
            "station_id":s["station_id"],
            "original_DWD_station_latitude_as_of_Feb2020":s["feb2020_latitude"],
            "original_DWD_station_longitude_as_of_Feb2020":s["feb2020_longitude"],
            "original_DWD_station_elevation_m_as_of_Feb2020":s["feb2020_station_elevation_m"],
            "original_FX911_anemometer_height_above_ground_m_as_of_Feb2020":
                s["feb2020_wind_anemometer_height_above_ground_m"],
            "original_FX911_instrument_type_as_of_Feb2020":s["feb2020_instrument_type"],
            "original_FX911_procedure_as_of_Feb2020":s["feb2020_measurement_procedure"],
            "original_DWD_FX911_hour_label_declared_UTC":True,
            "original_DWD_FX911_gust_highest_during_previous_hour":True,
            "DWD_FX911_exact_same_postprocess_window_as_ERA5_10fg_verified":False,
            "nearest_2020_ERA5_grid_lat":s["2020_original_era5_comparison_grid_lat"],
            "nearest_2020_ERA5_grid_lon":s["2020_original_era5_comparison_grid_lon"],
            "historical_station_to_ERA5_grid_centre_km":
                s["nearest_original_era5_grid_distance_km"],
            "DWD_original_zip_sha256":s["original_zip_sha256"],
            "original_geo_interval_from":s["feb2020_geo_valid_from"],
            "original_instrument_interval_from":s["feb2020_device_valid_from"],
            "original_parameter_interval_from":s["feb2020_parameter_valid_from"],
            "historical_member_sha256":{
                "geographie":s["geo_member_sha256"],
                "geraete":s["device_member_sha256"],
                "parameter":s["parameter_member_sha256"],
            },
        })
    return {
        "schema":m.historic.SCHEMA,
        "station_count":3,
        "DWD_original_site_geography_Feb2020_verified":True,
        "DWD_original_sensor_height_type_Feb2020_verified":True,
        "DWD_original_FX911_hour_reference_declared_UTC":True,
        "DWD_FX911_and_ERA5_10fg_exact_gust_aggregation_same":False,
        "ERA5_station_matched_hour_bias_or_RMSE_approved":False,
        "insurer_real_2020_loss_vulnerability_GUL_IL_RI_OEP_AEP_admitted":False,
        "stations":records,
    }


def accepted_real_peak_grid():
    w=original_grid_fixture()
    w["_internal_public_10x16_event_peak_gust_mps"][7][6]=31.169416427612305
    w["_internal_public_10x16_event_peak_gust_mps"][5][6]=32.13789749145508
    return w


class Historical2020SiteCorrectedGustResearch(unittest.TestCase):
    def test_first_real_2020_station_source_record_and_no_damage(self):
        with m.ORIGINAL_DWD_HISTORIC_RECEIPT.open("rb") as f:
            accepted=tomllib.load(f)
        self.assertEqual([r["station_id"] for r in accepted["stations"]],list(m.EXPECTED))
        self.assertEqual([r["feb2020_wind_anemometer_height_above_ground_m"]
                          for r in accepted["stations"]],[10,12,10])
        self.assertEqual(accepted["stations"][2]["feb2020_latitude"],50.735)
        self.assertEqual(accepted["stations"][2]["feb2020_longitude"],7.1931)
        self.assertEqual(accepted["stations"][2]["after_event_station_move_effective"],"20201001")
        self.assertTrue(accepted["source_original_DWD_FX911_UTC_reference_hour_label_attested"])
        self.assertFalse(accepted["native_catastrophe_GUL_IL_RI_OEP_AEP_or_SCR_admitted"])

    def test_historic_corrected_three_station_two_grid_source_peak_is_descriptive_only(self):
        result=m.research_historical_site_grid_crosswalk(
            original_dwd_fixture(),accepted_real_peak_grid(),actual_historical_fixture()
        )
        self.assertEqual(result["actual_source_verified_2020_DWD_station_count"],3)
        self.assertEqual(result["actual_source_verified_2020_ERA5_unique_grid_cells"],2)
        self.assertEqual(result["original_source_historical_site_member_SHAs_checked"],9)
        self.assertTrue(result["nominal_UTC_hour_ending_support_for_DWD_and_ERA5_documented"])
        self.assertTrue(result["2020_station_site_and_instrument_verified"])
        self.assertFalse(result["same_UTC_hour_wind_pairs_retrieved"])
        self.assertFalse(result["same_hour_gust_sampling_methods_ERA5_DWD_physically_equivalent"])
        for key in ("independent_ERA5_station_gridpoint_skill_RMSE_bias_approved",
                    "observed_RV_insured_2020_site_or_claims",
                    "German_wind_damage_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted",
                    "annual_stochastic_EP_or_SCR_admitted"):
            self.assertFalse(result[key])
        r=result["historically_correct_stations"]
        self.assertEqual([x["actual_2020_wind_anemometer_height_m"] for x in r],[10,12,10])
        self.assertEqual([x["2020_historic_sensor_to_model_grid_distance_km"] for x in r],
                         [14.295,2.412,4.337])
        self.assertEqual([x["prior_current_station_site_to_grid_distance_km"] for x in r],
                         [14.295,2.412,3.972])
        self.assertEqual([x["Google_ERA5_2020_96h_event_peak_mps"] for x in r],
                         [31.169416427612305,32.13789749145508,31.169416427612305])
        self.assertEqual([x["descriptive_event_peak_ERA5_minus_DWD_mps_NOT_BIAS"] for x in r],
                         [4.769416,1.037897,5.669416])
        self.assertEqual(r[0]["DWD_reported_peak_hour_label_in_UTC"],"2020-02-10T08:00:00Z")
        self.assertEqual(r[0]["DWD_peak_gust_previous_hour_start_UTC"],"2020-02-10T07:00:00Z")
        self.assertEqual(r[0]["DWD_peak_gust_previous_hour_end_UTC"],"2020-02-10T08:00:00Z")
        self.assertNotEqual(r[2]["actual_2020_DWD_station_latitude"],
                            50.7293)

    def test_original_source_site_or_sensor_tampering_cannot_be_forged(self):
        for field,value in (
            ("original_DWD_station_latitude_as_of_Feb2020",50.7293),
            ("original_DWD_station_longitude_as_of_Feb2020",7.204),
            ("original_FX911_anemometer_height_above_ground_m_as_of_Feb2020",12),
            ("historical_station_to_ERA5_grid_centre_km",3.972),
            ("original_DWD_FX911_hour_label_declared_UTC",False),
            ("DWD_FX911_exact_same_postprocess_window_as_ERA5_10fg_verified",True),
            ("DWD_original_zip_sha256","0"*64),
        ):
            with self.subTest(field=field):
                old=actual_historical_fixture()
                old["stations"][2][field]=value
                with self.assertRaises(m.HistoricSiteGridBlocked):
                    m.research_historical_site_grid_crosswalk(
                        original_dwd_fixture(),accepted_real_peak_grid(),old
                    )
        old=actual_historical_fixture()
        old["stations"][2]["historical_member_sha256"]["geographie"]="0"*64
        with self.assertRaises(m.HistoricSiteGridBlocked):
            m.research_historical_site_grid_crosswalk(original_dwd_fixture(),accepted_real_peak_grid(),old)

    def test_false_historical_source_and_loss_admission_rejected(self):
        for flag,value in (
            ("DWD_original_site_geography_Feb2020_verified",False),
            ("DWD_original_FX911_hour_reference_declared_UTC",False),
            ("DWD_FX911_and_ERA5_10fg_exact_gust_aggregation_same",True),
            ("ERA5_station_matched_hour_bias_or_RMSE_approved",True),
            ("insurer_real_2020_loss_vulnerability_GUL_IL_RI_OEP_AEP_admitted",True),
        ):
            with self.subTest(flag=flag):
                old=actual_historical_fixture()
                old[flag]=value
                with self.assertRaises(m.HistoricSiteGridBlocked):
                    m.research_historical_site_grid_crosswalk(original_dwd_fixture(),accepted_real_peak_grid(),old)

    def test_dwd_utc_hour_label_and_calendar_bounds(self):
        self.assertEqual(m._peak_utc_hour("2020020922"),
                         ("2020-02-09T22:00:00Z","2020-02-09T21:00:00Z","2020-02-09T22:00:00Z"))
        for label in ("2020021124","2020020623","2020021200","2020022900","202002091",
                      "20200209x2",""):
            with self.subTest(label=label):
                with self.assertRaises(m.HistoricSiteGridBlocked):
                    m._peak_utc_hour(label)

    def test_no_network_dry_run_does_not_claim_actual_historic_join(self):
        with patch.object(sys,"argv",["hist","--dry-run"]),\
             patch.object(m,"live_original_historical_site_peak_replay",side_effect=AssertionError("NO NETWORK")):
            out=StringIO()
            with redirect_stdout(out):
                self.assertEqual(m.main(),0)
        receipt=json.loads(out.getvalue())
        self.assertFalse(receipt["2020_original_DWD_ERA5_source_data_fetched"])
        self.assertFalse(receipt["2020_historic_sensor_site_replayed"])
        self.assertFalse(receipt["loss_model_approved"])


if __name__=="__main__":
    unittest.main()
