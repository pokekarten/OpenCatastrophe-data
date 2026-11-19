# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic-only tests for the full NYC archive record diagnostic."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from research_runners.nyc_building_archive_full_row_diagnostic_v0 import (
    ArchiveGateError, MAX_ROWS, _post_2024, scan,
)

HEADER = (
    "the_geom,BIN,DOITT_ID,BASE_BBL,Map Pluto BBL,Feature Code,"
    "Construction Year,LAST_EDITED_DATE,Other\n"
)
BODY = (
    'SHAPE_A,1000001,44,1000000001,1000000001,2100,1975,2024-01-02T07:00:00.000Z,other\n'
    'SHAPE_B,1000000,0,1000000002,1000000002,1003,0,,other\n'
    'SHAPE_C,1000003,55,1000000003,1000000023,2100,2025,2025-01-02T07:00:00.000Z,other\n'
)


class FullArchiveRecordDiagnosticTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def make_csv(self, body=BODY, header=HEADER):
        file = self.root / "original.csv"
        file.write_text(header + body, encoding="utf-8")
        return file

    def make_zip(self, body=BODY, header=HEADER):
        file = self.root / "original.zip"
        with ZipFile(file, "w", ZIP_DEFLATED) as archive:
            archive.writestr("building/official.csv", header + body)
        return file

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def run_file(self, file, count=3, date="2024-12-30"):
        return scan(str(file), self.sha(file), date, count)

    def test_full_csv_rows_counts_and_provider_attestation_blocked(self):
        file = self.make_csv()
        out = self.run_file(file)
        counts = out["anomaly_and_category_counts"]
        self.assertEqual(out["actual_local_csv_records"], 3)
        self.assertEqual(counts["standard_building_feature_code_2100"], 2)
        self.assertEqual(counts["placeholder_triangle_code_1003"], 1)
        self.assertEqual(counts["bin_unassigned_million_placeholder"], 1)
        self.assertEqual(counts["doitt_zero_unknown_historic_identity"], 1)
        self.assertEqual(counts["base_bbl_equal_billing"], 2)
        self.assertEqual(counts["base_bbl_different_billing"], 1)
        self.assertEqual(counts["construction_year_after_2024"], 1)
        self.assertEqual(counts["last_edit_after_2024_flagged"], 1)
        self.assertEqual(counts["geometry_nonempty_unverified"], 3)
        for flag in (
            "date_and_expected_row_count_provider_attested",
            "official_2024_inventory_release_authenticated",
            "source_rights_or_model_admission_approved",
            "insured_tiv_or_loss_calculated",
            "original_source_identifiers_emitted",
            "original_source_rows_or_geometry_persisted",
            "actual_polygon_geometry_topology_validated",
            "global_doitt_id_uniqueness_verified",
            "global_bin_uniqueness_verified",
        ):
            self.assertFalse(out[flag])
        for secret in ("1000001", "SHAPE_C", "original.csv", str(self.root)):
            self.assertNotIn(secret, str(out))

    def test_zip_scanned_without_extracting_rows(self):
        file = self.make_zip()
        out = self.run_file(file)
        self.assertEqual(out["actual_local_csv_records"], 3)
        self.assertFalse((self.root / "building/official.csv").exists())

    def test_wrong_expected_row_count_is_fail_closed(self):
        file = self.make_csv()
        for c in (1, 2, 4, 5):
            with self.subTest(count=c), self.assertRaisesRegex(ArchiveGateError, "row count"):
                self.run_file(file, c)

    def test_fake_source_vintage_cannot_be_admitted(self):
        file = self.make_csv()
        out = self.run_file(file)
        self.assertEqual(out["claimed_version_date"], "2024-12-30")
        self.assertFalse(out["official_2024_inventory_release_authenticated"])
        with self.assertRaises(ArchiveGateError):
            scan(str(file), self.sha(file), "2025-01-02", 3)
        with self.assertRaises(ArchiveGateError):
            scan(str(file), self.sha(file), "2024-12-30", 3, source_view="ipkp-snf6")

    def test_hash_mismatch_and_wrong_source_file_blocked(self):
        file = self.make_csv()
        with self.assertRaises(ArchiveGateError):
            scan(str(file), "0" * 64, "2024-12-30", 3)
        file.write_bytes(b"changed while processing")
        with self.assertRaises(ArchiveGateError):
            scan(str(file), "0" * 64, "2024-12-30", 3)

    def test_wrong_columns_and_incomplete_csv_blocked(self):
        file = self.make_csv(body=BODY.replace("SHAPE_C,1000003,55", "SHAPE_C,1000003"))
        with self.assertRaisesRegex(ArchiveGateError, "number of columns"):
            self.run_file(file)
        file = self.make_csv(body=BODY.replace("SHAPE_C", '"UNFINISHED'))
        with self.assertRaises(ArchiveGateError):
            self.run_file(file)

    def test_valid_multiline_quoted_source_cell_is_streamed(self):
        body = ('"SYNTHETIC\nSHAPE",1000001,22,1000000001,1000000001,2100,1980,2024-11-01T01:20:00,ok\n')
        file = self.make_csv(body=body)
        self.assertEqual(self.run_file(file, 1)["actual_local_csv_records"], 1)

    def test_invalid_placeholder_and_malformed_value_counts_not_source_bytes(self):
        file = self.make_csv(body='MISSING,INVALID,abc,not_a_bbl,,x,broken,not_a_date,owner_fake\n')
        out = self.run_file(file, 1)
        counts = out["anomaly_and_category_counts"]
        for name in (
            "bin_missing_or_invalid", "doitt_missing_or_invalid",
            "base_bbl_missing_or_invalid", "mappluto_bbl_missing_or_invalid",
            "feature_code_missing_or_invalid", "construction_year_malformed",
            "last_edit_missing_or_malformed",
        ):
            self.assertEqual(counts[name], 1)
        self.assertNotIn("owner_fake", str(out))
        self.assertNotIn("not_a_bbl", str(out))

    def test_large_untrusted_numeric_fields_not_coerced_to_int(self):
        body = "G," + "9" * 7000 + "," + "9" * 7000 + ",invalid,invalid," + "9" * 7000 + ",0,,x\n"
        file = self.make_csv(body=body)
        out = self.run_file(file, 1)
        self.assertEqual(out["anomaly_and_category_counts"]["doitt_missing_or_invalid"], 1)

    def test_reject_bad_expected_record_claim(self):
        file = self.make_csv()
        for count in (0, -1, True, 5_000_001, 2.0, "3"):
            with self.subTest(count=count), self.assertRaises(ArchiveGateError):
                self.run_file(file, count)

    def test_empty_source_rejected(self):
        file = self.make_csv(body="")
        with self.assertRaises(ArchiveGateError):
            self.run_file(file, 1)

    def test_archive_with_extra_csv_member_cannot_stream(self):
        file = self.root / "original.zip"
        with ZipFile(file, "w", ZIP_DEFLATED) as archive:
            archive.writestr("first.csv", HEADER + BODY)
            archive.writestr("second.csv", HEADER + BODY)
        with self.assertRaises(ArchiveGateError):
            self.run_file(file)

    def test_post_2024_timestamps_are_flags_only(self):
        self.assertTrue(_post_2024("2025-01-01T00:00:00Z"))
        self.assertFalse(_post_2024("2024-12-31T23:59:59Z"))
        self.assertIsNone(_post_2024("invalid"))
        self.assertIsNone(_post_2024(""))

    def test_no_export_after_row_structure_error(self):
        file = self.make_csv(body="SHAPE,1000001,44,1000000001,1000000001,2100,1970,2024-12-01,ok,unexpected\n")
        with self.assertRaises(ArchiveGateError):
            self.run_file(file, 1)


if __name__ == "__main__":
    unittest.main()
