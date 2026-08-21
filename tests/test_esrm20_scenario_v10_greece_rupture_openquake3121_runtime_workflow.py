# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class GreeceRuptureOpenQuake3121RuntimeWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        repo_root = Path(__file__).resolve().parents[1]
        cls.workflow = (
            repo_root
            / ".github"
            / "workflows"
            / "esrm20-scenario-v10-greece-rupture-openquake3121-runtime.yml"
        ).read_text(encoding="utf-8")

    def test_only_owner_issue_comment_can_enter_trusted_main_lane(self):
        workflow = self.workflow
        self.assertIn("issue_comment:", workflow)
        self.assertIn("github.event.issue.number == 285", workflow)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            workflow,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertNotIn("workflow_dispatch:", workflow)

    def test_exact_openquake_3121_tag_commit_and_container_are_fenced(self):
        workflow = self.workflow
        self.assertIn("refs/tags/v3.12.1:refs/tags/v3.12.1", workflow)
        self.assertIn("0bb8441aa202cd6ec075bf2044dd4aaeb26919b9", workflow)
        self.assertIn('BASE_IMAGE="openquake/engine:3.12.1"', workflow)
        self.assertIn("COPY --chown=root:root oq-engine /oq-engine", workflow)
        self.assertIn("RUN git config --system --add safe.directory /oq-engine", workflow)
        self.assertIn("USER openquake", workflow)
        self.assertIn("--entrypoint /opt/openquake/bin/python", workflow)
        self.assertIn("PYTHONPATH=/oq-engine:/workspace", workflow)

    def test_dedup_and_runtime_identity_precede_provider_execution(self):
        workflow = self.workflow
        dedup = workflow.index("Prove complete issue-local dedup before external activity")
        source = workflow.index("Fetch exact OpenQuake v3.12.1 source")
        execute = workflow.index("Run exact-byte native rupture acceptance gate")
        self.assertLess(dedup, source)
        self.assertLess(source, execute)
        self.assertIn(
            "scripts/run_esrm20_scenario_v10_greece_rupture_openquake3121_runtime_action.py",
            workflow,
        )

    def test_publisher_is_checkout_free_and_rejects_authority_promotion(self):
        workflow = self.workflow
        publisher = workflow.split("publish-native-runtime:", 1)[1]
        self.assertNotIn("actions/checkout@", publisher)
        self.assertIn(".historical_environment_verified == false", publisher)
        self.assertIn(".site_model_compatibility_verified == false", publisher)
        self.assertIn(".gsim_compatibility_verified == false", publisher)
        self.assertIn(".numerical_hazard_agreement_verified == false", publisher)
        self.assertIn(".vulnerability_compatibility_verified == false", publisher)
        self.assertIn(".reference_run_verified == false", publisher)
        self.assertIn(".independent_validation_established == false", publisher)
        self.assertIn(".publication_authorized == false", publisher)
        self.assertIn(".model_use_authorized == false", publisher)

    def test_no_arbitrary_provider_or_runtime_selector_is_exposed(self):
        workflow = self.workflow
        self.assertNotIn("workflow_dispatch", workflow)
        self.assertNotIn("inputs:", workflow)
        self.assertNotIn("curl ", workflow)
        self.assertNotIn("wget ", workflow)
        self.assertNotIn("repository_path=", workflow)
        self.assertNotIn("project_id=", workflow)


if __name__ == "__main__":
    unittest.main()
