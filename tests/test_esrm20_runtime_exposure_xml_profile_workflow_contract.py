# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = Path(".github/workflows/esrm20-runtime-exposure-xml-profile.yml").read_text(encoding="utf-8")

    def test_owner_only_issue_comment_trigger_and_trusted_main_fence(self):
        self.assertIn("github.event.issue.number == 282", self.text)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", self.text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.text)
        self.assertIn("--validate-request-only", self.text)

    def test_exact_receipt_identity_is_hard_fenced(self):
        self.assertIn("05f83bbc9df81d02ee8ddb1801d9d781355ce783", self.text)
        self.assertIn("Exposure/OQ_Exposure_Input_Kosovo.xml", self.text)
        self.assertIn("61be4c534e6bdd1577d15dd289b2c604fde41f00f8f636901634daf2f41bcceb", self.text)
        self.assertIn(".receipt.byte_count == 664", self.text)

    def test_publisher_has_no_checkout_and_authority_stays_false(self):
        publisher = self.text.split("publish-profile:", 1)[1]
        self.assertNotIn("actions/checkout", publisher)
        for field in ("exact_kosovo_exposure_selected", "value_structural_wiring_verified", "external_bytes_persisted", "publication_authorized", "model_use_authorized"):
            self.assertIn(f".{field} == false", publisher)

    def test_no_caller_selectable_provider_target(self):
        self.assertNotIn("workflow_dispatch", self.text)
        self.assertNotIn("inputs:", self.text)
        self.assertNotIn("curl ", self.text)
        self.assertNotIn("repository_path:", self.text)
        self.assertNotIn("project_id:", self.text)


if __name__ == "__main__":
    unittest.main()
