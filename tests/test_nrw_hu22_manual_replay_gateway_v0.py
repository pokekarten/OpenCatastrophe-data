# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Guard the exact-SHA, manual-only, read-only 901 MB research replay gateway."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/nrw-hu22-2022-manual-replay-gateway.yml"
SOURCE_SHA = "7df2bd716998eead99c5e4e114c8fa1d9a36cc95"
TARGET = "pokekarten/OpenCatastrophe-data/.github/workflows/rva-nrw-hu22-daria-fresh-independent-replay.yml"


class TestManualOriginalResearchReplayGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = WORKFLOW.read_text(encoding="utf-8")

    def test_manual_only_no_silent_901mb_download_on_pr_push(self):
        triggers = self.raw.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertEqual(triggers, "  workflow_dispatch:\n")
        for forbidden in ("pull_request:", "push:", "schedule:", "workflow_call:", "repository_dispatch:"):
            with self.subTest(trigger=forbidden):
                self.assertNotIn(forbidden, triggers)
        self.assertIn("permissions:\n  contents: read", self.raw)
        self.assertIn("    permissions:\n      contents: read", self.raw)
        self.assertNotIn("secrets: inherit", self.raw)
        self.assertNotIn("actions: write", self.raw)

    def test_full_exact_same_source_ref_in_caller_and_checkout_contract(self):
        self.assertRegex(SOURCE_SHA, r"^[a-f0-9]{40}$")
        self.assertIn(f"uses: {TARGET}@{SOURCE_SHA}", self.raw)
        self.assertIn(f"source_ref: {SOURCE_SHA}", self.raw)
        sources = re.findall(r"(?:uses: .*?@|source_ref: )([a-f0-9]{40})", self.raw)
        self.assertEqual(sources, [SOURCE_SHA, SOURCE_SHA])
        self.assertEqual(self.raw.count(SOURCE_SHA), 2)

    def test_no_raw_original_source_or_unreviewed_shell_in_gateway(self):
        self.assertNotIn("actions/checkout@", self.raw)
        self.assertNotIn("actions/upload-artifact@", self.raw)
        self.assertNotIn("gh run download", self.raw)
        self.assertNotIn("run: |", self.raw)
        self.assertNotIn("curl ", self.raw)
        self.assertNotIn("git clone", self.raw)


if __name__ == "__main__":
    unittest.main()
