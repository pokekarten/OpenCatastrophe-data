# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/esrm20-greece-exposure-csv-profiles.yml")


class GreeceExposureCsvProfilesWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_trigger_is_owner_issue_comment_on_canonical_issue(self) -> None:
        self.assertIn("issue_comment:", self.text)
        self.assertIn("github.event.issue.number == 285", self.text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            self.text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        self.assertIn(
            "oc-eq1-esrm20-greece-exposure-csv-profiles-request-v1",
            self.text,
        )
        self.assertNotIn("pull_request:", self.text)
        self.assertNotIn("workflow_dispatch:", self.text)

    def test_concurrency_isolates_trusted_requests_from_noise(self) -> None:
        concurrency = self.text[
            self.text.index("concurrency:") : self.text.index("\njobs:")
        ]
        self.assertIn("github.event.issue.number == 285", concurrency)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            concurrency,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", concurrency)
        self.assertIn(
            "oc-eq1-esrm20-greece-exposure-csv-profiles-request-v1",
            concurrency,
        )
        self.assertIn("&& 'trusted-request' ||", concurrency)
        self.assertIn("format('noise-{0}', github.event.comment.id)", concurrency)
        self.assertNotIn(
            "group: esrm20-greece-exposure-csv-profiles-${{ github.repository }}\n",
            concurrency,
        )

    def test_provider_execution_is_bound_to_trusted_default_branch(self) -> None:
        self.assertIn("Checkout trusted default branch", self.text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.text)
        self.assertIn('EXECUTION_SHA="$(git rev-parse HEAD)"', self.text)
        self.assertIn("Checkout exact trusted execution commit", self.text)
        self.assertIn(
            "ref: ${{ needs.validate-request.outputs.execution_sha }}",
            self.text,
        )
        self.assertGreaterEqual(self.text.count("persist-credentials: false"), 2)

    def test_dedup_precedes_all_provider_io(self) -> None:
        dedup = self.text.index("Deduplicate trusted terminal before provider I/O")
        acquire = self.text.index("Acquire exact three CSVs and run merged bounded profiler")
        self.assertLess(dedup, acquire)
        self.assertIn("has_terminal_result(", self.text)
        self.assertIn("steps.dedup.outputs.skip != 'true'", self.text)

    def test_publisher_refences_current_main_without_checkout(self) -> None:
        publish = self.text.index("publish-profile:")
        publisher = self.text[publish:]
        self.assertIn("Re-fence result and publish without checkout", publisher)
        self.assertIn("commits/$DEFAULT_BRANCH", publisher)
        self.assertIn('test "$LATEST_SHA" = "$EXECUTION_SHA"', publisher)
        self.assertNotIn("actions/checkout@", publisher)
        self.assertIn("issues/285/comments", publisher)

    def test_workflow_is_exact_three_receipt_bound(self) -> None:
        frozen = (
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
            "5397480571",
            "4b1d3c41a5df739b9686303eb753577ca39ec58e",
            "Exposure/OQ_Exposure_Input_Greece_Com.csv",
            "7672810",
            "2281f079a6e0b2215fab696d442f9d98b9b0ba94a2b4b24f23f1fff4018d1b57",
            "Exposure/OQ_Exposure_Input_Greece_Ind.csv",
            "2822653",
            "ad6698199d84002d017b41668dc204a2d53835a4b2429bc7e8eea56b328549c7",
            "Exposure/OQ_Exposure_Input_Greece_Res.csv",
            "5263604",
            "928ac7f069dfc3181a936f73caafb951a5c2437f70379fa29518c002bbd3ef28",
        )
        for value in frozen:
            with self.subTest(value=value):
                self.assertIn(value, self.text)

    def test_publisher_requires_nested_nonleaking_profiles(self) -> None:
        for condition in (
            ".profile.files[0].repository_path",
            ".profile.files[1].repository_path",
            ".profile.files[2].repository_path",
            ".profile.raw_rows_returned == false",
            ".profile.external_bytes_persisted == false",
            ".profile.publication_authorized == false",
            ".profile.exact_field_values_returned == false",
        ):
            with self.subTest(condition=condition):
                self.assertIn(condition, self.text)

    def test_publisher_keeps_scientific_authority_fail_closed(self) -> None:
        for condition in (
            ".content_semantics_verified == false",
            ".crs_semantics_verified == false",
            ".taxonomy_semantics_verified == false",
            ".replacement_cost_semantics_verified == false",
            ".vulnerability_imt_selection_verified == false",
            ".benchmark_agreement_inspected == false",
            ".independent_validation_established == false",
            ".holdout_status_established == false",
            ".external_bytes_persisted == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
        ):
            with self.subTest(condition=condition):
                self.assertIn(condition, self.text)


if __name__ == "__main__":
    unittest.main()
