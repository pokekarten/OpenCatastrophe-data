# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/esrm20-exposure-v10-tree.yml")
REQUEST_MARKER = "<!-- oc-eq1-esrm20-exposure-v10-tree-request-v1 -->"


class ExposureTreeWorkflowConcurrencyTests(unittest.TestCase):
    def test_trusted_requests_serialize_but_comment_noise_is_isolated(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        concurrency = text.split("concurrency:", 1)[1].split("jobs:", 1)[0]
        self.assertIn("github.event.issue.number == 282", concurrency)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            concurrency,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", concurrency)
        self.assertIn(REQUEST_MARKER, concurrency)
        self.assertIn(
            "&& 'trusted-request' || format('noise-{0}', github.event.comment.id)",
            concurrency,
        )
        self.assertIn("cancel-in-progress: false", concurrency)
        self.assertNotIn(
            "group: esrm20-exposure-v10-tree-${{ github.repository }}\n",
            concurrency,
        )

    def test_execution_job_keeps_closed_request_fence(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        execute = text.split("execute-exposure-tree:", 1)[1].split(
            "publish-exposure-tree:", 1
        )[0]
        self.assertIn("github.event.issue.number == 282", execute)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            execute,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", execute)
        self.assertIn(REQUEST_MARKER, execute)


if __name__ == "__main__":
    unittest.main()
