# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic tests for conservative, static agent test suggestions."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from scripts import suggest_tests


class SuggestTestsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "tests").mkdir()

    def test_import_and_filename_matches(self) -> None:
        (self.root / "tests/test_alpha.py").write_text("pass\n", encoding="utf-8")
        (self.root / "tests/test_other.py").write_text(
            "from scripts import alpha\nimport research_runners.beta\n", encoding="utf-8"
        )
        found = suggest_tests.suggest(["scripts/alpha.py", "research_runners/beta.py"], root=self.root)
        self.assertEqual(found["suggested_tests"], ["tests/test_alpha.py", "tests/test_other.py"])
        self.assertEqual(found["unmatched_paths"], [])
        self.assertEqual(found["command"], [
            "python", "-m", "unittest", "tests.test_alpha", "tests.test_other"
        ])

    def test_importlib_path_literal_is_detected(self) -> None:
        (self.root / "tests/test_loader.py").write_text(
            'SCRIPT = ROOT / "scripts" / "check_repository_hygiene.py"\n', encoding="utf-8"
        )
        found = suggest_tests.suggest(["scripts/check_repository_hygiene.py"], root=self.root)
        self.assertEqual(found["suggested_tests"], ["tests/test_loader.py"])

    def test_direct_root_join_for_importlib_loader(self) -> None:
        (self.root / "tests/test_manifest_contract.py").write_text(
            'SPEC = importlib.util.spec_from_file_location(\n'
            '    "validator", ROOT / "scripts/validate_manifest.py")\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/validate_manifest.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], ["tests/test_manifest_contract.py"])

    def test_direct_root_join_for_research_runner(self) -> None:
        (self.root / "tests/test_runner.py").write_text(
            'SCRIPT = ROOT / "research_runners/probe.py"\n', encoding="utf-8"
        )
        report = suggest_tests.suggest(["research_runners/probe.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], ["tests/test_runner.py"])

    def test_arbitrary_parent_is_not_a_root_join(self) -> None:
        (self.root / "tests/test_random.py").write_text(
            'SCRIPT = OTHER / "scripts/validate_manifest.py"\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/validate_manifest.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], [])

    def test_direct_root_join_requires_exact_area_and_filename(self) -> None:
        (self.root / "tests/test_other.py").write_text(
            'SCRIPT = ROOT / "research_runners/validate_manifest.py"\n'
            'ANOTHER = ROOT / "scripts/validate_manifest_v2.py"\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/validate_manifest.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], [])

    def test_string_mentions_of_script_in_fixture_do_not_count_as_coverage(self) -> None:
        (self.root / "tests/test_reader.py").write_text(
            'assert "scripts/alpha.py" == "scripts/alpha.py"\n', encoding="utf-8"
        )
        found = suggest_tests.suggest(["scripts/alpha.py"], root=self.root)
        self.assertEqual(found["suggested_tests"], [])

    def test_no_optimistic_generic_package_or_textual_comment_match(self) -> None:
        (self.root / "tests/test_unrelated.py").write_text(
            '# scripts/alpha.py\nimport scripts\n', encoding="utf-8"
        )
        found = suggest_tests.suggest(["scripts/alpha.py"], root=self.root)
        self.assertEqual(found["suggested_tests"], [])
        self.assertIn("scripts/alpha.py", found["unmatched_paths"])

    def test_non_python_changed_files_require_manual_mapping(self) -> None:
        (self.root / "tests/test_any.py").write_text("pass\n", encoding="utf-8")
        found = suggest_tests.suggest(["landscape/source.json", "AGENTS.md"], root=self.root)
        self.assertEqual(found["command"], [])
        self.assertEqual(found["unmatched_paths"], ["AGENTS.md", "landscape/source.json"])
        self.assertIn("ADVISORY ONLY", found["verification"])

    def test_changed_test_included_even_without_imports(self) -> None:
        (self.root / "tests/test_alpha.py").write_text("pass\n", encoding="utf-8")
        found = suggest_tests.suggest(["tests/test_alpha.py"], root=self.root)
        self.assertEqual(found["suggested_tests"], ["tests/test_alpha.py"])

    def test_unsafe_paths_fail_without_reading_outside_repo(self) -> None:
        for unsafe in ("/tmp/private.py", "../private.py", "scripts/../private.py", "scripts\\x.py", "", "."):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
                suggest_tests.suggest([unsafe], root=self.root)

    def test_unparseable_tests_fail_closed(self) -> None:
        (self.root / "tests/test_broken.py").write_text("def broken(:\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unparseable test file"):
            suggest_tests.suggest(["scripts/alpha.py"], root=self.root)

    def test_order_and_deduplication_are_deterministic(self) -> None:
        (self.root / "tests/test_beta.py").write_text("import scripts.alpha\n", encoding="utf-8")
        (self.root / "tests/test_alpha.py").write_text("import scripts.alpha\n", encoding="utf-8")
        report = suggest_tests.suggest(["scripts/alpha.py", "scripts/alpha.py"], root=self.root)
        self.assertEqual(report["changed_paths"], ["scripts/alpha.py"])
        self.assertEqual(report["suggested_tests"], ["tests/test_alpha.py", "tests/test_beta.py"])

    def test_git_errors_are_not_silent(self) -> None:
        with self.assertRaisesRegex(ValueError, "Git changes"):
            suggest_tests.git_changed_paths(self.root, "no-such-base")

    def test_json_cli_writes_machine_readable_report(self) -> None:
        (self.root / "tests/test_alpha.py").write_text("pass\n", encoding="utf-8")
        output = StringIO()
        with mock.patch.object(suggest_tests, "ROOT", self.root), redirect_stdout(output):
            self.assertEqual(suggest_tests.main(["scripts/alpha.py", "--json"]), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["suggested_tests"], ["tests/test_alpha.py"])
        self.assertIn("run full", report["verification"])


if __name__ == "__main__":
    unittest.main()
