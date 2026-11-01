# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No CAT source register access/linkage projection can silently grant authority."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from scripts.build_cat_source_crosswalk_v0 import CrosswalkError, build_crosswalk
from scripts.build_source_access_inventory import build_inventory
from scripts.source_landscape_contract import load_landscape_shards
from scripts.source_linkage_audit_v0 import build_audit


def fixture():
    access = {
        "entry_count": 3,
        "landscape_entry_count": 2,
        "manifest_entry_count": 1,
        "entries": [
            {"source_id": "synthetic.a", "record_type": "landscape_candidate",
             "source_registry_path": "landscape/sources-synthetic.json",
             "contract_ids": ["a.get"], "contract_statuses": ["probe_ready"],
             "operational_readiness": "bounded_probe_defined_not_executed",
             "next_action": "Review exact source access"},
            {"source_id": "synthetic.b", "record_type": "landscape_candidate",
             "source_registry_path": "landscape/sources-synthetic.json",
             "contract_ids": [], "contract_statuses": [],
             "operational_readiness": "no_concrete_access_contract",
             "next_action": "Study source access"},
            {"source_id": "synthetic.a", "record_type": "admitted_manifest",
             "source_registry_path": "manifests/synthetic.a.json",
             "contract_ids": [], "operational_readiness": "unknown",
             "next_action": "Study exact model role"},
        ],
    }
    def source(i):
        return {
            "candidate_id": i, "provider": "Synthetic Example", 
            "authoritative_url": "https://example.org/provider",
            "spatial_scope": "synthetic", "temporal_scope": "synthetic",
            "categories": ["flood"], "potential_roles": ["validation"],
            "admission_status": "not_admitted",
            "automated_model_import_allowed_by_this_audit": False,
        }
    links = {
        "source_count": 2, "source_inventory": [source("synthetic.a"), source("synthetic.b")],
        "linkage_recipe_count": 1, "this_report_is_a_model_input_allowlist": False,
        "linkage_hypotheses": [{
            "recipe_id": "synthetic-link", "source_candidate_ids": ["synthetic.a", "synthetic.b"],
            "relationship": "shared_lineage",
            "required_join_evidence": "shared raw bytes hash",
            "unverified_prerequisites": "raw bytes unavailable",
            "prohibited_inferences": "do not claim independent validation",
            "validation_only": True, "automatic_source_join_allowed": False,
            "scientific_independence_proven": False, "model_input_admitted": False,
        }],
    }
    return access, links


class CATCrosswalkTests(unittest.TestCase):
    def test_synthetic_access_and_manifest_are_not_merged(self):
        a, l = fixture()
        report = build_crosswalk(a, l)
        self.assertEqual(report["candidate_count"], 2)
        self.assertEqual(report["manifest_count"], 1)
        self.assertEqual(report["candidate_with_access_contract_count"], 1)
        self.assertEqual(report["candidate_without_access_contract_count"], 1)
        self.assertEqual(report["candidate_with_manual_link_hypothesis_count"], 2)
        self.assertFalse(report["new_rights_or_admission_granted"])
        self.assertFalse(report["permission_for_automated_source_join"])
        self.assertFalse(report["this_report_is_a_model_input_allowlist"])
        first, second = report["candidates"]
        self.assertEqual(first["source_id"], "synthetic.a")
        self.assertEqual(first["access_contract_ids"], ["a.get"])
        self.assertEqual(first["candidate_join_hypotheses"][0]["other_source_ids"], ["synthetic.b"])
        self.assertFalse(first["scientific_independence_proven"])
        self.assertFalse(second["scientific_independence_proven"])
        self.assertEqual(report["existing_manifests_separate"][0]["dataset_id"], "synthetic.a")
        self.assertFalse(report["existing_manifests_separate"][0]["any_additional_model_authority_granted"])

    def test_no_explicit_link_is_not_independent_validation(self):
        a, l = fixture()
        l["linkage_hypotheses"] = []
        l["linkage_recipe_count"] = 0
        r = build_crosswalk(a, l)
        for row in r["candidates"]:
            self.assertFalse(row["manual_lineage_review_required"])
            self.assertFalse(row["scientific_independence_proven"])
            self.assertEqual(row["candidate_join_hypotheses"], [])

    def test_discovery_access_mismatch_rejected(self):
        a, l = fixture()
        l["source_inventory"].pop()
        l["source_count"] -= 1
        with self.assertRaisesRegex(CrosswalkError, "discovery/access inventories disagree"):
            build_crosswalk(a, l)

    def test_authority_uplift_rejected(self):
        a, l = fixture()
        l["linkage_hypotheses"][0]["automatic_source_join_allowed"] = True
        with self.assertRaisesRegex(CrosswalkError, "non-admission boundary"):
            build_crosswalk(a, l)
        a, l = fixture()
        l["source_inventory"][0]["automated_model_import_allowed_by_this_audit"] = True
        with self.assertRaisesRegex(CrosswalkError, "cannot grant model admission"):
            build_crosswalk(a, l)

    def test_duplicate_and_unknown_recipe_endpoint_rejected(self):
        a, l = fixture()
        l["linkage_hypotheses"][0]["source_candidate_ids"] = ["synthetic.a", "synthetic.c"]
        with self.assertRaisesRegex(CrosswalkError, "malformed"):
            build_crosswalk(a, l)
        a, l = fixture()
        a["entries"][0]["contract_ids"] = ["a.get", "a.get"]
        with self.assertRaisesRegex(CrosswalkError, "ambiguous"):
            build_crosswalk(a, l)

    def test_full_current_repository_crosswalk_and_cli_summary(self):
        report = build_crosswalk(build_inventory(), build_audit(load_landscape_shards()))
        self.assertEqual(report["candidate_count"], len(report["candidates"]))
        self.assertEqual(report["manifest_count"], len(report["existing_manifests_separate"]))
        self.assertGreaterEqual(report["candidate_count"], 263)
        self.assertGreaterEqual(report["manual_linkage_recipe_count"], 20)
        self.assertEqual(
            report["candidate_with_access_contract_count"]
            + report["candidate_without_access_contract_count"],
            report["candidate_count"],
        )
        self.assertEqual(
            len({row["source_id"] for row in report["candidates"]}),
            report["candidate_count"],
        )
        self.assertFalse(any(row["scientific_join_verified_by_this_report"] for row in report["candidates"]))
        self.assertFalse(any(row["model_input_admitted_by_this_report"] for row in report["candidates"]))
        cmd = [sys.executable, "scripts/build_cat_source_crosswalk_v0.py", "--summary"]
        run = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=40)
        compact = json.loads(run.stdout)
        self.assertEqual(compact["candidate_count"], report["candidate_count"])
        self.assertEqual(compact["manual_linkage_recipe_count"], report["manual_linkage_recipe_count"])
        self.assertNotIn("candidates", compact)
        self.assertNotIn("existing_manifests_separate", compact)


if __name__ == "__main__":
    unittest.main()
