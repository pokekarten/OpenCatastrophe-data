# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""The fast agent preflight must never be mistaken for full verification."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from scripts import check_all


class CheckAllModesTests(unittest.TestCase):
    def test_full_default_keeps_complete_test_discovery(self) -> None:
        commands = check_all.commands_for_mode(fast=False)
        self.assertTrue(any("discover" in command and "test*.py" in command for command in commands))
        self.assertFalse(any("tests.test_agent_artifact_contracts" in command for command in commands))

    def test_fast_uses_focused_tests_not_full_discovery(self) -> None:
        commands = check_all.commands_for_mode(fast=True)
        self.assertFalse(any("discover" in command for command in commands))
        self.assertTrue(any("tests.test_agent_artifact_contracts" in command for command in commands))
        self.assertTrue(any("tests.test_contract_consistency" in command for command in commands))
        self.assertTrue(any("tests.test_source_access_failclosed_state" in command for command in commands))

    def test_both_modes_enforce_the_same_non_test_guards(self) -> None:
        full = check_all.commands_for_mode(fast=False)
        fast = check_all.commands_for_mode(fast=True)
        self.assertEqual(full[:1], fast[:1])
        self.assertEqual(full[2:], fast[2:])
        for name in ("check_projection_families.py", "check_yaml_mapping_keys.py",
                     "check_markdown_links.py", "check_repository_hygiene.py",
                     "check_license_metadata.py"):
            self.assertTrue(any(name in part for command in fast for part in command))

    def test_fast_prints_distinct_status(self) -> None:
        with (
            mock.patch.object(check_all, "ROOT", Path("/synthetic/check-all-modes")),
            mock.patch.object(check_all, "in_git_checkout", return_value=True),
            mock.patch.object(check_all, "run", return_value=True),
            mock.patch("builtins.print") as output,
        ):
            self.assertEqual(check_all.main(["--fast"]), 0)
        printed = " ".join(str(a) for call in output.call_args_list for a in call.args)
        self.assertIn("FAST PREFLIGHT ONLY", printed)
        self.assertIn("fast preflight", printed)
        self.assertNotIn("full definition-of-done checks succeeded", printed)

    def test_no_checkout_blocks_both_modes(self) -> None:
        with mock.patch.object(check_all, "in_git_checkout", return_value=False):
            self.assertEqual(check_all.main(["--fast"]), 2)
            self.assertEqual(check_all.main([]), 2)


if __name__ == "__main__":
    unittest.main()
