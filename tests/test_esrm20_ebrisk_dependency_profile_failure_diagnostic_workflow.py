# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(
    ".github/workflows/esrm20-ebrisk-dependency-profile-failure-diagnostic.yml"
)
RESULT_WORKFLOW_NAME = "ESRM20 EBRISK Risk Config Dependency Profiles"
DIAGNOSTIC_MARKER = (
    "<!-- oc-eq1-esrm20-ebrisk-risk-config-dependency-profiles-workflow-failure-v1 -->"
)


class EbriskDependencyProfileFailureDiagnosticWorkflowTests(unittest.TestCase):
    def test_observes_only_completed_target_workflow_runs(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        trigger = text.split("on:", 1)[1].split("permissions:", 1)[0]
        self.assertIn("workflow_run:", trigger)
        self.assertIn(f'workflows: ["{RESULT_WORKFLOW_NAME}"]', trigger)
        self.assertIn("types: [completed]", trigger)
        self.assertNotIn("issue_comment:", trigger)

    def test_failure_job_is_checkoutless_and_never_executes_provider(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        job = text.split("publish-failure-diagnostic:", 1)[1]
        self.assertIn("github.event.workflow_run.event == 'issue_comment'", job)
        self.assertIn("github.event.workflow_run.head_repository.full_name == github.repository", job)
        self.assertNotIn("github.event.workflow_run.conclusion != 'success'", job)
        for conclusion in (
            "failure",
            "cancelled",
            "timed_out",
            "action_required",
            "stale",
            "startup_failure",
        ):
            self.assertIn(
                f"github.event.workflow_run.conclusion == '{conclusion}'", job
            )
        self.assertNotIn("github.event.workflow_run.conclusion == 'skipped'", job)
        self.assertNotIn("github.event.workflow_run.conclusion == 'neutral'", job)
        self.assertIn("issues: write", job)
        self.assertNotIn("actions/checkout", job)
        self.assertNotIn("urllib", job)
        self.assertNotIn("curl ", job)
        self.assertNotIn("wget ", job)

    def test_published_diagnostic_is_closed_and_non_scientific(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(DIAGNOSTIC_MARKER, text)
        self.assertIn("workflow_run_id", text)
        self.assertIn("workflow_run_attempt", text)
        self.assertIn("workflow_head_sha", text)
        self.assertIn("provider_outcome_known:false", text)
        self.assertIn("dependency_evidence_returned:false", text)
        self.assertIn("external_bytes_persisted:false", text)
        self.assertIn("publication_authorized:false", text)
        self.assertIn("model_use_authorized:false", text)
        self.assertIn(
            "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/", text
        )


if __name__ == "__main__":
    unittest.main()
