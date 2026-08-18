# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import unittest
from pathlib import Path


WORKFLOW = Path(".github/workflows/esrm20-exposure-v10-tree.yml")


class ExposureTreeWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_request_is_owner_only_issue_282_and_trusted_default_branch(self) -> None:
        for literal in (
            "github.event.issue.number == 282",
            "github.event.comment.user.login == github.event.repository.owner.login",
            "github.event.comment.author_association == 'OWNER'",
            "<!-- oc-eq1-esrm20-exposure-v10-tree-request-v1 -->",
            "ref: ${{ github.event.repository.default_branch }}",
            "persist-credentials: false",
            "--expected-issue 282",
        ):
            self.assertIn(literal, self.text)
        self.assertNotIn("workflow_dispatch:", self.text)

    def test_execution_has_no_caller_selected_provider_surface(self) -> None:
        execute = self.text.split("publish-exposure-tree:", 1)[0]
        self.assertIn("scripts/run_esrm20_exposure_v10_tree_action.py", execute)
        for forbidden in (
            "--url",
            "--project",
            "--ref",
            "--path",
            "--country",
            "--candidate",
        ):
            self.assertNotIn(forbidden, execute)

    def test_privileged_publisher_has_no_checkout_and_refences_values(self) -> None:
        publish = self.text.split("publish-exposure-tree:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertIn("permissions:\n      issues: write", publish)
        for literal in (
            'dataset_id == "efehr.esrm20.risk-inputs.v1.0"',
            'project_id == 269',
            'project_path == "efehr/esrm20"',
            'commit_sha == "05f83bbc9df81d02ee8ddb1801d9d781355ce783"',
            'subtree_path == "Exposure_30arcsec"',
            'startswith("Exposure_30arcsec/")',
            'contains("Kosovo")',
            'endswith(".xml")',
            'test("^[0-9a-f]{40}$")',
            'test("^[0-9a-f]{64}$")',
            "exact_kosovo_exposure_selected == false",
            "value_structural_wiring_verified == false",
            "publication_authorized == false",
            "model_use_authorized == false",
        ):
            self.assertIn(literal, publish)

    def test_every_jq_exact_key_list_is_lexically_canonical(self) -> None:
        publish = self.text.split("publish-exposure-tree:", 1)[1]
        matches = re.findall(r"keys == \[(.*?)\]", publish)
        self.assertGreaterEqual(len(matches), 3)
        for raw in matches:
            fields = re.findall(r'"([a-z0-9_]+)"', raw)
            self.assertGreater(len(fields), 0)
            self.assertEqual(fields, sorted(fields))

    def test_publisher_checks_path_order_uniqueness_and_blocked_shape(self) -> None:
        publish = self.text.split("publish-exposure-tree:", 1)[1]
        for literal in (
            'split("/") | all(. != "" and . != "." and . != "..")',
            "kosovo_named_xml_candidates[].path] | sort",
            "kosovo_named_xml_candidates[].path] | unique | length",
            '.failure_class == "candidate_resolution_failure"',
            ".profile == null",
        ):
            self.assertIn(literal, publish)


if __name__ == "__main__":
    unittest.main()
