# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: no Hazard Plain provider bytes or network calls."""
from __future__ import annotations

import csv
import hashlib
import io
from unittest import TestCase, mock

from research_runners import hazardplain_202610_county_content_qa_v0 as m


COLUMNS = {
    m.NRI: ["stcofips", "hazard", "eal_total", "eal_b", "exp_b", "afreq", "applicable"],
    m.EAL: ["stcofips", "hazard", "eal_total", "neighbor_median_eal", "outlier"],
    m.NFIP: ["stcofips", "fma_rl", "nfip_rl", "any_category", "insured",
             "single_family_any_category", "as_of_date"],
}
ROWS = {
    m.NRI: [
        ["01001", "flood", "1.3", "1", "150", "0.1", "true"],
        ["01001", "hurricane_wind", "", "0", "500", "0", "false"],
        ["01003", "flood", "-1", "1", "NA", "0.1", "true"],
    ],
    m.EAL: [
        ["01001", "flood", "1.3", "0.3", "true"],
        ["01003", "flood", "-1", "", "false"],
    ],
    m.NFIP: [
        ["01001", "2", "3", "3", "2", "2", "2026-09-30"],
        ["01003", "0", "1", "1", "1", "1", "2026-09-30"],
    ],
}


def blob(path: str, records=None) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(COLUMNS[path])
    writer.writerows(ROWS[path] if records is None else records)
    return output.getvalue().encode("utf-8")


def check(path: str, records=None):
    raw = blob(path, records)
    return m.inspect_county_table(
        path, raw, expected_columns=COLUMNS[path],
        expected_rows=len(ROWS[path] if records is None else records),
        expected_bytes=len(raw), expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


class HazardPlainContentQATests(TestCase):
    def test_nri_content_profile_and_missingness(self):
        report, private = check(m.NRI)
        self.assertEqual(report["rows_verified"], 3)
        self.assertEqual(report["unique_five_digit_county_keys"], 2)
        self.assertEqual(report["distinct_hazard_categories"], 2)
        self.assertEqual(report["county_hazard_pairs"], 3)
        self.assertEqual(report["numeric_field_counts"]["eal_total"]["blank"], 1)
        self.assertEqual(report["numeric_field_counts"]["eal_total"]["negative"], 1)
        self.assertEqual(report["numeric_field_counts"]["eal_total"]["positive"], 1)
        self.assertEqual(report["numeric_field_counts"]["exp_b"]["nonnumeric"], 1)
        self.assertEqual(report["categorical_flag_counts"]["nri_applicable_true"], 2)
        self.assertEqual(report["nri_applicability_vs_eal_status"]["applicable_true__eal_positive"], 1)
        self.assertEqual(report["nri_applicability_vs_eal_status"]["applicable_true__eal_negative"], 1)
        self.assertEqual(report["nri_applicability_vs_eal_status"]["applicable_false__eal_blank"], 1)
        self.assertFalse(report["data_values_or_county_identifiers_emitted"])
        self.assertEqual(len(private["pairs"]), 3)

    def test_repeat_nfip_classes_not_summed(self):
        report, private = check(m.NFIP)
        self.assertEqual(report["unique_five_digit_county_keys"], 2)
        self.assertNotIn("total_properties", report)
        self.assertEqual(report["numeric_field_counts"]["any_category"]["positive"], 2)
        self.assertEqual(report["distinct_source_as_of_labels"], 1)
        self.assertEqual(len(private["fips"]), 2)

    def test_outlier_boolean_distribution_aggregated(self):
        report, _ = check(m.EAL)
        self.assertEqual(report["categorical_flag_counts"]["eal_outlier_true"], 1)
        self.assertEqual(report["categorical_flag_counts"]["eal_outlier_false"], 1)
        self.assertNotIn("01001", str(report))

    def test_duplicate_county_peril_counted(self):
        repeat = [ROWS[m.NRI][0], ROWS[m.NRI][0]]
        report, _ = check(m.NRI, repeat)
        self.assertEqual(report["invalid_or_duplicate_key_counters"]["duplicate_county_peril_key"], 1)

    def test_duplicate_nfip_county_counted(self):
        repeat = [ROWS[m.NFIP][0], ROWS[m.NFIP][0]]
        report, _ = check(m.NFIP, repeat)
        self.assertEqual(report["invalid_or_duplicate_key_counters"]["duplicate_county_key"], 1)

    def test_invalid_fips_not_echoed(self):
        bad = [list(ROWS[m.EAL][0])]
        bad[0][0] = "SECRET-ADDRESS-LOC"
        report, private = check(m.EAL, bad)
        self.assertEqual(report["invalid_or_duplicate_key_counters"]["invalid_five_digit_county_key"], 1)
        self.assertEqual(len(private["fips"]), 0)
        self.assertNotIn("SECRET", str(report))

    def test_negative_nonfinite_and_noninteger_counts(self):
        rows = [
            ["01001", "-1", "2.5", "NaN", "0", "5", "2026-09-30"],
            ["01003", "inf", "2", "1", "0", "5", "2026-09-30"],
        ]
        report, _ = check(m.NFIP, rows)
        self.assertEqual(report["numeric_field_counts"]["fma_rl"]["negative"], 1)
        self.assertEqual(report["numeric_field_counts"]["fma_rl"]["nonfinite"], 1)
        self.assertEqual(report["numeric_field_counts"]["nfip_rl"]["noninteger"], 1)
        self.assertEqual(report["numeric_field_counts"]["any_category"]["nonfinite"], 1)

    def test_nonfinite_float_and_unknown_flag(self):
        rows = [list(ROWS[m.NRI][0])]
        rows[0][2] = "Infinity"
        rows[0][6] = "SENSITIVE-SUPPLIER-VALUE"
        report, _ = check(m.NRI, rows)
        self.assertEqual(report["numeric_field_counts"]["eal_total"]["nonfinite"], 1)
        self.assertEqual(report["categorical_flag_counts"]["nri_applicable_other"], 1)
        self.assertNotIn("SENSITIVE", str(report))

    def test_wrong_exact_hash_blocks_before_quality(self):
        raw = blob(m.NRI)
        with self.assertRaisesRegex(m.OriginalCSVError, "SHA-256"):
            m.inspect_county_table(m.NRI, raw, expected_columns=COLUMNS[m.NRI],
                                   expected_rows=3, expected_bytes=len(raw),
                                   expected_sha256="0" * 64)

    def test_unsupported_table_blocked(self):
        with self.assertRaises(m.CountyQualityError):
            m.inspect_county_table("private.csv", b"", expected_columns=[],
                                   expected_rows=0, expected_bytes=0, expected_sha256="0"*64)

    def test_cross_table_full_synthetic_contract(self):
        fake_files = {
            path: {"table": m.EXPECTED_FILES[path]["table"], "rows": len(ROWS[path]),
                   "bytes": len(blob(path)), "sha256": hashlib.sha256(blob(path)).hexdigest()}
            for path in (m.NRI, m.EAL, m.NFIP)
        }
        fake_tables = {
            fake_files[path]["table"]: {"columns": COLUMNS[path]}
            for path in fake_files
        }
        with mock.patch.object(m, "EXPECTED_FILES", fake_files), \
             mock.patch.object(m, "validate_pinned_manifest", return_value=fake_tables):
            report = m.evaluate_original_quality(
                manifest_fetch=lambda: b"SYNTHETIC",
                data_fetch=lambda path: blob(path),
            )
        self.assertEqual(len(report["tables"]), 3)
        self.assertEqual(report["cross_table_counts"]["outlier_pairs_missing_from_nri_county_hazard"], 0)
        self.assertEqual(report["cross_table_counts"]["nri_counties_not_in_nfip_county_base"], 0)
        self.assertEqual(report["cross_table_counts"]["counties_present_in_all_three_tables"], 2)
        self.assertFalse(report["scientific_independence_established"])
        self.assertFalse(report["rights_reviewed_and_model_admitted"])
        self.assertFalse(report["raw_rows_or_individual_county_keys_emitted"])
        self.assertNotIn("01001", str(report))

    def test_cross_table_source_mismatch_is_diagnostic(self):
        fake_files = {
            path: {"table": m.EXPECTED_FILES[path]["table"], "rows": len(ROWS[path]),
                   "bytes": len(blob(path)), "sha256": hashlib.sha256(blob(path)).hexdigest()}
            for path in (m.NRI, m.EAL, m.NFIP)
        }
        fake_tables = {fake_files[path]["table"]: {"columns": COLUMNS[path]} for path in fake_files}
        altered = [list(x) for x in ROWS[m.EAL]]
        altered[0][0] = "99999"
        with mock.patch.object(m, "EXPECTED_FILES", fake_files), \
             mock.patch.object(m, "validate_pinned_manifest", return_value=fake_tables):
            # Path-specific expected byte/hash is a local synthetic change only.
            changed_raw = blob(m.EAL, altered)
            fake_files[m.EAL] = {**fake_files[m.EAL], "bytes": len(changed_raw),
                                 "sha256": hashlib.sha256(changed_raw).hexdigest()}
            fake_files[m.EAL]["rows"] = len(altered)
            result = m.evaluate_original_quality(
                manifest_fetch=lambda: b"SYNTHETIC",
                data_fetch=lambda path: changed_raw if path == m.EAL else blob(path),
            )
        self.assertEqual(result["cross_table_counts"]["outlier_pairs_missing_from_nri_county_hazard"], 1)
        self.assertEqual(result["cross_table_counts"]["outlier_counties_missing_from_nri_county_base"], 1)

    def test_boolean_semantics_preserve_missing(self):
        self.assertEqual(m._boolean_class(""), "missing")
        self.assertEqual(m._boolean_class("true"), "true")
        self.assertEqual(m._boolean_class("0"), "false")
        self.assertEqual(m._boolean_class("unknown"), "other")

    def test_failure_not_masked_by_nonadmission(self):
        with self.assertRaises(m.OriginalCSVError):
            m.inspect_county_table(m.NFIP, b"no data", expected_columns=COLUMNS[m.NFIP],
                                   expected_rows=1, expected_bytes=7,
                                   expected_sha256="0"*64)
