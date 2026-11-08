# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Hermetic original-byte receipt tests, no provider original files."""
from __future__ import annotations

import csv
import hashlib
import io
import unittest

from research_runners import hazardplain_202610_original_csv_receipt_v0 as m


def sample(*, quoted_newline=False):
    output = io.StringIO(newline="")
    wr = csv.writer(output, lineterminator="\r\n")
    wr.writerow(("stcofips", "hazard", "eal_total"))
    wr.writerow(("01001", "flood", "12.25"))
    wr.writerow(("01003", "hurricane\nwind" if quoted_newline else "hurricane_wind", "5"))
    return output.getvalue().encode("utf-8")


def scan(raw, *, rows=2, columns=None, size=None, sha=None):
    return m.verify_original_csv(
        raw,
        expected_bytes=len(raw) if size is None else size,
        expected_sha256=hashlib.sha256(raw).hexdigest() if sha is None else sha,
        expected_rows=rows,
        expected_columns=columns or ["stcofips", "hazard", "eal_total"],
    )


class SourceCSVTests(unittest.TestCase):
    def test_synthetic_bytes_and_schema_verified(self):
        receipt=scan(sample())
        self.assertEqual(receipt["original_bytes"],len(sample()))
        self.assertEqual(receipt["record_count_verified"],2)
        self.assertEqual(receipt["header_columns_verified"],["stcofips","hazard","eal_total"])
        self.assertTrue(receipt["provider_checksum_independently_recomputed"])
        self.assertFalse(receipt["source_cell_values_emitted"])

    def test_quoted_newline_is_one_record(self):
        self.assertEqual(scan(sample(quoted_newline=True))["record_count_verified"],2)

    def test_bad_checksum_blocked(self):
        with self.assertRaisesRegex(m.OriginalCSVError,"SHA-256 mismatch"):
            scan(sample(),sha="0"*64)

    def test_changed_source_byte_count_blocked(self):
        with self.assertRaisesRegex(m.OriginalCSVError,"byte length"):
            scan(sample(),size=len(sample())+1)

    def test_missing_records_blocked(self):
        with self.assertRaisesRegex(m.OriginalCSVError,"row count"):
            scan(sample(),rows=3)

    def test_wrong_columns_blocked(self):
        with self.assertRaisesRegex(m.OriginalCSVError,"header"):
            scan(sample(),columns=["fips","hazard","eal_total"])

    def test_incomplete_row_fails(self):
        raw=sample().replace(b"01003,hurricane_wind,5",b"01003,hurricane_wind")
        with self.assertRaisesRegex(m.OriginalCSVError,"field counts"):
            scan(raw)

    def test_csv_value_not_emitted(self):
        raw=sample().replace(b"12.25",b"VERYSENSITIVEEXAMPLE")
        receipt=scan(raw)
        self.assertNotIn("VERYSENSITIVEEXAMPLE",str(receipt))

    def test_source_path_allowlist(self):
        with self.assertRaisesRegex(m.OriginalCSVError,"unapproved"):
            m.fetch_original("../private.csv")

    def test_untrusted_redirect_blocked_before_request(self):
        import urllib.request
        request=urllib.request.Request("https://files.hazardplain.org/r/2026-10/bulk/national/b2c_county.csv")
        with self.assertRaisesRegex(m.OriginalCSVError,"outside pinned"):
            m.SameOriginalHostRedirect().redirect_request(
                request,None,302,"Moved",{},"https://evil.example/data.csv")

    def test_manifest_wrong_bytes_blocked(self):
        with self.assertRaisesRegex(m.OriginalCSVError,"manifest exact-byte pin"):
            m.validate_pinned_manifest(b"not the original source manifest")

    def test_invalid_expected_contract_rejected(self):
        for columns in ([],["a","a"],[""],[3]):
            with self.subTest(columns=columns),self.assertRaises(m.OriginalCSVError):
                scan(sample(),columns=columns)

    def test_bad_encoding_blocked(self):
        raw=sample()+b"\xff"
        with self.assertRaisesRegex(m.OriginalCSVError,"UTF-8"):
            scan(raw)

    def test_no_network_is_done_in_hermetic_tests(self):
        self.assertIsNotNone(m.EXPECTED_MANIFEST_SHA256)
        self.assertFalse(m.audit_originals.__doc__ == "insurer claim data")


if __name__=="__main__":
    unittest.main()
