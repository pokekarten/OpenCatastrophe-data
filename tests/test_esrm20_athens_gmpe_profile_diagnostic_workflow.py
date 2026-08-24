# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class AthensGmpeProfileDiagnosticWorkflowTests(unittest.TestCase):
    def test_workflow_is_owner_only_trusted_main_and_closed(self):
        text = Path(".github/workflows/esrm20-athens-gmpe-profile-diagnostic.yml").read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 285", text)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn("<!-- oc-eq1-esrm20-athens-gmpe-profile-diagnostic-request-v1 -->", text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", text)
        self.assertIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", text)
        self.assertGreaterEqual(text.count("persist-credentials: false"), 2)
        self.assertIn("issues: read", text)
        self.assertIn("issues: write", text)
        self.assertIn("run_esrm20_athens_gmpe_profile_diagnostic_action", text)
        self.assertIn(".external_bytes_persisted == false", text)
        self.assertIn(".gmpe_semantics_verified == false", text)
        self.assertIn(".gmpe_applicability_verified == false", text)
        self.assertIn(".numerical_equivalence_verified == false", text)
        self.assertIn(".publication_authorized == false", text)
        self.assertIn(".model_use_authorized == false", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("workflow_dispatch:", text)


if __name__ == "__main__":
    unittest.main()
