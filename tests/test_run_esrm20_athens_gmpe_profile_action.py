# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import acquire_efehr_esrm20_athens_gmpe_profile as worker
from scripts import run_esrm20_athens_gmpe_profile_action as action


SHA = "a" * 40


class _Headers:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, name):
        return self._values.get(name)


class _Response:
    def __init__(self, url: str, payload: bytes):
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self.headers = _Headers({"Content-Length": str(len(payload))})

    def geturl(self):
        return self._url

    def read(self, size=-1):
        if self._offset >= len(self._payload):
            return b""
        if size is None or size < 0:
            size = len(self._payload) - self._offset
        start = self._offset
        end = min(len(self._payload), start + size)
        self._offset = end
        return self._payload[start:end]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _profile_payload():
    return {
        "schema_version": "oc-esrm20-scenario-v10-greece-gmpe-logic-tree-profile-v1",
        "byte_count": worker.EXPECTED_BYTE_COUNT,
        "sha256": worker.EXPECTED_SHA256,
        "nrml_namespace": "http://openquake.org/xmlns/nrml/0.5",
        "element_count": 8,
        "max_depth": 6,
        "branching_level_count": 1,
        "branch_set_count": 1,
        "branch_count": 2,
        "uncertainty_model_count": 2,
        "uncertainty_weight_count": 2,
        "non_whitespace_text_element_count": 4,
        "distinct_text_value_fingerprint_count": 4,
        "attribute_name_counts": {"branchID": 2},
        "raw_model_values_returned": False,
        "gmpe_semantics_verified": False,
        "gmpe_applicability_verified": False,
        "numerical_equivalence_verified": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _evidence():
    return {
        "schema_version": "oc-esrm20-athens-gmpe-profile-evidence-v1",
        "source_issue": worker.SOURCE_ISSUE,
        "receipt_issue": worker.RECEIPT_ISSUE,
        "dataset_id": worker.DATASET_ID,
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "release_tag": worker.RELEASE_TAG,
        "commit_sha": worker.COMMIT_SHA,
        "event_id": worker.EVENT_ID,
        "repository_path": worker.REPOSITORY_PATH,
        "git_blob_sha1": worker.GIT_BLOB_SHA1,
        "receipt_comment_id": worker.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": worker.RECEIPT_EXECUTION_SHA,
        "receipt_retrieved_at": worker.RECEIPT_RETRIEVED_AT,
        "byte_count": worker.EXPECTED_BYTE_COUNT,
        "sha256": worker.EXPECTED_SHA256,
        "profile": _profile_payload(),
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _request(target_sha=SHA):
    payload = {
        "schema_version": action.REQUEST_SCHEMA_VERSION,
        "action": action.ACTION,
        "issue": action.CONTROL_ISSUE,
        "target_sha": target_sha,
        "dataset_id": worker.DATASET_ID,
        "requester": "unit-test",
    }
    return action.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


class FixedWorkerTests(unittest.TestCase):
    def test_fixed_url_is_project_273_commit_and_exact_path(self):
        url = worker.raw_file_url()
        self.assertIn("/api/v4/projects/273/repository/files/", url)
        self.assertIn("ref=" + worker.COMMIT_SHA, url)
        self.assertIn("gmpe_logic_tree_5br_shallow_default.xml", url)
        self.assertNotIn("?ref=v1.0", url)

    def test_transient_acquisition_delegates_only_exact_sized_bytes(self):
        payload = b"x" * worker.EXPECTED_BYTE_COUNT
        seen = []

        def opener(request, timeout):
            seen.append((request.full_url, timeout))
            return _Response(request.full_url, payload)

        result = worker.acquire_and_profile_athens_gmpe(
            opener=opener,
            monotonic=lambda: 0.0,
            profiler=lambda raw: (_profile_payload() if raw == payload else (_ for _ in ()).throw(AssertionError())),
        )
        self.assertEqual(len(seen), 1)
        self.assertEqual(result["repository_path"], worker.REPOSITORY_PATH)
        self.assertEqual(result["byte_count"], 6490)
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertNotIn(payload[:20].decode(), repr(result))

    def test_short_stream_fails_before_profile(self):
        called = False
        payload = b"x" * (worker.EXPECTED_BYTE_COUNT - 1)

        def opener(request, timeout):
            return _Response(request.full_url, payload)

        def profiler(raw):
            nonlocal called
            called = True
            return _profile_payload()

        with self.assertRaises(worker.AthensGmpeProfileAcquisitionError):
            worker.acquire_and_profile_athens_gmpe(
                opener=opener,
                monotonic=lambda: 0.0,
                profiler=profiler,
            )
        self.assertFalse(called)


class ActionTests(unittest.TestCase):
    def test_request_is_exact_sha_bound(self):
        result = action.validate_request(_request(), expected_issue=285, execution_sha=SHA)
        self.assertEqual(result["target_sha"], SHA)
        with self.assertRaises(action.AthensGmpeProfileActionError):
            action.validate_request(_request("b" * 40), expected_issue=285, execution_sha=SHA)

    def test_pass_preserves_false_authority_ceilings(self):
        result = action._run(execution_sha=SHA, acquirer=_evidence)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["gmpe_semantics_verified"])
        self.assertFalse(result["gmpe_applicability_verified"])
        self.assertFalse(result["numerical_equivalence_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["evidence"]["profile"]["raw_model_values_returned"])

    def test_acquisition_failure_is_bounded_and_does_not_claim_byte_read(self):
        def fail():
            raise worker.AthensGmpeProfileAcquisitionError("blocked")

        result = action._run(execution_sha=SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertIsNone(result["evidence"])

    def test_profile_failure_records_full_byte_read_but_no_semantics(self):
        def fail():
            raise worker.AthensGmpeProfileContentError("bad exact XML")

        result = action._run(execution_sha=SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertIsNone(result["evidence"])
        self.assertFalse(result["gmpe_semantics_verified"])

    def test_profile_contract_rejects_authority_uplift(self):
        payload = _profile_payload()
        payload["gmpe_semantics_verified"] = True
        with self.assertRaises(worker.AthensGmpeProfileContractError):
            worker._validate_profile_payload(payload)


if __name__ == "__main__":
    unittest.main()
