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
        effective_user = "runtime_user = pwd.getpwuid(os.geteuid()).pw_name"
        user_guard = 'if runtime_user != "openquake":'
        version_receipt = "openquake_version = openquake_baselib.__version__"

        self.assertIn(ownership, text)
        self.assertIn(runtime_user, text)
        self.assertIn(effective_user, text)
        self.assertIn(user_guard, text)
        self.assertIn(
            'if openquake_version != "3.13.0-git16dd69ecea":',
            text,
        )
        self.assertLess(text.index(ownership), text.index(runtime_user))
        self.assertLess(text.index(runtime_user), text.index(effective_user))
        self.assertLess(text.index(effective_user), text.index(user_guard))
        self.assertLess(text.index(user_guard), text.index(version_receipt))

    def test_probe_receipts_are_isolated_from_read_only_staged_inputs(self) -> None:
        text = self.text
        receipt_root = 'RECEIPT_ROOT="$RUNNER_TEMP/oq313-runtime-receipts"'
        stage_ro = '-v "$STAGE_ROOT:/stage:ro"'
        receipt_rw = '-v "$RECEIPT_ROOT:/receipts"'
        receipt_ro = '-v "$RECEIPT_ROOT:/receipts:ro"'

        self.assertNotIn('chmod a+rwx "$STAGE_ROOT"', text)
        self.assertIn(receipt_root, text)
        self.assertIn('sudo chown "$OPENQUAKE_UID:$OPENQUAKE_GID" "$RECEIPT_ROOT"', text)
        self.assertIn('chmod 700 "$RECEIPT_ROOT"', text)
        self.assertIn(stage_ro, text)
        self.assertIn(receipt_rw, text)
        self.assertIn(
            'with open("/receipts/runtime-identity.json", "w", encoding="utf-8")',
            text,
        )
        self.assertIn(
            'with open("/receipts/resolved-runtime.json", "w", encoding="utf-8")',
            text,
        )
        self.assertIn(receipt_ro, text)
        self.assertIn("--runtime-identity /receipts/runtime-identity.json", text)
        self.assertIn("--resolved-runtime /receipts/resolved-runtime.json", text)

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
