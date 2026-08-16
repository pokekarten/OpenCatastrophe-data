# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import unittest


class Eshm20GsimReferenceRuntimeWorkflowTests(unittest.TestCase):
    def test_exact_openquake_checkout_is_embedded_and_trusted_system_wide(self):
        repo_root = Path(__file__).resolve().parents[1]
        workflow = (
            repo_root / ".github" / "workflows" / "eshm20-gsim-reference-runtime.yml"
        ).read_text(encoding="utf-8")

        copy = "COPY --chown=root:root oq-engine /oq-engine"
        system_trust = "RUN git config --system --add safe.directory /oq-engine"
        runtime_user = "USER openquake"

        self.assertIn(copy, workflow)
        self.assertIn(system_trust, workflow)
        self.assertIn(runtime_user, workflow)
        self.assertLess(workflow.index(copy), workflow.index(system_trust))
        self.assertLess(workflow.index(system_trust), workflow.index(runtime_user))
        self.assertNotIn(
            '-v "$RUNNER_TEMP/oq-engine:/oq-engine:ro"',
            workflow,
        )
        self.assertNotIn("GIT_CONFIG_COUNT", workflow)
        self.assertNotIn("GIT_CONFIG_KEY_0", workflow)
        self.assertNotIn("GIT_CONFIG_VALUE_0", workflow)
        self.assertIn("PYTHONPATH=/oq-engine:/workspace", workflow)
        self.assertIn(
            "9f044c93d72846421a8faa90ebf0a6afacdf3c20",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
