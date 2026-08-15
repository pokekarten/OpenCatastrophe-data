# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import json
import unittest
import urllib.error
from unittest import mock

from scripts import acquire_eshm20_site_model_profile as worker


RAW = (
    b"alpha,beta,label\n"
    b"1,10,x\n"
    b"2.50,20,y\n"
    b",-3,PROVIDER_PRIVATE_BODY\n"
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


class FixedEshm20SiteModelProfileTests(unittest.TestCase):
    def patched_payload_identity(self, raw: bytes):
        digest = hashlib.sha256(raw).hexdigest()
        return (
            mock.patch.object(worker, "_CANONICAL_EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "_CANONICAL_EXPECTED_SHA256", digest),
        )

    def patched_network_identity(self, raw: bytes):
        digest = hashlib.sha256(raw).hexdigest()
        return (
            mock.patch.object(worker, "_CANONICAL_EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "_CANONICAL_EXPECTED_SHA256", digest),
            mock.patch.object(worker, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "EXPECTED_SHA256", digest),
        )

    def opener_for(self, raw: bytes, captured: list[str]):
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            return FakeResponse(raw, request.full_url)

        return opener

    def test_frozen_receipt_identity_is_exact_without_unproven_result_comment(self) -> None:
        self.assertEqual(worker.SOURCE_ISSUE, 281)
        self.assertEqual(worker.CONTROL_ISSUE, 372)
        self.assertEqual(worker.RECEIPT_SOURCE_ISSUE, 361)
        self.assertEqual(worker.PROJECT_ID, 197)
        self.assertEqual(
            worker.COMMIT_SHA,
            "fbd334de68f85d72669f73fc5a314a113db67317",
        )
        self.assertEqual(
            worker.REPOSITORY_PATH,
            worker.first_order_authority._SITE_MODEL.repository_path,
        )
        self.assertEqual(worker.EXPECTED_BYTE_COUNT, 3_873_324)
        self.assertEqual(
            worker.EXPECTED_SHA256,
            "d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529",
        )
        self.assertEqual(
            worker.INVENTORY_RECEIPT_COMMENT_ID,
            worker.inventory_authority.INVENTORY_RECEIPT_COMMENT_ID,
        )
        self.assertEqual(worker.INVENTORY_RECEIPT_COMMENT_ID, 5290449064)
        self.assertEqual(
            worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
            worker.first_order_authority.SELECTION_RESULT_COMMENT_ID,
        )
        self.assertNotEqual(
            worker.INVENTORY_RECEIPT_COMMENT_ID,
            worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        )
        self.assertEqual(worker.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID, 5301857400)
        self.assertEqual(worker.FIRST_ORDER_RECEIPT_RUN_ID, 31880089623)
        self.assertFalse(
            hasattr(worker, "FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID"),
            "the #361 GitHub result-comment id is not byte-bound by the canonical bridge",
        )

    def test_public_worker_exposes_no_target_schema_crs_or_column_selector(self) -> None:
        signature = inspect.signature(worker.acquire_eshm20_site_model_profile)
        self.assertEqual(set(signature.parameters), {"opener", "monotonic"})
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

    def test_verified_profile_is_interpretation_light_and_deterministic(self) -> None:
        count_patch, hash_patch = self.patched_payload_identity(RAW)
        with count_patch, hash_patch:
            result = worker.extract_verified_site_model_profile(RAW)

        profile = result["profile"]
        self.assertEqual(profile["header"], ["alpha", "beta", "label"])
        self.assertEqual(profile["record_count"], 3)
        self.assertEqual(profile["delimiter"], ",")
        self.assertEqual(
            profile["columns"][0],
            {
                "name": "alpha",
                "record_count": 3,
                "empty_count": 1,
                "nonempty_count": 2,
                "distinct_count": 3,
                "exact_value_set_sha256": worker._value_set_sha256({"", "1", "2.50"}),
                "decimal_summary": {
                    "all_nonempty_decimal": True,
                    "finite_decimal_count": 2,
                    "leading_or_trailing_whitespace_count": 0,
                },
            },
        )
        self.assertEqual(profile["columns"][2]["distinct_count"], 3)
        self.assertEqual(
            result["inventory_receipt_comment_id"],
            worker.inventory_authority.INVENTORY_RECEIPT_COMMENT_ID,
        )
        self.assertEqual(
            result["root_dependency_result_comment_id"],
            worker.first_order_authority.SELECTION_RESULT_COMMENT_ID,
        )
        self.assertNotEqual(
            result["inventory_receipt_comment_id"],
            result["root_dependency_result_comment_id"],
        )
        self.assertNotIn("numeric_min", json.dumps(result, sort_keys=True))
        self.assertNotIn("numeric_max", json.dumps(result, sort_keys=True))
        for field in (
            "raw_rows_returned",
            "schema_interpretation_authorized",
            "crs_authorized",
            "coordinate_semantics_authorized",
            "site_response_authorized",
            "site_semantics_authorized",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)
        self.assertNotIn("PROVIDER_PRIVATE_BODY", json.dumps(result, sort_keys=True))
        self.assertNotIn("first_order_receipt_result_comment_id", result)

    def test_exact_value_set_hash_preserves_case_and_whitespace(self) -> None:
        raw_a = b"a,b\nX,1\nx,2\n x ,3\n"
        raw_b = b"a,b\nX,1\nx,2\nx,3\n"

        a_count, a_hash = self.patched_payload_identity(raw_a)
        with a_count, a_hash:
            a = worker.extract_verified_site_model_profile(raw_a)

        b_count, b_hash = self.patched_payload_identity(raw_b)
        with b_count, b_hash:
            b = worker.extract_verified_site_model_profile(raw_b)

        col_a = a["profile"]["columns"][0]
        col_b = b["profile"]["columns"][0]
        self.assertNotEqual(
            col_a["exact_value_set_sha256"],
            col_b["exact_value_set_sha256"],
        )
        self.assertEqual(
            col_a["decimal_summary"]["leading_or_trailing_whitespace_count"],
            1,
        )

    def test_nonfinite_decimal_tokens_are_not_promoted_to_numeric_evidence(self) -> None:
        raw = b"name,value\nA,NaN\nB,Infinity\nC,-Inf\nD,1.5\n"
        count_patch, hash_patch = self.patched_payload_identity(raw)
        with count_patch, hash_patch:
            result = worker.extract_verified_site_model_profile(raw)

        summary = result["profile"]["columns"][1]["decimal_summary"]
        self.assertFalse(summary["all_nonempty_decimal"])
        self.assertEqual(summary["finite_decimal_count"], 1)

    def test_identity_fails_before_decode_or_csv_profile(self) -> None:
        count_patch, hash_patch = self.patched_payload_identity(RAW)
        tampered = RAW[:-1] + bytes([RAW[-1] ^ 1])
        with count_patch, hash_patch, mock.patch.object(
            worker, "_profile_csv_text"
        ) as profiler:
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "SHA-256"):
                worker.extract_verified_site_model_profile(tampered)
            profiler.assert_not_called()

        with mock.patch.object(
            worker, "_CANONICAL_EXPECTED_BYTE_COUNT", len(RAW)
        ), mock.patch.object(
            worker,
            "_CANONICAL_EXPECTED_SHA256",
            hashlib.sha256(RAW).hexdigest(),
        ):
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "byte count"):
                worker.extract_verified_site_model_profile(RAW + b"x")

    def test_strict_utf8_nul_bom_and_line_endings(self) -> None:
        invalid = b"alpha,beta\n\xff,1\n"
        count_patch, hash_patch = self.patched_payload_identity(invalid)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "strict UTF-8"):
                worker.extract_verified_site_model_profile(invalid)

        nul = b"alpha,beta\n1,2\x00\n"
        count_patch, hash_patch = self.patched_payload_identity(nul)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "NUL"):
                worker.extract_verified_site_model_profile(nul)

        bom_crlf = b"\xef\xbb\xbfalpha,beta\r\n1,2\r\n"
        count_patch, hash_patch = self.patched_payload_identity(bom_crlf)
        with count_patch, hash_patch:
            result = worker.extract_verified_site_model_profile(bom_crlf)
        self.assertTrue(result["parser"]["bom_present"])
        self.assertEqual(result["parser"]["encoding"], "utf-8-sig")
        self.assertEqual(
            result["parser"]["line_endings"],
            {"crlf_count": 2, "lf_count": 0, "cr_count": 0},
        )

    def test_header_and_row_shape_fail_closed(self) -> None:
        cases = (
            (b"a,a\n1,2\n", "duplicate headers"),
            (b"a,\n1,2\n", "empty or oversized header"),
            (b"a,\x01b\n1,2\n", "control characters"),
            (b"a,b\n1\n", "row width"),
            (b"a,b\n", "no data records"),
        )
        for raw, message in cases:
            with self.subTest(message=message):
                count_patch, hash_patch = self.patched_payload_identity(raw)
                with count_patch, hash_patch:
                    with self.assertRaisesRegex(
                        worker.Eshm20SiteModelProfileError, message
                    ):
                        worker.extract_verified_site_model_profile(raw)

    def test_fixed_target_alias_drift_fails_before_network(self) -> None:
        cases = (
            ("PROJECT_ID", 198),
            ("COMMIT_SHA", "0" * 40),
            (
                "REPOSITORY_PATH",
                "oq_computational/oq_configuration_eshm20_v12e_region_main/"
                "gmpe_complete_logic_tree_5br.xml",
            ),
            ("EXPECTED_BYTE_COUNT", worker.EXPECTED_BYTE_COUNT + 1),
            ("EXPECTED_SHA256", "0" * 64),
        )
        for name, replacement in cases:
            with self.subTest(name=name), mock.patch.object(
                worker, name, replacement
            ), mock.patch.object(worker, "_open_fixed") as opener:
                with self.assertRaisesRegex(
                    worker.Eshm20SiteModelProfileError, "drifted"
                ):
                    worker.acquire_eshm20_site_model_profile()
                opener.assert_not_called()

    def test_equal_but_distinct_site_spec_fails_before_network(self) -> None:
        clone = worker.first_order_authority.DependencySpec(
            repository_path=worker._CANONICAL_SITE_SPEC.repository_path,
            parent_section=worker._CANONICAL_SITE_SPEC.parent_section,
            parent_option=worker._CANONICAL_SITE_SPEC.parent_option,
        )
        self.assertEqual(clone, worker._CANONICAL_SITE_SPEC)
        self.assertIsNot(clone, worker._CANONICAL_SITE_SPEC)
        with mock.patch.object(
            worker.first_order_authority, "_SITE_MODEL", clone
        ), mock.patch.object(worker, "_open_fixed") as opener:
            with self.assertRaisesRegex(
                worker.Eshm20SiteModelProfileError, "capability identity"
            ):
                worker.acquire_eshm20_site_model_profile()
            opener.assert_not_called()

    def test_worker_uses_canonical_provider_target_and_returns_no_rows(self) -> None:
        captured: list[str] = []
        patches = self.patched_network_identity(RAW)
        with patches[0], patches[1], patches[2], patches[3]:
            result = worker.acquire_eshm20_site_model_profile(
                opener=self.opener_for(RAW, captured)
            )

        self.assertEqual(len(captured), 1)
        self.assertIn(
            f"/api/v4/projects/{worker._CANONICAL_PROJECT_ID}/",
            captured[0],
        )
        self.assertIn(worker._CANONICAL_COMMIT_SHA, captured[0])
        self.assertEqual(
            result["repository_path"],
            worker.first_order_authority._SITE_MODEL.repository_path,
        )
        self.assertNotIn("PROVIDER_PRIVATE_BODY", json.dumps(result, sort_keys=True))
        self.assertNotIn("first_order_receipt_result_comment_id", result)

    def test_response_identity_drift_and_transport_errors_do_not_leak(self) -> None:
        patches = self.patched_network_identity(RAW)

        def drifted(request, timeout):
            self.assertGreater(timeout, 0)
            return FakeResponse(
                RAW,
                request.full_url,
                final_url="https://example.com/redirect",
            )

        with patches[0], patches[1], patches[2], patches[3]:
            with self.assertRaisesRegex(
                worker.Eshm20SiteModelProfileError, "failed closed"
            ):
                worker.acquire_eshm20_site_model_profile(opener=drifted)

        def broken(request, timeout):
            raise urllib.error.URLError("PROVIDER_PRIVATE_BODY")

        with self.assertRaises(worker.Eshm20SiteModelProfileError) as caught:
            worker.acquire_eshm20_site_model_profile(opener=broken)
        self.assertNotIn("PROVIDER_PRIVATE_BODY", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
