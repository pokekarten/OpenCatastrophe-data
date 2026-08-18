# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_ebrisk_config_receipts as worker
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target

RETRIEVED_AT = "2026-08-18T11:20:00Z"


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, status: int = 200, headers=None) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        end = (
            len(self._payload)
            if size is None or size < 0
            else min(len(self._payload), self._offset + size)
        )
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def _url(path: str) -> str:
    return raw_file_api_url(
        validate_target(
            source_issue=worker.SOURCE_ISSUE,
            dataset_id=worker.DATASET_ID,
            project_id=worker.PROJECT_ID,
            commit_sha=worker.COMMIT_SHA,
            repository_path=path,
        )
    )


class Esrm20EbriskConfigReceiptTests(unittest.TestCase):
    def test_private_helper_hashes_only_the_three_inventory_derived_candidates(self) -> None:
        cases = (
            (worker.GROUP1_REPOSITORY_PATH, worker.GROUP1_OPERATION_ID),
            (worker.GROUP2_REPOSITORY_PATH, worker.GROUP2_OPERATION_ID),
            (worker.ICELAND_REPOSITORY_PATH, worker.ICELAND_OPERATION_ID),
        )
        for path, operation_id in cases:
            with self.subTest(path=path):
                payload = f"[general]\nsource={path}\n".encode()
                url = _url(path)
                calls = []

                def opener(request, timeout):
                    calls.append((request, timeout))
                    return FakeResponse(
                        payload,
                        url,
                        headers={
                            "Content-Length": str(len(payload)),
                            "Content-Type": "text/plain",
                            "ETag": '"synthetic"',
                        },
                    )

                receipt = worker._acquire_candidate_receipt(
                    repository_path=path,
                    operation_id=operation_id,
                    opener=opener,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][0].full_url, url)
                self.assertEqual(receipt["operation_id"], operation_id)
                self.assertEqual(receipt["source_issue"], 281)
                self.assertEqual(receipt["dataset_id"], "efehr.esrm20.risk-inputs.v1.0")
                self.assertEqual(receipt["project_id"], 269)
                self.assertEqual(receipt["project_path"], "efehr/esrm20")
                self.assertEqual(
                    receipt["commit_sha"], "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
                )
                self.assertEqual(receipt["repository_path"], path)
                self.assertEqual(receipt["byte_count"], len(payload))
                self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
                self.assertFalse(receipt["external_bytes_persisted"])
                self.assertFalse(receipt["publication_authorized"])

    def test_public_entrypoints_are_zero_argument_and_frozen(self) -> None:
        for entrypoint in (
            worker.acquire_ebrisk_group1_candidate_receipt,
            worker.acquire_ebrisk_group2_candidate_receipt,
            worker.acquire_ebrisk_iceland_candidate_receipt,
        ):
            self.assertEqual(inspect.signature(entrypoint).parameters, {})

        self.assertEqual(
            (
                worker.GROUP1_REPOSITORY_PATH,
                worker.GROUP2_REPOSITORY_PATH,
                worker.ICELAND_REPOSITORY_PATH,
            ),
            (
                "Configuration_files/config_ebrisk_Group1.ini",
                "Configuration_files/config_ebrisk_Group2.ini",
                "Configuration_files/config_ebrisk_Iceland.ini",
            ),
        )

    def test_allowlist_is_exact_and_case_sensitive_for_new_candidates(self) -> None:
        for path in (
            worker.GROUP1_REPOSITORY_PATH,
            worker.GROUP2_REPOSITORY_PATH,
            worker.ICELAND_REPOSITORY_PATH,
        ):
            target = validate_target(
                source_issue=worker.SOURCE_ISSUE,
                dataset_id=worker.DATASET_ID,
                project_id=worker.PROJECT_ID,
                commit_sha=worker.COMMIT_SHA,
                repository_path=path,
            )
            self.assertEqual(target.repository_path, path)

        for path in (
            "Configuration_files/config_ebrisk_group1.ini",
            "Configuration_files/config_ebrisk_Group3.ini",
            "Configuration_files/CONFIG_EBRISK_GROUP1.INI",
            "Configuration_files/config_ebrisk_Iceland.ini/",
            "Configuration_files//config_ebrisk_Group1.ini",
        ):
            with self.subTest(path=path), self.assertRaises(EfehrReceiptError):
                validate_target(
                    source_issue=worker.SOURCE_ISSUE,
                    dataset_id=worker.DATASET_ID,
                    project_id=worker.PROJECT_ID,
                    commit_sha=worker.COMMIT_SHA,
                    repository_path=path,
                )

    def test_private_helper_rejects_operation_path_cross_binding_before_transport(self) -> None:
        calls = []

        def opener(request, timeout):
            calls.append(request)
            raise AssertionError("transport must not run")

        with self.assertRaisesRegex(EfehrAcquisitionError, "operation/path binding"):
            worker._acquire_candidate_receipt(
                repository_path=worker.GROUP1_REPOSITORY_PATH,
                operation_id=worker.GROUP2_OPERATION_ID,
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )
        self.assertEqual(calls, [])

    def test_production_entrypoint_rejects_rebinding_before_transport(self) -> None:
        for patcher, message in (
            (mock.patch.object(worker, "_open_fixed", lambda *args, **kwargs: None), "transport"),
            (mock.patch.object(worker.time, "monotonic", lambda: 0.0), "monotonic"),
            (mock.patch.object(worker, "utc_now", lambda: RETRIEVED_AT), "wall clock"),
            (mock.patch.object(worker, "_DeadlineStream", object()), "deadline stream"),
            (mock.patch.object(worker, "_declared_length", lambda *args: None), "length validator"),
            (mock.patch.object(worker, "_remaining", lambda *args: 1.0), "deadline helper"),
            (
                mock.patch.object(worker, "_validate_exact_response", lambda *args: None),
                "response validator",
            ),
            (mock.patch.object(worker, "validate_target", lambda **kwargs: None), "validator"),
            (
                mock.patch.object(
                    worker, "raw_file_api_url", lambda target: "https://example.invalid"
                ),
                "URL builder",
            ),
            (
                mock.patch.object(worker, "receipt_from_stream", lambda *args, **kwargs: {}),
                "receipt function",
            ),
            (
                mock.patch.object(worker.urllib.request, "Request", lambda *args, **kwargs: None),
                "request constructor",
            ),
            (
                mock.patch.object(worker, "_acquire_candidate_receipt", lambda **kwargs: {}),
                "private helper",
            ),
        ):
            with self.subTest(message=message), patcher:
                with self.assertRaisesRegex(EfehrAcquisitionError, message):
                    worker.acquire_ebrisk_group1_candidate_receipt()

    def test_production_entrypoint_rejects_frozen_constant_drift_before_transport(self) -> None:
        for name, value, message in (
            ("SCHEMA_VERSION", "drift", "schema version"),
            ("TOTAL_DEADLINE_SECONDS", 31.0, "deadline"),
            ("MAX_CONFIG_BYTES", worker.MAX_CONFIG_BYTES + 1, "maximum config bytes"),
            ("SOURCE_ISSUE", 999, "source issue"),
            ("DATASET_ID", "drift", "dataset"),
            ("PROJECT_ID", 197, "project id"),
            ("PROJECT_PATH", "drift", "project path"),
            ("COMMIT_SHA", "0" * 40, "commit"),
            ("GROUP1_REPOSITORY_PATH", worker.GROUP2_REPOSITORY_PATH, "repository paths"),
            ("GROUP1_OPERATION_ID", worker.GROUP2_OPERATION_ID, "operation ids"),
        ):
            with self.subTest(name=name), mock.patch.object(worker, name, value):
                with self.assertRaisesRegex(EfehrAcquisitionError, message):
                    worker.acquire_ebrisk_group1_candidate_receipt()

    def test_response_identity_status_empty_and_oversize_fail_closed(self) -> None:
        path = worker.GROUP1_REPOSITORY_PATH
        operation = worker.GROUP1_OPERATION_ID
        url = _url(path)
        payload = b"[general]\nsynthetic=true\n"
        for response in (
            FakeResponse(payload, url + "&drift=1"),
            FakeResponse(payload, url, status=206),
        ):
            with self.subTest(url=response.geturl(), status=response.status):
                with self.assertRaises(EfehrAcquisitionError):
                    worker._acquire_candidate_receipt(
                        repository_path=path,
                        operation_id=operation,
                        opener=lambda request, timeout, response=response: response,
                        now=lambda: RETRIEVED_AT,
                        monotonic=lambda: 0.0,
                    )

        oversized = FakeResponse(
            b"x",
            url,
            headers={"Content-Length": str(worker.MAX_CONFIG_BYTES + 1)},
        )
        with self.assertRaisesRegex(EfehrAcquisitionError, "Content-Length"):
            worker._acquire_candidate_receipt(
                repository_path=path,
                operation_id=operation,
                opener=lambda request, timeout: oversized,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

        empty = FakeResponse(b"", url)
        with self.assertRaisesRegex(EfehrAcquisitionError, "empty object"):
            worker._acquire_candidate_receipt(
                repository_path=path,
                operation_id=operation,
                opener=lambda request, timeout: empty,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

    def test_transport_failure_is_sanitized(self) -> None:
        def opener(request, timeout):
            raise OSError("secret local detail")

        with self.assertRaisesRegex(
            EfehrAcquisitionError, r"artifact retrieval failed: OSError$"
        ):
            worker._acquire_candidate_receipt(
                repository_path=worker.ICELAND_REPOSITORY_PATH,
                operation_id=worker.ICELAND_OPERATION_ID,
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )


if __name__ == "__main__":
    unittest.main()
