# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only security/science tests for independent DWD station 00348."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from scripts.probe_dwd_station00348_original_v0 import (
    WIND_FILE, METADATA_FILE, SecondStationBlocked, inspect, _wind_stats,
    _geography_stats, _snapshot, STATION_GEO,
)
from datetime import date

WIND_HEADER = "STATIONS_ID;MESS_DATUM;QN;FX_10;FNX_10;FMX_10;DX_10;eor\r\n"
WIND_ROWS = [
    "348;201001010000;3;14.4;1.0;3.0;200;eor\r\n",
    "348;201001010010;2;-999;1.0;3.0;200;eor\r\n",
    "348;201001010030;3;21.8;1.0;3.0;200;eor\r\n",
]
GEOGRAPHY_HEADER = (
    "Stations_id;Stationshoehe;Geogr.Breite;Geogr.Laenge;"
    "von_datum;bis_datum;Stationsname\r\n"
)
GEOGRAPHY_ROW = "348;300;48.0;10.0;19990101;20191231;SECRET_PLACE\r\n"


def fixture(folder: Path, *, wind_rows=None, geo_rows=None, member=None):
    wind_file = folder / WIND_FILE
    meta_file = folder / METADATA_FILE
    with ZipFile(wind_file, "w", ZIP_DEFLATED) as z:
        z.writestr("produkt_extrema_wind_00348_20100101_20110901.txt",
                   WIND_HEADER + "".join(WIND_ROWS if wind_rows is None else wind_rows))
        if member is not None:
            z.writestr(member, b"other")
    with ZipFile(meta_file, "w", ZIP_DEFLATED) as z:
        z.writestr(STATION_GEO, GEOGRAPHY_HEADER +
                   (GEOGRAPHY_ROW if geo_rows is None else "".join(geo_rows)))
        z.writestr("Metadaten_Geraete_Windgeschwindigkeit_Maxwind_00348.txt",
                   "Synthetic fake equipment")
        z.writestr("Metadaten_Parameter_00348.txt",
                   "Synthetic fake parameter")
    return wind_file, meta_file


class SecondStationOriginalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_two_original_zip_source_receipts_and_geography(self):
        w, m = fixture(self.root)
        r = inspect(w, m)
        self.assertEqual(r["station_id"], "00348")
        self.assertTrue(r["first_station_00003_independent"])
        self.assertEqual(r["measurement"]["observation_rows"], 3)
        self.assertEqual(r["measurement"]["fx_10_missing_sentinel_rows"], 1)
        self.assertEqual(r["measurement"]["fx_10_max_mps"], "21.8")
        self.assertEqual(r["measurement"]["missing_10minute_slots_between_first_and_last"], 1)
        self.assertEqual(r["geography"]["provisional_inclusive_unique_geography_days"], 1)
        self.assertEqual(r["geography"]["provisional_inclusive_missing_geography_days"], 0)
        self.assertEqual(r["measurement"]["quality_level_distribution"], {"2": 1, "3": 2})
        self.assertFalse(r["model_input_approved"])
        self.assertFalse(r["external_original_bytes_persisted"])
        self.assertNotIn("SECRET_PLACE", str(r))

    def test_source_digest_can_be_pinned_independently(self):
        w, m = fixture(self.root)
        report = inspect(w, m, expected_wind_sha256=hashlib.sha256(w.read_bytes()).hexdigest(),
                         expected_metadata_sha256=hashlib.sha256(m.read_bytes()).hexdigest())
        self.assertEqual(len(report["wind_original_sha256"]), 64)
        with self.assertRaises(SecondStationBlocked):
            inspect(w, m, expected_wind_sha256="0" * 64)
        with self.assertRaises(SecondStationBlocked):
            inspect(w, m, expected_metadata_sha256="0" * 64)

    def test_symlinks_and_wrong_original_names_rejected(self):
        w, m = fixture(self.root)
        alias = self.root / "alias.zip"
        alias.symlink_to(w)
        with self.assertRaises(SecondStationBlocked):
            _snapshot(alias, WIND_FILE, 1024 * 1024)
        renamed = self.root / "changed.zip"
        renamed.write_bytes(w.read_bytes())
        with self.assertRaises(SecondStationBlocked):
            inspect(renamed, m)

    def test_untrusted_zip_traversal_member_blocked(self):
        w, m = fixture(self.root, member="../../outside")
        with self.assertRaises(SecondStationBlocked):
            inspect(w, m)

    def test_other_station_in_data_blocked(self):
        rows = [WIND_ROWS[0].replace("348;", "349;"), *WIND_ROWS[1:]]
        w, m = fixture(self.root, wind_rows=rows)
        with self.assertRaises(SecondStationBlocked):
            inspect(w, m)

    def test_duplicate_and_non_ten_minute_timestamp_blocked(self):
        for rows in (
            [WIND_ROWS[0], WIND_ROWS[0]],
            [WIND_ROWS[0], WIND_ROWS[1].replace("0010", "0015")],
            [WIND_ROWS[0], WIND_ROWS[1].replace("20100101", "20130101")],
        ):
            with self.subTest(rows=rows):
                w, m = fixture(self.root, wind_rows=rows)
                with self.assertRaises(SecondStationBlocked):
                    inspect(w, m)

    def test_nonmissing_negative_or_nonfinite_wind_blocked(self):
        for gust in ("-12", "NaN", "Infinity"):
            with self.subTest(gust=gust):
                rows = [WIND_ROWS[0].replace("14.4", gust)]
                w, m = fixture(self.root, wind_rows=rows)
                with self.assertRaises(SecondStationBlocked):
                    inspect(w, m)

    def test_geography_identity_and_timeline_overlap(self):
        w, m = fixture(self.root, geo_rows=[
            "348;300;48;10;20100101;20100101;SECRET_A\n",
            "348;305;48.1;10.1;20100101;20101231;SECRET_B\n",
        ])
        r = inspect(w, m)
        self.assertEqual(r["geography"]["history_rows"], 2)
        self.assertEqual(r["geography"]["provisional_inclusive_overlapping_geography_days"], 1)
        self.assertFalse(r["model_input_approved"])
        self.assertNotIn("SECRET_A", str(r))

    def test_wrong_station_geography_blocked(self):
        w, m = fixture(self.root, geo_rows=[
            GEOGRAPHY_ROW.replace("348;", "349;")])
        with self.assertRaises(SecondStationBlocked):
            inspect(w, m)

    def test_metadata_other_required_families_missing_blocked(self):
        w, m = fixture(self.root)
        with ZipFile(m, "w", ZIP_DEFLATED) as z:
            z.writestr(STATION_GEO, GEOGRAPHY_HEADER + GEOGRAPHY_ROW)
        with self.assertRaises(SecondStationBlocked):
            inspect(w, m)

    def test_invalid_original_geography_numeric_blocked(self):
        for latitude in ("91", "NaN", "PRIVATE"):
            with self.subTest(latitude=latitude):
                row = GEOGRAPHY_ROW.replace(";48.0;", f";{latitude};")
                w, m = fixture(self.root, geo_rows=[row])
                with self.assertRaises(SecondStationBlocked):
                    inspect(w, m)

    def test_zip_truncation_blocked(self):
        w, m = fixture(self.root)
        w.write_bytes(w.read_bytes()[:20])
        with self.assertRaises(SecondStationBlocked):
            inspect(w, m)


if __name__ == "__main__":
    unittest.main()
