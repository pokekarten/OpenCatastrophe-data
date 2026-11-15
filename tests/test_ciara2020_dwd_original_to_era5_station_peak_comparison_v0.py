# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline adversarial 3 genuinely source-pinned DWD to 2 ERA5 grid cells."""
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
import ciara2020_dwd_original_to_era5_station_peak_comparison_v0 as m
import ciara2020_google_arco_real_96h_nrw_area_v0 as g
import ciara2020_dwd_hourly_fx_original_station_observations_v0 as d


def original_dwd_fixture():
    with d.FROZEN_FIRST_REAL_DWD_SOURCE.open("rb") as f:
        source=tomllib.load(f)
    records=[]
    for s in source["stations"]:
        records.append({
            "station_id":s["station_id"],
            "name_as_publisher_lists_today":s["name"],
            "latitude_as_publisher_lists_today":s["current_publisher_latitude"],
            "longitude_as_publisher_lists_today":s["current_publisher_longitude"],
            "distance_to_original_era5_51N_7E_km":s["distance_to_51N_7E_km"],
            "original_DWD_historical_FX_zip_url":s["original_archive_url"],
            "provider_original_zip_sha256":s["original_unmodified_zip_sha256"],
            "measured_2020_Ciara_window_peak_hour_as_publisher_reports":
                s["published_2020_peak_hour_label"],
            "measured_2020_02_08_through_11_max_hourly_gust_mps":
                s["observed_2020_96h_peak_gust_mps"],
            "original_station_fx911_hourly_valid_count":s["valid_2020_hour_count"],
            "original_station_fx911_missing_marker_count":s["missing_original_value_count"],
            "DWD_QN8_quality_level_hour_counts":{"3":96},
            "observed_station_max_gust_hours_full_96h":True,
        })
    return {
        "status":source["status"], "source_variable":"FX_911", "units":"m/s",
        "station_count":3,
        "historic_reference_time_interpretation_verified_as_UTC":False,
        "station_coordinates_reported_are_current_not_verified_historic_2020":True,
        "actual_2020_insurer_losses_or_building_vulnerability_calibrated":False,
        "native_NextGen_Oasis_GUL_IL_RI_OEP_AEP_admitted":False,
        "historical_station_archive_candidates_checked":4,
        "skipped_original_archives_due_to_insufficient_2020_gust_coverage":[{
            "original_station_id":source["rejected_station_id"],
            "original_station_zip_sha256":source["rejected_original_zip_sha256"],
        }],
        "stations":records,
    }


def original_grid_fixture():
    peaks=[[30.0 for _ in g.LONGITUDE] for _ in g.LATITUDE]
    peaks[7][6]=29.25  # Koeln/Bonn + Koenigswinter -> one actual quarter-degree cell
    peaks[5][6]=33.0   # Wuppertal -> separate original quarter-degree cell
    return {
        "normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256":
            m.ERA5_DECODED_96H_160_SHA,
        "actual_hourly_ERA5_original_grid_timestamps_verified":96,
        "original_source_0p25_degree_nodes":160,
        "previous_original_metadata_SHA256s_match":True,
        "real_RV_insurer_claims_or_policy_terms_obtained":False,
        "German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted":False,
        "public_original_source":
            "gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3",
        "_internal_public_10x16_event_peak_gust_mps":peaks,
    }


class DWDOriginalStationsToERA5TwoGridCells(unittest.TestCase):
    def test_exact_source_station_grid_centres_and_two_not_three_cells(self):
        current=[
            (50.8645,7.1575,50.75,7.25),
            (51.2531,7.2157,51.25,7.25),
            (50.7293,7.204,50.75,7.25),
        ]
        for lat,lon,wlat,wlon in current:
            with self.subTest(lat=lat,lon=lon):
                row,col,dist=m.station_to_grid(lat,lon)
                self.assertEqual((g.LATITUDE[row],g.LONGITUDE[col]),(wlat,wlon))
                self.assertGreater(dist,0)
                self.assertLess(dist,20)

    def test_historical_measurements_join_as_descriptive_event_max_only(self):
        dwd=original_dwd_fixture()
        weather=original_grid_fixture()
        joined=m.combine_original_2020_station_and_grid_peaks(dwd,weather)
        self.assertEqual(joined["source_verified_dwd_stations"],3)
        self.assertEqual(joined["source_verified_unique_nearest_era5_grid_cells"],2)
        self.assertEqual(joined["total_original_DWD_FX911_observed_hours"],288)
        three=joined["station_to_original_ERA5_peak_only"]
        self.assertEqual([x["dwd_measured_original_2020_96h_peak_FX911_mps"] for x in three],
                         [26.4,31.1,25.5])
        self.assertEqual([x["google_era5_modelled_original_2020_96h_peak_10fg_mps"]
                          for x in three],[29.25,33.0,29.25])
        self.assertEqual([x["descriptive_peak_difference_era5_minus_dwd_mps_not_bias_or_skill"]
                          for x in three],[2.85,1.9,3.75])
        self.assertEqual(three[0]["nearest_era5_grid_lat"],three[2]["nearest_era5_grid_lat"])
        for claim in (
            "DWD_2020_station_historic_instrument_and_geography_verified",
            "DWD_2020_hour_label_UTC_and_gust_window_aligned_with_ERA5",
            "matched_hour_errors_RMSE_or_model_skill_admitted",
            "2020_actual_RV_insured_sites_or_claims_observed",
            "German_wind_damage_vulnerability_native_GUL_IL_RI_OEP_AEP_admitted",
            "annual_event_frequency_or_capital_model_admitted",
        ):
            self.assertFalse(joined[claim])

    def test_spatial_midpoint_far_station_infinite_and_wrong_type_block(self):
        for lat,lon in (
            (50.875,7.0), # 0.25 midpoint tie latitude
            (51.0,7.125), # midpoint tie longitude
            (50.0,7.0), # out of 10x16 support
            (51.0,9.9),
            (float("nan"),7.0),
            (51.0,float("inf")),
            (True,7.0),
            ("51.0",7.0),
        ):
            with self.subTest(lat=lat,lon=lon):
                with self.assertRaises(m.DWDGridComparisonBlocked):
                    m.station_to_grid(lat,lon)

    def test_source_dwd_original_zip_sha_quality_and_false_loss_block(self):
        x=original_dwd_fixture()
        weather=original_grid_fixture()
        for field,value in (
            ("provider_original_zip_sha256","0"*64),
            ("original_station_fx911_hourly_valid_count",95),
            ("DWD_QN8_quality_level_hour_counts",{"10":96}),
            ("station_id","99999"),
            ("measured_2020_02_08_through_11_max_hourly_gust_mps",80.0),
        ):
            with self.subTest(field=field):
                bad=deepcopy(x)
                bad["stations"][1][field]=value
                with self.assertRaises((m.DWDGridComparisonBlocked,d.OriginalDWDRejected)):
                    m.combine_original_2020_station_and_grid_peaks(bad,weather)
        bad=deepcopy(x)
        bad["actual_2020_insurer_losses_or_building_vulnerability_calibrated"]=True
        with self.assertRaises((m.DWDGridComparisonBlocked,d.OriginalDWDRejected)):
            m.combine_original_2020_station_and_grid_peaks(bad,weather)

    def test_source_era5_original_sha_and_grid_values_are_required(self):
        dwd=original_dwd_fixture()
        for edit in (
            {"normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256":"0"*64},
            {"previous_original_metadata_SHA256s_match":False},
            {"actual_hourly_ERA5_original_grid_timestamps_verified":95},
            {"German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted":True},
            {"_internal_public_10x16_event_peak_gust_mps":None},
            {"_internal_public_10x16_event_peak_gust_mps":[[30.]*16]*9},
        ):
            with self.subTest(edit=list(edit.keys())):
                weather={**original_grid_fixture(),**edit}
                with self.assertRaises(m.DWDGridComparisonBlocked):
                    m.combine_original_2020_station_and_grid_peaks(dwd,weather)
        weather=original_grid_fixture()
        weather["_internal_public_10x16_event_peak_gust_mps"][7][6]=float("nan")
        with self.assertRaises(m.DWDGridComparisonBlocked):
            m.combine_original_2020_station_and_grid_peaks(dwd,weather)

    def test_first_actual_dwd_measured_vs_two_google_source_peaks_are_immutable(self):
        with m.FIRST_ACTUAL_SOURCE_COMPARISON.open("rb") as f:
            first=tomllib.load(f)
        self.assertEqual(first["first_genuine_source_comparison_github_run"],43603655228)
        self.assertEqual(first["source_genuine_distinct_ERA5_025degree_nodes"],2)
        self.assertEqual([x["station_id"] for x in first["stations"]],["02667","15200","00603"])
        self.assertEqual([x["DWD_observed_2020_event_peak_FX911_mps"]
                          for x in first["stations"]],[26.4,31.1,25.5])
        self.assertEqual([x["descriptive_ERA5_minus_DWD_peak_difference_mps_not_model_bias"]
                          for x in first["stations"]],[4.769416,1.037897,5.669416])
        self.assertFalse(first["ERA5_bias_RMSE_skill_model_approved"])
        self.assertFalse(first["actual_2020_real_RV_insurer_sites_claims_observed"])
        weather=original_grid_fixture()
        weather["_internal_public_10x16_event_peak_gust_mps"][7][6]=31.169416427612305
        weather["_internal_public_10x16_event_peak_gust_mps"][5][6]=32.13789749145508
        joined=m.combine_original_2020_station_and_grid_peaks(original_dwd_fixture(),weather)
        self.assertIsNone(m.verify_first_original_station_era5_comparison_receipt(joined))
        for field,value in (
            ("google_era5_modelled_original_2020_96h_peak_10fg_mps",29.25),
            ("dwd_original_zip_sha256","0"*64),
            ("nearest_era5_grid_lat",51.0),
            ("descriptive_peak_difference_era5_minus_dwd_mps_not_bias_or_skill",88.0),
        ):
            with self.subTest(field=field):
                bad=deepcopy(joined)
                bad["station_to_original_ERA5_peak_only"][0][field]=value
                with self.assertRaises(m.DWDGridComparisonBlocked):
                    m.verify_first_original_station_era5_comparison_receipt(bad)
        bad=deepcopy(joined)
        bad["matched_hour_errors_RMSE_or_model_skill_admitted"]=True
        with self.assertRaises(m.DWDGridComparisonBlocked):
            m.verify_first_original_station_era5_comparison_receipt(bad)

    def test_source_dry_run_without_call_to_era5_or_dwd(self):
        with patch.object(sys,"argv",["comp","--dry-run"]),\
             patch.object(m,"live_original_comparison",side_effect=AssertionError("NO NETWORK")):
            buffer=StringIO()
            with redirect_stdout(buffer):
                self.assertEqual(m.main(),0)
        report=json.loads(buffer.getvalue())
        self.assertFalse(report["2020_original_sources_reloaded"])
        self.assertFalse(report["skill_or_insurer_damage_admitted"])
        self.assertEqual(report["ERA5_actual_distinct_gridpoint_count_expected"],2)


if __name__=="__main__":
    unittest.main()
