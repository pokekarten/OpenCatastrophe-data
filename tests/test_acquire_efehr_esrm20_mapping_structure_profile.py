# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import urllib.error
import unittest
from contextlib import ExitStack
from unittest import mock

from scripts import acquire_efehr_esrm20_mapping_structure_profile as worker


RAW = b"A,B\nSYN-A,SYN-1\nSYN-B,SYN-2\n"


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


class Esrm20MappingStructureProfileAcquisitionTests(unittest.TestCase):
    def identity_patches(self, raw: bytes):
        digest = hashlib.sha256(raw).hexdigest()
        return (
            mock.patch.object(worker, "_CANONICAL_EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "_CANONICAL_EXPECTED_SHA256", digest),
            mock.patch.object(worker, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "EXPECTED_SHA256", digest),
            mock.patch.object(
                worker.mapping_profile,
                "_CANONICAL_EXPECTED_BYTE_COUNT",
                len(raw),
            ),
            mock.patch.object(
                worker.mapping_profile,
                "_CANONICAL_EXPECTED_SHA256",
                digest,
            ),
            mock.patch.object(worker.mapping_profile, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker.mapping_profile, "EXPECTED_SHA256", digest),
        )

    def enter_identity_patches(self, stack: ExitStack, raw: bytes) -> None:
        for patch in self.identity_patches(raw):
            stack.enter_context(patch)

    def private_acquire(self, opener, *, now=lambda: "2026-08-15T18:10:00Z"):
        return worker._acquire_esrm20_mapping_structure_profile(
            opener=opener,
            now=now,
            monotonic=lambda: 0.0,
        )

    def valid_profile_result(
        self,
        *,
        byte_count: int,
        sha256: str,
        nested_publication_authorized: bool = False,
    ) -> dict[str, object]:
        return {
            "source_issue": worker._CANONICAL_SOURCE_ISSUE,
            "profile_issue": worker._CANONICAL_PROFILE_ISSUE,
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
            "profile": {
                "schema_version": worker._CANONICAL_PROFILER_SCHEMA_VERSION,
                "header_strings_returned": False,
                "cell_values_returned": False,
                "raw_rows_returned": False,
                "normalization_applied": False,
                "mapping_interpretation_authorized": False,
                "vulnerability_selection_authorized": False,
                "external_bytes_persisted": False,
                "derived_bytes_persisted": False,
                "publication_authorized": nested_publication_authorized,
                "model_use_authorized": False,
            },
            "external_bytes_persisted": False,
            "derived_bytes_persisted": False,
            "publication_authorized": False,
            "mapping_interpretation_authorized": False,
            "vulnerability_selection_authorized": False,
            "model_use_authorized": False,
        }

    def test_frozen_target_receipt_and_profiler_identity_are_exact(self) -> None:
        self.assertEqual(worker.SCHEMA_VERSION, worker._CANONICAL_SCHEMA_VERSION)
        self.assertEqual(worker.OPERATION_ID, worker._CANONICAL_OPERATION_ID)
        self.assertEqual(worker.SOURCE_ISSUE, 283)
        self.assertEqual(worker.PROFILE_ISSUE, 404)
        self.assertEqual(worker.CONTROL_ISSUE, 411)
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
        self.assertEqual(worker.RECEIPT_COMMENT_ID, 5303466667)
        self.assertEqual(worker.RECEIPT_RUN_ID, 31899242278)
        self.assertEqual(
            worker.RECEIPT_EXECUTION_SHA,
            "9b1bb7127138247cf613dbf444d139c189c9b13a",
        )
        self.assertEqual(
            worker.PROFILER_SOURCE_COMMIT,
            "e172e5ad57d25fe43cb36810a6baa76e102a0187",
        )
        self.assertEqual(
            worker.PROFILER_PATH,
            "scripts/profile_efehr_esrm20_mapping_structure.py",
        )
        self.assertEqual(worker.PROFILER_FUNCTION, "profile_verified_mapping_bytes")
        self.assertEqual(
            worker.PROFILER_GIT_BLOB_SHA1,
            "5d5aa5c9c48880022235e727c9ec4d5e73df46de",
        )
        self.assertIs(
            worker._CANONICAL_PROFILER,
            worker.mapping_profile.profile_verified_mapping_bytes,
        )

    def test_public_worker_has_no_injectable_transport_clock_or_selector(self) -> None:
        signature = inspect.signature(worker.acquire_esrm20_mapping_structure_profile)
        self.assertEqual(signature.parameters, {})
        with self.assertRaises(TypeError):
            worker.acquire_esrm20_mapping_structure_profile(opener=lambda *_a, **_k: None)

    def test_public_worker_uses_import_time_transport_and_clocks(self) -> None:
        sentinel = {"ok": True}
        with mock.patch.object(
            worker,
            "_acquire_esrm20_mapping_structure_profile",
            return_value=sentinel,
        ) as private:
            self.assertIs(worker.acquire_esrm20_mapping_structure_profile(), sentinel)
            private.assert_called_once_with(
                opener=worker._CANONICAL_OPEN_FIXED,
                now=worker._CANONICAL_UTC_NOW,
                monotonic=worker._CANONICAL_MONOTONIC,
            )

    def test_public_worker_rejects_transport_rebinding_before_helper(self) -> None:
        with (
            mock.patch.object(worker, "_open_fixed", object()),
            mock.patch.object(
                worker,
                "_acquire_esrm20_mapping_structure_profile",
            ) as private,
            self.assertRaisesRegex(
                worker.Esrm20MappingProfileAcquisitionError,
                "production transport drifted",
            ),
        ):
            worker.acquire_esrm20_mapping_structure_profile()
        private.assert_not_called()

    def test_public_worker_rejects_utc_rebinding_before_helper(self) -> None:
        with (
            mock.patch.object(worker, "utc_now", object()),
            mock.patch.object(
                worker,
                "_acquire_esrm20_mapping_structure_profile",
            ) as private,
            self.assertRaisesRegex(
                worker.Esrm20MappingProfileAcquisitionError,
                "production UTC clock drifted",
            ),
        ):
            worker.acquire_esrm20_mapping_structure_profile()
        private.assert_not_called()

    def test_public_worker_rejects_monotonic_rebinding_before_helper(self) -> None:
        with (
            mock.patch.object(worker.time, "monotonic", object()),
            mock.patch.object(
                worker,
                "_acquire_esrm20_mapping_structure_profile",
            ) as private,
            self.assertRaisesRegex(
                worker.Esrm20MappingProfileAcquisitionError,
                "production monotonic clock drifted",
            ),
        ):
            worker.acquire_esrm20_mapping_structure_profile()
        private.assert_not_called()

    def test_acquisition_uses_private_target_and_returns_value_free_profile(self) -> None:
        captured: list[str] = []

        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            return FakeResponse(
                RAW,
                request.full_url,
                declared_length=len(RAW),
            )

        with ExitStack() as stack:
            self.enter_identity_patches(stack, RAW)
            result = self.private_acquire(opener)

        self.assertEqual(len(captured), 1)
        self.assertIn("/api/v4/projects/269/", captured[0])
        self.assertIn(worker._CANONICAL_COMMIT_SHA, captured[0])
        self.assertIn("esrm20_exposure_vulnerability_mapping.csv", captured[0])
        self.assertEqual(result["retrieved_at"], "2026-08-15T18:10:00Z")
        self.assertEqual(result["project_path"], "efehr/esrm20")
        self.assertEqual(
            result["profiler_git_blob_sha1"],
            worker._CANONICAL_PROFILER_GIT_BLOB_SHA1,
        )
        self.assertFalse(result["raw_bytes_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["derived_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["mapping_interpretation_authorized"])
        self.assertFalse(result["vulnerability_selection_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertNotIn("raw", result)
        profile = result["profile"]
        self.assertFalse(profile["profile"]["header_strings_returned"])
        self.assertFalse(profile["profile"]["cell_values_returned"])
        self.assertFalse(profile["profile"]["raw_rows_returned"])
        self.assertNotIn("header", profile["profile"])
        self.assertNotIn("rows", profile["profile"])

    def test_raw_bytes_are_passed_once_to_frozen_profiler_and_not_returned(self) -> None:
        captured_payloads: list[bytes] = []
        digest = hashlib.sha256(RAW).hexdigest()

        def fake_profiler(raw: bytes):
            captured_payloads.append(raw)
            return self.valid_profile_result(byte_count=len(raw), sha256=digest)

        def opener(request, timeout):
            return FakeResponse(RAW, request.full_url, declared_length=len(RAW))

        with ExitStack() as stack:
            self.enter_identity_patches(stack, RAW)
            stack.enter_context(mock.patch.object(worker, "_CANONICAL_PROFILER", fake_profiler))
            stack.enter_context(
                mock.patch.object(
                    worker.mapping_profile,
                    "profile_verified_mapping_bytes",
                    fake_profiler,
                )
            )
            result = self.private_acquire(opener)

        self.assertEqual(captured_payloads, [RAW])
        self.assertNotIn(RAW, repr(result).encode("utf-8"))
        self.assertFalse(result["raw_bytes_returned"])

    def test_fixed_public_alias_drift_fails_before_network(self) -> None:
        cases = (
            ("SCHEMA_VERSION", "other-schema"),
            ("OPERATION_ID", "other-operation"),
            ("SOURCE_ISSUE", 999),
            ("PROFILE_ISSUE", 999),
            ("CONTROL_ISSUE", 999),
            ("DATASET_ID", "other.dataset"),
            ("PROJECT_ID", 999),
            ("PROJECT_PATH", "other/project"),
            ("COMMIT_SHA", "0" * 40),
            ("REPOSITORY_PATH", "other.csv"),
            ("EXPECTED_BYTE_COUNT", worker.EXPECTED_BYTE_COUNT + 1),
            ("EXPECTED_SHA256", "0" * 64),
            ("RECEIPT_COMMENT_ID", 1),
            ("RECEIPT_RUN_ID", 1),
            ("RECEIPT_EXECUTION_SHA", "0" * 40),
            ("PROFILER_SOURCE_COMMIT", "0" * 40),
            ("PROFILER_PATH", "other.py"),
            ("PROFILER_FUNCTION", "other"),
            ("PROFILER_GIT_BLOB_SHA1", "0" * 40),
        )
        for name, replacement in cases:
            opened: list[bool] = []

            def opener(request, timeout):
                opened.append(True)
                raise AssertionError("provider must not be called")

            with self.subTest(name=name), mock.patch.object(worker, name, replacement):
                with self.assertRaisesRegex(
                    worker.Esrm20MappingProfileAcquisitionError,
                    "frozen ESRM20 mapping profile",
                ):
                    self.private_acquire(opener)
            self.assertEqual(opened, [])

    def test_dependency_alias_drift_fails_before_network(self) -> None:
        opened: list[bool] = []

        def opener(request, timeout):
            opened.append(True)
            raise AssertionError("provider must not be called")

        with mock.patch.object(worker.mapping_receipt, "PROJECT_ID", 999999):
            with self.assertRaisesRegex(
                worker.Esrm20MappingProfileAcquisitionError,
                "dependency receipt project id drifted",
            ):
                self.private_acquire(opener)
        self.assertEqual(opened, [])

    def test_profiler_function_rebinding_fails_before_network(self) -> None:
        opened: list[bool] = []

        def opener(request, timeout):
            opened.append(True)
            raise AssertionError("provider must not be called")

        with mock.patch.object(
            worker.mapping_profile,
            "profile_verified_mapping_bytes",
            lambda raw: {},
        ):
            with self.assertRaisesRegex(
                worker.Esrm20MappingProfileAcquisitionError,
                "profiler function identity drifted",
            ):
                self.private_acquire(opener)
        self.assertEqual(opened, [])

    def test_profiler_source_blob_drift_fails_before_network(self) -> None:
        opened: list[bool] = []

        def opener(request, timeout):
            opened.append(True)
            raise AssertionError("provider must not be called")

        with mock.patch.object(worker, "_git_blob_sha1", return_value="0" * 40):
            with self.assertRaisesRegex(
                worker.Esrm20MappingProfileAcquisitionError,
                "profiler source blob drifted",
            ):
                self.private_acquire(opener)
        self.assertEqual(opened, [])

    def test_declared_length_drift_fails_closed_without_provider_text(self) -> None:
        def opener(request, timeout):
            return FakeResponse(
                RAW,
                request.full_url,
                declared_length=len(RAW) - 1,
            )

        with ExitStack() as stack:
            self.enter_identity_patches(stack, RAW)
            with self.assertRaisesRegex(
                worker.Esrm20MappingProfileAcquisitionError,
                "retrieval failed closed",
            ):
                self.private_acquire(opener)

    def test_redirect_identity_drift_fails_closed(self) -> None:
        def opener(request, timeout):
            return FakeResponse(
                RAW,
                request.full_url,
                final_url="https://example.invalid/other",
                declared_length=len(RAW),
            )

        with ExitStack() as stack:
            self.enter_identity_patches(stack, RAW)
            with self.assertRaisesRegex(
                worker.Esrm20MappingProfileAcquisitionError,
                "retrieval failed closed",
            ):
                self.private_acquire(opener)

    def test_provider_error_text_is_sanitized(self) -> None:
        def opener(request, timeout):
            raise urllib.error.URLError("SECRET_PROVIDER_TEXT")

        with self.assertRaises(worker.Esrm20MappingProfileAcquisitionError) as caught:
            self.private_acquire(opener)
        self.assertNotIn("SECRET_PROVIDER_TEXT", str(caught.exception))

    def test_profiler_provenance_drift_is_rejected(self) -> None:
        profile = self.valid_profile_result(
            byte_count=worker._CANONICAL_EXPECTED_BYTE_COUNT,
            sha256=worker._CANONICAL_EXPECTED_SHA256,
        )
        profile["commit_sha"] = "0" * 40
        with self.assertRaisesRegex(
            worker.Esrm20MappingProfileAcquisitionError,
            "provenance drifted at commit_sha",
        ):
            worker._profile_ceiling_is_closed(profile)

    def test_profiler_authority_widening_is_rejected(self) -> None:
        profile = self.valid_profile_result(
            byte_count=worker._CANONICAL_EXPECTED_BYTE_COUNT,
            sha256=worker._CANONICAL_EXPECTED_SHA256,
            nested_publication_authorized=True,
        )
        with self.assertRaisesRegex(
            worker.Esrm20MappingProfileAcquisitionError,
            "widened nested authority",
        ):
            worker._profile_ceiling_is_closed(profile)


if __name__ == "__main__":
    unittest.main()