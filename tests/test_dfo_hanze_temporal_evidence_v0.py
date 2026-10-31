# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only temporal evidence checks: candidate pairs are never claims."""
from __future__ import annotations

import copy
import unittest

from research_runners.dfo_hanze_temporal_evidence_v0 import (
    TemporalDiagnosticError, summarize_candidate_evidence,
)


def example():
    dfo = {
        "evidence_class": "REPORTED_HISTORICAL_FLOOD_EVENTS_NO_DEPTH_NO_INSURED_LOSS",
        "events": [
            {"dfo_event_id": "5501", "reported_cause_text": "Heavy rain"},
            {"dfo_event_id": "5502", "reported_cause_text": "Flood"},
        ],
    }
    match = {
        "relationship": "SAME_COUNTRY_AND_OVERLAPPING_DATES_ONLY",
        "same_event_confirmed": False,
        "losses_joined": False,
        "dfo_event_id": "5501",
        "hanze_event_id": "99",
        "dfo_interval": ["2023-12-29", "2024-01-05"],
        "hanze_interval": ["2024-01-02", "2024-01-03"],
        "hanze_cause_unharmonized": "Heavy rainfall",
        "hanze_event_type_unharmonized": "River flood",
    }
    match2 = dict(match,
        dfo_event_id="5502", hanze_event_id="100",
        dfo_interval=["2024-01-04", "2024-01-08"],
        hanze_interval=["2024-01-04", "2024-01-04"],
        hanze_cause_unharmonized="flood",
        hanze_event_type_unharmonized="",
    )
    overlap = {
        "evidence_class": "HISTORICAL_FLOOD_EVENT_CANDIDATE_LINKS_ONLY",
        "common_event_identity_proven": False,
        "economic_or_insured_loss_joined": False,
        "model_input_admitted": False,
        "candidate_pair_count": 2,
        "candidate_pairs": [match, match2],
    }
    return overlap, dfo


class DFOHANZETemporalEvidenceTests(unittest.TestCase):
    def test_two_pairs_aggregate_temporal_quality_without_identity(self):
        overlap, dfo = example()
        result = summarize_candidate_evidence(overlap, dfo)
        self.assertEqual(result["candidate_pair_count"], 2)
        self.assertEqual(result["inclusive_temporal_overlap_days"],
                         {"1": 1, "2-3": 1, "4-7": 0, "8+": 0})
        self.assertEqual(result["absolute_start_date_difference_days"],
                         {"0": 1, "1-3": 0, "4-7": 1, "8+": 0})
        self.assertEqual(result["pairs_with_both_cause_texts"], 2)
        self.assertEqual(result["pairs_with_exactly_same_casefolded_cause_text"], 1)
        self.assertEqual(result["pairs_with_hanze_reported_event_type"], 1)
        for flag in ("source_cause_taxonomies_harmonized", "common_flood_event_identity_confirmed",
                     "same_geographic_footprint_confirmed", "source_reporting_independence_confirmed",
                     "provider_rows_or_pair_details_emitted", "economic_or_insured_losses_computed",
                     "model_source_admitted"):
            self.assertFalse(result[flag])
        output = str(result)
        self.assertNotIn("5501", output)
        self.assertNotIn("Heavy rain", output)
        self.assertNotIn("2024-01-04", output)

    def test_missing_cause_is_not_imputed_as_agreement(self):
        overlap, dfo = example()
        dfo["events"][0]["reported_cause_text"] = None
        overlap["candidate_pairs"][0]["hanze_cause_unharmonized"] = ""
        result = summarize_candidate_evidence(overlap, dfo)
        self.assertEqual(result["pairs_with_both_cause_texts"], 1)
        self.assertEqual(result["pairs_with_exactly_same_casefolded_cause_text"], 1)

    def test_nonoverlap_cannot_be_quantified_as_a_candidate(self):
        overlap, dfo = example()
        overlap["candidate_pairs"][0]["hanze_interval"] = ["2024-02-01", "2024-02-02"]
        with self.assertRaisesRegex(TemporalDiagnosticError, "invalid day count"):
            summarize_candidate_evidence(overlap, dfo)

    def test_fail_closed_on_wrong_evidence_stages(self):
        overlap, dfo = example()
        overlap["common_event_identity_proven"] = True
        with self.assertRaisesRegex(TemporalDiagnosticError, "wrong upstream evidence"):
            summarize_candidate_evidence(overlap, dfo)
        overlap, dfo = example()
        overlap["candidate_pairs"][0]["same_event_confirmed"] = True
        with self.assertRaisesRegex(TemporalDiagnosticError, "unsupported identity"):
            summarize_candidate_evidence(overlap, dfo)
        overlap, dfo = example()
        overlap["candidate_pair_count"] = 3
        with self.assertRaisesRegex(TemporalDiagnosticError, "candidate count"):
            summarize_candidate_evidence(overlap, dfo)

    def test_reject_unknown_ids_duplicated_pairs_or_bad_intervals(self):
        overlap, dfo = example()
        overlap["candidate_pairs"][0]["dfo_event_id"] = "unknown"
        with self.assertRaisesRegex(TemporalDiagnosticError, "unrecognized"):
            summarize_candidate_evidence(overlap, dfo)
        overlap, dfo = example()
        overlap["candidate_pairs"][1]["dfo_event_id"] = "5501"
        overlap["candidate_pairs"][1]["hanze_event_id"] = "99"
        with self.assertRaisesRegex(TemporalDiagnosticError, "duplicate"):
            summarize_candidate_evidence(overlap, dfo)
        overlap, dfo = example()
        overlap["candidate_pairs"][0]["dfo_interval"] = ["2024-01-10", "2024-01-01"]
        with self.assertRaisesRegex(TemporalDiagnosticError, "reversed"):
            summarize_candidate_evidence(overlap, dfo)

    def test_empty_candidate_set_means_no_matches_not_no_disaster(self):
        overlap, dfo = example()
        overlap["candidate_pairs"] = []
        overlap["candidate_pair_count"] = 0
        result = summarize_candidate_evidence(overlap, dfo)
        self.assertEqual(result["candidate_pair_count"], 0)
        self.assertEqual(sum(result["inclusive_temporal_overlap_days"].values()), 0)
        self.assertFalse(result["common_flood_event_identity_confirmed"])


if __name__ == "__main__":
    unittest.main()
