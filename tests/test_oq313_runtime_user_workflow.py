# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/oq313-kosovo-reconstructed-run.yml")


class OQ313RuntimeUserWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_runtime_probe_runs_as_openquake_before_version_receipt(self) -> None:
        text = self.text
        ownership = "chown -R openquake:openquake /oq-engine"
        runtime_user = "USER openquake"
        stage_write = 'chmod a+rwx "$STAGE_ROOT"'
        effective_user = "runtime_user = pwd.getpwuid(os.geteuid()).pw_name"
        user_guard = 'if runtime_user != "openquake":'
        version_receipt = "openquake_version = openquake_baselib.__version__"

        self.assertIn(ownership, text)
        self.assertIn(runtime_user, text)
        self.assertIn(stage_write, text)
        self.assertIn(effective_user, text)
        self.assertIn(user_guard, text)
        self.assertIn(
            'if openquake_version != "3.13.0-git16dd69ecea":',
            text,
        )
        self.assertLess(text.index(ownership), text.index(runtime_user))
        self.assertLess(text.index(runtime_user), text.index(stage_write))
        self.assertLess(text.index(stage_write), text.index(effective_user))
        self.assertLess(text.index(effective_user), text.index(user_guard))
        self.assertLess(text.index(user_guard), text.index(version_receipt))

    def test_numerical_execution_keeps_explicit_root_override(self) -> None:
        text = self.text
        probe = "Probe pinned runtime and write OqParam-observed runtime receipts"
        numerical = "Execute closed OQ3.13 envelope inside receipted image"
        root_override = "docker run --rm --user 0:0 --entrypoint python"

        self.assertIn(root_override, text)
        self.assertLess(text.index(probe), text.index(numerical))
        self.assertLess(text.index(numerical), text.index(root_override))


if __name__ == "__main__":
    unittest.main()
