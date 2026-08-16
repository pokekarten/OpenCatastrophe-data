# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest

from scripts.acquire_efehr_esrm20_event_hazard_receipts import (
    COMMIT_SHA,
    DATASET_ID,
    GROUP1_OPERATION_ID,
    GROUP1_REPOSITORY_PATH,
    GROUP2_OPERATION_ID,
    GROUP2_REPOSITORY_PATH,
    GSIM_LOGIC_TREE_OPERATION_ID,
    GSIM_LOGIC_TREE_REPOSITORY_PATH,
    MAX_CONFIG_BYTES,
    PROJECT_ID,
    SOURCE_ISSUE,
    SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
    SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
    acquire_event_hazard_group1_receipt,
    acquire_event_hazard_group2_receipt,
    acquire_event_hazard_gsim_logic_tree_receipt,
    acquire_event_hazard_source_model_logic_tree_receipt,
)
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target

RETRIEVED_AT = "2026-08-14T18:45:00Z"


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
        end = len(self._payload) if size is None or size < 0 else min(len(self._payload), self._offset + size)
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def _url(path: str) -> str:
    return raw_file_api_url(
        validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=path,
        )
    )


class Esrm20EventHazardReceiptTests(unittest.TestCase):
    def test_fixed_workers_hash_only_their_immutable_inputs(self) -> None:
        cases = (
            (acquire_event_hazard_group1_receipt, GROUP1_REPOSITORY_PATH, GROUP1_OPERATION_ID),
            (acquire_event_hazard_group2_receipt, GROUP2_REPOSITORY_PATH, GROUP2_OPERATION_ID),
            (
                acquire_event_hazard_gsim_logic_tree_receipt,
                GSIM_LOGIC_TREE_REPOSITORY_PATH,
                GSIM_LOGIC_TREE_OPERATION_ID,
            ),
            (
                acquire_event_hazard_source_model_logic_tree_receipt,
                SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
                SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
            ),
        )
        for worker, path, operation_id in cases:
            with self.subTest(path=path):
                payload = f"synthetic={path}\n".encode()
                url = _url(path)
                calls = []

                def opener(request, timeout):
                    calls.append((request, timeout))
                    return FakeResponse(
                        payload,
                        url,
                        headers={"Content-Length": str(len(payload)), "Content-Type": "application/xml", "ETag": '"synthetic"'},
                    )

                receipt = worker(opener=opener, now=lambda: RETRIEVED_AT, monotonic=lambda: 0.0)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][0].full_url, url)
                self.assertEqual(receipt["operation_id"], operation_id)
                self.assertEqual(receipt["source_issue"], SOURCE_ISSUE)
                self.assertEqual(receipt["dataset_id"], DATASET_ID)
                self.assertEqual(receipt["project_id"], PROJECT_ID)
                self.assertEqual(receipt["project_path"], "efehr/esrm20")
                self.assertEqual(receipt["commit_sha"], COMMIT_SHA)
                self.assertEqual(receipt["repository_path"], path)
                self.assertEqual(receipt["byte_count"], len(payload))
                self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
                self.assertFalse(receipt["external_bytes_persisted"])
                self.assertFalse(receipt["publication_authorized"])

    def test_public_workers_expose_no_group_or_provider_target_selector(self) -> None:
        for worker in (
            acquire_event_hazard_group1_receipt,
            acquire_event_hazard_group2_receipt,
            acquire_event_hazard_gsim_logic_tree_receipt,
            acquire_event_hazard_source_model_logic_tree_receipt,
        ):
            self.assertEqual(set(inspect.signature(worker).parameters), {"opener", "now", "monotonic"})
        self.assertEqual(COMMIT_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783")
        self.assertEqual(DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(PROJECT_ID, 269)
        self.assertEqual(SOURCE_ISSUE, 281)

    def test_response_identity_status_empty_and_oversize_fail_closed(self) -> None:
        url = _url(GROUP1_REPOSITORY_PATH)
        payload = b"[general]\nsynthetic=true\n"
        for response in (FakeResponse(payload, url + "&drift=1"), FakeResponse(payload, url, status=206)):
            with self.subTest(url=response.geturl(), status=response.status), self.assertRaises(EfehrAcquisitionError):
                acquire_event_hazard_group1_receipt(
                    opener=lambda request, timeout, response=response: response,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )

        oversized = FakeResponse(b"x", url, headers={"Content-Length": str(MAX_CONFIG_BYTES + 1)})
        with self.assertRaisesRegex(EfehrAcquisitionError, "Content-Length"):
            acquire_event_hazard_group1_receipt(opener=lambda request, timeout: oversized, now=lambda: RETRIEVED_AT, monotonic=lambda: 0.0)

        empty = FakeResponse(b"", url)
        with self.assertRaisesRegex(EfehrAcquisitionError, "empty object"):
            acquire_event_hazard_group1_receipt(opener=lambda request, timeout: empty, now=lambda: RETRIEVED_AT, monotonic=lambda: 0.0)

    def test_transport_failure_is_sanitized(self) -> None:
        def opener(request, timeout):
            raise OSError("secret local detail")

        with self.assertRaisesRegex(EfehrAcquisitionError, r"artifact retrieval failed: OSError$"):
            acquire_event_hazard_gsim_logic_tree_receipt(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )


if __name__ == "__main__":
    unittest.main()
