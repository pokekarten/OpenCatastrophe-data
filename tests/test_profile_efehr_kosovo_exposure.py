# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import http.client
import unittest

from scripts import profile_efehr_kosovo_exposure as profile


def identity(raw: bytes) -> tuple[int, str]:
    return len(raw), hashlib.sha256(raw).hexdigest()


class ProfileVerifiedCsvBytesTests(unittest.TestCase):
    def test_profiles_structure_without_returning_row_values(self) -> None:
        raw = (
            b"taxonomy,longitude,value\n"
            b"A,20.0,100\n"
            b"a,21.5,200\n"
            b" A,22.0,\n"
        )
        size, sha256 = identity(raw)

        result = profile.profile_verified_csv_bytes(
            raw,
            expected_byte_count=size,
            expected_sha256=sha256,
        )

        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["header"], ["taxonomy", "longitude", "value"])
        self.assertEqual(result["parser"]["delimiter"], ",")
        self.assertFalse(result["parser"]["bom_present"])
        self.assertFalse(result["raw_rows_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])

        by_name = {column["name"]: column for column in result["columns"]}
        self.assertEqual(by_name["taxonomy"]["distinct_count"], 3)
        self.assertEqual(
            by_name["taxonomy"]["decimal_summary"],
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
        self.assertNotIn("'A'", rendered)
        self.assertNotIn("'a'", rendered)
        self.assertNotIn("' A'", rendered)

    def test_hash_mismatch_fails_before_invalid_utf8_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.ExposureProfileError, "SHA-256"):
            profile.profile_verified_csv_bytes(
                raw,
                expected_byte_count=1,
                expected_sha256="0" * 64,
            )

    def test_valid_identity_then_invalid_utf8_fails_closed(self) -> None:
        raw = b"\xff"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.ExposureProfileError, "UTF-8"):
            profile.profile_verified_csv_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_byte_count_mismatch_fails_before_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.ExposureProfileError, "byte count"):
            profile.profile_verified_csv_bytes(
                raw,
                expected_byte_count=2,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_wrong_delimiter_shape_fails_closed_as_one_column(self) -> None:
        raw = b"a;b\n1;2\n"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.ExposureProfileError, "column count"):
            profile.profile_verified_csv_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_duplicate_header_fails_closed(self) -> None:
        raw = b"a,a\n1,2\n"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.ExposureProfileError, "duplicate"):
            profile.profile_verified_csv_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_empty_header_fails_closed(self) -> None:
        raw = b"a,\n1,2\n"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.ExposureProfileError, "empty header"):
            profile.profile_verified_csv_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_ragged_row_fails_closed(self) -> None:
        raw = b"a,b\n1,2\n3\n"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.ExposureProfileError, "ragged"):
            profile.profile_verified_csv_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_utf8_bom_is_explicit_not_silently_part_of_header(self) -> None:
        raw = b"\xef\xbb\xbfa,b\r\n1,2\r\n"
        size, sha256 = identity(raw)
        result = profile.profile_verified_csv_bytes(
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
        result = profile.profile_verified_csv_bytes(
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
                result = profile.profile_verified_csv_bytes(
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
        with self.assertRaisesRegex(profile.ExposureProfileError, "no data records"):
            profile.profile_verified_csv_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_acquisition_incomplete_read_fails_closed(self) -> None:
        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            self.assertIn(profile.COMMIT_SHA, request.full_url)
            raise http.client.IncompleteRead(b"partial", 10)

        with self.assertRaisesRegex(profile.ExposureProfileError, "IncompleteRead"):
            profile.acquire_and_profile_kosovo_exposure(opener=opener)

    def test_acquisition_uses_only_fixed_target_and_profiles_after_identity_match(self) -> None:
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
            self.assertIn("/api/v4/projects/186/", request.full_url)
            self.assertIn(
                "_exposure_models%2FExposure_Model_Kosovo_Res.csv",
                request.full_url,
            )
            self.assertIn(profile.COMMIT_SHA, request.full_url)
            return FakeResponse()

        original_count = profile.EXPECTED_BYTE_COUNT
        original_sha = profile.EXPECTED_SHA256
        try:
            profile.EXPECTED_BYTE_COUNT = size
            profile.EXPECTED_SHA256 = sha256
            result = profile.acquire_and_profile_kosovo_exposure(opener=opener)
        finally:
            profile.EXPECTED_BYTE_COUNT = original_count
            profile.EXPECTED_SHA256 = original_sha

        self.assertEqual(len(captured), 1)
        self.assertEqual(result["profile"]["record_count"], 1)
        self.assertEqual(result["repository_path"], profile.REPOSITORY_PATH)
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertNotIn("1", result["profile"]["header"])
        self.assertNotIn("2", result["profile"]["header"])


if __name__ == "__main__":
    unittest.main()
