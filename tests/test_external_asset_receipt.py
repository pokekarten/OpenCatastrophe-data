# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.validate_external_asset_receipt import (
    ReceiptError,
    canonical_receipt_bytes,
    load_receipt,
    receipt_sha256,
    validate_receipt,
    verify_artifact,
)


class ExternalAssetReceiptTests(unittest.TestCase):
    def _receipt(self) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "acquisition_intent_sha256": "a" * 64,
            "manifest": {
                "path": "manifests/example.dataset.json",
                "sha256": "b" * 64,
            },
            "request": {
                "exact_request": {
                    "provider": "example",
                    "dataset": "historical",
                    "area": [51.1, 13.7, 51.0, 13.8],
                    "years": [2020, 2021, 2022, 2023],
                    "endpoint": "https://example.org/data?format=csv",
                },
                "retrieved_at": "2026-08-10T15:30:00Z",
            },
            "artifact": {
                "logical_identity": "example:historical:2020-2023",
                "byte_size": 1234,
                "sha256": "c" * 64,
                "storage_reference": "external://source-cache/example-2020-2023.bin",
            },
        }

    def test_valid_receipt_has_deterministic_identity(self) -> None:
        receipt = self._receipt()
        validate_receipt(
            receipt,
            expected_intent_sha256="a" * 64,
            expected_manifest="manifests/example.dataset.json",
            expected_manifest_sha256="b" * 64,
        )
        self.assertEqual(receipt_sha256(receipt), receipt_sha256(dict(reversed(list(receipt.items())))))
        self.assertTrue(canonical_receipt_bytes(receipt).startswith(b'{"acquisition_intent_sha256":'))

    def test_closed_contract_rejects_missing_extra_and_type_confusion(self) -> None:
        extra = self._receipt()
        extra["unreviewed"] = True
        with self.assertRaisesRegex(ReceiptError, "unexpected fields"):
            validate_receipt(extra)

        missing = self._receipt()
        del missing["artifact"]
        with self.assertRaisesRegex(ReceiptError, "missing fields"):
            validate_receipt(missing)

        confused = self._receipt()
        confused["artifact"]["byte_size"] = True  # type: ignore[index]
        with self.assertRaisesRegex(ReceiptError, "positive integer"):
            validate_receipt(confused)

    def test_expected_bindings_fail_closed(self) -> None:
        receipt = self._receipt()
        with self.assertRaisesRegex(ReceiptError, "expected frozen intent"):
            validate_receipt(receipt, expected_intent_sha256="d" * 64)
        with self.assertRaisesRegex(ReceiptError, "expected admitted manifest"):
            validate_receipt(receipt, expected_manifest="manifests/other.json")
        with self.assertRaisesRegex(ReceiptError, "manifest identity"):
            validate_receipt(receipt, expected_manifest_sha256="d" * 64)

    def test_verify_artifact_rehashes_exact_external_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "artifact.bin"
            payload = b"exact external bytes\n"
            artifact_path.write_bytes(payload)

            receipt = self._receipt()
            receipt["artifact"]["byte_size"] = len(payload)  # type: ignore[index]
            receipt["artifact"]["sha256"] = hashlib.sha256(payload).hexdigest()  # type: ignore[index]
            verify_artifact(receipt, artifact_path)

            artifact_path.write_bytes(b"x" * len(payload))
            with self.assertRaisesRegex(ReceiptError, "SHA-256"):
                verify_artifact(receipt, artifact_path)

            artifact_path.write_bytes(payload + b"drift")
            with self.assertRaisesRegex(ReceiptError, "byte size"):
                verify_artifact(receipt, artifact_path)

    def test_paths_hashes_timestamp_and_storage_are_strict(self) -> None:
        receipt = self._receipt()
        receipt["manifest"]["path"] = "../manifests/example.json"  # type: ignore[index]
        with self.assertRaisesRegex(ReceiptError, "manifests/.*json"):
            validate_receipt(receipt)

        receipt = self._receipt()
        receipt["artifact"]["sha256"] = "C" * 64  # type: ignore[index]
        with self.assertRaisesRegex(ReceiptError, "lowercase SHA-256"):
            validate_receipt(receipt)

        receipt = self._receipt()
        receipt["request"]["retrieved_at"] = "2026-08-10 15:30:00"  # type: ignore[index]
        with self.assertRaisesRegex(ReceiptError, "RFC-3339"):
            validate_receipt(receipt)

        receipt = self._receipt()
        receipt["artifact"]["storage_reference"] = "data/example.bin"  # type: ignore[index]
        with self.assertRaisesRegex(ReceiptError, "external://"):
            validate_receipt(receipt)

    def test_exact_request_rejects_secret_material(self) -> None:
        for exact_request in (
            {"authorization": "Bearer secret"},
            {"headers": {"Cookie": "session=secret"}},
            {"url": "https://example.org/data?token=secret"},
            {"url": "https://user:secret@example.org/data"},
            {"X-Amz-Signature": "secret"},
        ):
            with self.subTest(exact_request=exact_request):
                receipt = self._receipt()
                receipt["request"]["exact_request"] = exact_request  # type: ignore[index]
                with self.assertRaises(ReceiptError):
                    validate_receipt(receipt)

    def test_loader_rejects_duplicate_keys_and_non_finite_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "receipt.json"
            path.write_text('{"schema_version":"1.0.0","schema_version":"1.0.0"}', encoding="utf-8")
            with self.assertRaisesRegex(ReceiptError, "duplicate JSON key"):
                load_receipt(path)

            path.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ReceiptError, "non-finite"):
                load_receipt(path)

    def test_request_json_rejects_nonfinite_and_control_characters(self) -> None:
        receipt = self._receipt()
        receipt["request"]["exact_request"] = {"threshold": float("nan")}  # type: ignore[index]
        with self.assertRaisesRegex(ReceiptError, "non-finite"):
            validate_receipt(receipt)

        receipt = self._receipt()
        receipt["artifact"]["logical_identity"] = "bad\nidentity"  # type: ignore[index]
        with self.assertRaisesRegex(ReceiptError, "control characters"):
            validate_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
