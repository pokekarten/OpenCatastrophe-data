# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from unittest.mock import Mock, patch

from scripts import acquire_efehr_kosovo_taxonomy as worker

RETRIEVED_AT = "2026-08-15T10:45:00Z"


class FakeResponse:
    status = 200

    def __init__(self, raw: bytes, url: str, *, content_length: int | None = None) -> None:
        self._raw = raw
        self._url = url
        self._offset = 0
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)

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


def canonical_identity(values: list[str]) -> tuple[int, str]:
    digest = hashlib.sha256()
    byte_count = 0
    for value in sorted(values, key=lambda item: item.encode("utf-8")):
        encoded = value.encode("utf-8")
        prefix = len(encoded).to_bytes(8, "big")
        digest.update(prefix)
        digest.update(encoded)
        byte_count += len(prefix) + len(encoded)
    return byte_count, digest.hexdigest()


class KosovoTaxonomyAcquisitionTests(unittest.TestCase):
    def _evidence(self, values: list[str], raw: bytes) -> dict[str, object]:
        _, fingerprint = canonical_identity(values)
        return {
            "schema_version": worker.TAXONOMY_SET_SCHEMA_VERSION,
            "source_issue": worker.exposure.SOURCE_ISSUE,
            "dataset_id": worker.exposure.DATASET_ID,
            "project_id": worker.exposure.PROJECT_ID,
            "project_path": worker.exposure.PROJECT_PATH,
            "commit_sha": worker.exposure.COMMIT_SHA,
            "repository_path": worker.exposure.REPOSITORY_PATH,
            "receipt_comment_id": worker.exposure.RECEIPT_COMMENT_ID,
            "receipt_execution_sha": worker.exposure.RECEIPT_EXECUTION_SHA,
            "byte_count": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "taxonomy_field": worker.TAXONOMY_FIELD,
            "taxonomy_count": len(values),
            "taxonomy_value_set_sha256": fingerprint,
            "taxonomies": values,
            "normalization_applied": False,
            "raw_rows_returned": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }

    def test_fixed_target_returns_identity_without_taxonomy_values(self) -> None:
        raw = b"x" * 128
        values = ["private-A", "private-B", "private-C"]
        artifact_byte_count, artifact_sha256 = canonical_identity(values)
        captured = []

        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request)
            self.assertIn("/api/v4/projects/186/", request.full_url)
            self.assertIn(
                "_exposure_models%2FExposure_Model_Kosovo_Res.csv",
                request.full_url,
            )
            self.assertIn(worker.exposure.COMMIT_SHA, request.full_url)
            return FakeResponse(raw, request.full_url, content_length=len(raw))

        with (
            patch.object(worker.exposure, "EXPECTED_BYTE_COUNT", len(raw)),
            patch.object(worker.exposure, "EXPECTED_SHA256", hashlib.sha256(raw).hexdigest()),
            patch.object(worker, "EXPECTED_DISTINCT_COUNT", len(values)),
            patch.object(worker, "EXPECTED_VALUE_SET_SHA256", artifact_sha256),
            patch.object(
                worker,
                "extract_verified_kosovo_taxonomy",
                return_value=self._evidence(values, raw),
            ) as extractor,
        ):
            result = worker.acquire_verified_kosovo_taxonomy_identity(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

        self.assertEqual(len(captured), 1)
        extractor.assert_called_once_with(raw)
        self.assertEqual(result["control_issue"], 363)
        self.assertEqual(result["retrieved_at"], RETRIEVED_AT)
        self.assertEqual(result["taxonomy_field"], "TAXONOMY")
        self.assertEqual(result["taxonomy_count"], len(values))
        self.assertEqual(
            result["taxonomy_artifact_representation"],
            "oc-taxonomy-u64be-utf8-sorted-v1",
        )
        self.assertEqual(result["taxonomy_artifact_byte_count"], artifact_byte_count)
        self.assertEqual(result["taxonomy_artifact_sha256"], artifact_sha256)
        self.assertNotIn("taxonomies", result)
        self.assertFalse(result["taxonomy_values_returned"])
        self.assertFalse(result["normalization_applied"])
        self.assertFalse(result["raw_rows_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["derived_artifact_persisted"])
        self.assertFalse(result["publication_authorized"])

        durable_text = json.dumps(result, sort_keys=True)
        self.assertNotIn(raw.decode(), durable_text)
        for value in values:
            self.assertNotIn(value, durable_text)

    def test_canonical_identity_is_length_prefixed_utf8_stream(self) -> None:
        values = ["A", "B/ä", "ZZ"]
        expected_stream = b"".join(
            len(value.encode("utf-8")).to_bytes(8, "big") + value.encode("utf-8")
            for value in sorted(values, key=lambda item: item.encode("utf-8"))
        )
        byte_count, digest = worker._canonical_artifact_identity(
            sorted(values, key=lambda item: item.encode("utf-8"))
        )
        self.assertEqual(byte_count, len(expected_stream))
        self.assertEqual(digest, hashlib.sha256(expected_stream).hexdigest())

    def test_response_identity_drift_fails_before_extraction(self) -> None:
        raw = b"synthetic"
        extractor = Mock()

        def opener(request, timeout):
            return FakeResponse(raw, "https://gitlab.seismo.ethz.ch/wrong")

        with (
            patch.object(worker.exposure, "EXPECTED_BYTE_COUNT", len(raw)),
            patch.object(worker.exposure, "EXPECTED_SHA256", hashlib.sha256(raw).hexdigest()),
            patch.object(worker, "extract_verified_kosovo_taxonomy", extractor),
        ):
            with self.assertRaisesRegex(worker.KosovoTaxonomyAcquisitionError, "failed closed"):
                worker.acquire_verified_kosovo_taxonomy_identity(
                    opener=opener,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )
        extractor.assert_not_called()

    def test_oversize_response_fails_before_extraction(self) -> None:
        raw = b"abcd"
        extractor = Mock()

        def opener(request, timeout):
            return FakeResponse(raw, request.full_url, content_length=len(raw))

        with (
            patch.object(worker.exposure, "EXPECTED_BYTE_COUNT", 3),
            patch.object(worker, "extract_verified_kosovo_taxonomy", extractor),
        ):
            with self.assertRaisesRegex(worker.KosovoTaxonomyAcquisitionError, "failed closed"):
                worker.acquire_verified_kosovo_taxonomy_identity(
                    opener=opener,
                    now=lambda: RETRIEVED_AT,
                    monotonic=lambda: 0.0,
                )
        extractor.assert_not_called()

    def test_worker_rejects_widened_or_drifted_evidence(self) -> None:
        raw = b"synthetic provider bytes with enough room"
        values = ["A", "B"]
        _, fingerprint = canonical_identity(values)
        base = self._evidence(values, raw)

        cases = []
        widened = dict(base)
        widened["publication_authorized"] = True
        cases.append(widened)
        wrong_field = dict(base)
        wrong_field["taxonomy_field"] = "MACRO_TAXONOMY"
        cases.append(wrong_field)
        duplicate = dict(base)
        duplicate["taxonomies"] = ["A", "A"]
        cases.append(duplicate)
        unsorted = dict(base)
        unsorted["taxonomies"] = ["B", "A"]
        cases.append(unsorted)
        control = dict(base)
        control["taxonomies"] = ["A", "B\n"]
        cases.append(control)
        wrong_type = dict(base)
        wrong_type["taxonomy_count"] = 2.0
        cases.append(wrong_type)
        extra = dict(base)
        extra["unexpected"] = "field"
        cases.append(extra)

        with (
            patch.object(worker.exposure, "EXPECTED_BYTE_COUNT", len(raw)),
            patch.object(worker.exposure, "EXPECTED_SHA256", hashlib.sha256(raw).hexdigest()),
            patch.object(worker, "EXPECTED_DISTINCT_COUNT", len(values)),
            patch.object(worker, "EXPECTED_VALUE_SET_SHA256", fingerprint),
        ):
            for evidence in cases:
                with self.subTest(evidence=evidence):
                    with self.assertRaises(worker.KosovoTaxonomyAcquisitionError):
                        worker._validate_taxonomy_evidence(evidence)

    def test_worker_recomputes_canonical_artifact_fingerprint(self) -> None:
        raw = b"synthetic provider bytes with enough room"
        values = ["A", "B"]
        _, fingerprint = canonical_identity(values)
        evidence = self._evidence(values, raw)
        forged = dict(evidence)
        forged["taxonomies"] = ["A", "C"]

        with (
            patch.object(worker.exposure, "EXPECTED_BYTE_COUNT", len(raw)),
            patch.object(worker.exposure, "EXPECTED_SHA256", hashlib.sha256(raw).hexdigest()),
            patch.object(worker, "EXPECTED_DISTINCT_COUNT", len(values)),
            patch.object(worker, "EXPECTED_VALUE_SET_SHA256", fingerprint),
        ):
            with self.assertRaisesRegex(worker.KosovoTaxonomyAcquisitionError, "fingerprint"):
                worker._validate_taxonomy_evidence(forged)

    def test_transport_exception_is_sanitized(self) -> None:
        def opener(request, timeout):
            raise OSError("secret local cache/provider payload")

        with self.assertRaisesRegex(
            worker.KosovoTaxonomyAcquisitionError,
            r"retrieval failed: OSError$",
        ) as caught:
            worker.acquire_verified_kosovo_taxonomy_identity(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )
        self.assertNotIn("secret local cache", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
