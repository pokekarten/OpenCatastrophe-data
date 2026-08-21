# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class Group1RuntimeScalarsWorkflowTests(unittest.TestCase):
    def test_workflow_is_trusted_main_owner_gated_and_non_persistent(self):
        repo_root = Path(__file__).resolve().parents[1]
        workflow = (
            repo_root / ".github" / "workflows" / "esrm20-group1-risk-runtime-scalars.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("github.event.issue.number == 287", workflow)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", workflow)
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("--validate-request-only", workflow)
        self.assertIn("has_terminal_result", workflow)
        self.assertIn("--execution-sha \"$EXECUTION_SHA\"", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("actions/upload-artifact", workflow)
        self.assertNotIn("pull_request", workflow)

    def test_publisher_keeps_science_and_model_authority_false(self):
        repo_root = Path(__file__).resolve().parents[1]
        workflow = (
            repo_root / ".github" / "workflows" / "esrm20-group1-risk-runtime-scalars.yml"
        ).read_text(encoding="utf-8")
        for fence in (
            ".raw_config_returned == false",
            ".historical_group_assignment_verified == false",
            ".runtime_compatibility_verified == false",
            ".numerical_loss_reproduction_verified == false",
            ".external_bytes_persisted == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
            ".evidence.runtime_scalars.defaults_inferred == false",
        ):
            self.assertIn(fence, workflow)


if __name__ == "__main__":
    unittest.main()
