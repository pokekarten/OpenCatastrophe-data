# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only native FRS projection and fail-closed tests."""
from __future__ import annotations

import csv
import hashlib
import io
import unittest

from research_runners import epa_frs_native_projection_v0 as w


def native(rows, fields=("REGISTRY_ID", "LATITUDE_MEASURE", "LONGITUDE_MEASURE", "FAC_NAME")):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    data = out.getvalue().encode()
    return data, hashlib.sha256(data).hexdigest()


def rec(**extra):
    row = {"REGISTRY_ID": "110000000001", "LATITUDE_MEASURE": "40.00001",
           "LONGITUDE_MEASURE": "-75.12345", "FAC_NAME": "SYNTHETIC_SITE_ONLY"}
    row.update(extra)
    return row


def project(rows=None, fields=None, **flags):
    source, sha = native([rec()] if rows is None else rows,
                         fields=fields or ("REGISTRY_ID", "LATITUDE_MEASURE", "LONGITUDE_MEASURE", "FAC_NAME"))
    return w.project_native_frs(source, sha, release_date=flags.get("release_date", "2026-10-30"),
                                coordinates_approved=flags.get("coordinates_approved", False))


class NativeEPAProjectionTests(unittest.TestCase):
    def test_default_suppresses_unreviewed_coordinates_and_pins_hashes(self):
        blob, report = project()
        self.assertEqual(blob, b"frs_id,country_code,latitude,longitude\n110000000001,US,,\n")
        self.assertTrue(report["projected_coordinates_suppressed"])
        self.assertEqual(report["normalized_projection_sha256"], hashlib.sha256(blob).hexdigest())
        self.assertFalse(report["source_bytes_independently_authenticated"])
        self.assertFalse(report["insured_asset_or_tiv_inferred"])
        self.assertNotIn("SYNTHETIC_SITE_ONLY", str(report))
        self.assertNotIn("110000000001", str(report))

    def test_caller_coordinate_flag_keeps_original_precision_but_not_approval_proof(self):
        blob, report = project(coordinates_approved=True)
        self.assertIn(b"40.00001,-75.12345", blob)
        self.assertFalse(report["source_rights_or_model_admission_granted"])

    def test_missing_both_coordinates_is_preserved(self):
        blob, report = project(rows=[rec(LATITUDE_MEASURE="", LONGITUDE_MEASURE="")],
                               coordinates_approved=True)
        self.assertIn(b",US,,", blob)
        self.assertEqual(report["native_rows_without_both_coordinates"], 1)

    def test_hash_mismatch_fails(self):
        source, _ = native([rec()])
        with self.assertRaisesRegex(w.FRSProjectionBlocked, "SHA-256 mismatch"):
            w.project_native_frs(source, "0" * 64, release_date="2026-10-30")

    def test_reject_repeated_registry_id(self):
        with self.assertRaisesRegex(w.FRSProjectionBlocked, "duplicate native"):
            project(rows=[rec(), rec()])

    def test_reject_partial_and_invalid_coordinates(self):
        for updated in ({"LATITUDE_MEASURE": ""},
                        {"LATITUDE_MEASURE": "nan"},
                        {"LONGITUDE_MEASURE": "181"},
                        {"LATITUDE_MEASURE": "40.1\rBAD"}):
            with self.subTest(updated=updated), self.assertRaises(w.FRSProjectionBlocked):
                project(rows=[rec(**updated)])

    def test_reject_missing_required_header(self):
        source, sha = native([{"REGISTRY_ID": "123", "LATITUDE_MEASURE": "1"}],
                             fields=("REGISTRY_ID", "LATITUDE_MEASURE"))
        with self.assertRaisesRegex(w.FRSProjectionBlocked, "columns missing"):
            w.project_native_frs(source, sha, release_date="2026-10-30")

    def test_reject_invalid_original_id(self):
        with self.assertRaisesRegex(w.FRSProjectionBlocked, "invalid FRS original"):
            project(rows=[rec(REGISTRY_ID="")])

    def test_deterministic_sorted_output_and_no_raw_name(self):
        one = rec(REGISTRY_ID="112", FAC_NAME="EXAMPLE")
        two = rec(REGISTRY_ID="111", FAC_NAME="EXAMPLE2")
        first, _ = project(rows=[one, two])
        second, _ = project(rows=[two, one])
        self.assertEqual(first, second)
        self.assertNotIn(b"EXAMPLE", first)
        self.assertLess(first.index(b"111,US"), first.index(b"112,US"))

    def test_reject_invalid_release_or_future_date(self):
        for value in ("latest", "2026-02-30", "2099-01-01"):
            with self.subTest(date=value), self.assertRaises(w.FRSProjectionBlocked):
                project(release_date=value)

    def test_reject_empty_body(self):
        with self.assertRaisesRegex(w.FRSProjectionBlocked, "no records"):
            project(rows=[])

    def test_wrong_approval_flag_type_fails(self):
        with self.assertRaises(w.FRSProjectionBlocked):
            project(coordinates_approved="yes")


if __name__ == "__main__":
    unittest.main()
