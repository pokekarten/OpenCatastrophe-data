# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest

WORKFLOW = Path(".github/workflows/esrm20-runtime-exposure-receipt.yml")


class RuntimeExposureReceiptWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_trigger_is_owner_authored_issue_282_only(self) -> None:
        self.assertIn("github.event.issue.number == 282", self.text)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", self.text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        self.assertIn(
            "<!-- oc-eq1-esrm20-runtime-exposure-receipt-request-v1 -->",
            self.text,
        )
        self.assertNotIn("pull_request_target:", self.text)
        self.assertNotIn("workflow_dispatch:", self.text)

    def test_execution_is_bound_to_trusted_main_then_exact_execution_sha(self) -> None:
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.text)
        self.assertIn("EXECUTION_SHA=\"$(git rev-parse HEAD)\"", self.text)
        self.assertIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", self.text)
        self.assertGreaterEqual(self.text.count("persist-credentials: false"), 2)

    def test_dedup_precedes_provider_worker_and_is_issue_local(self) -> None:
        dedup = self.text.index("Prove complete issue-local dedup before provider access")
        worker = self.text.index("Run exact frozen runtime exposure worker")
        self.assertLess(dedup, worker)
        self.assertIn("has_terminal_result(", self.text)
        self.assertIn("--expected-issue 282", self.text)

    def test_workflow_exposes_no_caller_selected_provider_target(self) -> None:
        for forbidden in (
            "repository_path:",
            "provider_url:",
            "project_id:",
            "commit_sha:",
            "download_url:",
            "archive_url:",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.text)
        self.assertIn("Exposure/OQ_Exposure_Input_Kosovo.xml", self.text)
        self.assertIn("05f83bbc9df81d02ee8ddb1801d9d781355ce783", self.text)

    def test_publisher_has_no_repository_checkout_and_preserves_authority_ceiling(self) -> None:
        publisher = self.text.split("publish-receipt:", 1)[1]
        self.assertNotIn("actions/checkout", publisher)
        for field in (
            ".xml_content_interpreted == false",
            ".exact_kosovo_exposure_selected == false",
            ".value_structural_wiring_verified == false",
            ".external_bytes_persisted == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
        ):
            with self.subTest(field=field):
                self.assertIn(field, publisher)

    def test_result_publication_is_bounded(self) -> None:
        self.assertIn("MAX_TERMINAL_UTF8_BYTES = 20_000", Path(
            "scripts/run_esrm20_runtime_exposure_receipt_action.py"
        ).read_text(encoding="utf-8"))
        self.assertIn("-le 20000", self.text)


if __name__ == "__main__":
    unittest.main()
