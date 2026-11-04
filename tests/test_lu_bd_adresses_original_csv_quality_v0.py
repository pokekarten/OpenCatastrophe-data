# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Zero-network, fictional original CSV and hash-contract regression tests."""
from __future__ import annotations

import hashlib
import io
import unittest

from research_runners.lu_bd_adresses_original_csv_quality_v0 import (
    HEADER, OriginalAddressError, inspect_csv, verify_original_stream, main,
)


def sample(*, fields=None, repeated=False):
    row = ["Invented St", "10", "Fictionburg", "0000", "synthetic-street-01",
           "synthetic-building-01", "49.6", "6.1", "76000", "75000", "invented-id-1", "Fictionburg", "1234"]
    data = [list(HEADER), fields or row]
    if repeated:
        data.append(list(data[1]))
    return ("\ufeff" + "\r\n".join(";".join(x) for x in data) + "\r\n").encode("utf-8")


class FakeTransformer:
    def transform(self, x, y):
        return 6.1, 49.6


class OriginalQualityTests(unittest.TestCase):
    def test_verified_full_synthetic_file(self):
        original = sample(repeated=True)
        outcome = verify_original_stream(io.BytesIO(original), expected_size=len(original),
                                         expected_md5=hashlib.md5(original).hexdigest(),
                                         transformer=FakeTransformer())
        self.assertEqual(outcome["row_count"], 2)
        self.assertEqual(outcome["duplicate_exact_coordinate_rows"], 1)
        self.assertEqual(outcome["repeated_caclr_building_id_rows"], 1)
        self.assertEqual(outcome["paired_crs_error_median_m"], 0.0)
        self.assertEqual(outcome["original_sha256_computed"], hashlib.sha256(original).hexdigest())
        self.assertFalse(outcome["building_identity_proven"])
        self.assertFalse(outcome["rights_admitted"])

    def test_bad_md5_fails_before_parsing(self):
        original = sample()
        with self.assertRaises(OriginalAddressError):
            verify_original_stream(io.BytesIO(original), expected_size=len(original), expected_md5="0" * 32)

    def test_truncation_fails(self):
        original = sample()
        with self.assertRaises(OriginalAddressError):
            verify_original_stream(io.BytesIO(original[:-3]), expected_size=len(original),
                                   expected_md5=hashlib.md5(original).hexdigest())

    def test_bad_header_fails(self):
        original = sample().replace(b"lat_wgs84", b"lat_changed")
        with self.assertRaises(OriginalAddressError):
            inspect_csv(io.BytesIO(original))

    def test_wrong_column_count_fails(self):
        original = sample()[:-2] + b";EXTRA\r\n"
        with self.assertRaises(OriginalAddressError):
            inspect_csv(io.BytesIO(original))

    def test_bad_coordinate_number_fails(self):
        row = sample().decode("utf-8").splitlines()[1].split(";")
        row[6] = "NaN"
        with self.assertRaises(OriginalAddressError):
            inspect_csv(io.BytesIO(sample(fields=row)))

    def test_partial_coordinate_pair_fails(self):
        row = sample().decode("utf-8").splitlines()[1].split(";")
        row[7] = ""
        with self.assertRaises(OriginalAddressError):
            inspect_csv(io.BytesIO(sample(fields=row)))

    def test_missing_both_coordinate_values_counted(self):
        row = sample().decode("utf-8").splitlines()[1].split(";")
        row[6] = row[7] = ""
        report = inspect_csv(io.BytesIO(sample(fields=row)))
        self.assertEqual(report["missing_wgs84_pairs"], 1)
        self.assertFalse(report["paired_crs_transform_evaluated"])

    def test_duplicated_exact_coordinate_counted(self):
        report = inspect_csv(io.BytesIO(sample(repeated=True)))
        self.assertEqual(report["distinct_exact_coordinate_pairs"], 1)

    def test_without_transform_no_fake_metric(self):
        report = inspect_csv(io.BytesIO(sample()))
        self.assertIsNone(report["paired_crs_error_p95_m"])

    def test_default_offline_no_network(self):
        self.assertEqual(main([]), 0)

    def test_real_source_url_not_leaking_into_address_content(self):
        r = inspect_csv(io.BytesIO(sample()))
        for val in r.values():
            self.assertNotIn("Invented St", str(val))
            self.assertNotIn("synthetic-building-01", str(val))


if __name__ == "__main__":
    unittest.main()
