# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Guard the exact-SHA, manual-only, read-only 901 MB research replay gateway."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/nrw-hu22-2022-manual-replay-gateway.yml"
SOURCE_SHA = "75dba089478927003d201032cb41303ebf587952"
TARGET = "pokekarten/OpenCatastrophe-data/.github/workflows/rva-nrw-hu22-daria-fresh-independent-replay.yml"


class NoDuplicateKeysBaseLoader(yaml.BaseLoader):
    """Keep GitHub's 'on' literal and reject ambiguous duplicate YAML keys."""

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise ValueError("Expected a mapping in gateway YAML")
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise ValueError(f"Duplicate or non-string YAML key in gateway: {key!r}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def verify_manual_gateway_shape(raw: str) -> None:
    """Fail closed if a 901 MB manual gateway gains any execution surface."""
    workflow = yaml.load(raw, Loader=NoDuplicateKeysBaseLoader)
    assert isinstance(workflow, dict)
    assert set(workflow) == {"name", "on", "permissions", "jobs"}
    assert workflow["on"] == {"workflow_dispatch": ""}
    assert workflow["permissions"] == {"contents": "read"}
    assert isinstance(workflow["jobs"], dict)
    assert set(workflow["jobs"]) == {"original-hu22-replay"}
    job = workflow["jobs"]["original-hu22-replay"]
    assert isinstance(job, dict)
    assert job == {
        "uses": f"{TARGET}@{SOURCE_SHA}",
        "with": {"source_ref": SOURCE_SHA},
        "permissions": {"contents": "read"},
    }


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

    def test_complete_yaml_shape_no_hidden_jobs_or_extra_triggers(self):
        verify_manual_gateway_shape(self.raw)

    def test_mutations_fail_closed(self):
        variants = {
            "push-trigger": self.raw.replace("  workflow_dispatch:\n", "  workflow_dispatch:\n  push:\n"),
            "duplicate-on-key": self.raw + "\non:\n  push:\n",
            "second-job": self.raw + "  injected-job:\n    runs-on: ubuntu-latest\n",
            "extra-permission": self.raw.replace("  contents: read\n", "  contents: read\n  actions: write\n", 1),
            "unreviewed-script-step": self.raw + "    steps:\n      - run: echo 'unexpected'\n",
            "pinned-source-drift": self.raw.replace(f"source_ref: {SOURCE_SHA}", "source_ref: " + "f" * 40),
            "duplicate-source-ref": self.raw.replace(f"source_ref: {SOURCE_SHA}", f"source_ref: {SOURCE_SHA}\n      source_ref: {SOURCE_SHA}"),
        }
        for label, variant in variants.items():
            with self.subTest(mutant=label):
                with self.assertRaises((AssertionError, ValueError, yaml.YAMLError)):
                    verify_manual_gateway_shape(variant)


if __name__ == "__main__":
    unittest.main()
