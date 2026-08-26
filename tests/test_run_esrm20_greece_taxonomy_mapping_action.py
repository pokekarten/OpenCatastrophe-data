# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from unittest import mock

from scripts import run_esrm20_greece_taxonomy_mapping_action as subject


class _Response:
    def __init__(self, url: str, raw: bytes):
        self.status = 200
        self._url = url
        self._raw = raw
        self._offset = 0
        self.headers = {"Content-Length": str(len(raw))}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._raw):
            return b""
        if size < 0:
            size = len(self._raw) - self._offset
        chunk = self._raw[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


class GreeceTaxonomyMappingActionTests(unittest.TestCase):
    SHA = "a" * 40
    PRIOR_SHA = "b" * 40

    def request_body(self) -> str:
        payload = {
            "schema_version": subject.REQUEST_SCHEMA_VERSION,
            "action": subject.ACTION,
            "issue": subject.CONTROL_ISSUE,
            "target_sha": self.SHA,
            "dataset_id": subject.DATASET_ID,
            "requester": "unit-test",
        }
        return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))

    def trusted_comment(self, body: str) -> dict[str, object]:
        return {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": body}

    def blocked_terminal_body(self, sha: str) -> str:
        payload = subject._base_result(execution_sha=sha)
        payload.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "component_compatibility_established": False,
            }
        )
        return subject.RESULT_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))

    def pass_terminal_body(self, sha: str) -> str:
        payload = subject._base_result(execution_sha=sha)
        payload.update(
            {
                "status": "pass",
                "failure_class": None,
                "component_compatibility_established": True,
            }
        )
        return subject.RESULT_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))

    def test_validate_request_binds_execution_sha(self):
        result = subject.validate_request(
            self.request_body(),
            expected_issue=subject.CONTROL_ISSUE,
            execution_sha=self.SHA,
        )
        self.assertEqual(result["target_sha"], self.SHA)

    def test_validate_request_rejects_duplicate_json_key(self):
        payload = self.request_body().replace(
            '"requester":"unit-test"',
            '"requester":"unit-test","requester":"duplicate"',
        )
        with self.assertRaisesRegex(subject.GreeceTaxonomyMappingActionError, "duplicate JSON key"):
            subject.validate_request(
                payload,
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=self.SHA,
            )

    def test_fixed_acquisition_accepts_exact_bytes(self):
        raw = b"abc"
        target = ("Exposure/test.csv", len(raw), hashlib.sha256(raw).hexdigest())
        url = (
            f"{subject.PROVIDER_ROOT}/api/v4/projects/{subject.PROJECT_ID}/repository/files/"
            f"Exposure%2Ftest.csv/raw?ref={subject.COMMIT_SHA}"
        )

        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            self.assertEqual(request.full_url, url)
            return _Response(url, raw)

        with (
            mock.patch.object(subject, "_CANONICAL_TARGETS", (target,)),
            mock.patch.object(subject, "_require_frozen_authority", return_value=None),
        ):
            result = subject._acquire_inputs_for_test(opener=opener, monotonic=lambda: 0.0)
        self.assertEqual(result, {"Exposure/test.csv": raw})

    def test_fixed_acquisition_rejects_byte_count_drift(self):
        raw = b"abc"
        target = ("Exposure/test.csv", 4, hashlib.sha256(b"abcd").hexdigest())
        url = subject._raw_file_url.__globals__["PROVIDER_ROOT"]

        def opener(request, timeout):
            return _Response(request.full_url, raw)

        with (
            mock.patch.object(subject, "_CANONICAL_TARGETS", (target,)),
            mock.patch.object(subject, "_require_frozen_authority", return_value=None),
        ):
            with self.assertRaisesRegex(subject.transport.EfehrAcquisitionError, "byte count"):
                subject._acquire_inputs_for_test(opener=opener, monotonic=lambda: 0.0)
        self.assertTrue(url.startswith("https://"))

    def test_fixed_acquisition_rejects_sha_drift(self):
        raw = b"abc"
        target = ("Exposure/test.csv", len(raw), "0" * 64)

        def opener(request, timeout):
            return _Response(request.full_url, raw)

        with (
            mock.patch.object(subject, "_CANONICAL_TARGETS", (target,)),
            mock.patch.object(subject, "_require_frozen_authority", return_value=None),
        ):
            with self.assertRaisesRegex(subject.transport.EfehrAcquisitionError, "SHA-256"):
                subject._acquire_inputs_for_test(opener=opener, monotonic=lambda: 0.0)

    def test_run_mapping_pass_is_non_disclosive(self):
        mapping_path = subject.exact_join._MAPPING_REPOSITORY_PATH
        acquired = {
            path: b"exposure" for path, _, _ in subject.exposure_source.RECEIPTS
        }
        acquired[mapping_path] = b"mapping"
        joined = {
            "classification_counts": {"resolved": 10, "unsupported": 0, "ambiguous": 0},
            "taxonomy_union_count": 10,
            "all_taxonomies_resolved": True,
            "mapping_target_risk_ids": ["A", "B"],
            "records": [{"provider": "row-must-not-leak"}],
        }
        with (
            mock.patch.object(subject, "acquire_inputs", return_value=acquired),
            mock.patch.object(
                subject.join,
                "join_verified_greece_taxonomy_mapping",
                return_value=joined,
            ),
        ):
            result = subject.run_mapping(execution_sha=self.SHA)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["component_compatibility_established"])
        for field in subject._DERIVED_PRIVATE_FIELDS:
            self.assertNotIn(field, result)
        self.assertNotIn("records", result)
        self.assertNotIn("row-must-not-leak", json.dumps(result, sort_keys=True))
        self.assertNotIn('"A"', json.dumps(result, sort_keys=True))
        for field in subject._FALSE_FIELDS:
            self.assertIs(result[field], False)

    def test_unresolved_mapping_is_bounded_component_failure(self):
        mapping_path = subject.exact_join._MAPPING_REPOSITORY_PATH
        acquired = {
            path: b"exposure" for path, _, _ in subject.exposure_source.RECEIPTS
        }
        acquired[mapping_path] = b"mapping"
        joined = {
            "classification_counts": {"resolved": 7, "unsupported": 2, "ambiguous": 1},
            "taxonomy_union_count": 10,
            "all_taxonomies_resolved": False,
            "mapping_target_risk_ids": ["A", "B"],
        }
        with (
            mock.patch.object(subject, "acquire_inputs", return_value=acquired),
            mock.patch.object(
                subject.join,
                "join_verified_greece_taxonomy_mapping",
                return_value=joined,
            ),
        ):
            result = subject.run_mapping(execution_sha=self.SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "component_compatibility_failure")
        self.assertFalse(result["component_compatibility_established"])
        for field in subject._DERIVED_PRIVATE_FIELDS:
            self.assertNotIn(field, result)

    def test_acquisition_failure_is_bounded(self):
        with mock.patch.object(
            subject,
            "acquire_inputs",
            side_effect=subject.transport.EfehrAcquisitionError("secret provider detail"),
        ):
            result = subject.run_mapping(execution_sha=self.SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertNotIn("secret provider detail", json.dumps(result, sort_keys=True))
        for field in subject._DERIVED_PRIVATE_FIELDS:
            self.assertNotIn(field, result)

    def test_component_failure_is_bounded(self):
        mapping_path = subject.exact_join._MAPPING_REPOSITORY_PATH
        acquired = {
            path: b"exposure" for path, _, _ in subject.exposure_source.RECEIPTS
        }
        acquired[mapping_path] = b"mapping"
        with (
            mock.patch.object(subject, "acquire_inputs", return_value=acquired),
            mock.patch.object(
                subject.join,
                "join_verified_greece_taxonomy_mapping",
                side_effect=subject.join.GreeceTaxonomyMappingJoinError("private row detail"),
            ),
        ):
            result = subject.run_mapping(execution_sha=self.SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "component_compatibility_failure")
        self.assertFalse(result["component_compatibility_established"])
        self.assertNotIn("private row detail", json.dumps(result, sort_keys=True))
        for field in subject._DERIVED_PRIVATE_FIELDS:
            self.assertNotIn(field, result)

    def test_terminal_result_is_bounded_before_json(self):
        body = subject.RESULT_MARKER + "\n" + ("é" * 30_000)
        with self.assertRaisesRegex(subject.GreeceTaxonomyMappingActionError, "byte bound"):
            subject._parse_trusted_terminal_result(body)

    def test_prior_sha_terminal_is_valid_non_match(self):
        comments = [self.trusted_comment(self.blocked_terminal_body(self.PRIOR_SHA))]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertFalse(
                subject.has_terminal_result(
                    repository="owner/repo",
                    token="token",
                    execution_sha=self.SHA,
                )
            )

    def test_trusted_pass_rejects_derived_detail(self):
        payload = subject._base_result(execution_sha=self.SHA)
        payload.update(
            {
                "status": "pass",
                "failure_class": None,
                "component_compatibility_established": True,
                "classification_counts": {"resolved": 1, "unsupported": 0, "ambiguous": 0},
            }
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))
        with self.assertRaisesRegex(subject.GreeceTaxonomyMappingActionError, "fields drifted"):
            subject._parse_trusted_terminal_result(body)

    def test_trusted_pass_accepts_non_disclosive_terminal(self):
        self.assertEqual(subject._parse_trusted_terminal_result(self.pass_terminal_body(self.SHA)), self.SHA)

    def test_summary_rejects_non_exhaustive_counts(self):
        with self.assertRaisesRegex(subject.GreeceTaxonomyMappingActionError, "not exhaustive"):
            subject._validate_summary(
                {
                    "classification_counts": {
                        "resolved": 1,
                        "unsupported": 0,
                        "ambiguous": 0,
                    },
                    "taxonomy_union_count": 2,
                    "all_taxonomies_resolved": True,
                    "mapping_target_risk_ids": ["A"],
                }
            )


if __name__ == "__main__":
    unittest.main()
