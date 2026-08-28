# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import io
import json
import unittest
from unittest import mock

from scripts import profile_esrm20_project278_manual as parent
from scripts import profile_esrm20_project278_manual_context as subject


_PAGE_TEXT = [
    (
        "Exposure-to-site tool and site model use longitude and latitude coordinates "
        "with WGS 84 projection. A shapefile is joined to exposure locations."
    ),
    "Vs30, slope, geology and xvf are sampled and assigned for the site model.",
]


class _Page:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _Reader:
    is_encrypted = False

    def __init__(self, _stream: io.BytesIO, *, strict: bool) -> None:
        assert strict is True
        self.pages = [_Page(text) for text in _PAGE_TEXT]


def _normalized_identity() -> tuple[int, str]:
    pages = [" ".join(text.split()).casefold() for text in _PAGE_TEXT]
    return sum(len(page) for page in pages), hashlib.sha256("\n".join(pages).encode()).hexdigest()


class Project278ManualContextProfileTests(unittest.TestCase):
    SHA = "a" * 40

    def _request(self) -> str:
        return subject.REQUEST_MARKER + "\n" + json.dumps(
            {
                "schema_version": subject.REQUEST_SCHEMA_VERSION,
                "action": subject.ACTION,
                "issue": subject.CONTROL_ISSUE,
                "target_sha": self.SHA,
                "dataset_id": subject.DATASET_ID,
                "requester": "TEST",
            },
            separators=(",", ":"),
        )

    def _synthetic_profile(self) -> dict[str, object]:
        payload = b"%PDF synthetic context profile"
        character_count, text_digest = _normalized_identity()
        return subject._context_profile_for_test(
            payload,
            expected_byte_count=len(payload),
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            reader_factory=_Reader,
            parser_version="test",
            expected_page_count=2,
            expected_character_count=character_count,
            expected_text_sha256=text_digest,
        )

    def test_request_is_exact_and_sha_bound(self) -> None:
        parsed = subject.validate_request(
            self._request(), expected_issue=subject.CONTROL_ISSUE, execution_sha=self.SHA
        )
        self.assertEqual(parsed["target_sha"], self.SHA)
        with self.assertRaises(subject.Project278ManualContextProfileError):
            subject.validate_request(
                self._request(), expected_issue=subject.CONTROL_ISSUE, execution_sha="b" * 40
            )

    def test_context_profile_returns_only_bounded_non_text_evidence(self) -> None:
        profile = self._synthetic_profile()

        self.assertEqual(profile["focus_summary"]["wgs84"]["pages"], [1])
        self.assertEqual(profile["focus_summary"]["vs30"]["pages"], [2])
        self.assertGreaterEqual(profile["focus_summary"]["site_model"]["count"], 2)
        wgs_record = next(record for record in profile["records"] if record["focus"] == "wgs84")
        self.assertGreaterEqual(wgs_record["nearby_terms"]["longitude"], 1)
        self.assertGreaterEqual(wgs_record["nearby_terms"]["latitude"], 1)
        self.assertGreaterEqual(wgs_record["nearby_terms"]["projection"], 1)
        self.assertIs(profile["raw_text_exposed"], False)
        self.assertIs(profile["snippets_exposed"], False)

        serialized = json.dumps(profile, sort_keys=True)
        self.assertNotIn("Exposure-to-site tool", serialized)
        self.assertNotIn("sampled and assigned", serialized)

    def test_context_profile_requires_exact_prior_text_identity(self) -> None:
        payload = b"%PDF synthetic context profile"
        character_count, text_digest = _normalized_identity()
        with self.assertRaisesRegex(
            subject.Project278ManualContextProfileError,
            "trusted extracted-text digest drifted",
        ):
            subject._context_profile_for_test(
                payload,
                expected_byte_count=len(payload),
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                reader_factory=_Reader,
                parser_version="test",
                expected_page_count=2,
                expected_character_count=character_count,
                expected_text_sha256="0" * 64 if text_digest != "0" * 64 else "1" * 64,
            )

    def test_run_blocks_provider_failure_before_context_parsing(self) -> None:
        with mock.patch.object(
            subject.parent,
            "acquire_verified_pdf_bytes",
            side_effect=parent.Project278ManualContentProfileError("blocked"),
        ), mock.patch.object(subject, "profile_verified_pdf_context") as profiler:
            result = subject.run_context_profile(execution_sha=self.SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIs(result["context_profiled"], False)
        profiler.assert_not_called()

    def test_terminal_validator_rejects_unapproved_nearby_vocabulary(self) -> None:
        records = []
        summary = {}
        for index, focus in enumerate(subject._FOCUS_KEYS, start=1):
            page = min(index, subject.EXPECTED_PAGE_COUNT)
            summary[focus] = {"count": 1, "pages": [page]}
            records.append(
                {
                    "focus": focus,
                    "page": page,
                    "occurrence": 1,
                    "window_utf8_bytes": 10,
                    "window_sha256": hashlib.sha256(f"{focus}-window".encode()).hexdigest(),
                    "nearby_terms": {focus if focus in subject._CONTEXT_PATTERNS else "coordinate": 1},
                }
            )
        profile = {
            "schema_version": subject.CONTEXT_PROFILE_SCHEMA_VERSION,
            "parser": {
                "package": parent.PARSER_PACKAGE,
                "version": parent.EXPECTED_PARSER_VERSION,
            },
            "source_text": {
                "page_count": subject.EXPECTED_PAGE_COUNT,
                "normalized_text_character_count": subject.EXPECTED_NORMALIZED_TEXT_CHARACTER_COUNT,
                "normalized_text_sha256": subject.EXPECTED_NORMALIZED_TEXT_SHA256,
            },
            "focus_terms": list(subject._FOCUS_KEYS),
            "vocabulary": list(subject._CONTEXT_KEYS),
            "window_radius_chars": subject.CONTEXT_RADIUS_CHARS,
            "focus_summary": summary,
            "records": records,
            "raw_text_exposed": False,
            "snippets_exposed": False,
        }
        result = subject._base_result(execution_sha=self.SHA)
        result.update(
            {
                "status": "pass",
                "failure_class": None,
                "context_profiled": True,
                "context_profile": profile,
            }
        )
        self.assertTrue(subject._validate_terminal_payload(result, execution_sha=self.SHA))
        records[0]["nearby_terms"]["provider_secret"] = 1
        with self.assertRaises(subject.Project278ManualContextProfileError):
            subject._validate_terminal_payload(result, execution_sha=self.SHA)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
