# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independently synthetic WSM 2025 original-format and security boundary checks."""

import csv
import hashlib
import io
import unittest

from scripts.wsm2025_original_csv_preflight_v0 import (
    FIELDS, MAX_ORIGINAL_BYTES, MAX_ROWS, Wsm2025FormatError,
    screen_wsm2025_csv_bytes,
)


def synthetic_csv(*overrides):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for index, delta in enumerate(overrides, start=1):
        row = {key: "" for key in FIELDS}
        row.update({"ID": f"wsm{index}", "LAT": "46.5", "LON": "119.68",
                    "AZI": "45", "TYPE": "BO", "QUALITY": "A", "REGIME": "SS"})
        row.update(delta)
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


class Wsm2025CsvScreenTests(unittest.TestCase):
    def test_quality_sentinel_and_unmodified_source_hash(self):
        data = synthetic_csv({}, {"QUALITY": "Xmi", "AZI": "999", "REGIME": "U"})
        receipt = screen_wsm2025_csv_bytes(data)
        self.assertEqual(receipt["original_sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(receipt["rows_screened"], 2)
        self.assertEqual(receipt["missing_orientation_rows"], 1)
        self.assertEqual(receipt["valid_orientation_rows"], 1)
        self.assertEqual(receipt["cat_model_admission"], "not_admitted")
        self.assertEqual(receipt["neon_storage"], "storage_not_verified")

    def test_quoted_comment_with_comma_does_not_shift_columns(self):
        result = screen_wsm2025_csv_bytes(synthetic_csv({"COMMENT": "anomaly, independently checked"}))
        self.assertEqual(result["rows_screened"], 1)

    def test_rejects_shape_quality_and_numeric_defects(self):
        invalid = [
            b"", b"<html>404 not found</html>", b"\xff",
            synthetic_csv({"LAT": "91"}), synthetic_csv({"LON": "-181"}),
            synthetic_csv({"AZI": "181"}), synthetic_csv({"AZI": "NaN"}),
            synthetic_csv({"QUALITY": "Z"}), synthetic_csv({"REGIME": "unknown"}),
            synthetic_csv({"AZI": "999", "QUALITY": "A"}),
            synthetic_csv({"ID": "!wsm7"}),
            synthetic_csv({"ID": "wsm1"}, {"ID": "wsm1"}),
            synthetic_csv({"LAT": "inf"}),
            synthetic_csv({}).replace(b"ID,ISC_ID", b"BAD,ISC_ID", 1),
            synthetic_csv({}) + b"bad,row\n",
            synthetic_csv({}) + b'"unterminated\n',
            b"x" * (MAX_ORIGINAL_BYTES + 1),
            synthetic_csv(*([{}] * (MAX_ROWS + 1))),
        ]
        for data in invalid:
            with self.subTest(case=data[:80]):
                with self.assertRaises(Wsm2025FormatError):
                    screen_wsm2025_csv_bytes(data)


if __name__ == "__main__":
    unittest.main()
