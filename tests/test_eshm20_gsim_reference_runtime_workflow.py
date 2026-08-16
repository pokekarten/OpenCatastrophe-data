# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class Eshm20GsimReferenceRuntimeWorkflowTests(unittest.TestCase):
    def test_exact_openquake_checkout_is_embedded_not_host_bound(self):
        repo_root = Path(__file__).resolve().parents[1]
        workflow = (
            repo_root / ".github" / "workflows" / "eshm20-gsim-reference-runtime.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "COPY --chown=root:root oq-engine /oq-engine",
            workflow,
        )
        self.assertNotIn(
            '-v "$RUNNER_TEMP/oq-engine:/oq-engine:ro"',
            workflow,
        )
        self.assertIn("PYTHONPATH=/oq-engine:/workspace", workflow)
        self.assertIn("GIT_CONFIG_VALUE_0=/oq-engine", workflow)
        self.assertIn(
            "9f044c93d72846421a8faa90ebf0a6afacdf3c20",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
