# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ESRM20_WORKFLOW = ROOT / ".github/workflows/esrm20-gsim-reference-runtime.yml"
ESHM20_WORKFLOW = ROOT / ".github/workflows/eshm20-gsim-reference-runtime.yml"


class Esrm20RuntimeWorkflowContractTests(unittest.TestCase):
    def test_reuses_reviewed_openquake_checkout_and_container_bootstrap(self) -> None:
        esrm20 = ESRM20_WORKFLOW.read_text(encoding="utf-8")
        eshm20 = ESHM20_WORKFLOW.read_text(encoding="utf-8")

        shared_fragments = (
            "git -C \"$OQ_ROOT\" fetch --depth=1 origin",
            "refs/tags/v3.14.0:refs/tags/v3.14.0",
            "rev-parse 'refs/tags/v3.14.0^{commit}'",
            'BASE_IMAGE="openquake/engine:3.14.0"',
            "grep -Eq '^openquake/engine@sha256:[0-9a-f]{64}$'",
            "COPY --chown=root:root oq-engine /oq-engine",
            "RUN git config --system --add safe.directory /oq-engine",
            "--entrypoint /opt/openquake/bin/python",
            "-e PYTHONPATH=/oq-engine:/workspace",
        )
        for fragment in shared_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, eshm20)
                self.assertIn(fragment, esrm20)

    def test_rejects_failed_tarball_fake_ref_bootstrap(self) -> None:
        esrm20 = ESRM20_WORKFLOW.read_text(encoding="utf-8")
        forbidden = (
            "api.github.com/repos/gem/oq-engine/tarball/",
            "git commit-tree",
            "git update-ref refs/heads/receipt",
            "eshm20_openquake314_runtime.Dockerfile",
        )
        for fragment in forbidden:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, esrm20)

    def test_workflow_concurrency_isolates_non_request_issue_comments(self) -> None:
        esrm20 = ESRM20_WORKFLOW.read_text(encoding="utf-8")
        header, jobs = esrm20.split("\njobs:\n", 1)
        self.assertTrue(jobs)
        self.assertIn("concurrency:", header)
        self.assertIn("github.event.issue.number == 493", header)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            header,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", header)
        self.assertIn("<!-- oc-eq1-esrm20-gsim-reference-runtime-request-v1 -->", header)
        self.assertIn("'trusted-request'", header)
        self.assertIn("format('noise-{0}', github.event.comment.id)", header)
        self.assertIn("cancel-in-progress: false", header)

    def test_preserves_exact_openquake_commit_and_trusted_main_fences(self) -> None:
        esrm20 = ESRM20_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "OQ_COMMIT: 9f044c93d72846421a8faa90ebf0a6afacdf3c20",
            esrm20,
        )
        self.assertIn("Checkout exact trusted execution commit", esrm20)
        self.assertIn("Prove complete issue-local dedup before external/provider access", esrm20)
        self.assertIn("--expected-issue 493", esrm20)
        self.assertIn("--runtime-image-digest-env RUNTIME_IMAGE_DIGEST", esrm20)
        self.assertIn("publication_authorized == false", esrm20)
        self.assertIn("model_use_authorized == false", esrm20)


if __name__ == "__main__":
    unittest.main()
