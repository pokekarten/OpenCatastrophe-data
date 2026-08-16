# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_efehr_kosovo_site_receipt as worker
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target

RETRIEVED_AT = "2026-08-14T17:34:00Z"


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
        source_issue=worker.SOURCE_ISSUE,
        dataset_id=worker.DATASET_ID,
        project_id=worker.PROJECT_ID,
        commit_sha=worker.COMMIT_SHA,
        repository_path=worker.REPOSITORY_PATH,
    )
    return raw_file_api_url(target)


def fake_core_receipt(
    url: str,
    payload: bytes,
    **overrides: object,
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "source_issue": 284,
        "dataset_id": "efehr.esrm20.risk-inputs.v1.0",
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": 269,
        "project_path": "efehr/esrm20",
        "commit_sha": "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        "repository_path": "Vs30/Site_model_Kosovo.xml",
        "requested_url": url,
        "final_url": url,
        "retrieved_at": RETRIEVED_AT,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "content_type": "application/xml",
        "etag": '"synthetic"',
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    receipt.update(overrides)
    return receipt


class KosovoSiteReceiptTests(unittest.TestCase):
    def test_private_helper_hashes_only_the_immutable_site_object(self) -> None:
        payload = b"synthetic site receipt payload\n"
        url = expected_url()
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(
                payload,
                url,
                headers={
                    "Content-Length": str(len(payload)),
                    "Content-Type": "application/xml",
                    "ETag": '"synthetic"',
                },
            )

        receipt = worker._acquire_kosovo_site_receipt(
            opener=opener,
            now=lambda: RETRIEVED_AT,
            monotonic=lambda: 0.0,
        )

        self.assertEqual(len(calls), 1)
        request, timeout = calls[0]
        self.assertEqual(request.full_url, url)
        self.assertEqual(request.get_method(), "GET")
        self.assertGreater(timeout, 0)
        self.assertEqual(receipt["operation_id"], worker.OPERATION_ID)
        self.assertEqual(receipt["source_issue"], worker.SOURCE_ISSUE)
        self.assertEqual(receipt["dataset_id"], worker.DATASET_ID)
        self.assertEqual(receipt["project_id"], worker.PROJECT_ID)
        self.assertEqual(receipt["project_path"], "efehr/esrm20")
        self.assertEqual(receipt["commit_sha"], worker.COMMIT_SHA)
        self.assertEqual(receipt["repository_path"], worker.REPOSITORY_PATH)
        self.assertEqual(receipt["requested_url"], url)
        self.assertEqual(receipt["final_url"], url)
        self.assertEqual(receipt["retrieved_at"], RETRIEVED_AT)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])
        self.assertEqual(
            set(receipt),
            {
                "schema_version",
                "operation_id",
                "source_issue",
                "dataset_id",
                "provider_host",
                "project_id",
                "project_path",
                "commit_sha",
                "repository_path",
                "requested_url",
                "final_url",
                "retrieved_at",
                "byte_count",
                "sha256",
                "content_type",
                "etag",
                "external_bytes_persisted",
                "publication_authorized",
            },
        )

    def test_public_worker_has_no_caller_controlled_surface(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(worker.acquire_kosovo_site_receipt).parameters),
            (),
        )
        self.assertEqual(
            set(inspect.signature(worker._acquire_kosovo_site_receipt).parameters),
            {"opener", "now", "monotonic"},
        )
        self.assertEqual(worker.SOURCE_ISSUE, 284)
        self.assertEqual(worker.DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(worker.PROJECT_ID, 269)
        self.assertEqual(
            worker.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(worker.REPOSITORY_PATH, "Vs30/Site_model_Kosovo.xml")

    def test_public_worker_uses_import_time_canonical_transport_and_clocks(self) -> None:
        sentinel = {"ok": True}
        with mock.patch.object(
            worker,
            "_acquire_kosovo_site_receipt",
            return_value=sentinel,
        ) as private:
            self.assertIs(worker.acquire_kosovo_site_receipt(), sentinel)
            private.assert_called_once_with(
                opener=worker._CANONICAL_OPEN_FIXED,
                now=worker._CANONICAL_UTC_NOW,
                monotonic=worker._CANONICAL_MONOTONIC,
            )

    def test_public_worker_rejects_transport_rebinding_before_helper(self) -> None:
        with (
            mock.patch.object(worker, "_open_fixed", object()),
            mock.patch.object(worker, "_acquire_kosovo_site_receipt") as private,
            self.assertRaisesRegex(EfehrAcquisitionError, "production transport drifted"),
        ):
            worker.acquire_kosovo_site_receipt()
        private.assert_not_called()

    def test_public_worker_rejects_utc_clock_rebinding_before_helper(self) -> None:
        with (
            mock.patch.object(worker, "utc_now", object()),
            mock.patch.object(worker, "_acquire_kosovo_site_receipt") as private,
            self.assertRaisesRegex(EfehrAcquisitionError, "production UTC clock drifted"),
        ):
            worker.acquire_kosovo_site_receipt()
        private.assert_not_called()

    def test_public_worker_rejects_monotonic_rebinding_before_helper(self) -> None:
        with (
            mock.patch.object(worker.time, "monotonic", object()),
            mock.patch.object(worker, "_acquire_kosovo_site_receipt") as private,
            self.assertRaisesRegex(
                EfehrAcquisitionError,
                "production monotonic clock drifted",
            ),
        ):
            worker.acquire_kosovo_site_receipt()
        private.assert_not_called()

    def test_alias_drift_fails_before_provider_io(self) -> None:
        for field, bad_value in (
            ("COMMIT_SHA", "0" * 40),
            ("SOURCE_ISSUE", 999),
            ("OPERATION_ID", "other-operation"),
        ):
            with self.subTest(field=field):
                calls = []

                def opener(request, timeout):
                    calls.append((request, timeout))
                    raise AssertionError("provider I/O must not occur")

                with (
                    mock.patch.object(worker, field, bad_value),
                    self.assertRaisesRegex(EfehrAcquisitionError, "drifted"),
                ):
                    worker._acquire_kosovo_site_receipt(
                        opener=opener,
                        now=lambda: RETRIEVED_AT,
                        monotonic=lambda: 0.0,
                    )
                self.assertEqual(calls, [])

    def test_response_identity_and_status_drift_fail_closed(self) -> None:
        url = expected_url()
        payload = b"synthetic payload\n"
        for response in (
            FakeResponse(payload, url + "&unexpected=1"),
            FakeResponse(payload, url, status=206),
        ):
            with self.subTest(url=response.geturl(), status=response.status):
                with self.assertRaises(EfehrAcquisitionError):
                    worker._acquire_kosovo_site_receipt(
                        opener=lambda request, timeout, response=response: response,
                        now=lambda: RETRIEVED_AT,
                        monotonic=lambda: 0.0,
                    )

    def test_declared_oversize_and_empty_payload_fail_closed(self) -> None:
        url = expected_url()
        oversized = FakeResponse(
            b"x",
            url,
            headers={"Content-Length": str(worker.MAX_SITE_MODEL_BYTES + 1)},
        )
        with self.assertRaisesRegex(EfehrAcquisitionError, "Content-Length"):
            worker._acquire_kosovo_site_receipt(
                opener=lambda request, timeout: oversized,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

        empty = FakeResponse(b"", url, headers={})
        with self.assertRaisesRegex(EfehrAcquisitionError, "artifact receipt failed"):
            worker._acquire_kosovo_site_receipt(
                opener=lambda request, timeout: empty,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

    def test_core_receipt_identity_drift_fails_closed(self) -> None:
        url = expected_url()
        payload = b"synthetic payload\n"
        response = FakeResponse(payload, url)
        forged = fake_core_receipt(url, payload, commit_sha="0" * 40)

        with (
            mock.patch.object(worker, "receipt_from_stream", return_value=forged),
            self.assertRaisesRegex(EfehrAcquisitionError, "identity drifted"),
        ):
            worker._acquire_kosovo_site_receipt(
                opener=lambda request, timeout: response,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

    def test_core_receipt_authority_widening_fails_closed(self) -> None:
        url = expected_url()
        payload = b"synthetic payload\n"
        for field in (
            "publication_authorized",
            "model_use_authorized",
            "dependency_receipt_authorized",
            "derived_bytes_persisted",
        ):
            with self.subTest(field=field):
                response = FakeResponse(payload, url)
                widened = fake_core_receipt(url, payload, **{field: True})
                with (
                    mock.patch.object(
                        worker,
                        "receipt_from_stream",
                        return_value=widened,
                    ),
                    self.assertRaisesRegex(EfehrAcquisitionError, "widened authority"),
                ):
                    worker._acquire_kosovo_site_receipt(
                        opener=lambda request, timeout: response,
                        now=lambda: RETRIEVED_AT,
                        monotonic=lambda: 0.0,
                    )

    def test_bool_byte_count_and_invalid_hash_fail_closed(self) -> None:
        url = expected_url()
        payload = b"synthetic payload\n"
        for overrides in (
            {"byte_count": True},
            {"sha256": "0" * 63},
        ):
            with self.subTest(overrides=overrides):
                response = FakeResponse(payload, url)
                forged = fake_core_receipt(url, payload, **overrides)
                with (
                    mock.patch.object(
                        worker,
                        "receipt_from_stream",
                        return_value=forged,
                    ),
                    self.assertRaises(EfehrAcquisitionError),
                ):
                    worker._acquire_kosovo_site_receipt(
                        opener=lambda request, timeout: response,
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
            worker._acquire_kosovo_site_receipt(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )


if __name__ == "__main__":
    unittest.main()
