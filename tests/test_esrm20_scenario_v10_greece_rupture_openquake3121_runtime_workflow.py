# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import unittest
from pathlib import Path


WORKFLOW = Path(
    ".github/workflows/esrm20-scenario-v10-greece-rupture-openquake3121-runtime.yml"
)


class OpenQuake3121RuptureRuntimeWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_trigger_is_owner_issue_comment_only(self):
        self.assertIn("issue_comment:", self.text)
        self.assertIn("github.event.issue.number == 285", self.text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            self.text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        for forbidden in (
            "pull_request:",
            "pull_request_target:",
            "workflow_dispatch:",
            "schedule:",
            "push:",
        ):
            self.assertNotIn(forbidden, self.text)

    def test_request_checks_out_trusted_default_branch_and_exact_execution_sha(self):
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.text)
        self.assertIn(
            "ref: ${{ needs.validate-request.outputs.execution_sha }}", self.text
        )
        self.assertIn("persist-credentials: false", self.text)
        self.assertIn("--validate-request-only", self.text)

    def test_openquake_tag_commit_and_image_are_hard_pinned(self):
        self.assertIn("refs/tags/v3.12.1:refs/tags/v3.12.1", self.text)
        self.assertIn(
            "0bb8441aa202cd6ec075bf2044dd4aaeb26919b9", self.text
        )
        self.assertIn('BASE_IMAGE="openquake/engine:3.12.1"', self.text)
        self.assertIn(
            "grep -Eq '^openquake/engine@sha256:[0-9a-f]{64}$'", self.text
        )

    def test_runtime_is_verified_before_provider_reacquisition(self):
        fetch = self.text.index("Fetch exact model-era OpenQuake v3.12.1 source")
        image = self.text.index("Build observed OQ 3.12.1 execution container")
        preflight = self.text.index("Verify exact runtime before provider access")
        provider = self.text.index("Reacquire exact rupture and run native ingestion")
        self.assertLess(fetch, image)
        self.assertLess(image, preflight)
        self.assertLess(preflight, provider)

    def test_model_era_python_and_checkout_shadow_installed_source(self):
        self.assertIn("--entrypoint /opt/openquake/bin/python", self.text)
        self.assertIn("-e PYTHONPATH=/oq-engine:/workspace", self.text)
        self.assertIn("-e OC_OQ_CHECKOUT_ROOT=/oq-engine", self.text)
        self.assertIn(
            'assert baselib.__version__.startswith("3.12.1")', self.text
        )
        self.assertIn(
            'assert observed == "0bb8441aa202cd6ec075bf2044dd4aaeb26919b9"',
            self.text,
        )

    def test_provider_action_runs_only_inside_observed_container(self):
        self.assertIn("Reacquire exact rupture and run native ingestion", self.text)
        self.assertIn(
            "scripts/run_esrm20_scenario_v10_greece_rupture_"
            "openquake3121_runtime_action.py",
            self.text,
        )
        self.assertIn("--image-digest \"$IMAGE_ID\"", self.text)
        self.assertIn("-v \"$GITHUB_WORKSPACE:/workspace:ro\"", self.text)
        self.assertIn("-v \"$OUTPUT_DIR:/output\"", self.text)

    def test_result_contract_keeps_broader_authority_false(self):
        for field in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "site_gsim_compatibility_established",
            "numerical_hazard_agreement_established",
            "vulnerability_compatibility_established",
            "reference_run_established",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIn(f".{field} == false", self.text)
        self.assertIn('.rupture_class == "BaseRupture"', self.text)
        self.assertIn('.surface_class == "PlanarSurface"', self.text)

    def test_no_provider_bytes_are_uploaded_as_artifacts(self):
        self.assertNotIn("actions/upload-artifact", self.text)

    def test_publisher_has_no_repository_checkout(self):
        publish = self.text.split("  publish-runtime:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertIn("permissions:\n      issues: write", publish)
        self.assertIn(
            "oc-eq1-esrm20-scenario-v10-greece-rupture-oq3121-runtime-result-v1",
            publish,
        )


if __name__ == "__main__":
    unittest.main()
