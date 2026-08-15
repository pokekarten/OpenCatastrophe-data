# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import inspect
import json
import unittest
import urllib.error
from decimal import Context, Decimal, localcontext
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
    def patched_identity(self, raw: bytes):
        return (
            mock.patch.object(worker, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(worker, "EXPECTED_SHA256", hashlib.sha256(raw).hexdigest()),
        )

    def opener_for(self, raw: bytes, captured: list[str]):
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            return FakeResponse(raw, request.full_url)

        return opener

    def test_frozen_receipt_identity_is_exact(self) -> None:
        self.assertEqual(worker.SOURCE_ISSUE, 281)
        self.assertEqual(worker.CONTROL_ISSUE, 372)
        self.assertEqual(worker.PROJECT_ID, 197)
        self.assertEqual(
            worker.COMMIT_SHA,
            "fbd334de68f85d72669f73fc5a314a113db67317",
        )
        self.assertTrue(worker.REPOSITORY_PATH.endswith("eshm20_site_model_v06d.csv"))
        self.assertEqual(worker.EXPECTED_BYTE_COUNT, 3_873_324)
        self.assertEqual(
            worker.EXPECTED_SHA256,
            "d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529",
        )
        self.assertEqual(worker.FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID, 5301858821)
        self.assertEqual(worker.FIRST_ORDER_RECEIPT_RUN_ID, 31880089623)

    def test_public_worker_exposes_no_target_schema_crs_or_column_selector(self) -> None:
        signature = inspect.signature(worker.acquire_eshm20_site_model_profile)
        self.assertEqual(set(signature.parameters), {"opener", "monotonic"})
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

    def test_verified_profile_is_descriptive_and_deterministic(self) -> None:
        count_patch, hash_patch = self.patched_identity(RAW)
        with count_patch, hash_patch:
            result = worker.extract_verified_site_model_profile(RAW)

        profile = result["profile"]
        self.assertEqual(profile["header"], ["alpha", "beta", "label"])
        self.assertEqual(profile["column_count"], 3)
        self.assertEqual(profile["data_row_count"], 3)
        self.assertEqual(
            profile["columns"],
            [
                {
                    "name": "alpha",
                    "nonempty_count": 2,
                    "numeric_count": 2,
                    "numeric_min": "1",
                    "numeric_max": "2.5",
                },
                {
                    "name": "beta",
                    "nonempty_count": 3,
                    "numeric_count": 3,
                    "numeric_min": "-3",
                    "numeric_max": "2E+1",
                },
                {
                    "name": "label",
                    "nonempty_count": 3,
                    "numeric_count": 0,
                    "numeric_min": None,
                    "numeric_max": None,
                },
            ],
        )
        for field in (
            "schema_interpretation_authorized",
            "crs_authorized",
            "coordinate_semantics_authorized",
            "site_response_authorized",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)
        self.assertNotIn("PROVIDER_PRIVATE_BODY", json.dumps(result, sort_keys=True))

    def test_numeric_extrema_are_exact_and_context_independent(self) -> None:
        raw = b"value\n123456789012345678901234567890.123000\n"
        expected = "123456789012345678901234567890.123"

        count_patch, hash_patch = self.patched_identity(raw)
        with count_patch, hash_patch:
            default_result = worker.extract_verified_site_model_profile(raw)

        count_patch, hash_patch = self.patched_identity(raw)
        with localcontext(Context(prec=5, Emax=9, Emin=-9)), count_patch, hash_patch:
            constrained_result = worker.extract_verified_site_model_profile(raw)

        default_column = default_result["profile"]["columns"][0]
        constrained_column = constrained_result["profile"]["columns"][0]
        self.assertEqual(default_column["numeric_min"], expected)
        self.assertEqual(default_column["numeric_max"], expected)
        self.assertEqual(constrained_column, default_column)

    def test_numeric_extrema_large_exponent_is_compact_and_bounded(self) -> None:
        raw = b"value\n1e999999999\n"
        count_patch, hash_patch = self.patched_identity(raw)
        with count_patch, hash_patch:
            result = worker.extract_verified_site_model_profile(raw)

        rendered = result["profile"]["columns"][0]["numeric_max"]
        self.assertEqual(rendered, "1E+999999999")
        self.assertLessEqual(len(rendered), worker.MAX_NUMERIC_EXTREMA_CHARS)

        oversized = Decimal("1" * (worker.MAX_NUMERIC_EXTREMA_CHARS + 1))
        with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "bounded"):
            worker._canonical_decimal(oversized)

    def test_identity_fails_before_decode_or_csv_profile(self) -> None:
        count_patch, hash_patch = self.patched_identity(RAW)
        tampered = RAW[:-1] + bytes([RAW[-1] ^ 1])
        with count_patch, hash_patch, mock.patch.object(worker, "_profile_csv_text") as profiler:
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "SHA-256"):
                worker.extract_verified_site_model_profile(tampered)
            profiler.assert_not_called()

        with mock.patch.object(worker, "EXPECTED_BYTE_COUNT", len(RAW)):
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "byte count"):
                worker.extract_verified_site_model_profile(RAW + b"x")

    def test_strict_utf8_nul_and_bom_handling(self) -> None:
        invalid = b"alpha\n\xff\n"
        count_patch, hash_patch = self.patched_identity(invalid)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "strict UTF-8"):
                worker.extract_verified_site_model_profile(invalid)

        nul = b"alpha\n1\x00\n"
        count_patch, hash_patch = self.patched_identity(nul)
        with count_patch, hash_patch:
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "NUL"):
                worker.extract_verified_site_model_profile(nul)

        bom = b"\xef\xbb\xbfalpha\n1\n"
        count_patch, hash_patch = self.patched_identity(bom)
        with count_patch, hash_patch:
            result = worker.extract_verified_site_model_profile(bom)
        self.assertTrue(result["utf8_bom_present"])
        self.assertEqual(result["profile"]["header"], ["alpha"])

    def test_duplicate_empty_header_and_row_width_drift_fail_closed(self) -> None:
        cases = (
            (b"a,a\n1,2\n", "duplicate headers"),
            (b"a,\n1,2\n", "empty or oversized header"),
            (b"a,b\n1\n", "row width"),
        )
        for raw, message in cases:
            with self.subTest(message=message):
                count_patch, hash_patch = self.patched_identity(raw)
                with count_patch, hash_patch:
                    with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, message):
                        worker.extract_verified_site_model_profile(raw)

    def test_nonfinite_numeric_token_fails_closed(self) -> None:
        for token in (b"NaN", b"Infinity", b"-Inf"):
            raw = b"value\n" + token + b"\n"
            count_patch, hash_patch = self.patched_identity(raw)
            with count_patch, hash_patch:
                with self.assertRaisesRegex(
                    worker.Eshm20SiteModelProfileError, "non-finite numeric token"
                ):
                    worker.extract_verified_site_model_profile(raw)

    def test_worker_uses_only_fixed_provider_target_and_returns_no_rows(self) -> None:
        captured: list[str] = []
        count_patch, hash_patch = self.patched_identity(RAW)
        with count_patch, hash_patch:
            result = worker.acquire_eshm20_site_model_profile(
                opener=self.opener_for(RAW, captured)
            )

        self.assertEqual(len(captured), 1)
        self.assertIn(f"/api/v4/projects/{worker.PROJECT_ID}/", captured[0])
        self.assertIn(worker.COMMIT_SHA, captured[0])
        self.assertIn("eshm20_site_model_v06d.csv", result["repository_path"])
        self.assertNotIn("PROVIDER_PRIVATE_BODY", json.dumps(result, sort_keys=True))

    def test_response_identity_drift_and_transport_errors_do_not_leak(self) -> None:
        count_patch, hash_patch = self.patched_identity(RAW)

        def drifted(request, timeout):
            self.assertGreater(timeout, 0)
            return FakeResponse(RAW, request.full_url, final_url="https://example.com/redirect")

        with count_patch, hash_patch:
            with self.assertRaisesRegex(worker.Eshm20SiteModelProfileError, "failed closed"):
                worker.acquire_eshm20_site_model_profile(opener=drifted)

        def broken(request, timeout):
            raise urllib.error.URLError("PROVIDER_PRIVATE_BODY")

        with self.assertRaises(worker.Eshm20SiteModelProfileError) as caught:
            worker.acquire_eshm20_site_model_profile(opener=broken)
        self.assertNotIn("PROVIDER_PRIVATE_BODY", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
