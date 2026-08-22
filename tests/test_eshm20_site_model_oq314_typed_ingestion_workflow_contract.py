# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


class TypedSiteIngestionWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "eshm20-site-model-oq314-typed-ingestion.yml"
        ).read_text(encoding="utf-8")

    def test_trigger_is_owner_gated_issue_local_and_not_pr_executable(self):
        self.assertIn("github.event.issue.number == 281", self.text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            self.text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", self.text)
        self.assertIn("oc-eq1-eshm20-site-oq314-typed-ingestion-request-v1", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertNotIn("workflow_dispatch:", self.text)

    def test_dedup_precedes_all_openquake_and_provider_external_access(self):
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.text)
        self.assertIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", self.text)
        dedup = self.text.index("Prove complete issue-local dedup before any external access")
        fetch_oq = self.text.index("Fetch exact OpenQuake v3.14.0 source")
        run_site = self.text.index("Run exact receipt-bound site CSV through OQ3.14 parser")
        self.assertLess(dedup, fetch_oq)
        self.assertLess(fetch_oq, run_site)
        self.assertEqual(self.text.count("persist-credentials: false"), 2)

    def test_openquake_runtime_is_exact_source_and_observed_bootstrap_digest(self):
        self.assertIn(
            "OQ_COMMIT: 9f044c93d72846421a8faa90ebf0a6afacdf3c20",
            self.text,
        )
        self.assertIn("refs/tags/v3.14.0:refs/tags/v3.14.0", self.text)
        self.assertIn("test \"$OBSERVED\" = \"$OQ_COMMIT\"", self.text)
        self.assertIn("BASE_IMAGE=\"openquake/engine:3.14.0\"", self.text)
        self.assertIn("BASE_REPO_DIGEST", self.text)
        self.assertIn("FROM $BASE_REPO_DIGEST", self.text)
        self.assertIn("-e OPENBLAS_NUM_THREADS=1", self.text)
        self.assertIn("-e PYTHONPATH=/oq-engine:/workspace", self.text)
        self.assertIn("--entrypoint /opt/openquake/bin/python", self.text)

    def test_execution_calls_only_fixed_action_and_persists_no_provider_bytes(self):
        self.assertIn(
            "python scripts/run_eshm20_site_model_oq314_typed_ingestion_action.py",
            self.text,
        )
        self.assertNotIn("curl ", self.text)
        self.assertNotIn("wget ", self.text)
        self.assertNotIn("workflow_dispatch", self.text)
        self.assertNotIn("actions/upload-artifact", self.text)
        self.assertNotIn("actions/cache", self.text)

    def test_publisher_is_checkout_free_and_exact_identity_fenced(self):
        publish = self.text.split("publish-typed-ingestion:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertEqual(
            publish.count('"repos/$GITHUB_REPOSITORY/issues/281/comments"'), 2
        )
        self.assertIn(".source_profile_result_comment_id == 5376038471", publish)
        self.assertIn(".source_semantics_handoff_comment_id == 5376088705", publish)
        self.assertIn(
            '.source_identity.commit_sha == "fbd334de68f85d72669f73fc5a314a113db67317"',
            publish,
        )
        self.assertIn(
            '.source_identity.sha256 == "d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529"',
            publish,
        )
        self.assertIn(
            '.openquake_reference.commit == "9f044c93d72846421a8faa90ebf0a6afacdf3c20"',
            publish,
        )

    def test_pass_and_blocked_states_keep_scientific_authority_ceiling_closed(self):
        publish = self.text.split("publish-typed-ingestion:", 1)[1]
        self.assertIn(".bounded_dtype_value_and_observed_support_verified == true", publish)
        self.assertNotIn(".mode_a_required_field_dtype_domain_verified", publish)
        self.assertIn(".typed_ingestion.raw_values_returned == false", publish)
        self.assertIn(".failure_class == \"typed_site_ingestion_rejected\"", publish)
        for expression in (
            ".historical_environment_verified == false",
            ".reference_base_image_byte_identity_verified == false",
            ".wheel_byte_identity_verified == false",
            ".crs_authorized == false",
            ".coordinate_semantics_authorized == false",
            ".site_response_authorized == false",
            ".site_semantics_authorized == false",
            ".numerical_hazard_agreement_verified == false",
            ".full_hazard_compatibility_verified == false",
            ".site_model_compatibility_verified == false",
            ".reference_run_verified == false",
            ".scientific_validity_verified == false",
            ".external_bytes_persisted == false",
            ".publication_authorized == false",
            ".model_use_authorized == false",
        ):
            self.assertIn(expression, publish)

    def test_derived_publication_notice_is_bounded_and_precedes_result(self):
        publish = self.text.split("publish-typed-ingestion:", 1)[1]
        self.assertIn(
            'DERIVED_PUBLICATION_SCOPE: "bounded-derived-oq314-typed-site-evidence-only"',
            publish,
        )
        self.assertIn(
            "provider bytes, rows and raw values are not reproduced",
            publish,
        )
        self.assertIn("Provider/raw publication authority: false", publish)
        self.assertLess(
            publish.index("eshm20-site-oq314-typed-publication-notice.json"),
            publish.index("eshm20-site-oq314-typed-result-comment.json"),
        )


if __name__ == "__main__":
    unittest.main()
