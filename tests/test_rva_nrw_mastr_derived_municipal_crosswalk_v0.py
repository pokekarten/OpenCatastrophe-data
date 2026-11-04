# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for R+V NRW PV source-mismatch privacy and non-admission gates."""
from decimal import Decimal
import copy
import csv
import hashlib
import io
import unittest

from research_runners import rva_nrw_mastr_derived_municipal_crosswalk_v0 as m

HEADERS = [
    "ags", "name", "einheiten_in_betrieb", "gebaeudesolaranlagen",
    "balkonkraftwerke", "freiflaeche", "sonstige", "kwp", "export_datum",
]


def fake_csv(rows=None):
    if rows is None:
        rows = [
            ["05162020", "PRIVATE_SYN_A", "10", "6", "2", "2", "0", "45.80", "2026-10-02"],
            ["09162000", "PRIVATE_SYN_B", "20", "12", "2", "6", "0", "65.25", "2026-10-02"],
        ]
    f = io.StringIO(newline="")
    w = csv.writer(f)
    w.writerow(HEADERS)
    w.writerows(rows)
    return f.getvalue().encode("utf-8")


class NRWMaStRDerivedCrosswalkTests(unittest.TestCase):
    def test_blob_hash_uses_actual_git_blob_prefix_and_NUL(self):
        raw = fake_csv()
        h = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        self.assertEqual(m.git_blob_sha1(raw), h)
        self.assertNotEqual(m.git_blob_sha1(raw), hashlib.sha1(raw).hexdigest())

    def test_small_synthetic_csv_no_location_row_leaks(self):
        got = m.inspect_secondary(fake_csv(), pin_blob=False)
        self.assertEqual(got["source_municipality_count"], 2)
        self.assertEqual(got["nrw_unit_sums"]["einheiten_in_betrieb"], 10)
        self.assertEqual(got["nrw_unit_sums"]["gebaeudesolaranlagen"], 6)
        self.assertEqual(Decimal(got["nrw_all_generation_pv_capacity_kwp"]), Decimal("45.80"))
        # The temporary key set is intentionally private until crosswalk().
        # Only the published receipt may be checked for non-disclosure.
        published = {k: v for k, v in got.items() if k != "nrw_key_set_private_only"}
        self.assertNotIn("PRIVATE_SYN_A", str(published))
        self.assertNotIn("05162020", str(published))
        self.assertEqual(got["nrw_key_set_private_only"], {"05162020"})
        self.assertFalse(got["source_is_federal_original_export"])

    def test_synthetic_is_rejected_by_pinned_git_sha(self):
        with self.assertRaisesRegex(ValueError, "GIT_BLOB_SHA_MISMATCH"):
            m.inspect_secondary(fake_csv(), pin_blob=True)

    def test_duplicate_AGS_blocks(self):
        raw = fake_csv([
            ["05162020", "PRIVATE_SYN_A", "10", "6", "2", "2", "0", "45.8", "2026-10-02"],
            ["05162020", "PRIVATE_SYN_B", "10", "6", "2", "2", "0", "45.8", "2026-10-02"],
        ])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_BAD_FORMAT"):
            m.inspect_secondary(raw, pin_blob=False)

    def test_AGS_truncation_fails_closed(self):
        raw = fake_csv([["5162020", "PRIVATE_SYN_A", "10", "6", "2", "2", "0", "45.8", "2026-10-02"]])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_BAD_FORMAT"):
            m.inspect_secondary(raw, pin_blob=False)

    def test_unknown_PV_count_cannot_be_zero_filled(self):
        raw = fake_csv([["05162020", "PRIVATE_SYN_A", "10", "", "2", "2", "0", "45.8", "2026-10-02"]])
        with self.assertRaisesRegex(ValueError, "NONNEG_INTEGER_REQUIRED"):
            m.inspect_secondary(raw, pin_blob=False)

    def test_power_float_is_decimal_not_kw_vs_kwp_substitution(self):
        self.assertEqual(m.parse_power("12.00"), Decimal("12.00"))
        for invalid in ("NaN", "1,200", "-1", "Infinity", "00.4", ""):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                m.parse_power(invalid)

    def test_nonnegative_active_unit_counts(self):
        self.assertEqual(m.parse_count("0"), 0)
        for invalid in ("", "-1", "1.25", "1e4", "00", "NaN"):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                m.parse_count(invalid)

    def test_missing_required_column_blocks(self):
        raw = fake_csv().replace(b"gebaeudesolaranlagen", b"renamed_category")
        with self.assertRaisesRegex(ValueError, "SCHEMA_MISMATCH"):
            m.inspect_secondary(raw, pin_blob=False)

    def test_bom_utf8_preserves_schema(self):
        raw = bytes([0xef, 0xbb, 0xbf]) + fake_csv()
        self.assertEqual(m.inspect_secondary(raw,pin_blob=False)["source_municipality_count"], 2)

    def test_official_crosswalk_cannot_fabricate_missing_municipalities(self):
        official = {f"05{i:06d}" for i in range(396)}
        secondary = {
            "nrw_key_set_private_only": set(list(sorted(official))[:-1]),
            "secondary_csv_exact_git_blob_sha1": m.THIRD_PARTY_BLOB_SHA1,
            "secondary_csv_full_sha256": "0"*64, "secondary_original_bytes": 1000,
            "nrw_unit_sums": {}, "nrw_all_generation_pv_capacity_kwp": "0",
            "nrw_rows_with_category_count_difference": 0,
        }
        with self.assertRaisesRegex(ValueError, "CROSSWALK_INCOMPLETE"):
            m.crosswalk(secondary, official)

    def test_crosswalk_only_aggregate_counts_no_location_identifiers(self):
        official = {f"05{i:06d}" for i in range(396)}
        secondary = {
            "nrw_key_set_private_only": set(official),
            "secondary_csv_exact_git_blob_sha1": m.THIRD_PARTY_BLOB_SHA1,
            "secondary_csv_full_sha256": "0"*64, "secondary_original_bytes": 1000,
            "nrw_unit_sums": {"gebaeudesolaranlagen": 1},
            "nrw_all_generation_pv_capacity_kwp": "2",
            "nrw_rows_with_category_count_difference": 0,
        }
        out = m.crosswalk(secondary, official)
        self.assertEqual(out["join_exact_AGS_count"], 396)
        self.assertEqual(out["secondary_nrw_reported_active_pv_unit_sums_by_type"]["gebaeudesolaranlagen"], 1)
        self.assertFalse(out["real_RV_installed_covered_pv_units_or_sums_observed"])
        self.assertFalse(out["independent_mastr_primary_xml_verified"])
        self.assertFalse(out["source_rights_model_admission_complete"])
        self.assertNotIn("05000001", str(out))

    def test_outside_NRW_code_does_not_make_fake_NRW_match(self):
        official = {f"05{i:06d}" for i in range(396)}
        alt = set(official)
        alt.pop()
        alt.add("09000001")
        secondary = {"nrw_key_set_private_only": alt}
        with self.assertRaisesRegex(ValueError, "INCOMPLETE"):
            m.crosswalk(secondary, official)


if __name__ == "__main__":
    unittest.main()
