# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Contract gates for two exact original GHSL BUILT-S/V E2020 objects; offline."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_source_access import validate_path, validate_contract, SourceAccessError
from scripts.structured_public_views import render_structured_markdown
from scripts.verify_ghsl_built_r2023a_native_prefix_v0 import PRODUCTS

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_FILES = {
    "surface": "ec-jrc.ghsl.ghs-built-s.r2023a",
    "volume": "ec-jrc.ghsl.ghs-built-v.r2023a",
}

class GHSLBuiltExactAccessContractsTests(unittest.TestCase):
    def test_exact_source_and_projection(self):
        for kind, source_id in PRODUCT_FILES.items():
            with self.subTest(kind=kind):
                path = ROOT / "access" / (source_id + ".json")
                data = validate_path(path)
                self.assertEqual(data["source_ids"], [PRODUCTS[kind]["source_id"]])
                self.assertEqual(data["access_id"], source_id)
                self.assertEqual(data["status"], "documented_only")
                self.assertEqual(data["implementation_decision"], "document_only")
                self.assertEqual(data["interface_type"], "object_store")
                self.assertEqual(data["service_root"], "https://jrc-ghsl.s3.eu-central-1.amazonaws.com")
                self.assertEqual(len(data["request_contract"]["path_templates"]), 1)
                self.assertIn("/r2023a/4326/30asec/2020/", data["request_contract"]["path_templates"][0])
                self.assertEqual(data["rights_and_policy"]["dataset_rights_status"], "verified")
                self.assertEqual(data["rights_and_policy"]["api_terms_status"], "unknown")
                self.assertEqual(data["rights_and_policy"]["commercial_automation_status"], "unknown")
                self.assertEqual(data["probe_contract"]["mode"], "none")
                self.assertIsNone(data["probe_contract"]["operation"])
                self.assertFalse(data["probe_contract"]["requires_credentials"])
                self.assertIn(PRODUCTS[kind]["prefix_sha256"], data["operational_constraints"]["mutability_notes"])
                self.assertIn(str(PRODUCTS[kind]["native_block_offset"]), data["operational_constraints"]["mutability_notes"])
                self.assertIn(str(PRODUCTS[kind]["native_block_bytes"]), data["operational_constraints"]["mutability_notes"])
                md = path.with_suffix(".md").read_text(encoding="utf-8")
                self.assertEqual(md, render_structured_markdown(path, data, kind="access"))

    def test_fail_closed_on_unauthorized_promotion(self):
        for source_id in PRODUCT_FILES.values():
            original = validate_path(ROOT / "access" / (source_id + ".json"))
            with self.subTest(source_id=source_id):
                modified = deepcopy(original)
                modified["status"] = "probe_ready"
                modified["probe_contract"]["mode"] = "head"
                modified["probe_contract"]["operation"] = "head_fixed_asset"
                modified["probe_contract"]["expected_evidence"] = ["hypothetical only"]
                with self.assertRaisesRegex(SourceAccessError, "rights|API terms|automation"):
                    validate_contract(modified)

    def test_exact_files_not_broad_global_api(self):
        for source_id in PRODUCT_FILES.values():
            data = validate_path(ROOT / "access" / (source_id + ".json"))
            self.assertLess(data["operational_constraints"]["max_sample_bytes"], 600000)
            self.assertNotIn("bulk", data["access_scope"])
            self.assertNotIn("realtime", data["access_scope"])
            self.assertIn("no new HTTP fetch", data["notes"])
            self.assertFalse(data["authentication"]["secret_in_repository"])

if __name__ == "__main__":
    unittest.main()
