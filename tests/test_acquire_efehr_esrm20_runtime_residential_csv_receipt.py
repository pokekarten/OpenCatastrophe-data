# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_runtime_residential_csv_receipt as worker
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target

RETRIEVED_AT = "2026-08-20T21:30:00Z"


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, status: int = 200) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "text/csv; charset=utf-8",
            "ETag": '"synthetic"',
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        end = len(self._payload) if size < 0 else min(len(self._payload), self._offset + size)
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


class RuntimeResidentialCsvReceiptTests(unittest.TestCase):
    def test_only_source_derived_residential_csv_is_newly_allowlisted(self) -> None:
        target = validate_target(
            source_issue=282,
            dataset_id="efehr.esrm20.risk-inputs.v1.0",
            project_id=269,
            commit_sha=worker.COMMIT_SHA,
            repository_path="Exposure/OQ_Exposure_Input_Kosovo_Res.csv",
        )
        self.assertEqual(target.project_path, "efehr/esrm20")
        for path in (
            "Exposure/OQ_Exposure_Input_Kosovo_Com.csv",
            "Exposure/OQ_Exposure_Input_Kosovo_Ind.csv",
            "Exposure/OQ_Exposure_Input_Albania_Res.csv",
            "Exposure/OQ_Exposure_Input_Kosovo.csv",
        ):
            with self.subTest(path=path), self.assertRaises(EfehrReceiptError):
                validate_target(
                    source_issue=282,
                    dataset_id="efehr.esrm20.risk-inputs.v1.0",
                    project_id=269,
                    commit_sha=worker.COMMIT_SHA,
                    repository_path=path,
                )

    def test_private_helper_hashes_only_fixed_runtime_residential_csv(self) -> None:
        payload = b"id,taxonomy,value-structural\n1,synthetic,100\n"
        url = expected_url()
        calls = []

        def opener(request, timeout):
            calls.append((request, timeout))
            return FakeResponse(payload, url)

        receipt = worker._acquire_runtime_residential_csv_receipt(
            opener=opener,
            now=lambda: RETRIEVED_AT,
            monotonic=lambda: 0.0,
        )
        self.assertEqual(len(calls), 1)
        request, timeout = calls[0]
        self.assertEqual(request.full_url, url)
        self.assertEqual(request.get_method(), "GET")
        self.assertGreater(timeout, 0)
        self.assertEqual(receipt["source_issue"], 282)
        self.assertEqual(receipt["project_id"], 269)
        self.assertEqual(receipt["commit_sha"], worker.COMMIT_SHA)
        self.assertEqual(receipt["repository_path"], worker.REPOSITORY_PATH)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])
        self.assertNotIn(payload.decode(), repr(receipt))

    def test_public_worker_has_no_caller_selectable_target(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(worker.acquire_runtime_residential_csv_receipt).parameters),
            (),
        )
        self.assertEqual(worker.PROJECT_ID, 269)
        self.assertEqual(worker.COMMIT_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783")
        self.assertEqual(worker.REPOSITORY_PATH, "Exposure/OQ_Exposure_Input_Kosovo_Res.csv")

    def test_alias_and_transport_drift_fail_before_provider_io(self) -> None:
        for field, bad_value in (
            ("COMMIT_SHA", "0" * 40),
            ("SOURCE_ISSUE", 999),
            ("REPOSITORY_PATH", "Exposure/OQ_Exposure_Input_Kosovo_Com.csv"),
        ):
            with self.subTest(field=field):
                opener = mock.Mock(side_effect=AssertionError("provider I/O must not occur"))
                with (
                    mock.patch.object(worker, field, bad_value),
                    self.assertRaisesRegex(EfehrAcquisitionError, "drifted"),
                ):
                    worker._acquire_runtime_residential_csv_receipt(
                        opener=opener,
                        now=lambda: RETRIEVED_AT,
                        monotonic=lambda: 0.0,
                    )
                opener.assert_not_called()

        with (
            mock.patch.object(worker, "_open_fixed", object()),
            mock.patch.object(worker, "_acquire_runtime_residential_csv_receipt") as private,
            self.assertRaisesRegex(EfehrAcquisitionError, "production transport drifted"),
        ):
            worker.acquire_runtime_residential_csv_receipt()
        private.assert_not_called()

    def test_response_identity_and_status_fail_closed(self) -> None:
        payload = b"a,b\n1,2\n"
        url = expected_url()
        for response in (
            FakeResponse(payload, url + "&drift=1"),
            FakeResponse(payload, url, status=206),
        ):
            with self.subTest(status=response.status), self.assertRaises(EfehrAcquisitionError):
                worker._acquire_runtime_residential_csv_receipt(
                    opener=lambda request, timeout, response=response: response,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )


if __name__ == "__main__":
    unittest.main()
