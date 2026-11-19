# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed offline CROPGRIDS Figshare v9 rights and version regression."""

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_source_access import SourceAccessError, validate_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access" / "fao.cropgrids.2020.figshare-v9.json"


class CropgridsFigshareV9AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_exact_original_article_identity_and_no_execution(self) -> None:
        obj = validate_contract(self.contract)
        self.assertEqual(obj["source_ids"], ["fao.cropgrids.2020.global"])
        self.assertEqual(obj["service_root"], "https://api.figshare.com")
        self.assertEqual(obj["request_contract"]["path_templates"], ["/v2/articles/22491997/versions/9"])
        self.assertEqual(obj["status"], "documented_only")
        self.assertEqual(obj["probe_contract"]["mode"], "none")

    def test_rights_are_not_inferred_from_public_release(self) -> None:
        policy = self.contract["rights_and_policy"]
        self.assertEqual(policy["dataset_rights_status"], "not_reviewed")
        self.assertEqual(policy["api_terms_status"], "separate_unreviewed")
        self.assertEqual(policy["commercial_automation_status"], "unknown")
        self.assertEqual(policy["redistribution_status"], "unknown")
        self.assertEqual(self.contract["implementation_decision"], "document_only")

    def test_cannot_upgrade_rights_without_explicit_review(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["rights_and_policy"]["commercial_automation_status"] = "allowed"
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)

    def test_cannot_run_metadata_probe_before_rights_clearance(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["status"] = "probe_ready"
        changed["probe_contract"].update(
            mode="metadata_get",
            operation="cropgrids_v9_article_metadata",
            expected_evidence=["original response checksum"],
        )
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)


if __name__ == "__main__":
    unittest.main()
