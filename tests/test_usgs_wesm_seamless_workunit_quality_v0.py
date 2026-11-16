# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only WESM quality status and source-lineage fail-closed regressions."""
from __future__ import annotations

import unittest

from research_runners.usgs_wesm_seamless_workunit_quality_v0 import (
    Blocked, CATEGORIES, SEAMLESS_REASONS, classify_wesm_seamless_workunit,
)


def sample(**kw):
    row = {
        "workunit_id": "example-wu-001",
        "project_id": "example-project-2025",
        "lpc_category": "Meets",
        "sourcedem_category": "Meets",
        "seamless_category": "Meets",
        "seamless_reason": "Meets 3DEP seamless requirements",
    }
    row.update(kw)
    return row


class WESMScienceTests(unittest.TestCase):
    def test_meets_is_only_source_workunit_status_never_model_admission(self):
        out = classify_wesm_seamless_workunit(sample())
        self.assertTrue(out["status_reports_meets"])
        self.assertEqual(out["classification"], "workunit_reports_meets_not_tile_verified")
        for key in (
            "cat_model_input_approved",
            "provider_original_csv_full_hash_verified",
            "provider_original_geopackage_full_hash_verified",
            "workunit_geometry_intersection_with_exact_s1m_tile_verified",
            "tile_specific_lidar_vintage_and_void_fill_verified",
            "original_vertical_accuracy_independently_assessed",
        ):
            self.assertIs(out[key], False)
        self.assertTrue(out["source_is_workunit_not_s1m_pixel"])

    def test_all_official_seamless_categories_covered_with_exact_reasons(self):
        rows = (
            ("Pending publication", "Awaiting final absolute vertical accuracy assessment",
             "Expected to meet", "Expected to meet",
             "pending_final_vertical_accuracy_not_approved"),
            ("Under review", "Pending LPC/source DEM review",
             "Under review", "Under review",
             "source_lineage_under_review_not_approved"),
            ("Meets", "Meets 3DEP seamless requirements",
             "Meets", "Meets",
             "workunit_reports_meets_not_tile_verified"),
            ("Meets with variance", "LPC meets v.1.0 or earlier draft specification",
             "Meets with variance", "Meets",
             "source_variance_requires_independent_review"),
            ("Does not meet", "Source DEM resolution too coarse",
             "Does not meet", "Does not meet",
             "source_workunit_fails_3dep_requirements"),
        )
        self.assertEqual(len(rows), len(SEAMLESS_REASONS))
        for category, reason, lpc, source_dem, quality in rows:
            with self.subTest(category=category):
                out = classify_wesm_seamless_workunit(sample(
                    seamless_category=category, seamless_reason=reason,
                    lpc_category=lpc, sourcedem_category=source_dem,
                ))
                self.assertEqual(out["classification"], quality)
                self.assertIs(out["cat_model_input_approved"], False)
                self.assertEqual(out["variance_or_failure_present"],
                                 category in ("Meets with variance", "Does not meet"))

    def test_all_fail_reasons_are_kept_as_failures(self):
        for reason in SEAMLESS_REASONS["Does not meet"]:
            with self.subTest(reason=reason):
                result = classify_wesm_seamless_workunit(sample(
                    seamless_category="Does not meet", seamless_reason=reason))
                self.assertTrue(result["variance_or_failure_present"])
                self.assertFalse(result["status_reports_meets"])

    def test_unknown_reasons_product_category_and_cross_product_reuse_fail(self):
        bad = (
            ("seamless_category", "Expected to meet"),
            ("seamless_category", "Not applicable"),
            ("seamless_category", "meets"),
            ("seamless_category", ""),
            ("seamless_category", None),
            ("seamless_category", True),
            ("seamless_reason", "LPC does not meet"),
            ("seamless_reason", "Meets 3DEP 1-m requirements"),
            ("seamless_reason", "Meets"),
            ("seamless_reason", None),
            ("lpc_category", "Pending publication"),
            ("lpc_category", None),
            ("sourcedem_category", "Not applicable"),
            ("sourcedem_category", True),
        )
        for key, value in bad:
            with self.subTest(field=key, value=value), self.assertRaises(Blocked):
                classify_wesm_seamless_workunit(sample(**{key: value}))

    def test_upstream_inconsistency_and_premature_meets_are_blocked(self):
        scenarios = (
            {"seamless_category": "Pending publication",
             "seamless_reason": "Awaiting final absolute vertical accuracy assessment"},
            {"lpc_category": "Expected to meet"},
            {"lpc_category": "Under review"},
            {"sourcedem_category": "Expected to meet"},
            {"sourcedem_category": "Does not meet"},
            {"lpc_category": "Meets with variance"},
            {"sourcedem_category": "Meets with variance"},
            {"lpc_category": "Not applicable"},
        )
        for updates in scenarios:
            with self.subTest(scenario=updates), self.assertRaises(Blocked):
                classify_wesm_seamless_workunit(sample(**updates))

    def test_field_integrity_identifiers_and_untrusted_shapes(self):
        for row in (None, "row", [], {}, 1, True):
            with self.subTest(value=repr(row)), self.assertRaises(Blocked):
                classify_wesm_seamless_workunit(row)
        for field in ("workunit_id", "project_id"):
            for value in ("", " ", " ../foreign", "https://example.org",
                          "bad\ncsv", 17, True, None, "x" * 129):
                with self.subTest(field=field, value=value), self.assertRaises(Blocked):
                    classify_wesm_seamless_workunit(sample(**{field: value}))
        for field in sample():
            row = sample()
            row.pop(field)
            with self.subTest(missing=field), self.assertRaises(Blocked):
                classify_wesm_seamless_workunit(row)

    def test_extra_native_columns_do_not_make_source_verified(self):
        row = sample(collect_start="2022-01-01", collect_end="2023-06-01",
                     seamless_status_verified=True,
                     source_tiff="S1M_n0450e1510_20260821.tif")
        out = classify_wesm_seamless_workunit(row)
        self.assertFalse(out["workunit_geometry_intersection_with_exact_s1m_tile_verified"])
        self.assertFalse(out["provider_original_csv_full_hash_verified"])
        self.assertFalse(out["cat_model_input_approved"])


if __name__ == "__main__":
    unittest.main()
