# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-bound Ciara event QA, never a model validation."""
from __future__ import annotations
import gzip
import json
import unittest
from unittest.mock import patch

from research_runners import meteofrance_four_north_original_v0 as fr
from research_runners.meteofrance_ciara2020_four_original_window_v0 import (
    Blocked, event_envelope, _peak_band
)

HEADER = "NUM_POSTE;AAAAMMJJHH;FF;FXI;FXI3S;QFXI3S;STATUS_FXI3S;LAT\n"
STATION = "02010001"
ROWS = (
    "02010001;2020020900;4;15;19.4;1;0;49.0\n"
    "02010001;2020020915;6;30;31.2;1;1;49.0\n"
    "02010001;2020021023;5;34;35.5;9;0;49.0\n"
    "02010001;2020021123;7;20;22.1;1;0;49.0\n"
    "02010001;2020021200;6;32;55.1;1;0;49.0\n"
)


def data(rows: str = ROWS) -> bytes:
    return gzip.compress((HEADER + rows).encode("utf-8"), mtime=0)


def run(rows: str = ROWS) -> dict:
    original = data(rows)
    patched = {"02": (fr.ASSETS["02"][0], len(original), None)}
    with patch.object(fr, "ASSETS", patched):
        return event_envelope("02", original)


class TestCiaraOriginalEnvelope(unittest.TestCase):
    def test_hour_window_exact_and_transfer_quality(self):
        a=run()
        self.assertEqual(a["nominal_hours"], 72)
        self.assertEqual(a["station_hour_rows_in_window"], 4)
        self.assertEqual(a["stations_with_any_hour"], 1)
        self.assertEqual(a["quality_checked_three_second_gusts"], 3)
        self.assertEqual(a["transfer_derived_valid_gusts"], 1)
        self.assertEqual(a["not_transfer_derived_valid_gusts"], 2)
        self.assertEqual(a["quality_checked_gust_peak_mps"], 31.2)
        self.assertEqual(a["station_quality_checked_peak_bins"], {"30_to_below_40_mps":1})
        self.assertEqual(sum(a["station_quality_checked_peak_bins"].values()),
                         a["quality_checked_hourly_station_count"])
        self.assertEqual(sum(a["quality_counts_all_window_rows"].values()),
                         a["station_hour_rows_in_window"])
        self.assertEqual(a["stations_with_full_72_hour_labels"], 0)
        self.assertFalse(a["hazard_calibration_authorized"])
        self.assertFalse(a["annual_ep_authorized"])
        self.assertNotIn(STATION, json.dumps(a))

    def test_duplicate_hour_rejected(self):
        row="02010001;2020020900;4;15;19.4;1;0;49.0\n"
        with self.assertRaisesRegex(Blocked, "duplicate"):
            run(ROWS + row)

    def test_bad_hour_and_wind_in_the_entire_original_blocks(self):
        for bad in ("2020023023", "2020020924"):
            with self.subTest(hour=bad), self.assertRaises(Blocked):
                run(ROWS.replace("2020020900",bad))
        with self.assertRaises(Blocked):
            run(ROWS.replace(";19.4;", ";nan;"))

    def test_empty_event_window_blocks(self):
        outside="02010001;2020030900;4;15;19.4;1;0;49.0\n"
        with self.assertRaisesRegex(Blocked, "no valid Ciara"):
            run(outside)

    def test_qc9_excluded_and_event_end_exclusive(self):
        r=run()
        self.assertEqual(r["quality_counts_all_window_rows"]["9"],1)
        self.assertNotEqual(r["quality_checked_gust_peak_mps"],55.1)
        self.assertNotEqual(r["quality_checked_gust_peak_mps"],35.5)

    def test_peak_bins_no_location(self):
        self.assertEqual(_peak_band(19.99),"below_20_mps")
        self.assertEqual(_peak_band(20),"20_to_below_30_mps")
        self.assertEqual(_peak_band(30),"30_to_below_40_mps")
        self.assertEqual(_peak_band(40),"40_mps_or_more")

    def test_coverage_station_full_labels(self):
        rows="".join(f"02010001;202002{day:02d}{hour:02d};4;15;22.0;1;0;49.0\n"
                     for day in (9,10,11) for hour in range(24))
        a=run(rows)
        self.assertEqual(a["station_hour_rows_in_window"],72)
        self.assertEqual(a["stations_with_full_72_hour_labels"],1)
        self.assertEqual(a["quality_checked_full_72_hour_stations"],1)
        self.assertEqual(a["quality_checked_three_second_gusts"],72)

    def test_exact_asset_sha_required(self):
        original=data()
        patched={"02": (fr.ASSETS["02"][0],len(original),"0"*64)}
        with patch.object(fr,"ASSETS",patched):
            with self.assertRaisesRegex(Blocked,"SHA-256"):
                event_envelope("02",original)


if __name__=="__main__":
    unittest.main()
