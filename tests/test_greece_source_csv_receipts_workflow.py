# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path


class GreeceSourceCsvReceiptsWorkflowTests(unittest.TestCase):
    def test_workflow_is_trusted_main_only_and_refences_before_publish(self):
        text = Path(".github/workflows/esrm20-greece-source-csv-receipts.yml").read_text(encoding="utf-8")
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn("python -m scripts.run_esrm20_greece_source_csv_receipts_action", text)
        self.assertIn("Prove complete issue-local dedup before provider access", text)
        self.assertIn("LATEST_SHA=", text)
        self.assertIn('test "$LATEST_SHA" = "$EXECUTION_SHA"', text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("external_bytes_persisted == false", text)
        self.assertIn("source_runtime_lineage_verified == false", text)

    def test_publisher_does_not_checkout_repository(self):
        text = Path(".github/workflows/esrm20-greece-source-csv-receipts.yml").read_text(encoding="utf-8")
        publish = text.split("  publish-receipts:", 1)[1]
        self.assertNotIn("actions/checkout@", publish)
        self.assertIn("issues: write", publish)
        self.assertIn("contents: read", publish)


if __name__ == "__main__":
    unittest.main()
