# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class Group2RuntimeScalarsWorkflowTests(unittest.TestCase):
    def workflow(self) -> str:
        repo_root = Path(__file__).resolve().parents[1]
        return (
            repo_root / ".github" / "workflows" / "esrm20-group2-risk-runtime-scalars.yml"
        ).read_text(encoding="utf-8")

    def test_workflow_is_trusted_main_owner_gated_and_non_persistent(self):
        workflow = self.workflow()
        self.assertIn("github.event.issue.number == 287", workflow)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            workflow,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("--validate-request-only", workflow)
        self.assertIn("has_terminal_result", workflow)
        self.assertIn("--execution-sha \"$EXECUTION_SHA\"", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("actions/upload-artifact", workflow)
        self.assertNotIn("pull_request", workflow)

    def test_runner_uses_group2_package_module_invocation(self):
        workflow = self.workflow()
        module_invocation = (
            "python -m scripts.run_esrm20_group2_risk_runtime_scalars_action"
        )
        self.assertEqual(workflow.count(module_invocation), 2)
        self.assertNotIn(
            "python scripts/run_esrm20_group2_risk_runtime_scalars_action.py",
            workflow,
        )
        self.assertNotIn(
            "python -m scripts.run_esrm20_group1_risk_runtime_scalars_action",
            workflow,
        )

    def test_request_and_result_markers_are_group2_specific(self):
        workflow = self.workflow()
        self.assertIn(
            "<!-- oc-eq1-esrm20-group2-risk-runtime-scalars-request-v1 -->",
            workflow,
        )
        self.assertIn(
            "<!-- oc-eq1-esrm20-group2-risk-runtime-scalars-result-v1 -->",
            workflow,
        )
        self.assertNotIn(
            "<!-- oc-eq1-esrm20-group1-risk-runtime-scalars-request-v1 -->",
            workflow,
        )

    def test_publisher_keeps_science_and_model_authority_false(self):
        workflow = self.workflow()
        for fence in (
            ".raw_config_returned == false",
            ".historical_group_assignment_verified == false",
            ".runtime_compatibility_verified == false",
            ".numerical_loss_reproduction_verified == false",
            ".external_bytes_persisted == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
            ".evidence.runtime_scalars.defaults_inferred == false",
            ".evidence.runtime_scalars.vulnerability_sampling_seed_semantics_verified == false",
        ):
            self.assertIn(fence, workflow)


if __name__ == "__main__":
    unittest.main()
