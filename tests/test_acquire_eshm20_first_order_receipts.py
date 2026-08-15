# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import unittest
from unittest import mock

from scripts import acquire_eshm20_first_order_receipts as worker


PAYLOADS = {
    worker.DEPENDENCIES[0].repository_path: b"site_model_fixture\n",
    worker.DEPENDENCIES[1].repository_path: b"<gmpe>fixture</gmpe>\n",
    worker.DEPENDENCIES[2].repository_path: b"<source>fixture</source>\n",
}


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
        self.headers = {
            "Content-Length": str(len(raw)),
            "Content-Type": "application/octet-stream",
            "ETag": '"synthetic"',
        }
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


def repository_path_from_url(url: str) -> str:
    from urllib.parse import unquote, urlsplit

    path = urlsplit(url).path
    marker = "/repository/files/"
    encoded = path.split(marker, 1)[1].rsplit("/raw", 1)[0]
    return unquote(encoded)


class Eshm20FirstOrderReceiptWorkerTests(unittest.TestCase):
    def opener(self, captured: list[tuple[str, float]]):
        def open_response(request, timeout):
            path = repository_path_from_url(request.full_url)
            captured.append((path, timeout))
            return FakeResponse(PAYLOADS[path], request.full_url)

        return open_response

    def test_public_worker_exposes_no_target_or_file_selector(self) -> None:
        signature = inspect.signature(worker.acquire_eshm20_first_order_receipts)
        self.assertEqual(set(signature.parameters), {"opener", "now", "monotonic"})
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

    def test_receipts_exact_three_paths_in_frozen_order_with_parent_binding(self) -> None:
        captured: list[tuple[str, float]] = []
        times = iter(
            (
                "2026-08-15T10:10:01Z",
                "2026-08-15T10:10:02Z",
                "2026-08-15T10:10:03Z",
            )
        )
        result = worker.acquire_eshm20_first_order_receipts(
            opener=self.opener(captured),
            now=lambda: next(times),
            monotonic=lambda: 100.0,
        )

        expected_paths = [spec.repository_path for spec in worker.DEPENDENCIES]
        self.assertEqual([path for path, _ in captured], expected_paths)
        self.assertEqual([item["repository_path"] for item in result["receipts"]], expected_paths)
        self.assertEqual(result["selection_request_comment_id"], 5301725105)
        self.assertEqual(result["selection_result_comment_id"], 5301726249)
        self.assertEqual(result["selection_run_id"], 31878511737)
        self.assertEqual(
            result["selection_execution_sha"],
            "bd146a19fa4a1dc85b616288ec6d24946336a483",
        )
        self.assertFalse(result["dependency_inventory_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])

        for item, spec in zip(result["receipts"], worker.DEPENDENCIES, strict=True):
            self.assertEqual(item["source_issue"], 281)
            self.assertEqual(item["dataset_id"], "efehr.eshm20")
            self.assertEqual(item["project_id"], 197)
            self.assertEqual(item["project_path"], "efehr/eshm20")
            self.assertEqual(item["commit_sha"], worker.COMMIT_SHA)
            self.assertEqual(item["parent_result_comment_id"], 5301726249)
            self.assertEqual(item["parent_section"], spec.parent_section)
            self.assertEqual(item["parent_option"], spec.parent_option)
            self.assertFalse(item["external_bytes_persisted"])
            self.assertFalse(item["publication_authorized"])
            self.assertNotIn(PAYLOADS[spec.repository_path].decode().strip(), repr(item))

    def test_one_total_deadline_is_shared_across_all_three_requests(self) -> None:
        captured: list[tuple[str, float]] = []
        clock = [10.0]

        def monotonic() -> float:
            current = clock[0]
            clock[0] += 0.1
            return current

        worker.acquire_eshm20_first_order_receipts(
            opener=self.opener(captured),
            now=lambda: "2026-08-15T10:10:01Z",
            monotonic=monotonic,
        )
        timeouts = [timeout for _, timeout in captured]
        self.assertEqual(len(timeouts), 3)
        self.assertGreater(timeouts[0], timeouts[1])
        self.assertGreater(timeouts[1], timeouts[2])

    def test_response_identity_drift_fails_without_partial_result(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            path = repository_path_from_url(request.full_url)
            if calls == 2:
                return FakeResponse(
                    PAYLOADS[path],
                    request.full_url,
                    final_url="https://gitlab.seismo.ethz.ch/unexpected",
                )
            return FakeResponse(PAYLOADS[path], request.full_url)

        with self.assertRaises(worker.Eshm20FirstOrderReceiptError):
            worker.acquire_eshm20_first_order_receipts(
                opener=opener,
                now=lambda: "2026-08-15T10:10:01Z",
                monotonic=lambda: 10.0,
            )
        self.assertEqual(calls, 2)

    def test_non_success_status_fails_closed(self) -> None:
        def opener(request, timeout):
            path = repository_path_from_url(request.full_url)
            return FakeResponse(PAYLOADS[path], request.full_url, status=206)

        with self.assertRaises(worker.Eshm20FirstOrderReceiptError):
            worker.acquire_eshm20_first_order_receipts(
                opener=opener,
                now=lambda: "2026-08-15T10:10:01Z",
                monotonic=lambda: 10.0,
            )

    def test_transport_exception_does_not_leak_provider_text(self) -> None:
        def opener(request, timeout):
            raise OSError("PROVIDER_SECRET_BODY")

        with self.assertRaises(worker.Eshm20FirstOrderReceiptError) as caught:
            worker.acquire_eshm20_first_order_receipts(
                opener=opener,
                monotonic=lambda: 10.0,
            )
        self.assertIn("OSError", str(caught.exception))
        self.assertNotIn("PROVIDER_SECRET_BODY", str(caught.exception))

    def test_internal_duplicate_or_reordered_frozen_set_fails_before_network(self) -> None:
        duplicate = (
            worker.DEPENDENCIES[0],
            worker.DEPENDENCIES[0],
            worker.DEPENDENCIES[2],
        )
        reordered = tuple(reversed(worker.DEPENDENCIES))
        for mutated in (duplicate, reordered):
            with self.subTest(mutated=mutated):
                opener = mock.Mock()
                with mock.patch.object(worker, "DEPENDENCIES", mutated):
                    with self.assertRaises(worker.Eshm20FirstOrderReceiptError):
                        worker.acquire_eshm20_first_order_receipts(opener=opener)
                opener.assert_not_called()

    def test_worker_rejects_widened_nested_receipt_authority(self) -> None:
        original = worker.receipt_from_stream

        def widened(*args, **kwargs):
            receipt = original(*args, **kwargs)
            receipt["publication_authorized"] = True
            return receipt

        with mock.patch.object(worker, "receipt_from_stream", side_effect=widened):
            with self.assertRaisesRegex(
                worker.Eshm20FirstOrderReceiptError, "widened"
            ):
                worker.acquire_eshm20_first_order_receipts(
                    opener=self.opener([]),
                    now=lambda: "2026-08-15T10:10:01Z",
                    monotonic=lambda: 10.0,
                )


if __name__ == "__main__":
    unittest.main()
