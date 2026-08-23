# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "esrm20-athens-local-receipts.yml"
)


class AthensLocalWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_provider_execution_is_issue_comment_only_and_owner_gated(self):
        self.assertIn("issue_comment:", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertIn("github.event.issue.number == 658", self.text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        self.assertIn(
            "<!-- oc-eq1-esrm20-athens-local-receipts-request-v1 -->",
            self.text,
        )

    def test_execution_checks_out_only_trusted_default_branch(self):
        self.assertIn("Checkout trusted default branch", self.text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.text)
        self.assertIn("persist-credentials: false", self.text)
        self.assertIn(
            "python -m scripts.run_efehr_esrm20_athens_local_receipts_action",
            self.text,
        )
        self.assertNotIn(
            "python scripts/run_efehr_esrm20_athens_local_receipts_action.py",
            self.text,
        )
        self.assertIn("--expected-issue 658", self.text)

    def test_publisher_has_no_checkout_and_refences_execution_sha(self):
        publisher = self.text.split("publish-athens-local-receipts:", 1)[1]
        self.assertNotIn("actions/checkout", publisher)
        self.assertIn('test "$LATEST_SHA" = "$EXECUTION_SHA"', publisher)
        self.assertIn(".target_sha == $sha and .execution_sha == $sha", publisher)

    def test_publisher_fixes_all_four_paths_and_false_authority(self):
        for path in (
            "ruptures/source_models/rupture_Greece_07-9-1999.xml",
            "ruptures/ground-motion-models/gmpe_logic_tree_5br_shallow_default.xml",
            "ruptures/vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
            "ruptures/vulnerability/vulnerability_loss-of-life_ESRM20_VariousIM_day.xml",
        ):
            self.assertIn(path, self.text)
        for assertion in (
            ".content_semantics_verified == false",
            ".benchmark_agreement_inspected == false",
            ".independent_validation_established == false",
            ".holdout_status_established == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
        ):
            self.assertIn(assertion, self.text)


if __name__ == "__main__":
    unittest.main()
