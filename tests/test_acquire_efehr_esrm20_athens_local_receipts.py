# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import acquire_efehr_esrm20_athens_local_receipts as subject

SHA = "a" * 40


def _request(target: str = SHA) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": target,
        "requester": "tests",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True)


def _receipt(item):
    role, path, blob, size = item
    return {
        "role": role,
        "repository_path": path,
        "git_blob_sha1": blob,
        "retrieved_at": "2026-08-23T23:00:00Z",
        "byte_count": size,
        "sha256": "0" * 64,
        "content_type": "application/xml",
        "etag": None,
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def _pass_result():
    return {
        **subject._base_result(execution_sha=SHA),
        "status": "pass",
        "failure_class": None,
        "receipts": [_receipt(item) for item in subject.INPUTS],
        "provider_file_bytes_read": True,
    }


class AthensLocalReceiptTests(unittest.TestCase):
    def test_canonical_provider_and_four_path_set_are_frozen(self):
        self.assertEqual(subject.SOURCE_ISSUE, 658)
        self.assertEqual(subject.DATASET_ID, "efehr.esrm20.scenario-tests.v1.0")
        self.assertEqual(subject.PROJECT_ID, 273)
        self.assertEqual(subject.PROJECT_PATH, "efehr/esrm20_scenario_tests")
        self.assertEqual(subject.RELEASE_TAG, "v1.0")
        self.assertEqual(
            subject.COMMIT_SHA,
            "041f90d950d6ff84180b2faa11319a42c66c74cc",
        )
        self.assertEqual(subject.EVENT_ID, "Greece_07-9-1999")
        self.assertEqual(len(subject.INPUTS), 4)
        self.assertEqual(
            [item[2] for item in subject.INPUTS],
            [
                "fa3bfd7aedfb63869c5808785b0ca712b6e45859",
                "7f6ac690bf0f0538dabc4ef957db5b48e9fd35d3",
                "9e3ddc6196665db8e6256341dc735b84b8aff39c",
                "c5f140abe59c847869545fb9414d54452d6ad960",
            ],
        )
        self.assertEqual(
            [item[3] for item in subject.INPUTS],
            [666, 6490, 908623, 702053],
        )
        self.assertEqual(subject.MAX_TOTAL_BYTES, 1_617_832)

    def test_raw_url_accepts_only_frozen_paths_and_commit(self):
        for _, path, _, _ in subject.INPUTS:
            url = subject._raw_file_url(path)
            self.assertIn("/api/v4/projects/273/repository/files/", url)
            self.assertTrue(
                url.endswith(
                    "?ref=041f90d950d6ff84180b2faa11319a42c66c74cc"
                )
            )
        with self.assertRaisesRegex(subject.AthensLocalReceiptError, "fixed set"):
            subject._raw_file_url("../../arbitrary.xml")

    def test_request_requires_exact_issue_and_execution_sha(self):
        parsed = subject.validate_request(
            _request(), expected_issue=658, execution_sha=SHA
        )
        self.assertEqual(parsed["target_sha"], SHA)
        with self.assertRaisesRegex(subject.AthensLocalReceiptError, "target_sha"):
            subject.validate_request(
                _request("b" * 40), expected_issue=658, execution_sha=SHA
            )
        with self.assertRaisesRegex(subject.AthensLocalReceiptError, "wrong"):
            subject.validate_request(
                _request(), expected_issue=285, execution_sha=SHA
            )

    def test_pass_result_preserves_authority_ceiling(self):
        result = subject.validate_result(_pass_result())
        for field in (
            "provider_file_content_profiled",
            "output_payload_bytes_read",
            "content_semantics_verified",
            "benchmark_agreement_inspected",
            "external_bytes_persisted",
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_receipt_rejects_tree_size_and_blob_drift(self):
        first = _receipt(subject.INPUTS[0])
        first["byte_count"] += 1
        with self.assertRaisesRegex(subject.AthensLocalReceiptError, "byte_count"):
            subject.validate_receipt(first, expected=subject.INPUTS[0])

        first = _receipt(subject.INPUTS[0])
        first["git_blob_sha1"] = "f" * 40
        with self.assertRaisesRegex(
            subject.AthensLocalReceiptError, "git_blob_sha1"
        ):
            subject.validate_receipt(first, expected=subject.INPUTS[0])

    def test_authority_promotion_fails_closed(self):
        result = _pass_result()
        result["content_semantics_verified"] = True
        with self.assertRaisesRegex(
            subject.AthensLocalReceiptError, "content_semantics"
        ):
            subject.validate_result(result)

    def test_malformed_trusted_terminal_fails_before_dedup(self):
        comments = [
            {
                "id": 99,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": subject.RESULT_MARKER + "\n" + '{"status":"pass"}',
            }
        ]
        with self.assertRaises(subject.AthensLocalReceiptError):
            subject.find_existing_terminal(comments, execution_sha=SHA)

    def test_valid_terminal_is_deduplicated(self):
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            _pass_result(), sort_keys=True, separators=(",", ":")
        )
        comments = [
            {
                "id": 1234,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": body,
            }
        ]
        self.assertEqual(
            subject.find_existing_terminal(comments, execution_sha=SHA),
            1234,
        )

    def test_production_transport_monkeypatch_fails_before_provider(self):
        original = subject._open_fixed
        subject._open_fixed = object()
        try:
            with self.assertRaisesRegex(
                subject.AthensLocalReceiptError,
                "production transport drifted",
            ):
                subject.acquire_local_receipts()
        finally:
            subject._open_fixed = original


if __name__ == "__main__":
    unittest.main()
