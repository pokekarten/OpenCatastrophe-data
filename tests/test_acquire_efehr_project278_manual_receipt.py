# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest

import scripts.acquire_efehr_project278_manual_receipt as subject
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target

RETRIEVED_AT = "2026-08-25T22:05:00Z"


class FakeResponse:
    def __init__(
        self,
        payload: bytes,
        url: str,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
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
        if size is None or size < 0:
            end = len(self._payload)
        else:
            end = min(len(self._payload), self._offset + size)
        chunk = self._payload[self._offset : end]
        self._offset = end
        return chunk


def expected_url() -> str:
    target = validate_target(
        source_issue=subject.SOURCE_ISSUE,
        dataset_id=subject.DATASET_ID,
        project_id=subject.PROJECT_ID,
        commit_sha=subject.COMMIT_SHA,
        repository_path=subject.REPOSITORY_PATH,
    )
    return raw_file_api_url(target)


class Project278ManualReceiptTests(unittest.TestCase):
    def test_private_helper_hashes_only_the_immutable_manual(self) -> None:
        payload = b"%PDF-1.4\nsynthetic project-278 manual fixture\n%%EOF\n"
        url = expected_url()
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(
                payload,
                url,
                headers={
                    "Content-Length": str(len(payload)),
                    "Content-Type": "application/pdf",
                    "ETag": '"synthetic"',
                },
            )

        receipt = subject._acquire_for_test(
            opener=opener,
            now=lambda: RETRIEVED_AT,
            monotonic=lambda: 0.0,
        )

        self.assertEqual(len(calls), 1)
        request, timeout = calls[0]
        self.assertEqual(request.full_url, url)
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(
            request.get_header("Accept"),
            "application/pdf,application/octet-stream;q=0.9",
        )
        self.assertGreater(timeout, 0)
        self.assertEqual(receipt["operation_id"], subject.OPERATION_ID)
        self.assertEqual(receipt["source_issue"], subject.SOURCE_ISSUE)
        self.assertEqual(receipt["dataset_id"], subject.DATASET_ID)
        self.assertEqual(receipt["project_id"], subject.PROJECT_ID)
        self.assertEqual(receipt["project_path"], "efehr/esrm20_sitemodel")
        self.assertEqual(receipt["commit_sha"], subject.COMMIT_SHA)
        self.assertEqual(receipt["repository_path"], subject.REPOSITORY_PATH)
        self.assertEqual(receipt["requested_url"], url)
        self.assertEqual(receipt["final_url"], url)
        self.assertEqual(receipt["retrieved_at"], RETRIEVED_AT)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_public_worker_has_no_caller_injection_surface(self) -> None:
        self.assertEqual(
            set(inspect.signature(subject.acquire_project278_manual_receipt).parameters),
            set(),
        )
        self.assertEqual(
            subject.COMMIT_SHA,
            "038c91d2bf5a07f6b54ff51639aad874d6837ea9",
        )
        self.assertEqual(subject.REPOSITORY_PATH, "ExposureReadme.pdf")
        self.assertEqual(subject.DATASET_ID, "efehr.esrm20.sitemodel-source")
        self.assertEqual(subject.SOURCE_ISSUE, 291)
        self.assertEqual(subject.PROJECT_ID, 278)

    def test_public_worker_rejects_production_transport_drift(self) -> None:
        original = subject._open_fixed

        def fake_open_fixed(request, timeout):
            return None

        try:
            subject._open_fixed = fake_open_fixed
            with self.assertRaisesRegex(
                EfehrAcquisitionError,
                "production transport drifted",
            ):
                subject.acquire_project278_manual_receipt()
        finally:
            subject._open_fixed = original

    def test_public_worker_rejects_target_authority_drift(self) -> None:
        original = subject.COMMIT_SHA
        try:
            subject.COMMIT_SHA = "0" * 40
            with self.assertRaisesRegex(
                EfehrAcquisitionError,
                "commit authority drifted",
            ):
                subject.acquire_project278_manual_receipt()
        finally:
            subject.COMMIT_SHA = original

    def test_response_identity_and_status_drift_fail_closed(self) -> None:
        url = expected_url()
        payload = b"%PDF-1.4\nfixture\n"
        for response in (
            FakeResponse(payload, url + "&unexpected=1"),
            FakeResponse(payload, url, status=206),
        ):
            with self.subTest(url=response.geturl(), status=response.status):
                with self.assertRaises(EfehrAcquisitionError):
                    subject._acquire_for_test(
                        opener=lambda request, timeout, response=response: response,
                        now=lambda: RETRIEVED_AT,
                        monotonic=lambda: 0.0,
                    )

    def test_declared_oversize_and_empty_payload_fail_closed(self) -> None:
        url = expected_url()
        oversized = FakeResponse(
            b"x",
            url,
            headers={"Content-Length": str(subject.MAX_FILE_BYTES + 1)},
        )
        with self.assertRaisesRegex(EfehrAcquisitionError, "Content-Length"):
            subject._acquire_for_test(
                opener=lambda request, timeout: oversized,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

        empty = FakeResponse(b"", url, headers={})
        with self.assertRaisesRegex(EfehrAcquisitionError, "empty object"):
            subject._acquire_for_test(
                opener=lambda request, timeout: empty,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

    def test_transport_failures_are_sanitized(self) -> None:
        def opener(request, timeout):
            raise OSError("secret local detail")

        with self.assertRaisesRegex(
            EfehrAcquisitionError,
            r"artifact retrieval failed: OSError$",
        ):
            subject._acquire_for_test(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )


if __name__ == "__main__":
    unittest.main()
