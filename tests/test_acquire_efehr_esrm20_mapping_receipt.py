# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest

from scripts.acquire_efehr_esrm20_mapping_receipt import (
    COMMIT_SHA,
    DATASET_ID,
    MAX_FILE_BYTES,
    OPERATION_ID,
    PROJECT_ID,
    REPOSITORY_PATH,
    SOURCE_ISSUE,
    acquire_esrm20_mapping_receipt,
)
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target

RETRIEVED_AT = "2026-08-14T17:20:00Z"


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
        source_issue=SOURCE_ISSUE,
        dataset_id=DATASET_ID,
        project_id=PROJECT_ID,
        commit_sha=COMMIT_SHA,
        repository_path=REPOSITORY_PATH,
    )
    return raw_file_api_url(target)


class Esrm20MappingReceiptTests(unittest.TestCase):
    def test_fixed_worker_hashes_only_the_immutable_mapping_csv(self) -> None:
        payload = b"taxonomy,vulnerability_id\nCR_LFINF-CDN-H2,CR_LFINF-CDN-H2\n"
        url = expected_url()
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(
                payload,
                url,
                headers={
                    "Content-Length": str(len(payload)),
                    "Content-Type": "text/csv",
                    "ETag": '"synthetic"',
                },
            )

        receipt = acquire_esrm20_mapping_receipt(
            opener=opener,
            now=lambda: RETRIEVED_AT,
            monotonic=lambda: 0.0,
        )

        self.assertEqual(len(calls), 1)
        request, timeout = calls[0]
        self.assertEqual(request.full_url, url)
        self.assertEqual(request.get_method(), "GET")
        self.assertGreater(timeout, 0)
        self.assertEqual(receipt["operation_id"], OPERATION_ID)
        self.assertEqual(receipt["source_issue"], SOURCE_ISSUE)
        self.assertEqual(receipt["dataset_id"], DATASET_ID)
        self.assertEqual(receipt["project_id"], PROJECT_ID)
        self.assertEqual(receipt["project_path"], "efehr/esrm20")
        self.assertEqual(receipt["commit_sha"], COMMIT_SHA)
        self.assertEqual(receipt["repository_path"], REPOSITORY_PATH)
        self.assertEqual(receipt["requested_url"], url)
        self.assertEqual(receipt["final_url"], url)
        self.assertEqual(receipt["retrieved_at"], RETRIEVED_AT)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_worker_has_no_caller_controlled_provider_target_surface(self) -> None:
        parameters = set(inspect.signature(acquire_esrm20_mapping_receipt).parameters)
        self.assertEqual(parameters, {"opener", "now", "monotonic"})
        self.assertEqual(COMMIT_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783")
        self.assertEqual(REPOSITORY_PATH, "Vulnerability/esrm20_exposure_vulnerability_mapping.csv")
        self.assertEqual(DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(PROJECT_ID, 269)
        self.assertEqual(SOURCE_ISSUE, 283)

    def test_response_identity_and_status_drift_fail_closed(self) -> None:
        url = expected_url()
        payload = b"a,b\n1,2\n"
        for response in (
            FakeResponse(payload, url + "&unexpected=1"),
            FakeResponse(payload, url, status=206),
        ):
            with self.subTest(url=response.geturl(), status=response.status):
                with self.assertRaises(EfehrAcquisitionError):
                    acquire_esrm20_mapping_receipt(
                        opener=lambda request, timeout, response=response: response,
                        now=lambda: RETRIEVED_AT,
                        monotonic=lambda: 0.0,
                    )

    def test_declared_oversize_and_empty_payload_fail_closed(self) -> None:
        url = expected_url()
        oversized = FakeResponse(
            b"x",
            url,
            headers={"Content-Length": str(MAX_FILE_BYTES + 1)},
        )
        with self.assertRaisesRegex(EfehrAcquisitionError, "Content-Length"):
            acquire_esrm20_mapping_receipt(
                opener=lambda request, timeout: oversized,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

        empty = FakeResponse(b"", url, headers={})
        with self.assertRaisesRegex(EfehrAcquisitionError, "empty object"):
            acquire_esrm20_mapping_receipt(
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
            acquire_esrm20_mapping_receipt(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )


if __name__ == "__main__":
    unittest.main()
