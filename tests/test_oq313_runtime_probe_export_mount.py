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
        probe_start = text.index(
            "      - name: Probe pinned runtime and write OqParam-observed runtime receipts"
        )
        numerical_start = text.index(
            "      - name: Execute closed OQ3.13 envelope inside receipted image",
            probe_start,
        )
        publish_start = text.index(
            "      - name: Re-fence bounded result and publish terminal evidence",
            numerical_start,
        )
        cls.probe = text[probe_start:numerical_start]
        cls.numerical = text[numerical_start:publish_start]

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

    def test_numerical_keeps_stage_read_only_and_overlays_only_export_dir(self) -> None:
        numerical = self.numerical
        stage_ro = '-v "$STAGE_ROOT:/stage:ro" \\'
        export_rw = '-v "$RUNTIME_EXPORT_ROOT:/stage/Risk" \\'
        receipts_ro = '-v "$RECEIPT_ROOT:/receipts:ro" \\'

        self.assertIn(
            'RUNTIME_EXPORT_ROOT="$RUNNER_TEMP/oq313-runtime-export"',
            numerical,
        )
        self.assertIn(stage_ro, numerical)
        self.assertIn(export_rw, numerical)
        self.assertIn(receipts_ro, numerical)
        self.assertLess(numerical.index(stage_ro), numerical.index(export_rw))
        self.assertLess(numerical.index(export_rw), numerical.index(receipts_ro))
        self.assertNotIn('-v "$STAGE_ROOT:/stage" \\', numerical)


if __name__ == "__main__":
    unittest.main()
