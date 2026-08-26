# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


class Project278ManualReceiptWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = Path(".github/workflows/esrm20-project278-manual-receipt.yml")
        cls.text = cls.path.read_text(encoding="utf-8")

    def test_owner_gated_issue_and_marker_are_fixed(self) -> None:
        self.assertIn("github.event.issue.number == 291", self.text)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", self.text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        self.assertIn("oc-eq1-esrm20-project278-manual-receipt-request-v1", self.text)

    def test_execution_uses_package_module_and_exact_trusted_sha(self) -> None:
        self.assertGreaterEqual(
            self.text.count("python -m scripts.run_esrm20_project278_manual_receipt_action"),
            2,
        )
        self.assertNotIn("python scripts/run_esrm20_project278_manual_receipt_action.py", self.text)
        self.assertIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", self.text)
        self.assertIn("persist-credentials: false", self.text)

    def test_dedup_precedes_provider_worker(self) -> None:
        dedup = self.text.index("Prove complete issue-local dedup before provider access")
        worker = self.text.index("Run exact frozen project-278 manual receipt worker")
        self.assertLess(dedup, worker)
        self.assertIn("has_terminal_manual_result", self.text)

    def test_publisher_is_checkoutless_and_refences_live_main(self) -> None:
        publish = self.text.split("publish-manual-receipt:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertIn("contents: read", publish)
        self.assertIn("issues: write", publish)
        lookup = publish.index('LATEST_SHA="$(gh api')
        fence = publish.index('test "$LATEST_SHA" = "$EXECUTION_SHA"')
        post = publish.index('"repos/$GITHUB_REPOSITORY/issues/291/comments"')
        self.assertLess(lookup, fence)
        self.assertLess(fence, post)

    def test_publisher_keeps_science_authority_closed(self) -> None:
        for expression in (
            ".pdf_content_interpreted == false",
            ".crs_coordinate_semantics_verified == false",
            ".generator_invocation_verified == false",
            ".missingness_semantics_verified == false",
            ".site_model_compatibility_verified == false",
            ".external_bytes_persisted == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
        ):
            self.assertIn(expression, self.text)
        self.assertIn('.manual_identity.project_id == 278', self.text)
        self.assertIn('.manual_identity.repository_path == "ExposureReadme.pdf"', self.text)


if __name__ == "__main__":
    unittest.main()
