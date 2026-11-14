# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import climk_era5_dwd_50event_station_audit_v0 as m


def windows_fixture():
    result=[]
    for i in range(50):
        count=72 if i<25 else 48
        qn=3 if i<20 else 1
        result.append({
            "dwd_hourly_gust_qn":[[20.0+i,qn] for _ in range(count)],
            "dwd_storm_date_gust_qn":[[20.0+i,qn] for _ in range(24 if i<30 else 16)],
            "climk_per_storm_gust_mps":22.0+i,
            "era5_grid_node":[50.75,7.25],
            "sensor_height_m":10.0 if i<30 else 12.0,
            "station_elevation_m":100.0,
            "historical_metadata_verified":i<40,
        })
    return result


class ClimkEra5DWDTop50AuditTests(unittest.TestCase):
    def test_source_population_includes_third_dwd_station(self):
        self.assertEqual(m.STATIONS,("02667","00603","15200"))

    def test_partial_windows_excluded_and_qn3_subset_separate(self):
        result=m.summarize_windows(windows_fixture())
        self.assertIn("daily maximum wind gust derived from hourly gust data",m.CLIMK_PARAMETER_DESCRIPTION)
        self.assertEqual(result["CLIMK_top50_rows"],50)
        self.assertEqual(result["station_windows_with_any_valid_DWD_hours_and_unmasked_model_value"],50)
        self.assertEqual(result["station_windows_with_complete_72h_DWD"],25)
        self.assertEqual(result["station_windows_with_complete_72h_DWD_QN8_3"],20)
        self.assertEqual(result["station_storm_dates_with_complete_24h_DWD"],30)
        self.assertEqual(result["station_storm_dates_with_complete_24h_DWD_QN8_3"],20)
        self.assertGreater(result["station_storm_dates_with_complete_24h_DWD"],
                           result["station_windows_with_complete_72h_DWD"])
        self.assertEqual(result["station_windows_with_partial_DWD_hours"],25)
        self.assertEqual(result["event_windows_with_verified_historical_site_instrument_and_UTC_semantics"],40)
        self.assertEqual(result["unique_nearest_CLIMK_ERA5_grid_nodes"],1)
        self.assertEqual(result["historical_sensor_height_counts_m_for_windows_with_observations"],
                         {"10.0":30,"12.0":20})
        self.assertEqual(result["historical_station_elevation_counts_m_above_sea_level_for_windows_with_observations"],
                         {"100.0":50})
        daily=result["complete_storm_date_24h_unmatched_support_contrasts_descriptive_only"]
        self.assertEqual(daily["paired_values"],30)
        self.assertAlmostEqual(daily["mean_pairwise_difference_CLIMK_minus_DWD_mps"],2.0)
        self.assertAlmostEqual(daily["root_mean_square_pairwise_difference_mps"],2.0)
        self.assertIn("not error, bias, or skill",daily["interpretation"])
        daily_qn3=result["complete_storm_date_24h_QN8_3_unmatched_support_contrasts_descriptive_only"]
        self.assertEqual(daily_qn3["paired_values"],20)
        self.assertFalse(result["partial_DWD_windows_imputed_or_used_in_primary_metrics"])
        self.assertFalse(result["sensor_height_adjustment_applied"])

    def test_missing_events_invalid_gust_qn_and_grid_node_fail_closed(self):
        with self.assertRaises(m.CLIMKDWDBlocked):
            m.summarize_windows(windows_fixture()[:-1])
        bad=windows_fixture();bad[0]["dwd_hourly_gust_qn"][0]=[-1.0,3]
        with self.assertRaises(m.CLIMKDWDBlocked):
            m.summarize_windows(bad)
        bad=windows_fixture();bad[0]["dwd_hourly_gust_qn"][0]=[30.0,11]
        with self.assertRaises(m.CLIMKDWDBlocked):
            m.summarize_windows(bad)
        bad=windows_fixture();bad[0]["era5_grid_node"]=[50.75]
        with self.assertRaises(m.CLIMKDWDBlocked):
            m.summarize_windows(bad)

    def test_original_csv_parser_preserves_only_bounded_valid_hour_values(self):
        b=BytesIO()
        with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("produkt_fx_stunde_test.txt",
                       "STATIONS_ID;MESS_DATUM;QN_8;FX_911;eor\n"
                       "2667;2007011700;3;24.5;eor\n"
                       "2667;2007011701;1;-999;eor\n")
        parsed=m._parse_original_hourly(b.getvalue(),"02667")
        self.assertEqual(parsed,{"2007011700":(24.5,3)})
        for source,sid in ((b.getvalue(),"00603"),):
            with self.assertRaises(m.CLIMKDWDBlocked):
                m._parse_original_hourly(source,sid)

    def test_live_cli_prints_only_status(self):
        sink=StringIO()
        with patch.object(m,"live_analysis",return_value={"DWD_station_id":"private-row","gust":99.0}), \
             patch("sys.argv",["runner.py","--live-original-sources"]),redirect_stdout(sink):
            self.assertEqual(m.main(),0)
        self.assertIn("LIVE_SOURCE_AUDIT_COMPLETED",sink.getvalue())
        self.assertNotIn("private-row",sink.getvalue())
        self.assertNotIn("99.0",sink.getvalue())

    def test_live_cli_writes_aggregate_only_receipt_exclusively(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/"receipt.json"
            with patch.object(m,"live_analysis",return_value={"aggregate":True}), \
                 patch("sys.argv",["runner.py","--live-original-sources","--output",str(target)]), \
                 redirect_stdout(StringIO()):
                self.assertEqual(m.main(),0)
            self.assertEqual(target.read_text(encoding="utf-8"),'{\n  "aggregate": true\n}\n')
            with patch.object(m,"live_analysis",return_value={"aggregate":False}), \
                 patch("sys.argv",["runner.py","--live-original-sources","--output",str(target)]), \
                 redirect_stdout(StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    m.main()
            self.assertEqual(raised.exception.code,2)
            self.assertIn('"aggregate": true',target.read_text(encoding="utf-8"))


if __name__=="__main__":
    unittest.main()
