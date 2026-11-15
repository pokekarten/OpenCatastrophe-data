# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic tests: discovery collision does not equal scientific source admission."""
from __future__ import annotations

import unittest
from scripts.audit_source_overlap_candidates_v0 import (
    OverlapAuditError, audit, url_identity,
)


def source(sid, url):
    return {"candidate_id": sid, "authoritative_url": url}


def manifest(sid, url):
    return {"dataset_id": sid, "canonical_source": url}


class ProposedSourceOverlapTests(unittest.TestCase):
    def test_existing_c3s_manifest_overlaps_ui_tab_alias(self):
        result = audit([
            ("proposed.json", {"entries": [source(
                "copernicus.c3s.european-windstorm-reanalysis",
                "https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis?tab=overview")]})
        ], [], [
            ("original.json", manifest(
                "copernicus.c3s.european-windstorm-reanalysis.v1.0",
                "https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-reanalysis"))
        ])
        self.assertEqual(result["proposal_overlap_findings"], 1)
        self.assertIn("same_provider_product_page", result["findings"][0]["reasons"])
        self.assertEqual(result["findings"][0]["existing_kind"], "manifest")
        self.assertFalse(result["any_source_admitted"])

    def test_eiopa_same_catalogue_page_is_not_automatic_duplicate(self):
        url = "https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en"
        result = audit([("new", {"entries": [source("eiopa.hub", url)]})], [], [
            ("exposure", manifest("eiopa.exposure", url)),
            ("loss", manifest("eiopa.loss", url)),
        ])
        self.assertEqual(result["proposal_overlap_findings"], 2)
        self.assertTrue(result["provider_pages_can_contain_distinct_dataset_products"])
        self.assertTrue(all(not x["automatic_duplicate_decision"] for x in result["findings"]))

    def test_two_parallel_shards_same_id_and_url(self):
        x = audit([("a", {"entries": [source("shared.id", "https://example.org/data")]}),
                   ("b", {"entries": [source("shared.id", "https://example.org/data?tab=overview")]})], [], [])
        self.assertEqual(x["proposal_overlap_findings"], 2)
        self.assertEqual(x["proposed_candidates_with_findings"], 1)
        self.assertEqual(x["findings"][0]["reasons"], ["same_exact_id", "same_provider_product_page"])

    def test_baseline_same_id_but_different_page(self):
        x = audit([("proposal", {"entries": [source("same.id", "https://a.example.org/a")]})],
                  [("baseline", {"entries": [source("same.id", "https://b.example.org/a")]})], [])
        self.assertEqual(x["findings"][0]["reasons"], ["same_exact_id"])
        self.assertEqual(x["findings"][0]["existing_kind"], "discovery")

    def test_query_product_parameters_preserved(self):
        one = url_identity("https://example.org/data?file=loss&tab=overview")
        two = url_identity("https://example.org/data?file=exposure")
        self.assertNotEqual(one, two)
        self.assertEqual(one, "https://example.org/data?file=loss")

    def test_unrelated_entries_clear_and_deterministic(self):
        args = ([("a", {"entries": [source("a", "https://a.example.org")]})],
                [("b", {"entries": [source("b", "https://b.example.org")]})], [])
        self.assertEqual(audit(*args), audit(*args))
        self.assertEqual(audit(*args)["proposal_overlap_findings"], 0)

    def test_invalid_url_empty_proposal_block(self):
        with self.assertRaises(OverlapAuditError):
            audit([], [], [])
        with self.assertRaises(OverlapAuditError):
            audit([("a", {"entries": [source("a", "http://localhost")]})], [], [])


if __name__ == "__main__":
    unittest.main()
