# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/esrm20-ebrisk-risk-config-dependency-profiles.yml")
REQUEST_MARKER = "<!-- oc-eq1-esrm20-ebrisk-risk-config-dependency-profiles-request-v1 -->"


class EbriskDependencyProfileWorkflowConcurrencyTests(unittest.TestCase):
    def test_trusted_requests_serialize_but_comment_noise_is_isolated(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        concurrency = text.split("concurrency:", 1)[1].split("jobs:", 1)[0]
        self.assertIn(REQUEST_MARKER, concurrency)
        self.assertIn(
            "&& 'trusted-request' || format('noise-{0}', github.event.comment.id)",
            concurrency,
        )
        self.assertIn("cancel-in-progress: false", concurrency)
        self.assertNotIn(
            "group: esrm20-ebrisk-risk-config-dependency-profiles-${{ github.repository }}\n",
            concurrency,
        )

    def test_execution_job_keeps_closed_request_fence(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        execute = text.split("execute-dependency-profiles:", 1)[1].split(
            "publish-dependency-profiles:", 1
        )[0]
        self.assertIn("github.event.issue.number == 281", execute)
        self.assertIn("github.event.comment.author_association == 'OWNER'", execute)
        self.assertIn(REQUEST_MARKER, execute)


if __name__ == "__main__":
    unittest.main()
