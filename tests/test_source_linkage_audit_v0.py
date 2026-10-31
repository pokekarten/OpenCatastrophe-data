# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source linkage hypotheses are discovery only, with no implicit admission."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.source_landscape_contract import load_landscape_shards
from scripts.source_linkage_audit_v0 import RECIPES, build_audit


ROOT = Path(__file__).resolve().parents[1]


class SourceLinkageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = build_audit(load_landscape_shards())

    def test_registry_is_completely_inventoried(self):
        self.assertGreaterEqual(self.audit["source_count"], 145)
        self.assertEqual(len(self.audit["source_inventory"]), self.audit["source_count"])
        self.assertEqual(self.audit["sources_not_admitted"], self.audit["source_count"])
        self.assertEqual(self.audit["source_reviews_not_completed"], self.audit["source_count"])
        self.assertEqual(
            len({x["candidate_id"] for x in self.audit["source_inventory"]}),
            self.audit["source_count"],
        )

    def test_all_links_are_explicit_and_fail_closed(self):
        self.assertEqual(self.audit["linkage_recipe_count"], len(RECIPES))
        all_ids = {x["candidate_id"] for x in self.audit["source_inventory"]}
        for link in self.audit["linkage_hypotheses"]:
            with self.subTest(recipe=link["recipe_id"]):
                self.assertTrue(set(link["source_candidate_ids"]) <= all_ids)
                self.assertTrue(link["validation_only"])
                self.assertFalse(link["automatic_source_join_allowed"])
                self.assertFalse(link["scientific_independence_proven"])
                self.assertFalse(link["model_input_admitted"])
                self.assertTrue(link["required_join_evidence"])
                self.assertTrue(link["prohibited_inferences"])
        self.assertFalse(self.audit["this_report_is_a_model_input_allowlist"])

    def test_lineage_and_privacy_remain_explicit(self):
        links = {x["recipe_id"]: x for x in self.audit["linkage_hypotheses"]}
        self.assertEqual(links["dwd-radklim-catrare"]["relationship"], "shared_lineage")
        self.assertEqual(links["noaa-spc-ncei"]["relationship"], "same_underlying_reporting_lineage")
        self.assertEqual(links["usgs-gfid-original-versus-derived-flood-lineage"]["relationship"], "reused_upstream_records_and_unconfirmed_duplicate_screen")
        self.assertEqual(links["dwd-catrare-2026-threshold-overlap"]["relationship"], "shared_lineage_distinct_detection_thresholds")
        self.assertEqual(links["openfema-nfip-policy-claims"]["relationship"], "aggregate_only_insurance")
        self.assertIn("property", links["nfip-building-context"]["prohibited_inferences"])
        self.assertIn("PAGER", links["usgs-event-products"]["prohibited_inferences"])

    def test_unknown_endpoint_or_duplicate_recipe_fails_closed(self):
        fixture = [{
            "candidate_id": "synthetic.a", "provider": "test",
            "authoritative_url": "https://example.org/a", "categories": ["test"],
            "potential_roles": ["validation"], "spatial_scope": "test", "temporal_scope": "test",
            "access_class_hint": "test", "candidate_status": "evidence_checked",
            "rights_review_status": "not_reviewed", "scientific_review_status": "not_reviewed",
            "admission_status": "not_admitted",
        }]
        shards = ((Path("sources-test.json"), {"entries": fixture}),)
        with self.assertRaisesRegex(ValueError, "unknown source candidate"):
            build_audit(shards, (("bad", ("synthetic.a", "missing.b"), "test", "keys", "proof", "ban"),))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_audit(shards + shards, ())

    def test_deterministic_cli_report_and_independent_source_order(self):
        data = json.dumps(self.audit, sort_keys=True, ensure_ascii=False, allow_nan=False)
        again = build_audit(load_landscape_shards())
        self.assertEqual(data, json.dumps(again, sort_keys=True, ensure_ascii=False, allow_nan=False))
        self.assertEqual(
            [x["candidate_id"] for x in self.audit["source_inventory"]],
            sorted(x["candidate_id"] for x in self.audit["source_inventory"]),
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "audit.json"
            command = [sys.executable, "scripts/source_linkage_audit_v0.py", "--out", str(out)]
            subprocess.run(command, cwd=ROOT, capture_output=True, check=True, timeout=60)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), self.audit)


if __name__ == "__main__":
    unittest.main()
