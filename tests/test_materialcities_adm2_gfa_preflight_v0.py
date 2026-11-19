# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regressions for byte-pinned original MaterialCities 2026.9 ADM2."""
from __future__ import annotations

import csv
import hashlib
import io
import unittest
import zipfile

from research_runners.materialcities_adm2_gfa_preflight_v0 import (
    ADM2_MEMBER,
    GFA_FIELDS,
    MaterialCitiesPreflightError,
    ORIGINAL_SHA256,
    inspect_archive,
)


def _archive(rows=None, *, filename=ADM2_MEMBER, headers=None) -> bytes:
    fields = headers or ["GID_0", "GID_2", *GFA_FIELDS]
    data = rows if rows is not None else [
        {"GID_0": "DEU", "GID_2": "DEU.1.1_1", "GFA_NR_C": "100", "GFA_RS_M": "50"},
        {"GID_0": "FRA", "GID_2": "FRA.1.1_1", "GFA_RS_M": "200"},
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in data:
        writer.writerow({field: row.get(field, "0") for field in fields})
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(filename, stream.getvalue())
    return z.getvalue()


def _inspect(blob, *, country=None):
    return inspect_archive(blob, expected_md5=hashlib.md5(blob).hexdigest(),
                           expected_sha256=hashlib.sha256(blob).hexdigest(), country=country)


class MaterialCitiesOriginalSchemaTests(unittest.TestCase):
    def test_original_shaped_without_gfa_total_works(self):
        report = _inspect(_archive())
        self.assertEqual(report["source_adm2_rows_selected"], 2)
        self.assertEqual(report["source_row_gross_floor_area_m2"], 350.0)
        self.assertEqual(report["source_row_gfa_components_m2"]["GFA_NR_C"], 100.0)
        self.assertEqual(report["source_row_gfa_components_m2"]["GFA_RS_M"], 250.0)
        self.assertEqual(report["distinct_valid_adm2_keys"], 2)
        self.assertTrue(report["complete_unique_region_keyset"])
        self.assertFalse(report["independent_gfa_total_in_original_source"])
        for key in ("rights_reviewed", "commercial_use_cleared", "scientific_model_admitted",
                    "actual_insured_sites_proven", "insurer_tiv_inferred"):
            self.assertFalse(report[key])
        self.assertTrue(report["research_only"])

    def test_country_filter_keeps_only_source_deu_ids(self):
        report = _inspect(_archive(), country="DEU")
        self.assertEqual(report["csv_rows_scanned"], 2)
        self.assertEqual(report["source_adm2_rows_selected"], 1)
        self.assertEqual(report["source_row_gross_floor_area_m2"], 150.0)

    def test_stored_sha256_is_a_full_original_pinned_hash(self):
        self.assertEqual(len(ORIGINAL_SHA256), 64)
        data = _archive()
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "digest mismatch"):
            inspect_archive(data)
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "digest mismatch"):
            inspect_archive(data, expected_md5=hashlib.md5(data).hexdigest())

    def test_zero_gid2_is_not_a_unique_region(self):
        report = _inspect(_archive([
            {"GID_0": "ARM", "GID_2": "0", "GFA_NR_C": "20"},
            {"GID_0": "DEU", "GID_2": "DEU.1.1_1", "GFA_NR_C": "30"},
        ]))
        self.assertEqual(report["source_adm2_rows_selected"], 2)
        self.assertEqual(report["source_rows_without_unique_adm2_key"], 1)
        self.assertEqual(report["distinct_valid_adm2_keys"], 1)
        self.assertFalse(report["complete_unique_region_keyset"])
        self.assertEqual(report["source_row_gross_floor_area_m2"], 50)
        self.assertEqual(report["keyed_row_gross_floor_area_m2"], 30)

    def test_original_style_duplicate_gid_is_not_deduplicated(self):
        report = _inspect(_archive([
            {"GID_0": "ALA", "GID_2": "ALA.1.1_2", "GFA_NR_C": "10"},
            {"GID_0": "ALA", "GID_2": "ALA.1.1_2", "GFA_NR_C": "20"},
            {"GID_0": "ALA", "GID_2": "ALA.1.1_2", "GFA_NR_C": "30"},
        ]))
        self.assertEqual(report["duplicate_key_occurrences"], 2)
        self.assertEqual(report["distinct_collided_region_keys"], 1)
        self.assertEqual(report["source_adm2_rows_selected"], 3)
        self.assertEqual(report["source_row_gross_floor_area_m2"], 60.0)
        self.assertFalse(report["complete_unique_region_keyset"])

    def test_noncanonical_ghana_original_gid_is_quarantined(self):
        report = _inspect(_archive([{"GID_0": "GHA", "GID_2": "GHA1.1_2", "GFA_NR_C": "25"}]))
        self.assertEqual(report["source_rows_without_unique_adm2_key"], 1)
        self.assertFalse(report["complete_unique_region_keyset"])

    def test_gadm_special_z_territories_cannot_be_equated_to_iso3(self):
        report = _inspect(_archive([{"GID_0": "Z01", "GID_2": "Z01.14.1_1",
                                    "GFA_NR_C": "25"}]))
        self.assertEqual(report["non_iso_source_country_rows"], 1)
        self.assertEqual(report["distinct_valid_adm2_keys"], 1)
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "uppercase ISO3"):
            _inspect(_archive(), country="Z01")

    def test_reject_explicit_unreviewed_gfa_total_column(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "total GFA column"):
            _inspect(_archive(headers=["GID_0", "GID_2", "GFA", *GFA_FIELDS]))

    def test_no_automatic_country_coercion_or_empty_scope(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "uppercase ISO3"):
            _inspect(_archive(), country="deu")
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "no ADM2 records"):
            _inspect(_archive(), country="NZL")

    def test_missing_function_structure_field_rejected(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "schema"):
            _inspect(_archive(headers=["GID_0", "GID_2", *GFA_FIELDS[:-1]]))

    def test_unsafe_zip_member_rejected(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "unsafe ZIP"):
            _inspect(_archive(filename="../" + ADM2_MEMBER))

    def test_exact_member_identity_required(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "ADM2 CSV member absent"):
            _inspect(_archive(filename="adm2.csv"))

    def test_bad_numeric_cells_block(self):
        for bad in ("-1", "nan", "inf", "1e309", "abc", ""):
            with self.subTest(value=bad):
                blob = _archive([{"GID_0": "DEU", "GID_2": "DEU.1.1_1",
                                  "GFA_NR_C": bad}])
                with self.assertRaises(MaterialCitiesPreflightError):
                    _inspect(blob)

    def test_invalid_country_code_rejected(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "country code"):
            _inspect(_archive([{"GID_0": "???", "GID_2": "???", "GFA_NR_C": "1"}]))

    def test_row_component_overflow_rejected(self):
        with self.assertRaisesRegex(MaterialCitiesPreflightError, "unrepresentable"):
            _inspect(_archive([{"GID_0": "DEU", "GID_2": "DEU.1.1_1",
                                "GFA_NR_C": "1e308", "GFA_RS_C": "1e308"}]))


if __name__ == "__main__":
    unittest.main()
