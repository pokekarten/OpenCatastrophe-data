# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/esrm20-greece-exposure-profile.yml")


class GreeceExposureProfileWorkflowTests(unittest.TestCase):
    def test_trigger_is_owner_only_issue_comment_on_exact_control_issue(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 285", text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn(
            "<!-- oc-eq1-esrm20-greece-exposure-profile-request-v1 -->",
            text,
        )
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("workflow_dispatch:", text)

    def test_execution_is_refenced_to_current_default_branch(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertGreaterEqual(
            text.count("ref: ${{ github.event.repository.default_branch }}"),
            2,
        )
        self.assertIn('EXECUTION_SHA="$(git rev-parse HEAD)"', text)
        self.assertIn('--execution-sha "$EXECUTION_SHA"', text)
        self.assertNotIn(
            "ref: ${{ needs.validate-request.outputs.execution_sha }}",
            text,
        )
        self.assertIn(
            "Re-fence privileged checkout to validated main SHA",
            text,
        )
        self.assertIn('test "$(git rev-parse HEAD)" = "$EXECUTION_SHA"', text)
        self.assertIn("persist-credentials: false", text)

    def test_earliest_canonical_request_and_terminal_dedup_precede_provider(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        refence = text.index("Re-fence privileged checkout to validated main SHA")
        guard = text.index(
            "Select earliest canonical trusted request and deduplicate terminal"
        )
        execute = text.index("Run exact frozen Greece exposure-profile worker")
        self.assertLess(refence, guard)
        self.assertLess(guard, execute)
        self.assertIn(
            "CURRENT_REQUEST_COMMENT_ID: ${{ github.event.comment.id }}",
            text,
        )
        self.assertIn(
            "REPOSITORY_OWNER: ${{ github.event.repository.owner.login }}",
            text,
        )
        self.assertIn('comment.get("author_association") != "OWNER"', text)
        self.assertIn("subject.validate_request(", text)
        self.assertIn("winner_comment_id = min(canonical_requests)[1]", text)
        self.assertIn("current_comment_id != winner_comment_id", text)
        self.assertIn(
            "duplicate trusted request is not earliest canonical OWNER request",
            text,
        )
        self.assertIn("subject._parse_trusted_terminal_result(", text)
        self.assertIn("if: steps.dedup.outputs.skip != 'true'", text)

    def test_concurrency_serializes_only_canonical_trusted_requests(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "'trusted-request' || format('noise-{0}', github.event.comment.id)",
            text,
        )
        self.assertIn("cancel-in-progress: false", text)

    def test_action_runs_as_repository_package_module(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        module = "python -m scripts.run_esrm20_greece_exposure_profile_action"
        direct = "python scripts/run_esrm20_greece_exposure_profile_action.py"
        self.assertEqual(text.count(module), 2)
        self.assertNotIn(direct, text)

    def test_publisher_refences_current_main_and_exact_receipt_authority(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}", text)
        self.assertIn(
            'gh api "repos/$GITHUB_REPOSITORY/commits/$DEFAULT_BRANCH" --jq \' .sha\''.replace(" ", ""),
            text.replace(" ", ""),
        )
        self.assertIn('test "$LATEST_SHA" = "$EXECUTION_SHA"', text)
        for required in (
            ".source_issue == 285",
            ".receipt_issue == 285",
            '"project_id":269',
            '"repository_path":"Exposure/OQ_Exposure_Input_Greece.xml"',
            '"receipt_comment_id":5388640521',
            '"byte_count":697',
            '"sha256":"f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556"',
            ".profile.content_profile.source_declarations_profiled == true",
            ".profile.content_profile.raw_xml_returned == false",
            ".profile.content_profile.referenced_dependency_bytes_receipted == false",
            ".referenced_dependency_bytes_receipted == false",
            ".external_bytes_persisted == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
            '"repos/$GITHUB_REPOSITORY/issues/285/comments"',
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_publisher_has_no_repository_checkout(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        publisher = text.split("  publish-exposure-profile:", 1)[1]
        self.assertNotIn("actions/checkout", publisher)
        self.assertIn("contents: read", publisher)
        self.assertIn("issues: write", publisher)

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
