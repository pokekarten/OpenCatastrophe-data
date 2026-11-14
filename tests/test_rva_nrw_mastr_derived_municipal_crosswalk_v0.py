# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for R+V NRW PV source-mismatch privacy and non-admission gates."""
from decimal import Decimal
import copy
import csv
import hashlib
import io
import tomllib
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



def from_receipt(r: dict) -> dict:
    counts = r["nrw_public_MaStR_derived_unit_counts"]
    return {
        "secondary_original_sha256": r["secondary_original_sha256"],
        "secondary_original_bytes": r["secondary_original_size_bytes"],
        "secondary_nrw_reported_active_all_pv_capacity_kwp":
            r["nrw_secondary_reported_total_installed_pv_capacity_kwp"],
        "secondary_nrw_reported_active_pv_unit_sums_by_type": {
            "einheiten_in_betrieb": counts["active_solar_generating_units"],
            "gebaeudesolaranlagen": counts["building_solar_units"],
            "balkonkraftwerke": counts["balcony_solar_units"],
            "freiflaeche": counts["ground_mounted_solar_units"],
            "sonstige": counts["other_solar_units"],
        },
        "secondary_nrw_category_nonadditive_municipalities":
            counts["secondary_municipalities_with_nonadditive_category_counts"],
    }


class NRWMaStRDerivedCrosswalkTests(unittest.TestCase):
    def test_real_public_396_AGS_pinned_source_receipt_conserves_registered_units(self):
        r = tomllib.loads(m.RECEIPT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(r["secondary_original_size_bytes"], 2258397)
        self.assertEqual(r["secondary_original_germany_municipalities"], 10759)
        self.assertEqual(r["exact_ags_matches_between_sources"], 396)
        observed = from_receipt(r)
        self.assertTrue(m.assert_saved_aggregate_receipt(observed, receipt=r)[
            "original_git_pinned_secondary_and_state_checksum_receipt_match"
        ])
        self.assertEqual(r["nrw_public_MaStR_derived_unit_counts"]["building_solar_units"], 876684)
        self.assertFalse(r["federal_primary_xml_export_downloaded_and_verified"])
        self.assertFalse(r["insurer_company_actual_pv_exposure_or_value_observed"])

    def test_false_direct_federal_XML_provenance_blocked(self):
        r = tomllib.loads(m.RECEIPT_PATH.read_text(encoding="utf-8"))
        source = from_receipt(r)
        r["federal_primary_xml_export_downloaded_and_verified"] = True
        with self.assertRaisesRegex(ValueError, "FALSELY_PROMOTED"):
            m.assert_saved_aggregate_receipt(source, receipt=r)

    def test_tampered_registered_building_count_blocks(self):
        r = tomllib.loads(m.RECEIPT_PATH.read_text(encoding="utf-8"))
        source = from_receipt(r)
        source["secondary_nrw_reported_active_pv_unit_sums_by_type"]["gebaeudesolaranlagen"] += 1
        with self.assertRaisesRegex(ValueError, "UNIT_CATEGORY_DRIFT"):
            m.assert_saved_aggregate_receipt(source, receipt=r)

    def test_incomparable_PV_overall_capacity_never_admitted_as_roof_saturation(self):
        r = tomllib.loads(m.RECEIPT_PATH.read_text(encoding="utf-8"))
        source = from_receipt(r)
        r["nrw_technical_potential_and_installed_all_pv_denominators_comparable"] = True
        with self.assertRaisesRegex(ValueError, "FALSELY_PROMOTED"):
            m.assert_saved_aggregate_receipt(source, receipt=r)

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
            "source_municipality_count": 10759, "source_field_count": 31,
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
            "source_municipality_count": 10759, "source_field_count": 31,
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
