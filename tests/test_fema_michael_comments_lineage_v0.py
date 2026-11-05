# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, no-network FEMA original-image-lineage aggregate safety checks."""

from __future__ import annotations

import unittest

from research_runners.fema_michael_comments_lineage_v0 import (
    CommentsLineageError, TOKENS, SOURCE_COUNT, original_query_plan,
    reconcile_lineage_counts,
)


def original_cohort_reply() -> dict:
    values = {key: {"count": 0} for key in original_query_plan()}
    values["COMMENTS_non_null"] = {"count": 212}
    return values


class FEMAMichaelOriginalImageryLineageTests(unittest.TestCase):
    def test_fixed_18_aggregate_queries_without_sensitive_fields(self):
        q = original_query_plan()
        self.assertEqual(len(q), 18)
        for key, params in q.items():
            with self.subTest(key=key):
                self.assertEqual(set(params), {
                    "where", "returnCountOnly", "returnGeometry", "f",
                })
                self.assertIn("DIS_NUMBER = 'DR-4399'", params["where"])
                self.assertEqual(params["returnCountOnly"], "true")
                self.assertEqual(params["returnGeometry"], "false")
                self.assertNotIn("returnIdsOnly", params)
                self.assertNotIn("outFields", params)
                self.assertNotIn("geometry", params)
        self.assertEqual(set(q) - {"COMMENTS_non_null", "IMG_DATE_non_null",
                                   "PROD_DATE_non_null"},
                         {"COMMENTS_token_" + x for x in TOKENS})

    def test_original_212_nonnull_comments_all_selected_image_tokens_zero(self):
        report = reconcile_lineage_counts(original_cohort_reply())
        self.assertEqual(report["frozen_source_cohort_count"], SOURCE_COUNT)
        self.assertEqual(report["comment_field_nonnull_count"], 212)
        self.assertEqual(report["imagery_date_nonnull_count"], 0)
        self.assertEqual(report["production_date_nonnull_count"], 0)
        self.assertTrue(all(v == 0 for v in report["image_lineage_keyword_counts"].values()))
        for flag in ("per_feature_comments_requested_or_returned",
                     "missing_image_date_imputed_from_event",
                     "original_assessment_image_identified",
                     "independent_damage_labels_proven", "model_input_admitted"):
            self.assertFalse(report[flag])

    def test_do_not_assume_all_comments_absent_or_keyword_match_proves_lineage(self):
        r = original_cohort_reply()
        r["COMMENTS_token_NOAA"] = {"count": 1}
        q = reconcile_lineage_counts(r)
        self.assertEqual(q["image_lineage_keyword_counts"]["NOAA"], 1)
        self.assertFalse(q["original_assessment_image_identified"])

    def test_fail_closed_on_extra_feature_fields_and_malformed_counts(self):
        for bad in (
            {"count": True}, {"count": 1.0}, {"count": -1},
            {"count": "212"}, {"count": SOURCE_COUNT + 1},
            {"features": []}, {"count": 212, "features": []}, None,
        ):
            with self.subTest(reply=repr(bad)):
                r = original_cohort_reply()
                r["COMMENTS_non_null"] = bad
                with self.assertRaises(CommentsLineageError):
                    reconcile_lineage_counts(r)

    def test_mismatched_parent_or_incomplete_receipt_rejected(self):
        r = original_cohort_reply()
        r["COMMENTS_token_NICB"] = {"count": 213}
        with self.assertRaisesRegex(CommentsLineageError, "exceed"):
            reconcile_lineage_counts(r)
        r = original_cohort_reply()
        r.pop("IMG_DATE_non_null")
        with self.assertRaisesRegex(CommentsLineageError, "all frozen"):
            reconcile_lineage_counts(r)
        r = original_cohort_reply()
        r["source_features"] = [{"OBJECTID": 1}]
        with self.assertRaises(CommentsLineageError):
            reconcile_lineage_counts(r)


if __name__ == "__main__":
    unittest.main()
