# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class RuntimeResidentialCsvReceiptWorkflowInvocationTests(unittest.TestCase):
    def test_action_runner_uses_package_module_invocation(self):
        repo_root = Path(__file__).resolve().parents[1]
        workflow = (
            repo_root
            / ".github"
            / "workflows"
            / "esrm20-runtime-residential-csv-receipt.yml"
        ).read_text(encoding="utf-8")

        module_invocation = (
            "python -m scripts.run_esrm20_runtime_residential_csv_receipt_action"
        )
        direct_invocation = (
            "python scripts/run_esrm20_runtime_residential_csv_receipt_action.py"
        )

        self.assertEqual(workflow.count(module_invocation), 2)
        self.assertNotIn(direct_invocation, workflow)


if __name__ == "__main__":
    unittest.main()
