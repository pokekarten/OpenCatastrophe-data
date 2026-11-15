# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import gzip
import io
import unittest
from unittest.mock import patch
from research_runners.meteofrance_four_north_original_v0 import (
    ASSETS, Blocked, LimitedInflation, asset_url, audit_original, check_identity
)

HEADER = "NUM_POSTE;AAAAMMJJHH;FF;FXI;FXI3S;QFXI3S;STATUS_FXI3S;LAT\n"
ROWS = ("02010001;2020020915;7.1;18.5;19.4;1;0;49.0\n"
        "02010001;2020020916;8.0;20.0;22.0;1;1;49.0\n"
        "02010001;2020020917;8.0;21.0;22.0;9;;49.0\n")


def sample(rows=ROWS):
    return gzip.compress((HEADER + rows).encode(), mtime=0)


def fixture(bytes_to_read):
    return {"02": (ASSETS["02"][0], bytes_to_read, None)}


class TestFourNorthOriginals(unittest.TestCase):
    def test_exact_id_and_path(self):
        self.assertEqual(sorted(ASSETS), ["02", "62", "76", "80"])
        self.assertTrue(asset_url("02").endswith("H_02_previous-2020-2024.csv.gz"))
        with self.assertRaises(Blocked):
            asset_url("59")

    def test_valid_original_three_second_counts(self):
        with patch("research_runners.meteofrance_four_north_original_v0.ASSETS", fixture(len(sample()))):
            a = audit_original("02", sample())
        self.assertEqual(a["rows"], 3)
        self.assertEqual(a["stations"], 1)
        self.assertEqual(a["quality_checked_three_second_gusts"], 2)
        self.assertEqual(a["status_calculated_three_second_gusts"], 1)
        self.assertEqual(a["status_not_calculated_three_second_gusts"], 1)
        self.assertFalse(a["source_admitted"])
        self.assertFalse(a["annual_ep_authorized"])
        self.assertNotIn("02010001", str(a))

    def test_hash_and_size_are_separate_gates(self):
        with self.assertRaisesRegex(Blocked, "size"):
            audit_original("02", sample())
        with patch("research_runners.meteofrance_four_north_original_v0.ASSETS",
                   {"02": (ASSETS["02"][0], len(sample()), "0" * 64)}):
            with self.assertRaisesRegex(Blocked, "SHA-256"):
                audit_original("02", sample())

    def test_timestamp_and_wind_fail_closed(self):
        for text in ("2020023015", "2020020924", "2025020915"):
            bad = sample(ROWS.replace("2020020915", text))
            with patch("research_runners.meteofrance_four_north_original_v0.ASSETS", fixture(len(bad))):
                with self.assertRaises(Blocked):
                    audit_original("02", bad)
        bad = sample(ROWS.replace(";19.4;", ";nan;"))
        with patch("research_runners.meteofrance_four_north_original_v0.ASSETS", fixture(len(bad))):
            with self.assertRaises(Blocked):
                audit_original("02", bad)

    def test_gzip_decompression_byte_cap(self):
        content = gzip.compress(b"a" * 400)
        with gzip.GzipFile(fileobj=io.BytesIO(content)) as f:
            reader = LimitedInflation(f, 64)
            with self.assertRaisesRegex(Blocked, "inflated"):
                reader.readinto(bytearray(512))

    def test_catalogue_mutation_is_rejected(self):
        with self.assertRaises(Blocked):
            check_identity({"sources": [{"department":"02","resource_id":"invalid"}]}, "02")
        with self.assertRaises(Blocked):
            check_identity({"sources": []}, "99")

    def test_no_secret_original_rows_or_model_admission(self):
        with patch("research_runners.meteofrance_four_north_original_v0.ASSETS", fixture(len(sample()))):
            result = audit_original("02", sample())
        self.assertFalse(result["original_provider_bytes_committed"])
        self.assertNotIn("NUM_POSTE", str(result))


if __name__ == "__main__":
    unittest.main()
