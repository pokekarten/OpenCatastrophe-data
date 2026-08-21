# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


class Eshm20SiteModelProfileWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "eshm20-site-model-profile.yml"
        ).read_text(encoding="utf-8")

    def test_trigger_is_owner_gated_and_issue_local(self):
        self.assertIn("github.event.issue.number == 281", self.text)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", self.text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        self.assertIn("oc-eq1-eshm20-site-model-profile-request-v1", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertNotIn("workflow_dispatch:", self.text)

    def test_provider_execution_is_exact_trusted_main_and_dedup_precedes_worker(self):
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.text)
        self.assertIn("EXECUTION_SHA=\"$(git rev-parse HEAD)\"", self.text)
        self.assertIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", self.text)
        self.assertGreater(
            self.text.index("Prove complete issue-local dedup before provider access"),
            self.text.index("Checkout exact trusted execution commit"),
        )
        self.assertGreater(
            self.text.index("Run exact frozen ESHM20 site-profile worker"),
            self.text.index("Prove complete issue-local dedup before provider access"),
        )
        self.assertEqual(self.text.count("persist-credentials: false"), 2)

    def test_publisher_is_checkout_free_and_authority_ceiling_is_explicit(self):
        publish = self.text.split("publish-site-profile:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertEqual(publish.count('"repos/$GITHUB_REPOSITORY/issues/281/comments"'), 2)
        self.assertIn(".schema_interpretation_authorized == false", publish)
        self.assertIn(".crs_authorized == false", publish)
        self.assertIn(".site_response_authorized == false", publish)
        self.assertIn(".external_bytes_persisted == false", publish)
        self.assertIn(".publication_authorized == false", publish)
        self.assertIn(".model_use_authorized == false", publish)

    def test_derived_publication_notice_is_fixed_bounded_and_precedes_result(self):
        publish = self.text.split("publish-site-profile:", 1)[1]
        self.assertIn(
            'PUBLICATION_NOTICE_MARKER: "<!-- oc-eq1-eshm20-site-model-profile-publication-notice-v1 -->"',
            publish,
        )
        self.assertIn(
            'ESHM20_ATTRIBUTION: "European Seismic Hazard Model 2020 (ESHM20), EFEHR"',
            publish,
        )
        self.assertIn('ESHM20_LICENSE_ID: "CC-BY-4.0"', publish)
        self.assertIn(
            'ESHM20_LICENSE_URL: "https://creativecommons.org/licenses/by/4.0/"',
            publish,
        )
        self.assertIn(
            'ESHM20_CITATION: "Danciu et al. (2021), EFEHR Technical Report 001 v1.0.0"',
            publish,
        )
        self.assertIn('ESHM20_CITATION_URL: "https://doi.org/10.12686/a15"', publish)
        self.assertIn(
            'DERIVED_PUBLICATION_SCOPE: "bounded-derived-site-profile-action-evidence-only"',
            publish,
        )
        self.assertIn(
            'DERIVED_CHANGE_NOTICE: "Bounded action evidence for an attempted structural profile of the fixed receipt-bound ESHM20 site CSV; provider bytes and rows are not reproduced."',
            publish,
        )
        self.assertIn("Bounded derived action evidence publication authorized: true", publish)
        self.assertIn(
            "Derived action-evidence publication scope: $DERIVED_PUBLICATION_SCOPE",
            publish,
        )
        self.assertIn("Change notice: $DERIVED_CHANGE_NOTICE", publish)
        self.assertIn("Execution SHA: $EXECUTION_SHA", publish)
        self.assertIn(
            "Provider/raw publication authority: false; model-use authority: false.",
            publish,
        )
        self.assertLess(
            publish.index("eshm20-site-profile-publication-notice.json"),
            publish.index("eshm20-site-profile-comment.json"),
        )

    def test_blocked_result_publication_notice_is_status_neutral(self):
        publish = self.text.split("publish-site-profile:", 1)[1]
        self.assertIn(
            '.status == "blocked" and .failure_class == "site_profile_failure" and .profile == null',
            publish,
        )
        self.assertIn("bounded-derived-site-profile-action-evidence-only", publish)
        self.assertIn("for an attempted structural profile", publish)
        self.assertNotIn("bounded-derived-structural-profile-metadata-only", publish)
        self.assertNotIn("Derived structural-profile metadata computed", publish)

    def test_workflow_calls_only_fixed_source_specific_action(self):
        self.assertIn("python scripts/run_eshm20_site_model_profile_action.py", self.text)
        self.assertNotIn("curl ", self.text)
        self.assertNotIn("wget ", self.text)
        self.assertNotIn("http://", self.text)
        self.assertEqual(self.text.count("https://creativecommons.org/licenses/by/4.0/"), 2)
        self.assertEqual(self.text.count("https://doi.org/10.12686/a15"), 2)
        self.assertEqual(self.text.count("https://"), 4)


if __name__ == "__main__":
    unittest.main()
