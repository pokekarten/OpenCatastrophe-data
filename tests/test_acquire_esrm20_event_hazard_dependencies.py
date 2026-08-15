# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest import mock

from scripts import acquire_esrm20_event_hazard_dependencies as worker


GROUP1_RAW = (
    b"[general]\n"
    b"description = GROUP1_PRIVATE_BODY_MARKER\n"
    b"[input]\n"
    b"source_model_logic_tree_file = ../Hazard/source_g1.xml\n"
)
GROUP2_RAW = (
    b"[general]\n"
    b"description = GROUP2_PRIVATE_BODY_MARKER\n"
    b"[input]\n"
    b"source_model_logic_tree_file = ../Hazard/source_g2.xml\n"
)


def spec(group: int, raw: bytes) -> worker.bridge.RootSpec:
    return worker.bridge.RootSpec(
        group=group,
        repository_path=f"Configuration_files/config_event_hazard_Group{group}.ini",
        operation_id=f"synthetic-group-{group}",
        byte_count=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
        receipt_comment_id=1000 + group,
    )


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


class FixedEventHazardDependencyWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.specs = {1: spec(1, GROUP1_RAW), 2: spec(2, GROUP2_RAW)}

    def opener_for(self, raw: bytes, captured: list[str]):
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            return FakeResponse(raw, request.full_url)

        return opener

    def test_public_workers_expose_no_group_or_provider_target_selector(self) -> None:
        for function in (
            worker.acquire_event_hazard_group1_dependencies,
            worker.acquire_event_hazard_group2_dependencies,
        ):
            signature = inspect.signature(function)
            self.assertEqual(set(signature.parameters), {"opener", "monotonic"})
            self.assertTrue(
                all(
                    parameter.kind is inspect.Parameter.KEYWORD_ONLY
                    for parameter in signature.parameters.values()
                )
            )

    def test_group_entry_points_use_distinct_fixed_immutable_targets(self) -> None:
        group1_urls: list[str] = []
        group2_urls: list[str] = []
        with mock.patch.object(worker.bridge, "ROOT_SPECS", self.specs):
            result1 = worker.acquire_event_hazard_group1_dependencies(
                opener=self.opener_for(GROUP1_RAW, group1_urls)
            )
            result2 = worker.acquire_event_hazard_group2_dependencies(
                opener=self.opener_for(GROUP2_RAW, group2_urls)
            )

        self.assertEqual(len(group1_urls), 1)
        self.assertEqual(len(group2_urls), 1)
        self.assertNotEqual(group1_urls[0], group2_urls[0])
        for url in group1_urls + group2_urls:
            self.assertIn("/api/v4/projects/269/", url)
            self.assertIn(worker.bridge.COMMIT_SHA, url)
        self.assertIn("config_event_hazard_Group1.ini", result1["repository_path"])
        self.assertIn("config_event_hazard_Group2.ini", result2["repository_path"])
        self.assertEqual(result1["group"], 1)
        self.assertEqual(result2["group"], 2)

    def test_cross_group_bytes_fail_before_dependency_parser(self) -> None:
        self.assertEqual(len(GROUP1_RAW), len(GROUP2_RAW))
        with (
            mock.patch.object(worker.bridge, "ROOT_SPECS", self.specs),
            mock.patch.object(
                worker.bridge, "extract_openquake_config_references"
            ) as parser,
        ):
            with self.assertRaisesRegex(
                worker.EventHazardDependencyAcquisitionError, "verification failed"
            ):
                worker.acquire_event_hazard_group1_dependencies(
                    opener=self.opener_for(GROUP2_RAW, [])
                )
        parser.assert_not_called()

    def test_exact_verified_bytes_are_delegated_to_reviewed_bridge(self) -> None:
        captured: list[str] = []
        original = worker.bridge.extract_verified_event_hazard_dependencies
        with (
            mock.patch.object(worker.bridge, "ROOT_SPECS", self.specs),
            mock.patch.object(
                worker.bridge,
                "extract_verified_event_hazard_dependencies",
                wraps=original,
            ) as verified_bridge,
        ):
            result = worker.acquire_event_hazard_group1_dependencies(
                opener=self.opener_for(GROUP1_RAW, captured)
            )

        verified_bridge.assert_called_once_with(1, GROUP1_RAW)
        self.assertEqual(
            [item["resolved_path"] for item in result["dependencies"]],
            ["Hazard/source_g1.xml"],
        )
        self.assertFalse(result["dependency_inventory_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertNotIn("GROUP1_PRIVATE_BODY_MARKER", repr(result))

    def test_response_identity_drift_fails_before_parser(self) -> None:
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            return FakeResponse(
                GROUP1_RAW,
                request.full_url,
                final_url="https://gitlab.seismo.ethz.ch/unexpected",
            )

        with (
            mock.patch.object(worker.bridge, "ROOT_SPECS", self.specs),
            mock.patch.object(
                worker.bridge, "extract_openquake_config_references"
            ) as parser,
        ):
            with self.assertRaisesRegex(
                worker.EventHazardDependencyAcquisitionError, "retrieval failed closed"
            ):
                worker.acquire_event_hazard_group1_dependencies(opener=opener)
        parser.assert_not_called()

    def test_response_status_drift_fails_before_parser(self) -> None:
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            return FakeResponse(GROUP1_RAW, request.full_url, status=206)

        with (
            mock.patch.object(worker.bridge, "ROOT_SPECS", self.specs),
            mock.patch.object(
                worker.bridge, "extract_openquake_config_references"
            ) as parser,
        ):
            with self.assertRaisesRegex(
                worker.EventHazardDependencyAcquisitionError, "retrieval failed closed"
            ):
                worker.acquire_event_hazard_group1_dependencies(opener=opener)
        parser.assert_not_called()

    def test_transport_failure_does_not_leak_provider_exception_text(self) -> None:
        def opener(request, timeout):
            raise OSError("PROVIDER_SECRET_BODY")

        with mock.patch.object(worker.bridge, "ROOT_SPECS", self.specs):
            with self.assertRaises(worker.EventHazardDependencyAcquisitionError) as caught:
                worker.acquire_event_hazard_group1_dependencies(opener=opener)
        self.assertNotIn("PROVIDER_SECRET_BODY", str(caught.exception))
        self.assertIn("OSError", str(caught.exception))

    def test_worker_rejects_any_widened_bridge_authority(self) -> None:
        widened = {
            "dependency_inventory_authorized": False,
            "external_bytes_persisted": False,
            "publication_authorized": True,
        }
        with (
            mock.patch.object(worker.bridge, "ROOT_SPECS", self.specs),
            mock.patch.object(
                worker.bridge,
                "extract_verified_event_hazard_dependencies",
                return_value=widened,
            ),
        ):
            with self.assertRaisesRegex(
                worker.EventHazardDependencyAcquisitionError, "widened"
            ):
                worker.acquire_event_hazard_group1_dependencies(
                    opener=self.opener_for(GROUP1_RAW, [])
                )


if __name__ == "__main__":
    unittest.main()
