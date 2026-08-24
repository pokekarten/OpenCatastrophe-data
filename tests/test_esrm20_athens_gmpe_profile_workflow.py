# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class AthensGmpeProfileWorkflowTests(unittest.TestCase):
    def test_workflow_is_owner_gated_trusted_main_only(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / ".github/workflows/esrm20-athens-gmpe-profile.yml").read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 285", text)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", text)
        self.assertIn("persist-credentials: false", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("workflow_dispatch:", text)

    def test_workflow_deduplicates_before_fixed_provider_profile(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / ".github/workflows/esrm20-athens-gmpe-profile.yml").read_text(encoding="utf-8")
        dedup = text.index("Deduplicate trusted terminal before provider I/O")
        execute = text.index("Acquire exact bytes and emit bounded structural evidence")
        self.assertLess(dedup, execute)
        self.assertIn("has_terminal_result", text)
        self.assertIn("steps.dedup.outputs.skip != 'true'", text)

    def test_workflow_uses_package_action_and_fixed_authority_ceiling(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / ".github/workflows/esrm20-athens-gmpe-profile.yml").read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count("python -m scripts.run_esrm20_athens_gmpe_profile_action"), 2)
        self.assertIn("041f90d950d6ff84180b2faa11319a42c66c74cc", text)
        self.assertIn("gmpe_logic_tree_5br_shallow_default.xml", text)
        self.assertIn(".gmpe_semantics_verified == false", text)
        self.assertIn(".gmpe_applicability_verified == false", text)
        self.assertIn(".numerical_equivalence_verified == false", text)
        self.assertIn(".publication_authorized == false", text)
        self.assertIn(".model_use_authorized == false", text)


if __name__ == "__main__":
    unittest.main()
