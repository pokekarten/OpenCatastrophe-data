# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regressions for the non-admission MaterialCities archive gate."""
from __future__ import annotations

import csv
import hashlib
import io
import math
import unittest
import zipfile

from research_runners.materialcities_adm2_gfa_preflight_v0 import (
    GFA_FIELDS,
    MaterialCitiesPreflightError,
    inspect_archive,
)


def _archive(rows=None, *, member="MaterialCities_adm2.csv", fields=None) -> bytes:
    names = fields or ["GID_0", "GID_2", "GFA", *GFA_FIELDS]
    sample = rows if rows is not None else [
        {"GID_0": "DEU", "GID_2": "DEU.1.1_1", "GFA": "150",
         "GFA_NR_C": "100", "GFA_RS_M": "50"},
        {"GID_0": "FRA", "GID_2": "FRA.1.1_1", "GFA": "200",
         "GFA_RS_M": "200"},
    ]
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=names, extrasaction="ignore")
    writer.writeheader()
    for row in sample:
        writer.writerow({name: row.get(name, "0") for name in names})
    zipped = io.BytesIO()
    with zipfile.ZipFile(zipped, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, out.getvalue())
    return zipped.getvalue()


def _inspect(blob: bytes, *, country=None) -> dict:
    return inspect_archive(blob, expected_md5=hashlib.md5(blob).hexdigest(), country=country)


class MaterialCitiesPreflightTests(unittest.TestCase):
    def test_valid_original_shaped_archive_is_explicitly_research_only(self):
        receipt = _inspect(_archive())
        self.assertEqual(receipt["adm2_regions"], 2)
        self.assertEqual(receipt["gross_floor_area_m2"], 350)
        self.assertEqual(receipt["regional_component_mismatch_count"], 0)
        self.assertEqual(receipt["gfa_function_structure_m2"]["GFA_NR_C"], 100)
        self.assertEqual(receipt["gfa_function_structure_m2"]["GFA_RS_M"], 250)
        self.assertEqual(len(receipt["archive_sha256"]), 64)
        self.assertTrue(receipt["research_only"])
        for forbidden in ("source_rights_reviewed", "scientific_fitness_reviewed",
                          "site_geolocation_verified", "insured_portfolio_inferred",
                          "insured_tiv_inferred", "model_input_admitted"):
            self.assertFalse(receipt[forbidden])

    def test_country_filter_selects_only_matching_regions(self):
        receipt = _inspect(_archive(), country="DEU")
        self.assertEqual(receipt["adm2_regions"], 1)
        self.assertEqual(receipt["gross_floor_area_m2"], 150)
        self.assertEqual(receipt["country_filter"], "DEU")

    def test_wrong_publisher_fingerprint_is_blocking(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "MD5 mismatch"):
            inspect_archive(_archive())

    def test_duplicate_adm2_region_rejected(self):
        rows = [
            {"GID_0": "DEU", "GID_2": "DEU.1.1_1", "GFA": "1", "GFA_NR_C": "1"},
            {"GID_0": "DEU", "GID_2": "DEU.1.1_1", "GFA": "1", "GFA_NR_C": "1"},
        ]
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "duplicate ADM2"):
            _inspect(_archive(rows))

    def test_negative_nonfinite_and_non_numeric_rejected(self):
        for bad in ("-1", "NaN", "Infinity", "abc", ""):
            with self.subTest(value=bad):
                b = _archive([{"GID_0": "DEU", "GID_2": "DEU.1.1_1",
                               "GFA": bad, "GFA_NR_C": "1"}])
                with self.assertRaises(MaterialCitiesPreflightError):
                    _inspect(b)

    def test_unbalanced_regional_gfa_is_flagged_not_admitted(self):
        b = _archive([{"GID_0": "DEU", "GID_2": "DEU.1.1_1",
                       "GFA": "150", "GFA_NR_C": "100"}])
        receipt = _inspect(b)
        self.assertEqual(receipt["regional_component_mismatch_count"], 1)
        self.assertFalse(receipt["model_input_admitted"])

    def test_missing_function_structure_column_is_blocking(self):
        fields = ["GID_0", "GID_2", "GFA", *GFA_FIELDS[:-1]]
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "missing expected"):
            _inspect(_archive(fields=fields))

    def test_missing_country_identity_is_blocking_for_filter(self):
        fields = ["GID_2", "GFA", *GFA_FIELDS]
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "country filter"):
            _inspect(_archive(fields=fields), country="DEU")

    def test_zip_traversal_is_blocking(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "unsafe ZIP"):
            _inspect(_archive(member="../malicious.csv"))

    def test_country_filter_cannot_silently_return_no_records(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "no ADM2"):
            _inspect(_archive(), country="NZL")

    def test_unexpected_source_headers_and_no_csv_rejected(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "no ADM2"):
            _inspect(_archive(fields=["GFA", "GID_0"]))
        zipped = io.BytesIO()
        with zipfile.ZipFile(zipped, "w") as archive:
            archive.writestr("README.txt", "not a source CSV")
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "CSV member"):
            _inspect(zipped.getvalue())


if __name__ == "__main__":
    unittest.main()
