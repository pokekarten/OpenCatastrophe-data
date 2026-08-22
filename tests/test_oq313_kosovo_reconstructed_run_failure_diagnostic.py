# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = Path(
    ".github/workflows/oq313-kosovo-reconstructed-run-failure-diagnostic.yml"
)
PRIMARY_WORKFLOW = Path(".github/workflows/oq313-kosovo-reconstructed-run.yml")


class OQ313KosovoFailureDiagnosticWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.primary_text = PRIMARY_WORKFLOW.read_text(encoding="utf-8")

    def test_trigger_is_bounded_to_exact_primary_workflow_completion(self) -> None:
        text = self.text
        self.assertIn("workflow_run:", text)
        self.assertIn(
            'workflows: ["ESRM20 Kosovo Reconstructed OpenQuake 3.13 Run"]',
            text,
        )
        self.assertIn("types: [completed]", text)
        self.assertIn(
            "name: ESRM20 Kosovo Reconstructed OpenQuake 3.13 Run",
            self.primary_text,
        )

    def test_job_requires_same_repo_issue_comment_and_non_success(self) -> None:
        text = self.text
        self.assertIn(
            "github.event.workflow_run.event == 'issue_comment'",
            text,
        )
        self.assertIn(
            "github.event.workflow_run.head_repository.full_name == github.repository",
            text,
        )
        self.assertIn(
            "github.event.workflow_run.conclusion != 'success'",
            text,
        )
        self.assertIn(
            "failure|cancelled|timed_out|action_required|neutral|skipped|stale|startup_failure",
            text,
        )
        self.assertIn("unexpected workflow conclusion", text)

    def test_source_run_must_prove_canonical_request_validation(self) -> None:
        text = self.text
        self.assertIn("actions: read", text)
        self.assertIn(
            '"repos/$GITHUB_REPOSITORY/actions/runs/$RUN_ID/jobs?filter=latest&per_page=100"',
            text,
        )
        self.assertIn(
            'job.get("name") == "Validate trusted-main Kosovo OQ3.13 request"',
            text,
        )
        self.assertIn(
            'validate[0].get("conclusion") != "success"',
            text,
        )
        self.assertIn(
            'job.get("name") == "Stage exact inputs and execute fixed OQ3.13 adapter"',
            text,
        )
        self.assertIn(
            'raise SystemExit("canonical request validation was not proven successful")',
            text,
        )
        self.assertIn("request_provenance_bound:true", text)
        self.assertIn('request_validation_conclusion:"success"', text)

    def test_diagnostic_is_checkoutless_and_cannot_execute_provider_or_model(self) -> None:
        text = self.text
        for forbidden in (
            "actions/checkout",
            "actions/download-artifact",
            "git clone",
            "docker run",
            "curl ",
            "wget ",
            "openquake ",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("permissions:\n  actions: read", text)
        self.assertIn("permissions:\n      actions: read\n      issues: write", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("pull-requests: write", text)
        self.assertNotIn("actions: write", text)

    def test_diagnostic_metadata_is_typed_and_run_url_is_repository_bounded(self) -> None:
        text = self.text
        self.assertIn("printf '%s' \"$HEAD_SHA\" | grep -Eq '^[0-9a-f]{40}$'", text)
        self.assertIn("printf '%s' \"$RUN_ID\" | grep -Eq '^[1-9][0-9]*$'", text)
        self.assertIn(
            "printf '%s' \"$RUN_ATTEMPT\" | grep -Eq '^[1-9][0-9]*$'",
            text,
        )
        self.assertIn(
            "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/*",
            text,
        )
        self.assertIn("--argjson validation_job_id \"$VALIDATION_JOB_ID\"", text)
        self.assertIn("--argjson execution_job_id \"$EXECUTION_JOB_ID\"", text)

    def test_failure_comment_is_closed_evidence_only(self) -> None:
        text = self.text
        self.assertIn(
            "<!-- oc-eq1-esrm20-kosovo-oq313-workflow-failure-v1 -->",
            text,
        )
        self.assertIn(
            'schema_version:"oc-eq1-esrm20-kosovo-oq313-workflow-failure-v1"',
            text,
        )
        self.assertIn("source_issue:609", text)
        self.assertIn(
            'workflow_name:"ESRM20 Kosovo Reconstructed OpenQuake 3.13 Run"',
            text,
        )
        self.assertIn("execution_sha_known:false", text)
        for field in (
            "provider_outcome_known",
            "openquake_outcome_known",
            "numerical_evidence_returned",
            "external_provider_bytes_persisted",
            "historical_reproduction_verified",
            "scientific_validity_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIn(f"{field}:false", text)
            self.assertIn(f".{field} == false", text)
        self.assertIn(
            '"repos/$GITHUB_REPOSITORY/issues/609/comments"',
            text,
        )


if __name__ == "__main__":
    unittest.main()
