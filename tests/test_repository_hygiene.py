# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_repository_hygiene.py"
SPEC = importlib.util.spec_from_file_location("check_repository_hygiene", MODULE_PATH)
assert SPEC and SPEC.loader
hygiene = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = hygiene
SPEC.loader.exec_module(hygiene)


class RepositoryHygieneTests(unittest.TestCase):
    def _file(self, content: bytes = b"safe text\n") -> Path:
        tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "fixture.txt"
        path.write_bytes(content)
        return path

    def test_safe_regular_text_file_is_accepted(self) -> None:
        path = self._file()
        self.assertEqual(hygiene.check_file(path, git_mode="100644"), [])

    def test_blocked_directory_and_payload_suffix_are_reported(self) -> None:
        problems = hygiene.check_relative_path(Path("quarantine/source.zip"))
        self.assertIn("tracked file is inside a blocked private/data/output directory", problems)
        self.assertIn("tracked high-risk binary/data suffix: .zip", problems)

    def test_constructed_github_token_is_detected(self) -> None:
        token = ("gh" + "p_") + ("A" * 32)
        path = self._file(token.encode("ascii"))
        self.assertIn("possible GitHub token", hygiene.check_file(path, git_mode="100644"))

    def test_constructed_local_user_path_is_detected(self) -> None:
        local_path = ("/ho" + "me/example/") + "private.txt"
        path = self._file(local_path.encode("ascii"))
        self.assertIn("possible Linux user path", hygiene.check_file(path, git_mode="100644"))

    def test_constructed_signed_url_is_detected(self) -> None:
        signed_url = "https://example.invalid/object?X-Amz-" + "Signature=" + ("a" * 64)
        path = self._file(signed_url.encode("ascii"))
        self.assertIn("possible AWS signed URL", hygiene.check_file(path, git_mode="100644"))

    def test_symlink_and_non_regular_git_modes_are_rejected(self) -> None:
        target = self._file()
        link = target.with_name("fixture-link.txt")
        link.symlink_to(target)
        self.assertIn("tracked symlink is not allowed", hygiene.check_file(link, git_mode="120000"))
        self.assertIn(
            "tracked path uses an unsupported non-regular Git mode",
            hygiene.check_file(target, git_mode="160000"),
        )


if __name__ == "__main__":
    unittest.main()
