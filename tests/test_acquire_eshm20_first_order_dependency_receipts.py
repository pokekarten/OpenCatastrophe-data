# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest.mock import patch

from scripts import acquire_eshm20_first_order_dependency_receipts as worker
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.efehr_gitlab_receipt import MAX_FILE_BYTES, raw_file_api_url, validate_target

RETRIEVED_AT = "2026-08-15T10:15:00Z"


class FakeResponse:
    def __init__(
        self,
        payload: bytes | str,
        url: str,
        *,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1):
        if self._offset >= len(self._payload):
            return b"" if isinstance(self._payload, bytes) else ""
        if size is None or size < 0:
            end = len(self._payload)
        else:
            end = min(len(self._payload), self._offset + size)
        chunk = self._payload[self._offset : end]
        self._offset = end
        return chunk


def expected_url(path: str) -> str:
    target = validate_target(
        source_issue=worker.SOURCE_ISSUE,
        dataset_id=worker.DATASET_ID,
        project_id=worker.PROJECT_ID,
        commit_sha=worker.COMMIT_SHA,
        repository_path=path,
    )
    return raw_file_api_url(target)


CASES = (
    (
        worker.acquire_eshm20_site_model_receipt,
        worker._SITE_MODEL,
    ),
    (
        worker.acquire_eshm20_gmpe_logic_tree_receipt,
        worker._GMPE_LOGIC_TREE,
    ),
    (
        worker.acquire_eshm20_source_model_logic_tree_receipt,
        worker._SOURCE_MODEL_LOGIC_TREE,
    ),
)


class Eshm20FirstOrderDependencyReceiptTests(unittest.TestCase):
    def test_public_workers_have_no_caller_controlled_target_surface(self) -> None:
        for function, spec in CASES:
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    set(inspect.signature(function).parameters),
                    {"opener", "now", "monotonic"},
                )
                self.assertTrue(spec.repository_path.startswith(worker.DEPENDENCY_PREFIX))

        self.assertEqual(worker.SOURCE_ISSUE, 281)
        self.assertEqual(worker.DATASET_ID, "efehr.eshm20")
        self.assertEqual(worker.PROJECT_ID, 197)
        self.assertEqual(
            worker.COMMIT_SHA,
            "fbd334de68f85d72669f73fc5a314a113db67317",
        )
        self.assertEqual(worker.DISCOVERY_ISSUE, 353)
        self.assertEqual(worker.DISCOVERY_REQUEST_COMMENT_ID, 5301725105)
        self.assertEqual(worker.DISCOVERY_RESULT_COMMENT_ID, 5301726249)
        self.assertEqual(worker.DISCOVERY_RUN_ID, 31878511737)
        self.assertEqual(
            worker.DISCOVERY_EXECUTION_SHA,
            "bd146a19fa4a1dc85b616288ec6d24946336a483",
        )

    def test_fixed_workers_receipt_only_the_three_root_proven_paths(self) -> None:
        payloads = {
            worker._SITE_MODEL.repository_path: b"lon,lat,vs30\n1,2,760\n",
            worker._GMPE_LOGIC_TREE.repository_path: b"<nrml><logicTree/></nrml>\n",
            worker._SOURCE_MODEL_LOGIC_TREE.repository_path: b"<nrml><logicTree/></nrml>\n",
        }
        observed_urls: set[str] = set()

        for function, spec in CASES:
            url = expected_url(spec.repository_path)
            payload = payloads[spec.repository_path]
            calls = []

            def opener(request, timeout, *, payload=payload, url=url):
                calls.append((request, timeout))
                return FakeResponse(
                    payload,
                    url,
                    headers={
                        "Content-Length": str(len(payload)),
                        "Content-Type": "application/octet-stream",
                        "ETag": '"synthetic"',
                    },
                )

            receipt = function(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

            self.assertEqual(len(calls), 1)
            request, timeout = calls[0]
            self.assertEqual(request.full_url, url)
            self.assertEqual(request.get_method(), "GET")
            self.assertGreater(timeout, 0)
            observed_urls.add(url)

            self.assertEqual(receipt["schema_version"], worker.SCHEMA_VERSION)
            self.assertEqual(receipt["operation_id"], spec.operation_id)
            self.assertEqual(receipt["scientific_role"], spec.scientific_role)
            self.assertEqual(receipt["source_issue"], worker.SOURCE_ISSUE)
            self.assertEqual(receipt["dataset_id"], worker.DATASET_ID)
            self.assertEqual(receipt["project_id"], worker.PROJECT_ID)
            self.assertEqual(receipt["project_path"], "efehr/eshm20")
            self.assertEqual(receipt["commit_sha"], worker.COMMIT_SHA)
            self.assertEqual(receipt["repository_path"], spec.repository_path)
            self.assertEqual(receipt["requested_url"], url)
            self.assertEqual(receipt["final_url"], url)
            self.assertEqual(receipt["retrieved_at"], RETRIEVED_AT)
            self.assertEqual(receipt["byte_count"], len(payload))
            self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(receipt["parent_repository_path"], worker.ROOT_REPOSITORY_PATH)
            self.assertEqual(receipt["parent_section"], spec.parent_section)
            self.assertEqual(receipt["parent_option"], spec.parent_option)
            self.assertEqual(receipt["discovery_issue"], worker.DISCOVERY_ISSUE)
            self.assertEqual(
                receipt["discovery_request_comment_id"],
                worker.DISCOVERY_REQUEST_COMMENT_ID,
            )
            self.assertEqual(
                receipt["discovery_result_comment_id"],
                worker.DISCOVERY_RESULT_COMMENT_ID,
            )
            self.assertEqual(receipt["discovery_run_id"], worker.DISCOVERY_RUN_ID)
            self.assertEqual(
                receipt["discovery_execution_sha"],
                worker.DISCOVERY_EXECUTION_SHA,
            )
            self.assertIs(receipt["dependency_inventory_authorized"], False)
            self.assertIs(receipt["external_bytes_persisted"], False)
            self.assertIs(receipt["publication_authorized"], False)
            self.assertNotIn(payload.decode("utf-8"), repr(receipt))

        self.assertEqual(len(observed_urls), 3)

    def test_cross_dependency_response_identity_drift_fails_closed(self) -> None:
        site_url = expected_url(worker._SITE_MODEL.repository_path)
        gmm_url = expected_url(worker._GMPE_LOGIC_TREE.repository_path)
        self.assertNotEqual(site_url, gmm_url)

        response = FakeResponse(b"synthetic", gmm_url)
        with self.assertRaisesRegex(EfehrAcquisitionError, "identity drifted"):
            worker.acquire_eshm20_site_model_receipt(
                opener=lambda request, timeout: response,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

    def test_status_and_declared_size_drift_fail_closed(self) -> None:
        url = expected_url(worker._SOURCE_MODEL_LOGIC_TREE.repository_path)
        wrong_status = FakeResponse(b"synthetic", url, status=206)
        with self.assertRaisesRegex(EfehrAcquisitionError, "status is not 200"):
            worker.acquire_eshm20_source_model_logic_tree_receipt(
                opener=lambda request, timeout: wrong_status,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

        oversized = FakeResponse(
            b"x",
            url,
            headers={"Content-Length": str(MAX_FILE_BYTES + 1)},
        )
        with self.assertRaisesRegex(EfehrAcquisitionError, "Content-Length"):
            worker.acquire_eshm20_source_model_logic_tree_receipt(
                opener=lambda request, timeout: oversized,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

    def test_empty_and_nonbyte_payloads_fail_closed(self) -> None:
        url = expected_url(worker._GMPE_LOGIC_TREE.repository_path)
        for response, pattern in (
            (FakeResponse(b"", url), "empty object"),
            (FakeResponse("provider text must stay bytes", url), "non-byte content"),
        ):
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(EfehrAcquisitionError, pattern):
                    worker.acquire_eshm20_gmpe_logic_tree_receipt(
                        opener=lambda request, timeout, response=response: response,
                        now=lambda: RETRIEVED_AT,
                        monotonic=lambda: 0.0,
                    )

    def test_transport_failures_are_sanitized(self) -> None:
        def opener(request, timeout):
            raise OSError("secret local path and provider payload detail")

        with self.assertRaisesRegex(
            EfehrAcquisitionError,
            r"dependency retrieval failed: OSError$",
        ) as caught:
            worker.acquire_eshm20_site_model_receipt(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )
        self.assertNotIn("secret local path", str(caught.exception))

    def test_authority_ceiling_widening_from_receipt_is_rejected(self) -> None:
        spec = worker._SITE_MODEL
        url = expected_url(spec.repository_path)
        response = FakeResponse(b"synthetic", url)
        base = {
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }
        for field in ("external_bytes_persisted", "publication_authorized"):
            widened = dict(base)
            widened[field] = True
            with self.subTest(field=field):
                with patch.object(worker, "receipt_from_stream", return_value=widened):
                    with self.assertRaisesRegex(EfehrAcquisitionError, "widened"):
                        worker.acquire_eshm20_site_model_receipt(
                            opener=lambda request, timeout: response,
                            now=lambda: RETRIEVED_AT,
                            monotonic=lambda: 0.0,
                        )

    def test_specs_match_exact_root_derived_parent_edges(self) -> None:
        self.assertEqual(
            (
                worker._SITE_MODEL.repository_path,
                worker._SITE_MODEL.parent_section,
                worker._SITE_MODEL.parent_option,
            ),
            (
                worker.DEPENDENCY_PREFIX + "eshm20_site_model_v06d.csv",
                "site_params",
                "site_model_file",
            ),
        )
        self.assertEqual(
            (
                worker._GMPE_LOGIC_TREE.repository_path,
                worker._GMPE_LOGIC_TREE.parent_section,
                worker._GMPE_LOGIC_TREE.parent_option,
            ),
            (
                worker.DEPENDENCY_PREFIX + "gmpe_complete_logic_tree_5br.xml",
                "calculation",
                "gsim_logic_tree_file",
            ),
        )
        self.assertEqual(
            (
                worker._SOURCE_MODEL_LOGIC_TREE.repository_path,
                worker._SOURCE_MODEL_LOGIC_TREE.parent_section,
                worker._SOURCE_MODEL_LOGIC_TREE.parent_option,
            ),
            (
                worker.DEPENDENCY_PREFIX + "source_model_logic_tree_eshm20_model_v12e.xml",
                "calculation",
                "source_model_logic_tree_file",
            ),
        )


if __name__ == "__main__":
    unittest.main()
