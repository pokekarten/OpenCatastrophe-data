# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Cheap original XWS/CLIMADA CI must never pretend to run the 10k model."""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FAST = ROOT / ".github/workflows/rva-nrw-xws-daria-source.yml"
FULL = ROOT / ".github/workflows/rva-nrw-hu22-daria-fresh-independent-replay.yml"


class SourceOnlyCISeparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fast = FAST.read_text(encoding="utf-8")
        cls.full = FULL.read_text(encoding="utf-8")

    def test_fast_source_ci_never_fetches_expiring_artifact_or_large_hu(self):
        for blocked in (
            "gh run download", "42097472463", "13447603258", "GH_TOKEN:",
            "actions: read", "actions: write", "2022_hu_EPSG4647_Shape.original.zip",
            "rva_nrw_hu22_full_original_download_v0.py",
            "rva_nrw_hu22_full_source_to_fictional_oed_v0.py",
            "nrw-source-geocoded-10k",
        ):
            with self.subTest(blocked=blocked):
                self.assertNotIn(blocked, self.fast)
        self.assertIn("permissions:\n  contents: read\n", self.fast)

    def test_fast_success_cannot_look_like_2022_site_replay_or_insurer_loss(self):
        self.assertIn("preflight (NO 10k)", self.fast)
        self.assertIn("VERIFIED_ORIGINAL_SOURCE_BYTES_AND_METHOD_DEFINITIONS_ONLY", self.fast)
        for token in (
            '"actual_2022_NRW_10k_site_overlay_executed_in_this_workflow":False',
            '"original_CLIMADA_source_method_body_parity_executed_in_this_workflow":False',
            '"actual_insurer_RV_geographies_or_loss_calculated":False',
            '"annual_frequency_or_OEP_AEP_calculated":False',
            '"full_replay_requires_separate_manually_dispatched_901MB_HU22_workflow":True',
        ):
            with self.subTest(scope=token):
                self.assertIn(token, self.fast)
        # Original source fixture tests are allowed; the live 10k runner is not.
        self.assertNotIn("python research_runners/rva_nrw_xws_daria_10k_original_gust_overlay_v0.py", self.fast)
        self.assertNotIn("python research_runners/rva_nrw_daria_climada61_original_method_parity_v0.py", self.fast)

    def test_fast_source_pins_and_climada_defs_are_still_positively_checked(self):
        for term in (
            "xws_daria_1990_original_csv_preflight_v0.py --live",
            "test_rva_nrw_xws_daria_10k_original_gust_overlay_v0.py",
            "test_rva_nrw_xws_daria_invented_damage_v0.py",
            "test_rva_nrw_xws_daria_excess_cube_index_v0.py",
            "test_rva_nrw_daria_climada61_source_challenger_v0.py",
            "validate_original_bundle(raw)",
            "actual==SOURCE_PINS",
            "parse_pinned_public_curves(climada)",
            "source[\"original_files\"][name][\"full_sha256\"]==sha",
            "XWS-Daria-1990-CLIMADA61-four-source-SHA-only-NOT-10k-MODEL",
        ):
            with self.subTest(required=term):
                self.assertIn(term, self.fast)

    def test_live_original_provider_sources_require_trusted_manual_main(self):
        # PR changes must only test offline contracts. The original XWS CSV
        # and CLIMADA method downloads depend on external availability and
        # must never run automatically for pull_request heads.
        for step_name in (
            "Read exact original external GPL CLIMADA 6.1.0 source metadata (no redistribution)",
            "Source-original FULL CSV byte hashes and licence receipt (no raw upload)",
            "Validate original four Daria CSV SHA pins and original CLIMADA PAA/MDD method definitions ONLY",
            "Publish source-only SHA/method scope receipt (NO 10k site run)",
        ):
            with self.subTest(step=step_name):
                step = self.fast.split("      - name: " + step_name + "\n", 1)
                self.assertEqual(len(step), 2)
                body = step[1].split("\n      - name: ", 1)[0]
                self.assertIn(
                    "        if: github.event_name == 'workflow_dispatch' "
                    "&& github.ref == 'refs/heads/main'\n", body,
                )
        for step_name in (
            "Original XWS CSV source, geographic identity and no-model negative tests",
            "Entirely invented conditional impact arithmetic and negative tests",
            "Independent fixed-threshold wind severity index and fail-closed tests",
            "Original-code-isolated CLIMADA 6.1.0 PAA MDD interpolation negative tests",
            "Offline 1990 XWS 3-second original site overlay negative checks",
        ):
            with self.subTest(offline_step=step_name):
                step = self.fast.split("      - name: " + step_name + "\n", 1)
                self.assertEqual(len(step), 2)
                body = step[1].split("\n      - name: ", 1)[0]
                self.assertNotIn("if: github.event_name", body)
        self.assertIn("  pull_request:\n", self.fast)
        self.assertIn("  workflow_dispatch:\n", self.fast)
        self.assertIn("permissions:\n  contents: read\n", self.fast)

    def test_clean_ephemeral_provider_bytes_prior_to_no_loss_receipt(self):
        first=self.fast.index("Always remove original wind and GPL method source bytes")
        later=self.fast.index("Publish source-only SHA/method scope receipt")
        self.assertLess(first,later)
        self.assertIn("if: always()", self.fast[first:later])
        self.assertIn('rm -rf -- "${{ runner.temp }}/xws-daria-original-csv"', self.fast[first:later])
        self.assertIn('rm -rf -- "${{ runner.temp }}/climada61-original-gpl"', self.fast[first:later])
        self.assertNotIn("nrw-original-10k-verified-repacked.zip", self.fast)
        self.assertIn("retention-days: 14", self.fast[later:])

    def test_full_rebuild_is_manual_and_already_original_source_independent(self):
        on=self.full.split("\non:\n",1)[1].split("\npermissions:",1)[0]
        self.assertEqual(on, (
            "  workflow_dispatch:\n"
            "  workflow_call:\n"
            "    inputs:\n"
            "      source_ref:\n"
            "        description: Immutable forty-character Git commit SHA of the approved research replay\n"
            "        type: string\n"
            "        required: true\n"
        ))
        self.assertIn("ref: ${{ inputs.source_ref || github.sha }}", self.full)
        self.assertIn('test "$(git rev-parse HEAD)" = "$EXPECTED_SOURCE_SHA"', self.full)
        for forbidden in ("push:", "schedule:", "repository_dispatch:"):
            self.assertNotIn(forbidden, on)
        for term in (
            "rva_nrw_hu22_full_original_download_v0.py",
            "rva_nrw_hu22_full_source_to_fictional_oed_v0.py",
            "rva_nrw_xws_daria_10k_original_gust_overlay_v0.py",
            "rva_nrw_daria_climada61_original_method_parity_v0.py",
            "climada61-parity-venv",
        ):
            with self.subTest(full_scope=term):
                self.assertIn(term,self.full)
        self.assertNotIn("gh run download", self.full)
        self.assertNotIn("pull_request:", on)


if __name__ == "__main__":
    unittest.main()
