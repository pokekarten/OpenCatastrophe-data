# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/esrm20-athens-sibling-receipts.yml")


class AthensSiblingReceiptWorkflowTests(unittest.TestCase):
    def test_action_runs_as_repository_package_module(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        module = "python -m scripts.run_efehr_esrm20_athens_sibling_receipts_action"
        direct = "python scripts/run_efehr_esrm20_athens_sibling_receipts_action.py"

        self.assertEqual(text.count(module), 1)
        self.assertNotIn(direct, text)
        self.assertLess(text.index(module), text.index("--comment-body-env"))


if __name__ == "__main__":
    unittest.main()
