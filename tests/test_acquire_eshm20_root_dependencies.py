# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_eshm20_root_dependencies as worker


RAW = b"[input]\nsource_model_logic_tree_file = source.xml\n"
PRIVATE_MARKER_RAW = b"[general]\ndescription = PROVIDER_PRIVATE_BODY\n"


class FakeResponse:
    def __init__(
        self,
        raw: bytes,
        url: str,
        *,
        final_url: str | None = None,
        status: int = 200,
    ) -> None:
        self.status = status
        self.headers = {"Content-Length": str(len(raw))}
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


class FixedEshm20RootDependencyWorkerTests(unittest.TestCase):
    def opener_for(self, raw: bytes, captured: list[str]):
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            return FakeResponse(raw, request.full_url)

        return opener

    def synthetic_bridge_result(self) -> dict[str, object]:
        return {
            "schema_version": worker.bridge.SCHEMA_VERSION,
            "source_issue": worker.bridge.SOURCE_ISSUE,
            "dataset_id": worker.bridge.DATASET_ID,
            "project_id": worker.bridge.PROJECT_ID,
            "project_path": worker.bridge.PROJECT_PATH,
            "commit_sha": worker.bridge.COMMIT_SHA,
            "repository_path": worker.bridge.REPOSITORY_PATH,
            "byte_count": len(RAW),
            "sha256": hashlib.sha256(RAW).hexdigest(),
            "parser": worker.bridge.PARSER_ID,
            "inventory_receipt_comment_id": worker.bridge.INVENTORY_RECEIPT_COMMENT_ID,
            "dependencies": [],
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }

    def test_public_worker_exposes_no_provider_or_parser_selector(self) -> None:
        signature = inspect.signature(worker.acquire_eshm20_root_dependencies)
        self.assertEqual(set(signature.parameters), {"opener", "monotonic"})
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

    def test_worker_uses_only_fixed_project_commit_and_root_path(self) -> None:
        captured: list[str] = []
        with mock.patch.object(
            worker.bridge,
            "extract_verified_root_dependencies",
            return_value=self.synthetic_bridge_result(),
        ) as verified_bridge:
            result = worker.acquire_eshm20_root_dependencies(
                opener=self.opener_for(RAW, captured)
            )

        self.assertEqual(len(captured), 1)
        self.assertIn(f"/api/v4/projects/{worker.bridge.PROJECT_ID}/", captured[0])
        self.assertIn(worker.bridge.COMMIT_SHA, captured[0])
        self.assertIn("config_eshm20_v12e_main_region.ini", result["repository_path"])
        verified_bridge.assert_called_once_with(RAW)

    def test_worker_adds_only_frozen_receipt_and_non_authority_provenance(self) -> None:
        with mock.patch.object(
            worker.bridge,
            "extract_verified_root_dependencies",
            return_value=self.synthetic_bridge_result(),
        ):
            result = worker.acquire_eshm20_root_dependencies(
                opener=self.opener_for(RAW, [])
            )
        self.assertEqual(result["root_receipt_comment_id"], worker.ROOT_RECEIPT_COMMENT_ID)
        self.assertEqual(result["root_receipt_run_id"], worker.ROOT_RECEIPT_RUN_ID)
        self.assertEqual(
            result["root_receipt_execution_sha"], worker.ROOT_RECEIPT_EXECUTION_SHA
        )
        self.assertFalse(result["dependency_inventory_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])

    def test_exact_bytes_are_handed_to_reviewed_bridge_and_body_never_returned(self) -> None:
        with mock.patch.object(
            worker.bridge,
            "extract_verified_root_dependencies",
            return_value=self.synthetic_bridge_result(),
        ) as verified_bridge:
            result = worker.acquire_eshm20_root_dependencies(
                opener=self.opener_for(PRIVATE_MARKER_RAW, [])
            )
        verified_bridge.assert_called_once_with(PRIVATE_MARKER_RAW)
        self.assertNotIn("PROVIDER_PRIVATE_BODY", repr(result))

    def test_response_identity_and_status_drift_fail_before_bridge(self) -> None:
        def wrong_url_opener(request, timeout):
            self.assertGreater(timeout, 0)
            return FakeResponse(
                RAW,
                request.full_url,
                final_url="https://gitlab.seismo.ethz.ch/unexpected",
            )

        def wrong_status_opener(request, timeout):
            self.assertGreater(timeout, 0)
            return FakeResponse(RAW, request.full_url, status=206)

        for opener in (wrong_url_opener, wrong_status_opener):
            with self.subTest(opener=opener):
                with mock.patch.object(
                    worker.bridge, "extract_verified_root_dependencies"
                ) as verified_bridge:
                    with self.assertRaisesRegex(
                        worker.Eshm20RootDependencyAcquisitionError,
                        "retrieval failed closed",
                    ):
                        worker.acquire_eshm20_root_dependencies(opener=opener)
                verified_bridge.assert_not_called()

    def test_bridge_verifies_digest_before_dependency_parser(self) -> None:
        expected = hashlib.sha256(RAW).hexdigest()
        with (
            mock.patch.object(worker.bridge, "EXPECTED_BYTE_COUNT", len(RAW)),
            mock.patch.object(worker.bridge, "EXPECTED_SHA256", expected),
            mock.patch.object(
                worker.bridge, "extract_openquake_config_references", return_value=[]
            ) as parser,
        ):
            worker.bridge.extract_verified_root_dependencies(RAW)
            parser.assert_called_once()
            parser.reset_mock()
            tampered = RAW[:-1] + bytes([RAW[-1] ^ 1])
            with self.assertRaisesRegex(worker.bridge.VerifiedRootConfigError, "SHA-256"):
                worker.bridge.extract_verified_root_dependencies(tampered)
            parser.assert_not_called()

    def test_transport_failure_does_not_leak_provider_exception_text(self) -> None:
        def opener(request, timeout):
            raise OSError("PROVIDER_SECRET_BODY")

        with self.assertRaises(worker.Eshm20RootDependencyAcquisitionError) as caught:
            worker.acquire_eshm20_root_dependencies(opener=opener)
        self.assertNotIn("PROVIDER_SECRET_BODY", str(caught.exception))
        self.assertIn("OSError", str(caught.exception))

    def test_worker_rejects_any_widened_bridge_authority(self) -> None:
        for mutation in (
            {"external_bytes_persisted": True},
            {"publication_authorized": True},
        ):
            widened = self.synthetic_bridge_result()
            widened.update(mutation)
            with mock.patch.object(
                worker.bridge,
                "extract_verified_root_dependencies",
                return_value=widened,
            ):
                with self.assertRaisesRegex(
                    worker.Eshm20RootDependencyAcquisitionError, "widened"
                ):
                    worker.acquire_eshm20_root_dependencies(
                        opener=self.opener_for(RAW, [])
                    )


if __name__ == "__main__":
    unittest.main()
