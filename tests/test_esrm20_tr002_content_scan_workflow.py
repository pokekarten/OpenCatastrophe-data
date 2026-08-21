# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


WORKFLOW = Path(".github/workflows/esrm20-tr002-content-scan.yml")


class Tr002ContentScanWorkflowTests(unittest.TestCase):
    def test_trusted_execution_provisions_extractor_after_dedup_before_provider_scan(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        execute = workflow.split("\n  execute-and-publish-scan:\n", 1)[1]

        dedup_index = execute.index("Prove complete issue-local dedup before provider access")
        provision_index = execute.index("Provision bounded PDF text extractor")
        scan_index = execute.index("Run exact fixed TR002 content scan")
        self.assertLess(dedup_index, provision_index)
        self.assertLess(provision_index, scan_index)

        provision = execute.split("- name: Provision bounded PDF text extractor", 1)[1].split(
            "\n      - name:", 1
        )[0]
        self.assertIn("if: steps.dedup.outputs.skip != 'true'", provision)
        self.assertIn("sudo apt-get update", provision)
        self.assertIn("sudo apt-get install --no-install-recommends --yes poppler-utils", provision)
        self.assertIn("pdftotext -v", provision)
        self.assertNotIn("curl ", provision)
        self.assertNotIn("wget ", provision)

    def test_runtime_fix_does_not_add_raw_output_or_alternate_trigger_surface(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("actions/upload-artifact", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertNotIn("workflow_dispatch:", workflow)
        self.assertIn("github.event.issue.number == 596", workflow)
        self.assertIn("ref: ${{ needs.validate-request.outputs.execution_sha }}", workflow)


if __name__ == "__main__":
    unittest.main()
