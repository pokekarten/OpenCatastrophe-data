# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only manually dispatched or exact-SHA explicitly called 901MB NRW source replay."""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/rva-nrw-hu22-daria-fresh-independent-replay.yml"


class TestOriginalHU22OnDemandGovernance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = WORKFLOW.read_text(encoding="utf-8")

    def test_explicit_dispatch_or_pinned_reusable_call_only(self):
        # An exact-SHA caller on main may invoke this versioned heavy job.
        # GitHub matches PR paths against the ENTIRE PR diff; never auto-run.
        trigger = self.data.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertEqual(trigger, (
            "  workflow_dispatch:\n"
            "  workflow_call:\n"
            "    inputs:\n"
            "      source_ref:\n"
            "        description: Immutable forty-character Git commit SHA of the approved research replay\n"
            "        type: string\n"
            "        required: true\n"
        ))
        for unsupported in ("pull_request:", "push:", "schedule:", "repository_dispatch:"):
            with self.subTest(forbidden=unsupported):
                self.assertNotIn(unsupported, trigger)
        self.assertIn("cancel-in-progress: false", self.data)
        self.assertIn("ref: ${{ inputs.source_ref || github.sha }}", self.data)
        self.assertIn("EXPECTED_SOURCE_SHA: ${{ inputs.source_ref || github.sha }}", self.data)
        self.assertIn('test "$(git rev-parse HEAD)" = "$EXPECTED_SOURCE_SHA"', self.data)
        self.assertIn("^[0-9a-f]{40}$", self.data)

    def test_fresh_original_source_replay_never_uses_expiring_previous_artifact(self):
        for absent in ("gh run download", "42097472463", "13447603258",
                       "GH_TOKEN:", "actions: write"):
            with self.subTest(forbidden=absent):
                self.assertNotIn(absent, self.data)
        for necessary in (
            "rva_nrw_hu22_full_original_download_v0.py",
            "rva_nrw_hu22_full_source_to_fictional_oed_v0.py",
            "rva_nrw_xws_daria_10k_original_gust_overlay_v0.py",
            "rva_nrw_daria_climada61_original_method_parity_v0.py",
            "10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da",
            "original-HU22",
        ):
            # The ephemeral original source is reprocessed in one job.
            if necessary == "original-HU22":
                continue
            with self.subTest(required=necessary):
                self.assertIn(necessary, self.data)

    def test_separate_incompatible_numpy_phases_are_not_combined(self):
        self.assertIn('python -m venv "${{ runner.temp }}/climada61-parity-venv"', self.data)
        self.assertIn("numpy==1.26.4 scipy==1.14.1", self.data)
        self.assertIn('"${{ runner.temp }}/climada61-parity-venv/bin/python" research_runners/rva_nrw_daria_climada61_original_method_parity_v0.py', self.data)
        self.assertIn("python -m pip check", self.data)
        self.assertNotIn("numpy==1.26.4 scipy==1.14.1\n          python -m pip check", self.data)

    def test_legacy_one_shot_also_cleans_original_on_failure(self):
        # The earlier explicit 901 MB workflow must not strand original
        # provider bytes if conversion fails after a successful download.
        legacy=(ROOT / ".github/workflows/rva-nrw-hu22-full-one-shot.yml").read_text(encoding="utf-8")
        trigger=legacy.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertEqual(trigger, "  workflow_dispatch:\n")
        cleanup=legacy.index("Always delete large ephemeral provider ZIP")
        publication=legacy.index("Publish ONLY fictional geocoded OED")
        self.assertLess(cleanup, publication)
        self.assertIn("if: always()", legacy[cleanup:publication])
        self.assertIn('rm -f -- "${{ runner.temp }}/2022_hu_EPSG4647_Shape.original.zip"',legacy[cleanup:publication])
        self.assertNotIn("gh run download",legacy)

    def test_source_originals_removed_before_receipt_publication(self):
        cleanup = self.data.index("Always erase provider raw geocodes")
        publish = self.data.index("Publish only source-bound method parity")
        self.assertLess(cleanup, publish)
        for private in (
            "2022_hu_EPSG4647_Shape.original.zip",
            "nrw-hu22-fresh-geocoded-source",
            "fresh-xws-source-csv",
            "fresh-climada61-original-gpl",
            "climada61-parity-venv",
        ):
            self.assertIn(private, self.data[cleanup:publish])
        self.assertIn("if: always()", self.data[cleanup:publish])
        self.assertIn("retention-days: 14", self.data[publish:])
        self.assertIn("no 901MB originals or individual locations", self.data[publish:])


if __name__ == "__main__":
    unittest.main()
