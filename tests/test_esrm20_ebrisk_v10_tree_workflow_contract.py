# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import re
import unittest

from scripts import profile_esrm20_ebrisk_v10_tree as profile


_WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "esrm20-ebrisk-v10-tree.yml"
)


class EbriskWorkflowContractTests(unittest.TestCase):
    def test_publish_blocked_gate_matches_profiler_failure_classes_exactly(self) -> None:
        workflow = _WORKFLOW.read_text(encoding="utf-8")
        publish = workflow.split("  publish-ebrisk-tree:\n", 1)[1]
        blocked_gate = publish.split("            else\n", 1)[1].split(
            "            end)\n", 1
        )[0]

        observed = set(re.findall(r'\.failure_class == "([^"]+)"', blocked_gate))
        self.assertEqual(observed, set(profile.FAILURE_CLASSES))
        self.assertIn(".profile == null", blocked_gate)


if __name__ == "__main__":
    unittest.main()
