# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for fail-closed original DWD gust QC."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from scripts.dwd_frozen_gust_qc_v0 import GustQCBlocked, _decode_row, summarize


HEAD = "STATIONS_ID;MESS_DATUM;QN;FX_10;FNX_10;FMX_10;DX_10;eor\r\n"
ROWS = [
    "3;201001010000;1;30.0;2.0;5.0;180;eor\r\n",
    "3;201001010010;2;-999;-999;-999;-999;eor\r\n",
    "3;201001010020;3;15.5;1.0;6.0;180;eor\r\n",
    "3;201103312350;2;24.9;3.0;8.0;200;eor\r\n",
]


def zip_source(tmp: Path, rows=None) -> tuple[Path, str]:
    path = tmp / "frozen-original.zip"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "produkt_extrema_wind_00003_20100101_20110331.txt",
            HEAD + "".join(ROWS if rows is None else rows))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class FrozenGustTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_monthly_max_missingness_quality_and_gaps(self):
        path, digest = zip_source(self.root)
        report = summarize(path, expected_sha256=digest)
        self.assertEqual(report["observations"], 4)
        self.assertEqual(report["missing_fx_10"], 1)
        self.assertEqual(report["timestamp_basis"], "UTC_2010_2011_DWD")
        self.assertEqual(len(report["months"]), 2)
        jan = report["months"][0]
        self.assertEqual(jan["quality_level_counts"], {"1": 1, "2": 1, "3": 1})
        self.assertEqual(jan["max_fx_10_mps_all_quality"], "30.0")
        self.assertEqual(jan["max_fx_10_mps_qn_2_3"], "15.5")
        self.assertEqual(jan["fx_10_missing"], 1)
        self.assertGreater(report["unobserved_10min_slots_between_records"], 60000)
        self.assertFalse(report["model_input_approved"])
        self.assertFalse(report["geographic_station_metadata_validated"])

    def test_wrong_original_byte_hash_rejected(self):
        path, _ = zip_source(self.root)
        with self.assertRaisesRegex(GustQCBlocked, "SHA-256"):
            summarize(path, expected_sha256="f" * 64)

    def test_missing_source_file_and_symlink_rejected(self):
        with self.assertRaises(GustQCBlocked):
            summarize(self.root / "no.zip")
        path, digest = zip_source(self.root)
        alias = self.root / "alias.zip"
        alias.symlink_to(path)
        with self.assertRaises(GustQCBlocked):
            summarize(alias, expected_sha256=digest)

    def test_duplicated_timestamp_fails_closed(self):
        rows = [ROWS[0], ROWS[1], ROWS[1], ROWS[-1]]
        path, digest = zip_source(self.root, rows)
        with self.assertRaises(GustQCBlocked):
            summarize(path, expected_sha256=digest)

    def test_non_10_minute_cadence_fails_closed(self):
        rows = [ROWS[0], "3;201001010015;2;4.1;1.0;2.0;180;eor\r\n", ROWS[-1]]
        path, digest = zip_source(self.root, rows)
        with self.assertRaisesRegex(GustQCBlocked, "10-minute"):
            summarize(path, expected_sha256=digest)

    def test_negative_gust_not_missing_sentinel_fails_closed(self):
        path, digest = zip_source(self.root, [ROWS[0], "3;201001010010;2;-1;0;0;0;eor\r\n", ROWS[-1]])
        with self.assertRaises(GustQCBlocked):
            summarize(path, expected_sha256=digest)

    def test_nonnumeric_quality_and_nan_rejected(self):
        for row in (
            "3;201001010010;QA;3;0;0;0;eor\r\n",
            "3;201001010010;2;NaN;0;0;0;eor\r\n",
            "3;201001010010;2;Infinity;0;0;0;eor\r\n",
        ):
            with self.subTest(row=row):
                path, digest = zip_source(self.root, [ROWS[0], row, ROWS[-1]])
                with self.assertRaises(GustQCBlocked):
                    summarize(path, expected_sha256=digest)

    def test_wrong_station_or_date_fails_closed(self):
        for row in (
            "4;201001010010;2;4.0;0;0;0;eor\r\n",
            "3;201201010010;2;4.0;0;0;0;eor\r\n",
        ):
            with self.subTest(row=row):
                path, digest = zip_source(self.root, [ROWS[0], row, ROWS[-1]])
                with self.assertRaises(GustQCBlocked):
                    summarize(path, expected_sha256=digest)

    def test_truncated_or_wrong_product_header_rejected(self):
        path, digest = zip_source(self.root, [ROWS[0], ROWS[-1]])
        # Synthetic known good source first.
        self.assertEqual(summarize(path, expected_sha256=digest)["observations"], 2)
        path.write_bytes(path.read_bytes()[:32])
        with self.assertRaises(GustQCBlocked):
            summarize(path, expected_sha256=digest)

    def test_row_decoder_strict_fields(self):
        ix = {"STATIONS_ID": 0, "MESS_DATUM": 1, "QN": 2, "FX_10": 3}
        with self.assertRaises(GustQCBlocked):
            _decode_row(b"3;201001010000;2;2.2\n", ix, 8)

    def test_other_quality_levels_remain_outside_qn_two_three_subset(self):
        """Unknown QN levels must never enter the reviewed high-quality gust subset."""
        rows = [
            "3;201001010000;0;12.0;1.0;2.0;180;eor\r\n",
            "3;201001010010;4;25.0;2.0;4.0;190;eor\r\n",
            ROWS[-1],
        ]
        path, digest = zip_source(self.root, rows)
        result = summarize(path, expected_sha256=digest)
        jan = result["months"][0]
        self.assertEqual(jan["quality_level_counts"], {"0": 1, "4": 1})
        self.assertEqual(jan["max_fx_10_mps_all_quality"], "25.0")
        self.assertIsNone(jan["max_fx_10_mps_qn_2_3"])
        self.assertEqual(jan["qn_2_3_fx_10_nonmissing"], 0)

    def test_no_untrusted_qn1_promoted_to_quality_subset(self):
        path, digest = zip_source(self.root, [ROWS[0], "3;201001010010;1;-999;0;0;0;eor\r\n", ROWS[-1]])
        result = summarize(path, expected_sha256=digest)
        self.assertEqual(result["months"][0]["max_fx_10_mps_qn_2_3"], None)
        self.assertEqual(result["months"][0]["max_fx_10_mps_all_quality"], "30.0")


if __name__ == "__main__":
    unittest.main()
