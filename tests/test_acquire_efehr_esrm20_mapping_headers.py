# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import urllib.error
import unittest
from contextlib import ExitStack
from unittest import mock

from scripts import acquire_efehr_esrm20_mapping_headers as worker


RAW = b"alpha,beta\nx,y\n"
RETRIEVED_AT = "2026-08-16T08:05:00Z"


class FakeResponse:
    def __init__(
        self,
        raw: bytes,
        url: str,
        *,
        final_url: str | None = None,
        declared_length: int | None = None,
        status: int = 200,
    ) -> None:
        self.status = status
        self.headers = {}
        if declared_length is not None:
            self.headers["Content-Length"] = str(declared_length)
        self._raw = raw
        self._offset = 0
        self._url = final_url or url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, amount: int = -1) -> bytes:
        if self._offset >= len(self._raw):
            return b""
        if amount < 0:
            amount = len(self._raw) - self._offset
        chunk = self._raw[self._offset : self._offset + amount]
        self._offset += len(chunk)
        return chunk


def valid_disclosure(*, byte_count: int, sha256: str) -> dict[str, object]:
    return {
        "schema_version": worker._CANONICAL_HEADER_SCHEMA_VERSION,
        "decision_issue": worker._CANONICAL_CONTROL_ISSUE,
        "source_issue": worker._CANONICAL_SOURCE_ISSUE,
        "profile_issue": 404,
        "dataset_id": worker._CANONICAL_DATASET_ID,
        "project_id": worker._CANONICAL_PROJECT_ID,
        "project_path": worker._CANONICAL_PROJECT_PATH,
        "commit_sha": worker._CANONICAL_COMMIT_SHA,
        "repository_path": worker._CANONICAL_REPOSITORY_PATH,
        "receipt_comment_id": worker._CANONICAL_RECEIPT_COMMENT_ID,
        "receipt_run_id": worker._CANONICAL_RECEIPT_RUN_ID,
        "receipt_execution_sha": worker._CANONICAL_RECEIPT_EXECUTION_SHA,
        "byte_count": byte_count,
        "sha256": sha256,
        "column_count": 2,
        "ordered_header_sha256": "1" * 64,
        "headers": ["alpha", "beta"],
        "disclosure_scope": worker._CANONICAL_DISCLOSURE_SCOPE,
        "header_strings_returned": True,
        "cell_values_returned": False,
        "raw_rows_returned": False,
        "normalization_applied": False,
        "mapping_interpretation_authorized": False,
        "taxonomy_join_authorized": False,
        "vulnerability_selection_authorized": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class MappingHeaderAcquisitionTests(unittest.TestCase):
    def identity_patches(self, raw: bytes):
        digest = hashlib.sha256(raw).hexdigest()
        return (
            mock.patch.object(worker, "_CANONICAL_EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "_CANONICAL_EXPECTED_SHA256", digest),
            mock.patch.object(worker, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "EXPECTED_SHA256", digest),
        )

    def enter_identity_patches(self, stack: ExitStack, raw: bytes) -> None:
        for patch in self.identity_patches(raw):
            stack.enter_context(patch)

    def test_frozen_target_and_header_helper_identity_are_exact(self) -> None:
        self.assertEqual(worker.SOURCE_ISSUE, 283)
        self.assertEqual(worker.CONTROL_ISSUE, 410)
        self.assertEqual(worker.DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(worker.PROJECT_ID, 269)
        self.assertEqual(worker.PROJECT_PATH, "efehr/esrm20")
        self.assertEqual(
            worker.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(
            worker.REPOSITORY_PATH,
            "Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
        )
        self.assertEqual(worker.EXPECTED_BYTE_COUNT, 83_585)
        self.assertEqual(
            worker.EXPECTED_SHA256,
            "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c",
        )
        self.assertEqual(
            worker.HEADER_SOURCE_COMMIT,
            "e54b1f7a6220bafc67da540a57ed6fc7f6534e28",
        )
        self.assertEqual(
            worker.HEADER_GIT_BLOB_SHA1,
            "cd0aa5cb573dbd8db431ef27b6a762c0a1d54c7c",
        )

    def test_public_worker_has_zero_argument_surface(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(worker.acquire_esrm20_mapping_headers).parameters),
            (),
        )

    def test_public_worker_uses_import_time_transport_and_clocks(self) -> None:
        sentinel = {"ok": True}
        with mock.patch.object(
            worker,
            "_acquire_esrm20_mapping_headers",
            return_value=sentinel,
        ) as private:
            self.assertIs(worker.acquire_esrm20_mapping_headers(), sentinel)
            private.assert_called_once_with(
                opener=worker._CANONICAL_OPEN_FIXED,
                now=worker._CANONICAL_UTC_NOW,
                monotonic=worker._CANONICAL_MONOTONIC,
            )

    def test_public_worker_rejects_transport_and_clock_rebinding(self) -> None:
        cases = (
            (worker, "_open_fixed", "production transport drifted"),
            (worker, "utc_now", "production UTC clock drifted"),
            (worker.time, "monotonic", "production monotonic clock drifted"),
        )
        for target, field, message in cases:
            with self.subTest(field=field):
                with (
                    mock.patch.object(target, field, object()),
                    mock.patch.object(worker, "_acquire_esrm20_mapping_headers") as private,
                    self.assertRaisesRegex(
                        worker.Esrm20MappingHeaderAcquisitionError,
                        message,
                    ),
                ):
                    worker.acquire_esrm20_mapping_headers()
                private.assert_not_called()

    def test_public_worker_rejects_acquisition_primitive_rebinding(self) -> None:
        fake_reader = lambda *_args, **_kwargs: RAW
        cases = (
            ("_read_bounded", fake_reader, "production response reader drifted"),
            ("raw_file_api_url", object(), "production URL builder drifted"),
            ("validate_target", object(), "production target validator drifted"),
        )
        for field, replacement, message in cases:
            with self.subTest(field=field):
                with (
                    mock.patch.object(worker, field, replacement),
                    mock.patch.object(worker, "_acquire_esrm20_mapping_headers") as private,
                    self.assertRaisesRegex(
                        worker.Esrm20MappingHeaderAcquisitionError,
                        message,
                    ),
                ):
                    worker.acquire_esrm20_mapping_headers()
                private.assert_not_called()

    def test_private_worker_returns_only_bounded_header_evidence(self) -> None:
        captured: list[bytes] = []
        digest = hashlib.sha256(RAW).hexdigest()

        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            return FakeResponse(
                RAW,
                request.full_url,
                declared_length=len(RAW),
            )

        def discloser(raw: bytes):
            captured.append(raw)
            return valid_disclosure(byte_count=len(raw), sha256=digest)

        with ExitStack() as stack:
            self.enter_identity_patches(stack, RAW)
            stack.enter_context(
                mock.patch.object(worker, "_CANONICAL_HEADER_DISCLOSER", discloser)
            )
            stack.enter_context(
                mock.patch.object(
                    worker.header_profile,
                    "disclose_verified_mapping_headers",
                    discloser,
                )
            )
            result = worker._acquire_esrm20_mapping_headers(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

        self.assertEqual(captured, [RAW])
        self.assertEqual(result["retrieved_at"], RETRIEVED_AT)
        self.assertEqual(result["disclosure"]["headers"], ["alpha", "beta"])
        self.assertNotIn("raw", result)
        self.assertFalse(result["raw_bytes_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["derived_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["mapping_interpretation_authorized"])
        self.assertFalse(result["taxonomy_join_authorized"])
        self.assertFalse(result["vulnerability_selection_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_public_alias_drift_fails_before_network(self) -> None:
        opened: list[bool] = []

        def opener(request, timeout):
            opened.append(True)
            raise AssertionError("provider must not be called")

        with mock.patch.object(worker, "COMMIT_SHA", "0" * 40):
            with self.assertRaisesRegex(
                worker.Esrm20MappingHeaderAcquisitionError,
                "commit drifted",
            ):
                worker._acquire_esrm20_mapping_headers(
                    opener=opener,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )
        self.assertEqual(opened, [])

    def test_header_helper_rebinding_and_source_blob_drift_fail_before_network(self) -> None:
        opened: list[bool] = []

        def opener(request, timeout):
            opened.append(True)
            raise AssertionError("provider must not be called")

        with mock.patch.object(
            worker.header_profile,
            "disclose_verified_mapping_headers",
            lambda raw: {},
        ):
            with self.assertRaisesRegex(
                worker.Esrm20MappingHeaderAcquisitionError,
                "helper function identity drifted",
            ):
                worker._acquire_esrm20_mapping_headers(
                    opener=opener,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )
        self.assertEqual(opened, [])

        with mock.patch.object(worker, "_git_blob_sha1", return_value="0" * 40):
            with self.assertRaisesRegex(
                worker.Esrm20MappingHeaderAcquisitionError,
                "helper source blob drifted",
            ):
                worker._acquire_esrm20_mapping_headers(
                    opener=opener,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )
        self.assertEqual(opened, [])

    def test_wrong_exact_bytes_fail_before_header_disclosure(self) -> None:
        disclosure = mock.Mock()

        def opener(request, timeout):
            return FakeResponse(RAW, request.full_url, declared_length=len(RAW))

        with ExitStack() as stack:
            stack.enter_context(
                mock.patch.object(worker, "_CANONICAL_EXPECTED_BYTE_COUNT", len(RAW))
            )
            stack.enter_context(mock.patch.object(worker, "EXPECTED_BYTE_COUNT", len(RAW)))
            stack.enter_context(mock.patch.object(worker, "_CANONICAL_EXPECTED_SHA256", "0" * 64))
            stack.enter_context(mock.patch.object(worker, "EXPECTED_SHA256", "0" * 64))
            stack.enter_context(
                mock.patch.object(worker, "_CANONICAL_HEADER_DISCLOSER", disclosure)
            )
            stack.enter_context(
                mock.patch.object(
                    worker.header_profile,
                    "disclose_verified_mapping_headers",
                    disclosure,
                )
            )
            with self.assertRaisesRegex(
                worker.Esrm20MappingHeaderAcquisitionError,
                "retrieval failed closed",
            ):
                worker._acquire_esrm20_mapping_headers(
                    opener=opener,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )
        disclosure.assert_not_called()

    def test_disclosure_authority_widening_fails_closed(self) -> None:
        result = valid_disclosure(
            byte_count=worker._CANONICAL_EXPECTED_BYTE_COUNT,
            sha256=worker._CANONICAL_EXPECTED_SHA256,
        )
        result["mapping_interpretation_authorized"] = True
        with self.assertRaisesRegex(
            worker.Esrm20MappingHeaderAcquisitionError,
            "widened authority",
        ):
            worker._validate_disclosure(result)

    def test_provider_error_text_is_sanitized(self) -> None:
        def opener(request, timeout):
            raise urllib.error.URLError("SECRET_PROVIDER_TEXT")

        with self.assertRaises(worker.Esrm20MappingHeaderAcquisitionError) as caught:
            worker._acquire_esrm20_mapping_headers(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )
        self.assertNotIn("SECRET_PROVIDER_TEXT", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
