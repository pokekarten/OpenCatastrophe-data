# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class RuntimeResidentialCsvProfileWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = Path(
            ".github/workflows/esrm20-runtime-residential-csv-profile.yml"
        ).read_text(encoding="utf-8")

    def test_owner_only_issue_comment_trigger_and_trusted_main_fence(self):
        self.assertIn("github.event.issue.number == 282", self.text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            self.text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.text)
        self.assertIn("--validate-request-only", self.text)

    def test_exact_runtime_csv_receipt_identity_is_hard_fenced(self):
        self.assertIn("05f83bbc9df81d02ee8ddb1801d9d781355ce783", self.text)
        self.assertIn("Exposure/OQ_Exposure_Input_Kosovo_Res.csv", self.text)
        self.assertIn(
            "12a20d393c8d677d304263aed96eb05f81098104fd7e3fb0d119aafc336aa00f",
            self.text,
        )
        self.assertIn('"receipt_byte_count":160627', self.text)
        self.assertIn('"receipt_comment_id":5369154884', self.text)

    def test_publisher_has_no_checkout_and_authority_stays_false(self):
        publisher = self.text.split("publish-profile:", 1)[1]
        self.assertNotIn("actions/checkout", publisher)
        for field in (
            "taxonomy_semantics_verified",
            "crs_semantics_verified",
            "value_semantics_verified",
            "project186_equivalence_verified",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIn(f".{field} == false", publisher)

    def test_provider_target_is_not_caller_selectable(self):
        self.assertNotIn("workflow_dispatch", self.text)
        self.assertNotIn("inputs:", self.text)
        self.assertNotIn("curl ", self.text)
        self.assertIn("Checkout trusted default branch", self.text)
        self.assertIn("Checkout exact trusted execution commit", self.text)


if __name__ == "__main__":
    unittest.main()
