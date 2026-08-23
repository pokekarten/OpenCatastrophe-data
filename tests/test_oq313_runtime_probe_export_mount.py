# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/oq313-kosovo-reconstructed-run.yml")


class OQ313RuntimeProbeExportMountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        start = text.index(
            "      - name: Probe pinned runtime and write OqParam-observed runtime receipts"
        )
        end = text.index(
            "      - name: Execute closed OQ3.13 envelope inside receipted image",
            start,
        )
        cls.probe = text[start:end]

    def test_probe_keeps_stage_read_only_and_overlays_only_export_dir(self) -> None:
        probe = self.probe
        stage_ro = '-v "$STAGE_ROOT:/stage:ro" \\'
        export_rw = '-v "$RUNTIME_EXPORT_ROOT:/stage/Risk" \\'
        receipts_rw = '-v "$RECEIPT_ROOT:/receipts" \\'

        self.assertIn(
            'RUNTIME_EXPORT_ROOT="$RUNNER_TEMP/oq313-runtime-export"',
            probe,
        )
        self.assertIn('mkdir -p "$RECEIPT_ROOT" "$RUNTIME_EXPORT_ROOT"', probe)
        self.assertIn(stage_ro, probe)
        self.assertIn(export_rw, probe)
        self.assertIn(receipts_rw, probe)
        self.assertLess(probe.index(stage_ro), probe.index(export_rw))
        self.assertLess(probe.index(export_rw), probe.index(receipts_rw))
        self.assertNotIn('-v "$STAGE_ROOT:/stage" \\', probe)

    def test_probe_export_dir_uses_runtime_identity_permissions(self) -> None:
        probe = self.probe
        self.assertIn(
            'OPENQUAKE_UID="$(docker run --rm --entrypoint id "$EXEC_IMAGE" -u)"',
            probe,
        )
        self.assertIn(
            'OPENQUAKE_GID="$(docker run --rm --entrypoint id "$EXEC_IMAGE" -g)"',
            probe,
        )
        self.assertIn('sudo chown "$OPENQUAKE_UID:$OPENQUAKE_GID" \\', probe)
        self.assertIn('"$RECEIPT_ROOT" "$RUNTIME_EXPORT_ROOT"', probe)
        self.assertIn(
            'sudo chmod 700 "$RECEIPT_ROOT" "$RUNTIME_EXPORT_ROOT"',
            probe,
        )

    def test_probe_does_not_bypass_validation_as_root(self) -> None:
        self.assertNotIn("--user 0:0", self.probe)
        self.assertIn('runtime_user != "openquake"', self.probe)


if __name__ == "__main__":
    unittest.main()
