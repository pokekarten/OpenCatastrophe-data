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

    def test_every_blocked_directory_is_enforced_by_the_central_policy(self) -> None:
        for segment in hygiene.BLOCKED_SEGMENTS:
            with self.subTest(segment=segment):
                problems = hygiene.check_relative_path(Path(segment) / "fixture.txt")
                self.assertIn("tracked file is inside a blocked private/data/output directory", problems)

    def test_every_blocked_suffix_is_enforced_by_the_central_policy(self) -> None:
        for suffix in hygiene.BLOCKED_SUFFIXES:
            with self.subTest(suffix=suffix):
                problems = hygiene.check_relative_path(Path(f"fixture{suffix}"))
                self.assertIn(f"tracked high-risk binary/data suffix: {suffix}", problems)

    def test_every_reserved_local_filename_is_enforced_by_the_central_policy(self) -> None:
        for name in hygiene.BLOCKED_NAMES:
            with self.subTest(name=name):
                problems = hygiene.check_relative_path(Path(name))
                self.assertIn("tracked filename is reserved for local credentials/configuration", problems)
        for name in (".env.production", ".coverage.worker"):
            with self.subTest(name=name):
                problems = hygiene.check_relative_path(Path(name))
                self.assertIn("tracked filename is reserved for local credentials/configuration", problems)

    def test_every_secret_pattern_has_a_synthetic_detection_case(self) -> None:
        cases = {
            "private key": ("-----BEGIN " + "PRIVATE KEY-----").encode("ascii"),
            "AWS access key": (("AK" + "IA") + ("A" * 16)).encode("ascii"),
            "GitHub token": (("gh" + "p_") + ("A" * 32)).encode("ascii"),
            "Slack token": (("xo" + "xb-") + ("A" * 24)).encode("ascii"),
            "Google API key": (("AI" + "za") + ("A" * 32)).encode("ascii"),
            "OpenAI-style secret": (("sk-" + "proj-") + ("A" * 24)).encode("ascii"),
            "PyPI token": (("py" + "pi-") + ("A" * 24)).encode("ascii"),
            "Hugging Face token": (("h" + "f_") + ("A" * 24)).encode("ascii"),
            "Stripe live secret": (("sk_" + "live_") + ("A" * 24)).encode("ascii"),
        }
        self.assertEqual(set(cases), set(hygiene.SECRET_PATTERNS))
        for label, content in cases.items():
            with self.subTest(label=label):
                self.assertIn(f"possible {label}", hygiene.check_file(self._file(content), git_mode="100644"))

    def test_every_local_path_pattern_has_a_synthetic_detection_case(self) -> None:
        cases = {
            "macOS user path": (("/Us" + "ers/") + "example/private.txt").encode("ascii"),
            "Linux user path": (("/ho" + "me/") + "example/private.txt").encode("ascii"),
            "Windows user path": (("C:\\" + "Users\\") + "Example\\private.txt").encode("ascii"),
            "file URL": (("fi" + "le://") + "localhost/private.txt").encode("ascii"),
        }
        self.assertEqual(set(cases), set(hygiene.LOCAL_PATH_PATTERNS))
        for label, content in cases.items():
            with self.subTest(label=label):
                self.assertIn(f"possible {label}", hygiene.check_file(self._file(content), git_mode="100644"))

    def test_every_private_endpoint_pattern_has_a_synthetic_detection_case(self) -> None:
        cases = {
            "localhost endpoint": ("https://" + "local" + "host:8443/private").encode("ascii"),
            "IPv4 loopback endpoint": ("https://" + "127.0.0.1/private").encode("ascii"),
            "RFC1918 10/8 endpoint": ("https://" + "10.1.2.3/private").encode("ascii"),
            "RFC1918 172.16/12 endpoint": ("https://" + "172.16.1.2/private").encode("ascii"),
            "RFC1918 192.168/16 endpoint": ("https://" + "192.168.1.2/private").encode("ascii"),
            "IPv6 loopback endpoint": ("https://" + "[::1]/private").encode("ascii"),
        }
        self.assertEqual(set(cases), set(hygiene.PRIVATE_ENDPOINT_PATTERNS))
        for label, content in cases.items():
            with self.subTest(label=label):
                self.assertIn(f"possible {label}", hygiene.check_file(self._file(content), git_mode="100644"))

    def test_every_signed_url_pattern_has_a_synthetic_detection_case(self) -> None:
        cases = {
            "AWS signed URL": (
                "https://example.invalid/object?X-Amz-" + "Signature=" + ("a" * 64)
            ).encode("ascii"),
            "Google signed URL": (
                "https://example.invalid/object?X-Goog-" + "Signature=" + ("a" * 64)
            ).encode("ascii"),
            "Azure-style signed URL": (
                "https://example.invalid/object?" + "sig=" + ("A" * 24)
            ).encode("ascii"),
            "access-token URL": (
                "https://example.invalid/object?access_" + "token=" + ("A" * 24)
            ).encode("ascii"),
        }
        self.assertEqual(set(cases), set(hygiene.SIGNED_URL_PATTERNS))
        for label, content in cases.items():
            with self.subTest(label=label):
                self.assertIn(f"possible {label}", hygiene.check_file(self._file(content), git_mode="100644"))

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
