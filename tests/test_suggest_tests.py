# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic tests for conservative, static agent test suggestions."""

from __future__ import annotations

import json
import subprocess
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

    def test_unique_module_root_directory_alias_for_real_loader(self) -> None:
        (self.root / "tests/test_sample_candidates.py").write_text(
            'SCRIPTS = ROOT / "scripts"\n'
            'SPEC = importlib.util.spec_from_file_location('
            '"audit_sample_candidates", SCRIPTS / "audit_sample_candidates.py")\n',
            encoding="utf-8",
        )
        result = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(result["suggested_tests"], ["tests/test_sample_candidates.py"])

    def test_root_directory_alias_works_for_research_runners(self) -> None:
        (self.root / "tests/test_reader.py").write_text(
            'RUNNERS = ROOT / "research_runners"\n'
            'SCRIPT = RUNNERS / "probe_source.py"\n', encoding="utf-8"
        )
        result = suggest_tests.suggest(["research_runners/probe_source.py"], root=self.root)
        self.assertEqual(result["suggested_tests"], ["tests/test_reader.py"])

    def test_root_directory_alias_must_not_be_reassigned(self) -> None:
        (self.root / "tests/test_decoy.py").write_text(
            'SCRIPTS = ROOT / "scripts"\n'
            'SCRIPTS = OTHER / "scripts"\n'
            'SCRIPT = SCRIPTS / "audit_sample_candidates.py"\n', encoding="utf-8"
        )
        result = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(result["suggested_tests"], [])

    def test_non_root_or_different_directory_alias_does_not_match(self) -> None:
        (self.root / "tests/test_decoy.py").write_text(
            'OTHER_SCRIPTS = OTHER / "scripts"\n'
            'RUNNERS = ROOT / "research_runners"\n'
            'SCRIPT = OTHER_SCRIPTS / "audit_sample_candidates.py"\n'
            'ANOTHER = RUNNERS / "audit_sample_candidates.py"\n', encoding="utf-8"
        )
        result = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(result["suggested_tests"], [])

    def test_function_local_alias_does_not_infer_module_provenance(self) -> None:
        (self.root / "tests/test_decoy.py").write_text(
            'def local():\n'
            '    SCRIPTS = ROOT / "scripts"\n'
            '    return SCRIPTS / "audit_sample_candidates.py"\n', encoding="utf-8"
        )
        result = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(result["suggested_tests"], [])

    def test_function_parameter_shadow_does_not_count_as_root_alias(self) -> None:
        (self.root / "tests/test_decoy.py").write_text(
            'SCRIPTS = ROOT / "scripts"\n'
            'def local(SCRIPTS):\n'
            '    return SCRIPTS / "audit_sample_candidates.py"\n', encoding="utf-8"
        )
        result = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(result["suggested_tests"], [])

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

    def test_split_root_join_does_not_match_unrelated_base(self) -> None:
        (self.root / "tests/test_decoy.py").write_text(
            'SCRIPT = OTHER / "scripts" / "alpha.py"\n', encoding="utf-8"
        )
        report = suggest_tests.suggest(["scripts/alpha.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], [])
        self.assertEqual(report["unmatched_paths"], ["scripts/alpha.py"])

    def test_split_root_join_does_not_match_nested_unrelated_base(self) -> None:
        (self.root / "tests/test_decoy.py").write_text(
            'SCRIPT = (ROOT / "private") / "scripts" / "alpha.py"\n', encoding="utf-8"
        )
        report = suggest_tests.suggest(["scripts/alpha.py"], root=self.root)
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

    def test_subprocess_script_path_detected(self) -> None:
        (self.root / "tests/test_manifest_contract.py").write_text(
            'import subprocess, sys\n'
            'result = subprocess.run(\n'
            '    [sys.executable, "scripts/manifest_identity.py", "--help"],\n'
            '    cwd=ROOT, check=False)\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/manifest_identity.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], ["tests/test_manifest_contract.py"])

    def test_subprocess_multiline_command_detected(self) -> None:
        (self.root / "tests/test_cli.py").write_text(
            'result = subprocess.run(\n'
            '    [\n'
            '        sys.executable,\n'
            '        "scripts/audit_sample_candidates.py",\n'
            '        "--json",\n'
            '    ], cwd=ROOT)\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], ["tests/test_cli.py"])

    def test_subprocess_other_directory_not_suggested(self) -> None:
        (self.root / "tests/test_cli.py").write_text(
            'result = subprocess.run(\n'
            '    [sys.executable, "scripts/audit_sample_candidates.py"], cwd=OTHER)\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], [])

    def test_subprocess_without_explicit_root_not_suggested(self) -> None:
        (self.root / "tests/test_cli.py").write_text(
            'result = subprocess.run([sys.executable, "scripts/audit_sample_candidates.py"])\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], [])

    def test_subprocess_wrong_interpreter_not_suggested(self) -> None:
        (self.root / "tests/test_cli.py").write_text(
            'subprocess.run(["python", "scripts/audit_sample_candidates.py"], cwd=ROOT)\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], [])

    def test_subprocess_similar_script_path_not_suggested(self) -> None:
        (self.root / "tests/test_cli.py").write_text(
            'subprocess.run([sys.executable, "scripts/audit_sample_candidates_v2.py"], cwd=ROOT)\n',
            encoding="utf-8",
        )
        report = suggest_tests.suggest(["scripts/audit_sample_candidates.py"], root=self.root)
        self.assertEqual(report["suggested_tests"], [])


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

    def test_git_name_status_parser_handles_renames_and_copies(self) -> None:
        data = (b"R100\x00scripts/old.py\x00scripts/new.py\x00"
                b"C75\x00scripts/a.py\x00scripts/b.py\x00"
                b"M\x00tests/test_old.py\x00")
        paths = suggest_tests._diff_name_status_paths(data)
        self.assertEqual(paths, {
            "scripts/old.py", "scripts/new.py", "scripts/a.py", "scripts/b.py",
            "tests/test_old.py",
        })

    def test_git_name_status_parser_rejects_incomplete_or_unsafe_data(self) -> None:
        for malformed in (
            b"R100\x00scripts/old.py\x00",  # missing destination
            b"M\x00scripts/a.py",  # missing terminating NUL
            b"UNKNOWN\x00scripts/a.py\x00",
            b"A\x00../private.py\x00",
        ):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                suggest_tests._diff_name_status_paths(malformed)

    def test_git_renames_keep_old_and_new_paths_for_test_selection(self) -> None:
        def git(*args: str) -> None:
            subprocess.run(["git", *args], cwd=self.root, check=True,
                           capture_output=True)

        git("init", "-q")
        git("config", "user.email", "agent-tests@example.invalid")
        git("config", "user.name", "Synthetic Agent Test")
        (self.root / "scripts").mkdir()
        (self.root / "scripts/old.py").write_text("def sample(): return 1\n", encoding="utf-8")
        (self.root / "tests/test_old.py").write_text("from scripts import old\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "baseline")
        git("branch", "baseline")
        (self.root / "scripts/old.py").rename(self.root / "scripts/new.py")
        git("add", "-A")
        git("commit", "-qm", "rename")
        paths = suggest_tests.git_changed_paths(self.root, "baseline")
        self.assertEqual(paths, ["scripts/new.py", "scripts/old.py"])
        report = suggest_tests.suggest(paths, root=self.root)
        self.assertIn("tests/test_old.py", report["suggested_tests"])
        (self.root / "scripts/new.py").rename(self.root / "scripts/final.py")
        git("add", "-A")
        (self.root / "scripts/untracked.py").write_text("# untracked\n", encoding="utf-8")
        self.assertEqual(
            suggest_tests.git_changed_paths(self.root, "baseline"),
            ["scripts/final.py", "scripts/new.py", "scripts/old.py", "scripts/untracked.py"],
        )

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
