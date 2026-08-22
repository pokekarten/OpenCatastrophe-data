# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/oq313-kosovo-reconstructed-run.yml")


class OQ313KosovoReconstructedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_only_owner_issue_comment_can_reach_trusted_request_lane(self) -> None:
        text = self.text
        self.assertIn("issue_comment:", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("workflow_dispatch:", text)
        self.assertIn("github.event.issue.number == 609", text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn(
            "<!-- oc-eq1-esrm20-kosovo-oq313-run-request-v1 -->",
            text,
        )

    def test_execution_is_bound_to_trusted_default_branch_sha(self) -> None:
        text = self.text
        self.assertGreaterEqual(
            text.count("ref: ${{ github.event.repository.default_branch }}"),
            2,
        )
        self.assertIn('EXECUTION_SHA="$(git rev-parse HEAD)"', text)
        self.assertIn("--execution-sha \"$EXECUTION_SHA\"", text)
        self.assertNotIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", text)
        self.assertIn('test "$(git rev-parse HEAD)" = "$EXECUTION_SHA"', text)
        self.assertLess(
            text.index("Re-fence privileged checkout to validated main SHA"),
            text.index("Deduplicate trusted terminal result before external access"),
        )
        self.assertLess(
            text.index("Deduplicate trusted terminal result before external access"),
            text.index("Fetch exact ESRM20 v1.0 provider snapshot"),
        )

    def test_provider_and_runtime_refs_are_immutable_and_not_request_selectable(self) -> None:
        text = self.text
        self.assertIn(
            "ESRM20_COMMIT: 05f83bbc9df81d02ee8ddb1801d9d781355ce783",
            text,
        )
        self.assertIn("refs/tags/v1.0:refs/tags/v1.0", text)
        self.assertIn(
            "OQ_COMMIT: 16dd69ecea0c6dcaf49c22ca12edc9da3f024889",
            text,
        )
        self.assertIn("refs/tags/v3.13.0:refs/tags/v3.13.0", text)
        self.assertNotIn("github.event.inputs", text)
        self.assertNotIn("repository_path:", text)

    def test_fixed_source_identities_are_reverified_before_derivation(self) -> None:
        text = self.text
        self.assertIn("wrapper.SOURCE_BYTE_COUNT", text)
        self.assertIn("wrapper.SOURCE_SHA256", text)
        self.assertIn("wrapper.SELECTED_BYTE_COUNT", text)
        self.assertIn("wrapper.SELECTED_SHA256", text)
        self.assertIn("cfg.GROUP1_BYTE_COUNT", text)
        self.assertIn("cfg.GROUP1_SHA256", text)
        self.assertIn("build_kosovo_residential_exposure_wrapper", text)
        self.assertIn("build_kosovo_residential_ebrisk_config", text)

    def test_exact_oq313_envelope_is_invoked_and_raw_results_are_not_uploaded(self) -> None:
        text = self.text
        self.assertIn(
            "/repo/scripts/run_esrm20_kosovo_residential_ebrisk_openquake313_action.py",
            text,
        )
        self.assertIn("--expected-issue 609", text)
        self.assertIn("--source-group1-config", text)
        self.assertIn("--runtime-identity", text)
        self.assertIn("--resolved-runtime", text)
        self.assertNotIn("actions/upload-artifact", text)
        self.assertNotIn("artifact upload", text.casefold())
        self.assertIn('"external_provider_bytes_persisted": False', text)
        self.assertIn('"publication_authorized": False', text)
        self.assertIn('"model_use_authorized": False', text)

    def test_runtime_probe_pins_declared_dependency_receipt(self) -> None:
        text = self.text
        for name, version in {
            "h5py": "3.1.0",
            "numpy": "1.20.0",
            "pandas": "1.1.5",
            "psutil": "5.6.7",
            "pyzmq": "19.0.0",
            "scipy": "1.4.1",
            "shapely": "1.7.1",
        }.items():
            self.assertIn(f'"{name}": "{version}"', text)
        self.assertIn('sys.version_info[:2] != (3, 8)', text)
        self.assertIn('"ses_seed": 42', text)
        self.assertIn('"concurrent_tasks": 0', text)
        self.assertIn("docker run --rm -i --entrypoint python", text)


if __name__ == "__main__":
    unittest.main()
