# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Negative tests for GitHub configuration ambiguity and agent-written YAML."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import check_all as definition_of_done
from scripts import check_yaml_mapping_keys as guard


class GitHubYAMLMappingKeysTests(unittest.TestCase):
    def inspect(self, content: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.yml"
            path.write_text(content, encoding="utf-8")
            return guard.check_file(path)

    def test_literal_github_on_trigger_is_not_misread_as_boolean(self) -> None:
        self.assertEqual(
            self.inspect("name: Example\non:\n  push:\njobs:\n  check:\n    runs-on: ubuntu-latest\n"),
            [],
        )

    def test_two_on_triggers_fail_closed(self) -> None:
        errors = self.inspect("on: push\non: pull_request\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("duplicate key 'on'", errors[0])
        self.assertIn("line 1", errors[0])

    def test_nested_duplicate_job_steps_fail_closed(self) -> None:
        errors = self.inspect("jobs:\n  check:\n    steps: []\n    steps: []\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("duplicate key 'steps' at $/jobs/check", errors[0])

    def test_mapping_key_same_name_in_different_scopes_is_valid(self) -> None:
        self.assertEqual(self.inspect("jobs:\n  a:\n    steps: []\n  b:\n    steps: []\n"), [])

    def test_malformed_yaml_is_rejected(self) -> None:
        self.assertIn("invalid YAML", self.inspect("jobs: [broken\n")[0])

    def test_yaml_merge_key_is_rejected(self) -> None:
        self.assertIn("merge key", self.inspect("base: &base\n  a: 1\nitem:\n  <<: *base\n")[0])

    def test_recursive_alias_is_rejected(self) -> None:
        self.assertIn("recursive YAML alias", self.inspect("self: &self\n  again: *self\n")[0])

    def test_empty_document_is_rejected(self) -> None:
        self.assertIn("empty YAML document", self.inspect("# empty\n")[0])

    def test_unsupported_explicit_tags_fail_closed(self) -> None:
        for source in (
            "jobs: !dangerous payload\n",
            "jobs: !!int 10\n",
            "jobs: !unknown [a, b]\n",
            "!unknown {name: config}\n",
        ):
            with self.subTest(source=source):
                self.assertIn("unsupported YAML tag", self.inspect(source)[0])

    def test_explicit_typed_mapping_key_fails_closed(self) -> None:
        errors = self.inspect("!!int 1: value\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("unsupported YAML key tag", errors[0])

    def test_shared_alias_subtrees_are_inspected_once(self) -> None:
        # An alias graph has exponentially many *paths* but only linearly many
        # YAML nodes. The same ambiguous mapping needs one diagnostic, not 2**n.
        source = "leaf: &leaf {same: one, same: two}\n"
        source += "".join(
            f"level{index}: &level{index} [*{previous}, *{previous}]\n"
            for index, previous in ((index, "leaf" if index == 1 else f"level{index-1}")
                                    for index in range(1, 12))
        )
        errors = self.inspect(source)
        self.assertEqual(len(errors), 1)
        self.assertIn("duplicate key 'same'", errors[0])

    def test_yaml_alias_cycle_still_fails_when_nodes_are_shared(self) -> None:
        errors = self.inspect("other: &other [a]\ncycle: &cycle [*other, *cycle]\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("recursive YAML alias", errors[0])

    def test_scan_includes_issue_templates_and_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            templates = root / ".github" / "ISSUE_TEMPLATE"
            workflows = root / ".github" / "workflows"
            templates.mkdir(parents=True)
            workflows.mkdir(parents=True)
            (templates / "good.yml").write_text("name: Issue\n", encoding="utf-8")
            (workflows / "bad.yml").write_text("on: push\non: pull_request\n", encoding="utf-8")
            errors, count = guard.check_all(root)
            self.assertEqual(count, 2)
            self.assertEqual(len(errors), 1)
            self.assertIn("bad.yml", errors[0])

    def test_definition_of_done_checks_runners_and_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with (
                mock.patch.object(definition_of_done, "ROOT", Path(tmp)),
                mock.patch.object(definition_of_done, "in_git_checkout", return_value=True),
                mock.patch.object(definition_of_done, "run", return_value=True) as run,
            ):
                self.assertEqual(definition_of_done.main(), 0)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertTrue(any("compileall" in command and "research_runners" in command
                            for command in commands))
        self.assertTrue(any("scripts/check_yaml_mapping_keys.py" in command for command in commands))

    def test_current_repository_git_config_is_unambiguous(self) -> None:
        errors, count = guard.check_all(guard.ROOT)
        self.assertEqual(errors, [])
        self.assertGreater(count, 300)


if __name__ == "__main__":
    unittest.main()
