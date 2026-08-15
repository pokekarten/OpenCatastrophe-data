# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import urllib.error
import unittest
from unittest import mock

from scripts import profile_efehr_esrm20_mapping_structure as worker


RAW = (
    b"EXPOSURE_CLASS,VULNERABILITY_ID,CONDITION\r\n"
    b"SYN-A,V-01,\r\n"
    b"SYN-B,V-02,FLAG\r\n"
)


class FakeResponse:
    def __init__(self, raw: bytes, url: str) -> None:
        self.status = 200
        self.headers = {
            "Content-Length": str(len(raw)),
            "Content-Type": "text/csv",
        }
        self._raw = raw
        self._offset = 0
        self._url = url

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


class Esrm20MappingStructureTests(unittest.TestCase):
    def identity_patches(self, raw: bytes):
        return (
            mock.patch.object(worker, "_CANONICAL_EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(
                worker,
                "_CANONICAL_EXPECTED_SHA256",
                hashlib.sha256(raw).hexdigest(),
            ),
        )

    def test_frozen_receipt_identity_and_worker_surface_are_exact(self) -> None:
        self.assertEqual(worker._CANONICAL_SOURCE_ISSUE, 283)
        self.assertEqual(worker._CANONICAL_DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(worker._CANONICAL_PROJECT_ID, 269)
        self.assertEqual(
            worker._CANONICAL_COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(
            worker._CANONICAL_REPOSITORY_PATH,
            "Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
        )
        self.assertEqual(worker._CANONICAL_EXPECTED_BYTE_COUNT, 83_585)
        self.assertEqual(
            worker._CANONICAL_EXPECTED_SHA256,
            "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c",
        )
        self.assertEqual(worker.RECEIPT_RESULT_COMMENT_ID, 5303466667)
        self.assertEqual(worker.RECEIPT_RUN_ID, 31899242278)

        signature = inspect.signature(worker.acquire_verified_esrm20_mapping_structure)
        self.assertEqual(set(signature.parameters), {"opener", "now", "monotonic"})
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

    def test_profile_returns_structure_only_with_exact_ceiling(self) -> None:
        count_patch, hash_patch = self.identity_patches(RAW)
        with count_patch, hash_patch:
            result = worker.profile_verified_esrm20_mapping_structure(RAW)

        self.assertEqual(result["encoding"], "utf-8")
        self.assertFalse(result["utf8_bom"])
        self.assertEqual(result["newline_style"], "crlf")
        self.assertEqual(result["delimiter"], "comma")
        self.assertEqual(
            result["header"],
            ["EXPOSURE_CLASS", "VULNERABILITY_ID", "CONDITION"],
        )
        self.assertEqual(result["header_count"], 3)
        self.assertEqual(result["record_count"], 2)
        self.assertEqual(result["source_sha256"], hashlib.sha256(RAW).hexdigest())
        self.assertFalse(result["duplicate_headers"])
        self.assertFalse(result["duplicate_records"])
        self.assertFalse(result["ragged_rows"])
        self.assertFalse(result["normalization_applied"])
        self.assertFalse(result["mapping_semantics_interpreted"])
        self.assertFalse(result["taxonomy_join_performed"])
        self.assertFalse(result["vulnerability_ids_selected"])
        self.assertFalse(result["raw_rows_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertNotIn("rows", result)
        self.assertNotIn("taxonomies", result)
        self.assertNotIn("vulnerability_ids", result)

    def test_semicolon_delimiter_is_detected_without_normalization(self) -> None:
        raw = b"A;B;C\nalpha;beta;gamma\n"
        count_patch, hash_patch = self.identity_patches(raw)
        with count_patch, hash_patch:
            result = worker.profile_verified_esrm20_mapping_structure(raw)
        self.assertEqual(result["delimiter"], "semicolon")
        self.assertEqual(result["newline_style"], "lf")
        self.assertEqual(result["header"], ["A", "B", "C"])

    def test_byte_identity_fails_before_decode_or_csv_detection(self) -> None:
        tampered = RAW[:-1] + bytes([RAW[-1] ^ 1])
        with mock.patch.object(worker, "_detect_delimiter") as detect:
            with self.assertRaisesRegex(
                worker.Esrm20MappingStructureError, "SHA-256"
            ):
                worker.profile_verified_esrm20_mapping_structure(tampered)
            detect.assert_not_called()

    def test_invalid_utf8_fails_after_exact_identity(self) -> None:
        raw = b"A,B\n1,\xff\n"
        count_patch, hash_patch = self.identity_patches(raw)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(
                worker.Esrm20MappingStructureError, "strict UTF-8"
            ):
                worker.profile_verified_esrm20_mapping_structure(raw)

    def test_mixed_newlines_fail_closed(self) -> None:
        raw = b"A,B\r\n1,2\n"
        count_patch, hash_patch = self.identity_patches(raw)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(
                worker.Esrm20MappingStructureError,
                "exactly one physical newline style",
            ):
                worker.profile_verified_esrm20_mapping_structure(raw)

    def test_ambiguous_header_delimiter_fails_closed(self) -> None:
        raw = b"A,B;C\n1,2;3\n"
        count_patch, hash_patch = self.identity_patches(raw)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(
                worker.Esrm20MappingStructureError, "structurally ambiguous"
            ):
                worker.profile_verified_esrm20_mapping_structure(raw)

    def test_duplicate_header_fails_closed(self) -> None:
        raw = b"A,A\n1,2\n"
        count_patch, hash_patch = self.identity_patches(raw)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(
                worker.Esrm20MappingStructureError, "duplicate header"
            ):
                worker.profile_verified_esrm20_mapping_structure(raw)

    def test_ragged_record_fails_closed(self) -> None:
        raw = b"A,B\n1,2\n3\n"
        count_patch, hash_patch = self.identity_patches(raw)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(
                worker.Esrm20MappingStructureError, "ragged record"
            ):
                worker.profile_verified_esrm20_mapping_structure(raw)

    def test_duplicate_record_fails_closed(self) -> None:
        raw = b"A,B\n1,2\n1,2\n"
        count_patch, hash_patch = self.identity_patches(raw)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(
                worker.Esrm20MappingStructureError, "duplicate record"
            ):
                worker.profile_verified_esrm20_mapping_structure(raw)

    def test_control_characters_fail_closed(self) -> None:
        raw = b'A,B\n1,"bad\x01value"\n'
        count_patch, hash_patch = self.identity_patches(raw)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(
                worker.Esrm20MappingStructureError, "control characters"
            ):
                worker.profile_verified_esrm20_mapping_structure(raw)

    def test_acquisition_uses_private_canonical_target_and_discards_rows(self) -> None:
        captured: list[str] = []

        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            return FakeResponse(RAW, request.full_url)

        count_patch, hash_patch = self.identity_patches(RAW)
        with (
            count_patch,
            hash_patch,
            mock.patch.object(worker.mapping_receipt, "PROJECT_ID", 999999),
            mock.patch.object(worker.mapping_receipt, "COMMIT_SHA", "0" * 40),
            mock.patch.object(worker.mapping_receipt, "REPOSITORY_PATH", "other.csv"),
        ):
            result = worker.acquire_verified_esrm20_mapping_structure(
                opener=opener,
                now=lambda: "2026-08-15T17:50:00Z",
            )

        self.assertEqual(len(captured), 1)
        self.assertIn("/projects/269/", captured[0])
        self.assertIn(worker._CANONICAL_COMMIT_SHA, captured[0])
        self.assertIn("esrm20_exposure_vulnerability_mapping.csv", captured[0])
        self.assertEqual(result["operation_id"], worker.OPERATION_ID)
        self.assertEqual(result["retrieved_at"], "2026-08-15T17:50:00Z")
        self.assertEqual(result["record_count"], 2)
        self.assertNotIn("rows", result)

    def test_provider_error_is_sanitized(self) -> None:
        def opener(request, timeout):
            raise urllib.error.URLError("SECRET_PROVIDER_TEXT")

        with self.assertRaises(worker.Esrm20MappingStructureError) as caught:
            worker.acquire_verified_esrm20_mapping_structure(opener=opener)
        self.assertNotIn("SECRET_PROVIDER_TEXT", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
