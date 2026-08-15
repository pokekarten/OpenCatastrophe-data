# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import profile_eshm20_site_model as profile


def identity(raw: bytes) -> tuple[int, str]:
    return len(raw), hashlib.sha256(raw).hexdigest()


class ProfileVerifiedSiteModelBytesTests(unittest.TestCase):
    def test_frozen_receipt_and_parent_authority_is_exact(self) -> None:
        self.assertEqual(profile.CONTROL_ISSUE, 361)
        self.assertEqual(profile.SOURCE_ISSUE, 281)
        self.assertEqual(profile.DATASET_ID, "efehr.eshm20")
        self.assertEqual(profile.PROJECT_ID, 197)
        self.assertEqual(profile.PROJECT_PATH, "efehr/eshm20")
        self.assertEqual(
            profile.COMMIT_SHA,
            "fbd334de68f85d72669f73fc5a314a113db67317",
        )
        self.assertEqual(
            profile.REPOSITORY_PATH,
            "oq_computational/oq_configuration_eshm20_v12e_region_main/"
            "eshm20_site_model_v06d.csv",
        )
        self.assertEqual(profile.PARENT_RESULT_COMMENT_ID, 5301726249)
        self.assertEqual(profile.PARENT_SECTION, "site_params")
        self.assertEqual(profile.PARENT_OPTION, "site_model_file")
        self.assertEqual(profile.RECEIPT_REQUEST_COMMENT_ID, 5301857400)
        self.assertEqual(profile.RECEIPT_RESULT_COMMENT_ID, 5301858821)
        self.assertEqual(profile.RECEIPT_RUN_ID, 31880089623)
        self.assertEqual(
            profile.RECEIPT_EXECUTION_SHA,
            "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1",
        )
        self.assertEqual(profile.EXPECTED_BYTE_COUNT, 3_873_324)
        self.assertEqual(
            profile.EXPECTED_SHA256,
            "d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529",
        )

    def test_profiles_structure_without_returning_row_values(self) -> None:
        raw = (
            b"column_a,column_b,value\n"
            b"SECRET_A,20.0,100\n"
            b"secret_a,21.5,200\n"
            b" SECRET_A,22.0,\n"
        )
        size, sha256 = identity(raw)

        result = profile.profile_verified_site_model_bytes(
            raw,
            expected_byte_count=size,
            expected_sha256=sha256,
        )

        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["header"], ["column_a", "column_b", "value"])
        self.assertEqual(result["parser"]["delimiter"], ",")
        self.assertFalse(result["parser"]["bom_present"])
        self.assertFalse(result["raw_rows_returned"])
        self.assertFalse(result["site_semantics_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])

        by_name = {column["name"]: column for column in result["columns"]}
        self.assertEqual(by_name["column_a"]["distinct_count"], 3)
        self.assertEqual(
            by_name["column_a"]["decimal_summary"],
            {
                "all_nonempty_decimal": False,
                "finite_decimal_count": 0,
                "leading_or_trailing_whitespace_count": 1,
            },
        )
        self.assertEqual(by_name["value"]["empty_count"], 1)
        self.assertTrue(by_name["value"]["decimal_summary"]["all_nonempty_decimal"])
        self.assertEqual(by_name["value"]["decimal_summary"]["finite_decimal_count"], 2)
        rendered = repr(result)
        self.assertNotIn("SECRET_A", rendered)
        self.assertNotIn("secret_a", rendered)
        self.assertNotIn(" SECRET_A", rendered)
        self.assertNotIn("20.0", rendered)
        self.assertNotIn("21.5", rendered)
        self.assertNotIn("22.0", rendered)

    def test_hash_mismatch_fails_before_invalid_utf8_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, "SHA-256"):
            profile.profile_verified_site_model_bytes(
                raw,
                expected_byte_count=1,
                expected_sha256="0" * 64,
            )

    def test_valid_identity_then_invalid_utf8_fails_closed(self) -> None:
        raw = b"\xff"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, "UTF-8"):
            profile.profile_verified_site_model_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_byte_count_mismatch_fails_before_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, "byte count"):
            profile.profile_verified_site_model_bytes(
                raw,
                expected_byte_count=2,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_bool_byte_count_and_malformed_sha_fail_closed(self) -> None:
        raw = b"a,b\n1,2\n"
        with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, "integer"):
            profile.profile_verified_site_model_bytes(
                raw,
                expected_byte_count=True,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )
        with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, "lowercase hex"):
            profile.profile_verified_site_model_bytes(
                raw,
                expected_byte_count=len(raw),
                expected_sha256="A" * 64,
            )

    def test_wrong_delimiter_shape_fails_closed_as_one_column(self) -> None:
        raw = b"a;b\n1;2\n"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, "column count"):
            profile.profile_verified_site_model_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_duplicate_empty_control_and_oversized_headers_fail_closed(self) -> None:
        cases = (
            (b"a,a\n1,2\n", "duplicate"),
            (b"a,\n1,2\n", "empty header"),
            (b'a,"b\tc"\n1,2\n', "control characters"),
            (("a," + "b" * 257 + "\n1,2\n").encode(), "exceeds bounded policy"),
        )
        for raw, message in cases:
            with self.subTest(message=message):
                size, sha256 = identity(raw)
                with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, message):
                    profile.profile_verified_site_model_bytes(
                        raw,
                        expected_byte_count=size,
                        expected_sha256=sha256,
                    )

    def test_nul_and_ragged_rows_fail_closed(self) -> None:
        for raw, message in (
            (b"a,b\n1,\x002\n", "NUL"),
            (b"a,b\n1,2\n3\n", "ragged"),
        ):
            with self.subTest(message=message):
                size, sha256 = identity(raw)
                with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, message):
                    profile.profile_verified_site_model_bytes(
                        raw,
                        expected_byte_count=size,
                        expected_sha256=sha256,
                    )

    def test_utf8_bom_and_crlf_are_explicit(self) -> None:
        raw = b"\xef\xbb\xbfa,b\r\n1,2\r\n"
        size, sha256 = identity(raw)
        result = profile.profile_verified_site_model_bytes(
            raw,
            expected_byte_count=size,
            expected_sha256=sha256,
        )
        self.assertTrue(result["parser"]["bom_present"])
        self.assertEqual(result["parser"]["encoding"], "utf-8-sig")
        self.assertEqual(result["parser"]["line_endings"]["crlf_count"], 2)
        self.assertEqual(result["header"], ["a", "b"])

    def test_exact_value_set_hash_preserves_case_and_whitespace(self) -> None:
        raw = b"x,y\nA,1\na,2\n A,3\n"
        size, sha256 = identity(raw)
        result = profile.profile_verified_site_model_bytes(
            raw,
            expected_byte_count=size,
            expected_sha256=sha256,
        )
        column = result["columns"][0]
        self.assertEqual(column["distinct_count"], 3)

        expected = hashlib.sha256()
        for value in sorted({"A", "a", " A"}):
            encoded = value.encode("utf-8")
            expected.update(len(encoded).to_bytes(8, "big"))
            expected.update(encoded)
        self.assertEqual(column["exact_value_set_sha256"], expected.hexdigest())

    def test_nonfinite_decimal_tokens_are_not_numeric_summary(self) -> None:
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                raw = f"x,y\n{token},1\n".encode()
                size, sha256 = identity(raw)
                result = profile.profile_verified_site_model_bytes(
                    raw,
                    expected_byte_count=size,
                    expected_sha256=sha256,
                )
                summary = result["columns"][0]["decimal_summary"]
                self.assertFalse(summary["all_nonempty_decimal"])
                self.assertEqual(summary["finite_decimal_count"], 0)

    def test_no_data_records_fails_closed(self) -> None:
        raw = b"a,b\n"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.Eshm20SiteModelProfileError, "no data records"):
            profile.profile_verified_site_model_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_acquisition_uses_only_fixed_target_and_returns_bounded_authority(self) -> None:
        raw = b"a,b\n1,2\n"
        size, sha256 = identity(raw)
        captured: list[str] = []

        class FakeResponse:
            status = 200

            def __init__(self) -> None:
                self.headers = {"Content-Length": str(size)}
                self._offset = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self) -> str:
                return captured[0]

            def read(self, amount: int = -1) -> bytes:
                if self._offset >= len(raw):
                    return b""
                if amount < 0:
                    amount = len(raw) - self._offset
                chunk = raw[self._offset : self._offset + amount]
                self._offset += len(chunk)
                return chunk

        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            self.assertIn("/api/v4/projects/197/", request.full_url)
            self.assertIn(
                "oq_computational%2Foq_configuration_eshm20_v12e_region_main%2F"
                "eshm20_site_model_v06d.csv",
                request.full_url,
            )
            self.assertIn(profile.COMMIT_SHA, request.full_url)
            return FakeResponse()

        original_count = profile.EXPECTED_BYTE_COUNT
        original_sha = profile.EXPECTED_SHA256
        try:
            profile.EXPECTED_BYTE_COUNT = size
            profile.EXPECTED_SHA256 = sha256
            result = profile.acquire_and_profile_eshm20_site_model(opener=opener)
        finally:
            profile.EXPECTED_BYTE_COUNT = original_count
            profile.EXPECTED_SHA256 = original_sha

        self.assertEqual(len(captured), 1)
        self.assertEqual(result["profile"]["record_count"], 1)
        self.assertEqual(result["repository_path"], profile.REPOSITORY_PATH)
        self.assertEqual(result["parent_result_comment_id"], profile.PARENT_RESULT_COMMENT_ID)
        self.assertEqual(result["receipt_result_comment_id"], profile.RECEIPT_RESULT_COMMENT_ID)
        self.assertFalse(result["site_semantics_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        rendered = repr(result)
        self.assertNotIn("requested_url", rendered)
        self.assertNotIn("final_url", rendered)
        self.assertNotIn("https://", rendered)

    def test_transport_failure_is_sanitized(self) -> None:
        def opener(request, timeout):
            raise OSError("PROVIDER-PAYLOAD-SENTINEL")

        with self.assertRaises(profile.Eshm20SiteModelProfileError) as captured:
            profile.acquire_and_profile_eshm20_site_model(opener=opener)
        self.assertIn("OSError", str(captured.exception))
        self.assertNotIn("PROVIDER-PAYLOAD-SENTINEL", str(captured.exception))


if __name__ == "__main__":
    unittest.main()
