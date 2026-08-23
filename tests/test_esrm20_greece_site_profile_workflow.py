# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/esrm20-greece-site-profile.yml")


class GreeceSiteProfileWorkflowTests(unittest.TestCase):
    def test_trigger_is_owner_only_issue_comment_on_exact_control_issue(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 661", text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn(
            "<!-- oc-eq1-esrm20-greece-site-profile-request-v1 -->",
            text,
        )
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("workflow_dispatch:", text)

    def test_execution_is_fenced_to_checked_out_default_branch_sha(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", text)
        self.assertIn('EXECUTION_SHA="$(git rev-parse HEAD)"', text)
        self.assertIn('--execution-sha "$EXECUTION_SHA"', text)
        self.assertIn(
            "ref: ${{ needs.validate-request.outputs.execution_sha }}",
            text,
        )
        self.assertIn("persist-credentials: false", text)

    def test_dedup_occurs_before_fixed_provider_worker(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        dedup = text.index("Prove complete issue-local dedup before provider access")
        execute = text.index("Run exact frozen Greece site-profile worker")
        self.assertLess(dedup, execute)
        self.assertIn("has_terminal_greece_site_profile_result", text)
        self.assertIn("if: steps.dedup.outputs.skip != 'true'", text)

    def test_action_runs_as_repository_package_module(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        module = "python -m scripts.run_esrm20_greece_site_profile_action"
        direct = "python scripts/run_esrm20_greece_site_profile_action.py"
        self.assertEqual(text.count(module), 2)
        self.assertNotIn(direct, text)

    def test_publisher_rechecks_exact_receipt_identity_and_authority_ceiling(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            ".source_issue == 661",
            ".content_issue == 285",
            ".receipt_issue == 285",
            ".site_identity.project_id == 269",
            '.site_identity.repository_path == "Vs30/Site_model_Greece.xml"',
            ".site_identity.receipt_comment_id == 5388640521",
            ".site_identity.byte_count == 235015",
            '.site_identity.sha256 == "613938c3f9e63fb94490ba4514ef7faf4bf3141b86c33fdd5eb7f21f8c175f85"',
            ".profile.profile.raw_xml_returned == false",
            ".profile.profile.raw_attribute_values_returned == false",
            ".external_bytes_persisted == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
            '"repos/$GITHUB_REPOSITORY/issues/661/comments"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_no_caller_selectable_provider_or_path_input_exists(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for forbidden in (
            "--project",
            "--provider",
            "--host",
            "--path",
            "--ref",
            "--commit",
            "--event",
            "repository_dispatch",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
