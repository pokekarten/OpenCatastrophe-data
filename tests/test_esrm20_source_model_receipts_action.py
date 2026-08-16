# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from unittest import mock

from scripts import run_esrm20_source_model_receipts_action as subject

EXECUTION_SHA = "1" * 40
OLD_SHA = "2" * 40
NOW = "2026-08-16T23:30:00Z"


class FakeResponse:
    def __init__(self, url: str, payload: bytes):
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self.headers = {"Content-Length": str(len(payload)), "Content-Type": "application/xml"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        if size < 0:
            size = len(self._payload) - self._offset
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


class SequenceOpener:
    def __init__(self, payloads: list[bytes]):
        self.payloads = list(payloads)
        self.urls: list[str] = []

    def __call__(self, request, timeout: float):
        if not self.payloads:
            raise AssertionError("unexpected extra provider call")
        self.urls.append(request.full_url)
        return FakeResponse(request.full_url, self.payloads.pop(0))


def request_body(sha: str = EXECUTION_SHA) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True, separators=(",", ":"))


def synthetic_profile() -> dict:
    receipts = [
        {
            "repository_path": path,
            "retrieved_at": NOW,
            "byte_count": index + 1,
            "sha256": hashlib.sha256(path.encode("utf-8")).hexdigest(),
        }
        for index, path in enumerate(subject.SOURCE_MODEL_PATHS)
    ]
    return {
        "schema_version": subject.PROFILE_SCHEMA_VERSION,
        "source_issue": subject.SOURCE_ISSUE,
        "parent_science_issue": subject.PARENT_SCIENCE_ISSUE,
        "source_profile_result_comment_id": subject.SOURCE_PROFILE_RESULT_COMMENT_ID,
        "dataset_id": subject.DATASET_ID,
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "source_model_paths": list(subject.SOURCE_MODEL_PATHS),
        "receipts": receipts,
        "receipt_count": len(receipts),
        "total_byte_count": sum(item["byte_count"] for item in receipts),
        "receipt_set_sha256": subject._receipt_set_sha(receipts),
        "provider_file_bytes_read": True,
        "raw_xml_returned": False,
        "source_model_content_profiled": False,
        "hdf5_companions_inferred": False,
        "external_bytes_persisted": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def result_body(sha: str = EXECUTION_SHA, *, target_sha: str | None = None) -> str:
    result = {
        **subject._base_result(execution_sha=sha),
        "status": "pass",
        "failure_class": None,
        "profile": synthetic_profile(),
    }
    if target_sha is not None:
        result["target_sha"] = target_sha
    return subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))


class SourceModelReceiptActionTests(unittest.TestCase):
    def test_source_paths_are_exact_source_derived_set(self) -> None:
        self.assertEqual(len(subject.SOURCE_MODEL_PATHS), 10)
        self.assertEqual(len(set(subject.SOURCE_MODEL_PATHS)), 10)
        self.assertTrue(all(path.startswith("Hazard/source_models/") and path.endswith(".xml") for path in subject.SOURCE_MODEL_PATHS))

    def test_raw_url_is_fixed_to_allowlisted_path_and_immutable_commit(self) -> None:
        url = subject._raw_url(subject.SOURCE_MODEL_PATHS[0])
        self.assertIn("/api/v4/projects/269/repository/files/", url)
        self.assertIn("ref=" + subject.COMMIT_SHA, url)
        with self.assertRaises(subject.SourceModelReceiptError):
            subject._raw_url("Hazard/source_models/not-derived.xml")

    def test_acquire_receipts_streams_all_ten_without_returning_xml(self) -> None:
        payloads = [(f"<nrml id='{index}'/>".encode("utf-8")) for index in range(10)]
        opener = SequenceOpener(payloads.copy())
        profile = subject.acquire_receipts(opener=opener, monotonic=lambda: 0.0, now=lambda: NOW)
        self.assertEqual(profile["receipt_count"], 10)
        self.assertEqual(len(opener.urls), 10)
        self.assertEqual(profile["total_byte_count"], sum(len(item) for item in payloads))
        self.assertEqual(profile["receipts"][0]["sha256"], hashlib.sha256(payloads[0]).hexdigest())
        self.assertFalse(profile["raw_xml_returned"])
        self.assertFalse(profile["source_model_content_profiled"])
        self.assertFalse(profile["hdf5_companions_inferred"])
        self.assertFalse(profile["transitive_dependency_byte_closure_verified"])
        self.assertFalse(profile["runtime_compatibility_verified"])
        encoded = json.dumps(profile)
        self.assertNotIn("<nrml", encoded)

    def test_request_is_exact_head_and_has_no_provider_selector(self) -> None:
        parsed = subject.validate_request(request_body(), expected_issue=481, execution_sha=EXECUTION_SHA)
        self.assertEqual(set(parsed), subject._REQUEST_FIELDS)
        for forbidden in ("path", "project_id", "url", "commit_sha", "operation"):
            self.assertNotIn(forbidden, parsed)
        with self.assertRaises(subject.SourceModelReceiptError):
            subject.validate_request(request_body(OLD_SHA), expected_issue=481, execution_sha=EXECUTION_SHA)

    def test_profile_validator_rejects_scientific_authority_widening(self) -> None:
        profile = synthetic_profile()
        subject.validate_profile(profile)
        for field in (
            "source_model_content_profiled",
            "hdf5_companions_inferred",
            "transitive_dependency_byte_closure_verified",
            "runtime_compatibility_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            mutated = dict(profile)
            mutated[field] = True
            with self.subTest(field=field), self.assertRaises(subject.SourceModelReceiptError):
                subject.validate_profile(mutated)

    def test_historical_valid_result_does_not_deduplicate_new_head(self) -> None:
        comments = [{"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": result_body(OLD_SHA)}]
        with mock.patch.object(subject, "_FETCH_COMMENTS", return_value=comments):
            self.assertFalse(subject.has_terminal_result(repository="o/r", token="x", execution_sha=EXECUTION_SHA))

    def test_same_head_valid_result_deduplicates(self) -> None:
        comments = [{"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": result_body(EXECUTION_SHA)}]
        with mock.patch.object(subject, "_FETCH_COMMENTS", return_value=comments):
            self.assertTrue(subject.has_terminal_result(repository="o/r", token="x", execution_sha=EXECUTION_SHA))

    def test_internally_inconsistent_historical_sha_fails_closed(self) -> None:
        comments = [{
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": result_body(OLD_SHA, target_sha="3" * 40),
        }]
        with mock.patch.object(subject, "_FETCH_COMMENTS", return_value=comments):
            with self.assertRaises(subject.SourceModelReceiptError):
                subject.has_terminal_result(repository="o/r", token="x", execution_sha=EXECUTION_SHA)

    def test_blocked_result_is_atomic(self) -> None:
        result = {
            **subject._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "source_model_receipt_failure",
            "profile": None,
        }
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertTrue(subject.parse_terminal_result(body, execution_sha=EXECUTION_SHA))
        result["profile"] = synthetic_profile()
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        with self.assertRaises(subject.SourceModelReceiptError):
            subject.parse_terminal_result(body, execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
