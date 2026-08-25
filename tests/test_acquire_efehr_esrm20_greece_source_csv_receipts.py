# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_greece_source_csv_receipts as subject
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError


class FakeResponse:
    def __init__(
        self,
        data: bytes,
        *,
        url: str,
        status: int = 200,
        declared_length: int | None = None,
    ) -> None:
        self._data = data
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = {
            "Content-Type": "text/csv",
            "ETag": '"synthetic"',
            "Content-Length": str(
                len(data) if declared_length is None else declared_length
            ),
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._data):
            return b""
        if size < 0:
            end = len(self._data)
        else:
            end = min(len(self._data), self._offset + size)
        chunk = self._data[self._offset : end]
        self._offset = end
        return chunk


class GreeceSourceCsvReceiptsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.paths_and_blobs = tuple(
            (path, blob_sha1) for path, blob_sha1, _tree_bytes in subject.TARGETS
        )
        self.small_payloads = {
            self.paths_and_blobs[0][0]: b"com",
            self.paths_and_blobs[1][0]: b"ind!",
            self.paths_and_blobs[2][0]: b"res!!",
        }
        self.small_targets = tuple(
            (path, blob_sha1, len(self.small_payloads[path]))
            for path, blob_sha1 in self.paths_and_blobs
        )

    def _opener(
        self,
        *,
        status: int = 200,
        url_override: str | None = None,
        declared_delta: int = 0,
    ):
        seen: list[str] = []

        def open_response(request, timeout):
            self.assertGreater(timeout, 0)
            seen.append(request.full_url)
            path = next(
                path
                for path, _blob_sha1 in self.paths_and_blobs
                if path.replace("/", "%2F") in request.full_url
            )
            data = self.small_payloads[path]
            return FakeResponse(
                data,
                url=url_override or request.full_url,
                status=status,
                declared_length=len(data) + declared_delta,
            )

        return open_response, seen

    def _patch_small_targets(self):
        return (
            mock.patch.object(subject, "_CANONICAL_TARGETS", self.small_targets),
            mock.patch.object(subject, "TARGETS", self.small_targets),
        )

    def _valid_receipt(self, target: tuple[str, str, int]) -> dict[str, object]:
        path, blob_sha1, size = target
        return {
            "schema_version": subject.SCHEMA_VERSION,
            "canonical_issue": 285,
            "related_source_issue": 282,
            "parent_consumer_issue": 287,
            "dataset_id": "efehr.esrm20.european-exposure-model.v1.0",
            "provider_host": "gitlab.seismo.ethz.ch",
            "project_id": 186,
            "project_path": "efehr/esrm20_exposure",
            "release_tag": "v1.0",
            "commit_sha": "900433ada80fbb424c0976c34d72eeef97bab1af",
            "repository_path": path,
            "git_blob_sha1": blob_sha1,
            "expected_tree_byte_count": size,
            "retrieved_at": "2026-08-25T22:46:00Z",
            "byte_count": size,
            "sha256": "0" * 64,
            "content_type": "text/csv",
            "etag": '"synthetic"',
            "provider_file_bytes_read": True,
            "provider_file_content_profiled": False,
            "source_runtime_lineage_verified": False,
            "replacement_cost_semantics_verified": False,
            "taxonomy_semantics_verified": False,
            "crs_semantics_verified": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }

    def test_exact_source_targets_are_frozen(self) -> None:
        self.assertEqual(subject.PROJECT_ID, 186)
        self.assertEqual(subject.PROJECT_PATH, "efehr/esrm20_exposure")
        self.assertEqual(
            subject.COMMIT_SHA,
            "900433ada80fbb424c0976c34d72eeef97bab1af",
        )
        self.assertEqual(
            subject.TARGETS,
            (
                (
                    "_exposure_models/Exposure_Model_Greece_Com.csv",
                    "fd3e96c4121efb2e62bfb4b7a96b83b739888299",
                    12_578_244,
                ),
                (
                    "_exposure_models/Exposure_Model_Greece_Ind.csv",
                    "240d739b5b58b4d5701702d06a36e612a8c5b659",
                    4_600_971,
                ),
                (
                    "_exposure_models/Exposure_Model_Greece_Res.csv",
                    "c6bcd2df43d23009f4fea23be3934775ebabea0b",
                    9_011_434,
                ),
            ),
        )

    def test_production_entrypoint_has_no_caller_target_surface(self) -> None:
        self.assertEqual(dict(inspect.signature(subject.acquire_receipts).parameters), {})

    def test_synthetic_acquisition_hashes_all_three_and_keeps_authority_closed(self) -> None:
        opener, seen = self._opener()
        first_patch, second_patch = self._patch_small_targets()
        with first_patch, second_patch:
            receipts = subject._acquire_for_test(
                opener=opener,
                now=lambda: "2026-08-25T22:46:00Z",
                monotonic=lambda: 0.0,
            )

        self.assertEqual(len(receipts), 3)
        self.assertEqual(len(seen), 3)
        for receipt, (path, blob_sha1, expected_size) in zip(
            receipts,
            self.small_targets,
            strict=True,
        ):
            self.assertIn("/api/v4/projects/186/repository/files/", seen.pop(0))
            self.assertEqual(receipt["repository_path"], path)
            self.assertEqual(receipt["git_blob_sha1"], blob_sha1)
            self.assertEqual(receipt["byte_count"], expected_size)
            self.assertEqual(
                receipt["sha256"],
                hashlib.sha256(self.small_payloads[path]).hexdigest(),
            )
            self.assertTrue(receipt["provider_file_bytes_read"])
            for field in (
                "provider_file_content_profiled",
                "source_runtime_lineage_verified",
                "replacement_cost_semantics_verified",
                "taxonomy_semantics_verified",
                "crs_semantics_verified",
                "external_bytes_persisted",
                "publication_authorized",
                "model_use_authorized",
            ):
                self.assertIs(receipt[field], False)
            self.assertNotIn("bytes", receipt)

    def test_provider_response_url_drift_is_rejected(self) -> None:
        opener, _seen = self._opener(url_override="https://gitlab.seismo.ethz.ch/wrong")
        first_patch, second_patch = self._patch_small_targets()
        with first_patch, second_patch:
            with self.assertRaisesRegex(EfehrAcquisitionError, "identity drifted"):
                subject._acquire_for_test(
                    opener=opener,
                    now=lambda: "2026-08-25T22:46:00Z",
                    monotonic=lambda: 0.0,
                )

    def test_non_200_response_is_rejected(self) -> None:
        opener, _seen = self._opener(status=404)
        first_patch, second_patch = self._patch_small_targets()
        with first_patch, second_patch:
            with self.assertRaisesRegex(EfehrAcquisitionError, "status is not 200"):
                subject._acquire_for_test(
                    opener=opener,
                    now=lambda: "2026-08-25T22:46:00Z",
                    monotonic=lambda: 0.0,
                )

    def test_declared_oversize_is_rejected_before_receipt(self) -> None:
        opener, _seen = self._opener(declared_delta=1)
        first_patch, second_patch = self._patch_small_targets()
        with first_patch, second_patch:
            with self.assertRaisesRegex(EfehrAcquisitionError, "outside bounded policy"):
                subject._acquire_for_test(
                    opener=opener,
                    now=lambda: "2026-08-25T22:46:00Z",
                    monotonic=lambda: 0.0,
                )

    def test_short_body_cannot_masquerade_as_frozen_tree_object(self) -> None:
        opener, _seen = self._opener(declared_delta=0)
        mismatched = tuple(
            (path, blob_sha1, len(self.small_payloads[path]) + 1)
            for path, blob_sha1 in self.paths_and_blobs
        )
        with (
            mock.patch.object(subject, "_CANONICAL_TARGETS", mismatched),
            mock.patch.object(subject, "TARGETS", mismatched),
        ):
            with self.assertRaisesRegex(
                subject.GreeceSourceCsvReceiptsError,
                "byte count does not match frozen provider tree metadata",
            ):
                subject._acquire_for_test(
                    opener=opener,
                    now=lambda: "2026-08-25T22:46:00Z",
                    monotonic=lambda: 0.0,
                )

    def test_target_mutation_fails_closed(self) -> None:
        with mock.patch.object(subject, "PROJECT_ID", 269):
            with self.assertRaisesRegex(
                subject.GreeceSourceCsvReceiptsError,
                "project id authority drifted",
            ):
                subject._require_canonical_target()

        with mock.patch.object(subject, "TARGETS", tuple(reversed(subject.TARGETS))):
            with self.assertRaisesRegex(
                subject.GreeceSourceCsvReceiptsError,
                "target set authority drifted",
            ):
                subject._require_canonical_target()

    def test_receipt_cannot_launder_publication_or_lineage_authority(self) -> None:
        target = subject.TARGETS[0]
        receipt = self._valid_receipt(target)
        receipt["publication_authorized"] = True
        with self.assertRaisesRegex(
            subject.GreeceSourceCsvReceiptsError,
            "publication_authorized",
        ):
            subject.validate_receipt(receipt, expected_target=target)

        receipt = self._valid_receipt(target)
        receipt["source_runtime_lineage_verified"] = True
        with self.assertRaisesRegex(
            subject.GreeceSourceCsvReceiptsError,
            "source_runtime_lineage_verified",
        ):
            subject.validate_receipt(receipt, expected_target=target)


if __name__ == "__main__":
    unittest.main()
