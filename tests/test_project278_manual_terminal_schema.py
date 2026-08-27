# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest

from scripts import profile_esrm20_project278_manual as subject


class Project278ManualTerminalSchemaTests(unittest.TestCase):
    SHA = "a" * 40

    def _pass_result(self) -> dict[str, object]:
        result = subject._base_result(execution_sha=self.SHA)
        result.update(
            {
                "status": "pass",
                "failure_class": None,
                "pdf_content_profiled": True,
                "content_profile": {
                    "schema_version": subject.PROFILE_SCHEMA_VERSION,
                    "parser": {
                        "package": subject.PARSER_PACKAGE,
                        "version": subject.EXPECTED_PARSER_VERSION,
                    },
                    "page_count": 2,
                    "normalized_text_character_count": 42,
                    "normalized_text_sha256": "b" * 64,
                    "mention_pages": {key: [] for key in subject._MENTION_KEYS},
                    "raw_text_exposed": False,
                },
            }
        )
        return result

    def _blocked_result(self) -> dict[str, object]:
        result = subject._base_result(execution_sha=self.SHA)
        result.update(
            {
                "status": "blocked",
                "failure_class": "pdf_parse_failure",
                "content_profile": None,
            }
        )
        return result

    def test_exact_pass_and_blocked_shapes_are_accepted(self) -> None:
        self.assertTrue(
            subject._validate_terminal_payload(self._pass_result(), execution_sha=self.SHA)
        )
        self.assertTrue(
            subject._validate_terminal_payload(self._blocked_result(), execution_sha=self.SHA)
        )

    def test_extra_top_level_fields_fail_closed(self) -> None:
        for result in (self._pass_result(), self._blocked_result()):
            mutated = copy.deepcopy(result)
            mutated["raw_text"] = "must never become publishable"
            with self.assertRaises(subject.Project278ManualContentProfileError):
                subject._validate_terminal_payload(mutated, execution_sha=self.SHA)

    def test_extra_nested_profile_or_parser_fields_fail_closed(self) -> None:
        result = self._pass_result()
        profile = result["content_profile"]
        assert isinstance(profile, dict)
        profile["raw_text"] = "must never become publishable"
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._validate_terminal_payload(result, execution_sha=self.SHA)

        result = self._pass_result()
        profile = result["content_profile"]
        assert isinstance(profile, dict)
        parser = profile["parser"]
        assert isinstance(parser, dict)
        parser["build"] = "unexpected"
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._validate_terminal_payload(result, execution_sha=self.SHA)

    def test_parser_identity_and_digest_are_exact(self) -> None:
        result = self._pass_result()
        profile = result["content_profile"]
        assert isinstance(profile, dict)
        parser = profile["parser"]
        assert isinstance(parser, dict)
        parser["version"] = "6.16.1"
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._validate_terminal_payload(result, execution_sha=self.SHA)

        result = self._pass_result()
        profile = result["content_profile"]
        assert isinstance(profile, dict)
        profile["normalized_text_sha256"] = "not-a-digest"
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._validate_terminal_payload(result, execution_sha=self.SHA)

    def test_page_and_character_bounds_fail_closed(self) -> None:
        result = self._pass_result()
        profile = result["content_profile"]
        assert isinstance(profile, dict)
        profile["page_count"] = subject.MAX_PAGES + 1
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._validate_terminal_payload(result, execution_sha=self.SHA)

        result = self._pass_result()
        profile = result["content_profile"]
        assert isinstance(profile, dict)
        profile["normalized_text_character_count"] = subject.MAX_TOTAL_TEXT_CHARS + 1
        with self.assertRaises(subject.Project278ManualContentProfileError):
            subject._validate_terminal_payload(result, execution_sha=self.SHA)

    def test_mention_pages_must_be_unique_sorted_and_within_pdf(self) -> None:
        for pages in ([3], [2, 1], [1, 1]):
            result = self._pass_result()
            profile = result["content_profile"]
            assert isinstance(profile, dict)
            mentions = profile["mention_pages"]
            assert isinstance(mentions, dict)
            mentions[next(iter(subject._MENTION_KEYS))] = pages
            with self.assertRaises(subject.Project278ManualContentProfileError):
                subject._validate_terminal_payload(result, execution_sha=self.SHA)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
