# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic samples only; no original bridge rows in this test file."""
from __future__ import annotations

from hashlib import sha256
import json
import unittest

from research_runners import fhwa_nbi_socrata_original_rows_v0 as gate


def rows():
    return [
        {"year": "2025", "state_code_001": "1",
         "structure_number_008": f"0000000000000{n}", "lat_016": "33452500",
         "long_017": "086300000", "year_built_027": "1970"}
        for n in range(3)
    ]


def wire(r):
    return json.dumps(r, separators=(",", ":")).encode()


class NBISelectedOriginalRowTests(unittest.TestCase):
    def test_source_sample_receipt_no_raw_bridge_identity_or_coordinate(self):
        sample = wire(rows())
        r = gate.audit_rows(sample, expected_count=3, expected_sha256=sha256(sample).hexdigest())
        self.assertEqual(r["sample_rows"], 3)
        self.assertEqual(r["legacy_dms_format_plausible_count"], 3)
        self.assertEqual(r["build_year_range_plausible_count"], 3)
        self.assertFalse(r["model_input_admitted"])
        rendered = json.dumps(r)
        self.assertNotIn("0000000000000", rendered)
        self.assertNotIn("33452500", rendered)

    def test_dms_has_strict_coordinate_fields_without_geo_claim(self):
        self.assertTrue(gate._original_dms("33452500", 8))
        self.assertTrue(gate._original_dms("086300000", 9))
        self.assertTrue(gate._original_dms("86300000", 9))  # lost leading zero numeric API
        for v, width in [("33602500", 8), ("33596000", 8),
                         ("986300000", 9), ("086306000", 9),
                         ("33.45", 8), (None, 8), (True, 8)]:
            with self.subTest(value=v):
                self.assertFalse(gate._original_dms(v, width))

    def test_original_source_null_coords_are_counted_unknown_not_geocoded(self):
        f = rows()
        f[1].pop("lat_016")
        f[2]["long_017"] = "0"
        r = gate.audit_rows(wire(f), expected_count=3)
        self.assertEqual(r["legacy_dms_format_unverified_count"], 2)
        self.assertFalse(r["encoded_coordinate_crs_validated"])

    def test_reject_duplicate_bridge_year_and_bad_structure_identity(self):
        f = rows()
        f[1] = f[0].copy()
        with self.assertRaisesRegex(gate.Blocked, "duplicate bridge"):
            gate.audit_rows(wire(f), expected_count=3)
        f = rows()
        f[1]["structure_number_008"] = 101
        with self.assertRaisesRegex(gate.Blocked, "textual structure"):
            gate.audit_rows(wire(f), expected_count=3)

    def test_reject_missing_or_invalid_source_year_state(self):
        for field, val in [("year", "2028"), ("year", None),
                           ("state_code_001", "abc"), ("state_code_001", 0)]:
            f = rows()
            f[0][field] = val
            with self.subTest(field=field, value=val), self.assertRaises(gate.Blocked):
                gate.audit_rows(wire(f), expected_count=3)

    def test_reject_extra_fields_row_arrays_and_partial_sample(self):
        f = rows()
        f[0]["insurer"] = "invented"
        with self.assertRaisesRegex(gate.Blocked, "six selected"):
            gate.audit_rows(wire(f), expected_count=3)
        with self.assertRaisesRegex(gate.Blocked, "incomplete"):
            gate.audit_rows(wire(rows()[:2]), expected_count=3)
        with self.assertRaises(gate.Blocked):
            gate.audit_rows(wire({}), expected_count=3)

    def test_unverified_build_year_does_not_invent_valid_age(self):
        f = rows()
        f[0]["year_built_027"] = "0"
        f[1]["year_built_027"] = "9999"
        f[2].pop("year_built_027")
        r = gate.audit_rows(wire(f), expected_count=3)
        self.assertEqual(r["build_year_unknown_or_unverified_count"], 3)

    def test_adversarial_bytes_duplicate_json_keys_and_sha(self):
        for data in [b"<html>" * 20, b"\xff" * 60,
                     b'[{"year":NaN}]' * 20, None]:
            with self.subTest(value=repr(data)[:12]), self.assertRaises(gate.Blocked):
                gate.audit_rows(data, expected_count=3)
        duplicate = wire(rows()).replace(
            b'"year":"2025"', b'"year":"2025","year":"2025"', 1)
        with self.assertRaisesRegex(gate.Blocked, "duplicate JSON"):
            gate.audit_rows(duplicate, expected_count=3)
        with self.assertRaisesRegex(gate.Blocked, "SHA-256"):
            gate.audit_rows(wire(rows()), expected_count=3, expected_sha256="0"*64)


if __name__ == "__main__":
    unittest.main()
