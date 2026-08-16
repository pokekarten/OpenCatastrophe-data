# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import unittest
from unittest import mock

from scripts import acquire_eshm20_source_model_child_receipts as worker


PAYLOAD = b"<nrml synthetic='true'/>\n"


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
            "Content-Type": "application/xml",
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


class Eshm20SourceModelChildReceiptWorkerTests(unittest.TestCase):
    def opener(self, captured: list[tuple[str, float]]):
        def open_response(request, timeout):
            path = repository_path_from_url(request.full_url)
            captured.append((path, timeout))
            return FakeResponse(PAYLOAD, request.full_url)

        return open_response

    def test_public_worker_exposes_no_target_or_file_selector(self) -> None:
        signature = inspect.signature(worker.acquire_eshm20_source_model_child_receipts)
        self.assertEqual(set(signature.parameters), set())
        self.assertIs(worker.CHILDREN, worker._CANONICAL_CHILDREN)

    def test_exact_51_path_set_is_sorted_unique_and_fingerprint_bound(self) -> None:
        paths = tuple(spec.repository_path for spec in worker.CHILDREN)
        self.assertEqual(len(paths), 51)
        self.assertEqual(paths, tuple(sorted(paths)))
        self.assertEqual(len(set(paths)), 51)
        self.assertEqual(
            worker._paths_fingerprint(worker.CHILDREN),
            "2fcc885dc9fbbd8e9ee45b185dc9f2339af3654e9976ae5f07d4d097551944b7",
        )
        self.assertTrue(all("/source_models/" in path for path in paths))
        self.assertTrue(all(path.endswith(".xml") for path in paths))
        self.assertFalse(any(path.endswith(".hdf5") for path in paths))

    def test_receipts_all_51_paths_in_frozen_order_with_parent_binding(self) -> None:
        captured: list[tuple[str, float]] = []
        counter = 0

        def now() -> str:
            nonlocal counter
            counter += 1
            return f"2026-08-15T22:{counter // 60:02d}:{counter % 60:02d}Z"

        result = worker._acquire_eshm20_source_model_child_receipts(
            opener=self.opener(captured),
            now=now,
            monotonic=lambda: 100.0,
        )

        expected_paths = [spec.repository_path for spec in worker.CHILDREN]
        self.assertEqual([path for path, _ in captured], expected_paths)
        self.assertEqual([item["repository_path"] for item in result["receipts"]], expected_paths)
        self.assertEqual(result["child_count"], 51)
        self.assertEqual(result["child_paths_sha256"], worker.EXPECTED_PATHS_SHA256)
        self.assertEqual(result["parent_request_comment_id"], 5304431360)
        self.assertEqual(result["parent_result_comment_id"], 5304432768)
        self.assertEqual(result["parent_run_id"], 31910992436)
        self.assertEqual(
            result["parent_execution_sha"],
            "dac7c9ae1c391006b8272f1342143d1ace678234",
        )
        self.assertEqual(result["parent_source_tree_byte_count"], 17579)
        self.assertEqual(
            result["parent_source_tree_sha256"],
            "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867",
        )
        self.assertFalse(result["dependency_inventory_authorized"])
        self.assertFalse(result["dependency_receipt_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

        for item in result["receipts"]:
            self.assertEqual(item["project_id"], 197)
            self.assertEqual(item["project_path"], "efehr/eshm20")
            self.assertEqual(item["commit_sha"], worker.COMMIT_SHA)
            self.assertEqual(item["parent_result_comment_id"], 5304432768)
            self.assertFalse(item["external_bytes_persisted"])
            self.assertFalse(item["dependency_inventory_authorized"])
            self.assertFalse(item["dependency_receipt_authorized"])
            self.assertFalse(item["external_bytes_persisted"])
            self.assertFalse(item["publication_authorized"])
            self.assertFalse(item["model_use_authorized"])
            self.assertEqual(set(item), worker._CHILD_RECEIPT_FIELDS)
            self.assertNotIn("requested_url", item)
            self.assertNotIn("final_url", item)
            self.assertNotIn("content_type", item)
            self.assertNotIn("etag", item)
            self.assertNotIn(PAYLOAD.decode().strip(), repr(item))

    def test_one_total_deadline_is_shared_across_51_requests(self) -> None:
        captured: list[tuple[str, float]] = []
        clock = [10.0]

        def monotonic() -> float:
            current = clock[0]
            clock[0] += 0.01
            return current

        worker._acquire_eshm20_source_model_child_receipts(
            opener=self.opener(captured),
            now=lambda: "2026-08-15T22:00:00Z",
            monotonic=monotonic,
        )
        timeouts = [timeout for _, timeout in captured]
        self.assertEqual(len(timeouts), 51)
        self.assertGreater(timeouts[0], timeouts[-1])
        self.assertTrue(all(a > b for a, b in zip(timeouts, timeouts[1:])))

    def test_partial_transport_failure_returns_no_partial_result(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 17:
                raise OSError("PRIVATE_PROVIDER_BODY")
            return FakeResponse(PAYLOAD, request.full_url)

        with self.assertRaises(worker.Eshm20SourceModelChildReceiptError) as caught:
            worker._acquire_eshm20_source_model_child_receipts(
                opener=opener,
                now=lambda: "2026-08-15T22:00:00Z",
                monotonic=lambda: 10.0,
            )
        self.assertEqual(calls, 17)
        self.assertNotIn("PRIVATE_PROVIDER_BODY", str(caught.exception))

    def test_response_identity_drift_fails_closed(self) -> None:
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 2:
                return FakeResponse(
                    PAYLOAD,
                    request.full_url,
                    final_url="https://gitlab.seismo.ethz.ch/unexpected",
                )
            return FakeResponse(PAYLOAD, request.full_url)

        with self.assertRaises(worker.Eshm20SourceModelChildReceiptError):
            worker._acquire_eshm20_source_model_child_receipts(
                opener=opener,
                now=lambda: "2026-08-15T22:00:00Z",
                monotonic=lambda: 10.0,
            )
        self.assertEqual(calls, 2)

    def test_reordered_duplicate_clone_extra_or_short_set_fails_before_network(self) -> None:
        reordered = tuple(reversed(worker.CHILDREN))
        duplicate = (worker.CHILDREN[0],) + worker.CHILDREN[:-1]
        equal_clones = tuple(
            worker.ChildSpec(repository_path=spec.repository_path)
            for spec in worker.CHILDREN
        )
        forged = worker.ChildSpec(
            repository_path=(
                "oq_computational/oq_configuration_eshm20_v12e_region_main/"
                "config_eshm20_v12e_main_region.ini"
            )
        )
        extra = worker.CHILDREN + (forged,)
        short = worker.CHILDREN[:-1]

        for mutated in (reordered, duplicate, equal_clones, extra, short):
            with self.subTest(length=len(mutated)):
                opener = mock.Mock()
                with mock.patch.object(worker, "CHILDREN", mutated):
                    with self.assertRaises(worker.Eshm20SourceModelChildReceiptError):
                        worker._acquire_eshm20_source_model_child_receipts(
                            opener=opener,
                            now=lambda: "2026-08-15T22:00:00Z",
                            monotonic=lambda: 10.0,
                        )
                opener.assert_not_called()

    def test_direct_helper_rejects_constructed_equal_or_forged_spec_before_network(self) -> None:
        equal_clone = worker.ChildSpec(
            repository_path=worker.CHILDREN[0].repository_path
        )
        forged = worker.ChildSpec(
            repository_path=(
                "oq_computational/oq_configuration_eshm20_v12e_region_main/"
                "source_models/not-returned-by-397.xml"
            )
        )
        for spec in (equal_clone, forged):
            opener = mock.Mock()
            with self.subTest(spec=spec):
                with self.assertRaisesRegex(
                    worker.Eshm20SourceModelChildReceiptError,
                    "not an authorized fixed target",
                ):
                    worker._receipt_one(
                        spec,
                        deadline=100.0,
                        opener=opener,
                        now=lambda: "2026-08-15T22:00:00Z",
                        monotonic=lambda: 10.0,
                    )
                opener.assert_not_called()

    def test_worker_rejects_widened_or_open_ended_core_receipt(self) -> None:
        original = worker._CANONICAL_RECEIPT_FROM_STREAM

        def widened(*args, **kwargs):
            receipt = original(*args, **kwargs)
            receipt["model_use_authorized"] = True
            return receipt

        with self.assertRaisesRegex(
            worker.Eshm20SourceModelChildReceiptError,
            "fields drifted",
        ):
            worker._acquire_eshm20_source_model_child_receipts(
                opener=self.opener([]),
                now=lambda: "2026-08-15T22:00:00Z",
                monotonic=lambda: 10.0,
                receipt_builder=widened,
            )

    def test_public_authority_alias_drift_fails_before_network(self) -> None:
        for field, value in (
            ("COMMIT_SHA", "b" * 40),
            ("PARENT_RESULT_COMMENT_ID", 1),
        ):
            opener = mock.Mock()
            with self.subTest(field=field), mock.patch.object(worker, field, value):
                with self.assertRaisesRegex(
                    worker.Eshm20SourceModelChildReceiptError,
                    "drifted",
                ):
                    worker._acquire_eshm20_source_model_child_receipts(
                        opener=opener,
                        now=lambda: "2026-08-15T22:00:00Z",
                        monotonic=lambda: 10.0,
                    )
            opener.assert_not_called()

    def test_public_production_transport_or_clock_drift_fails_before_network(self) -> None:
        for field, replacement in (
            ("_open_fixed", mock.Mock()),
            ("utc_now", mock.Mock()),
            ("validate_target", mock.Mock()),
        ):
            with self.subTest(field=field), mock.patch.object(worker, field, replacement):
                with self.assertRaisesRegex(
                    worker.Eshm20SourceModelChildReceiptError,
                    "production .* drifted",
                ):
                    worker.acquire_eshm20_source_model_child_receipts()



if __name__ == "__main__":
    unittest.main()
