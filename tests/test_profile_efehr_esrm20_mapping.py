# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import profile_efehr_esrm20_mapping as profile


def identity(raw: bytes) -> tuple[int, str]:
    return len(raw), hashlib.sha256(raw).hexdigest()


class ProfileVerifiedMappingBytesTests(unittest.TestCase):
    def test_profiles_structure_without_returning_cell_values(self) -> None:
        raw = (
            b"taxonomy,model_id,weight\n"
            b"A,M1,1.0\n"
            b"a,M2,2.0\n"
            b" A,M3,\n"
        )
        size, sha256 = identity(raw)

        result = profile.profile_verified_mapping_bytes(
            raw,
            expected_byte_count=size,
            expected_sha256=sha256,
        )

        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["header"], ["taxonomy", "model_id", "weight"])
        self.assertEqual(result["parser"]["delimiter"], ",")
        self.assertEqual(result["parser"]["delimiter_candidates"], [",", ";", "\t"])
        self.assertFalse(result["parser"]["bom_present"])
        self.assertFalse(result["raw_rows_returned"])
        self.assertFalse(result["exact_cell_values_returned"])
        self.assertFalse(result["normalization_applied"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

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
        self.assertEqual(by_name["weight"]["empty_count"], 1)
        self.assertTrue(by_name["weight"]["decimal_summary"]["all_nonempty_decimal"])
        rendered = repr(result)
        for value in ("'A'", "'a'", "' A'", "'M1'", "'M2'", "'M3'"):
            self.assertNotIn(value, rendered)

    def test_semicolon_delimiter_can_be_uniquely_identified(self) -> None:
        raw = b"taxonomy;model\nA;M1\nB;M2\n"
        size, sha256 = identity(raw)
        result = profile.profile_verified_mapping_bytes(
            raw,
            expected_byte_count=size,
            expected_sha256=sha256,
        )
        self.assertEqual(result["parser"]["delimiter"], ";")
        self.assertEqual(result["header"], ["taxonomy", "model"])

    def test_structurally_ambiguous_delimiter_fails_closed(self) -> None:
        raw = b"a,b;c\n1,2;3\n"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.MappingProfileError, "ambiguous"):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_hash_mismatch_fails_before_invalid_utf8_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.MappingProfileError, "SHA-256"):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=1,
                expected_sha256="0" * 64,
            )

    def test_valid_identity_then_invalid_utf8_fails_closed(self) -> None:
        raw = b"\xff"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.MappingProfileError, "UTF-8"):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_byte_count_mismatch_fails_before_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.MappingProfileError, "byte count"):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=2,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_no_supported_delimiter_shape_fails_closed(self) -> None:
        raw = b"a|b\n1|2\n"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.MappingProfileError, "no structurally valid"):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_duplicate_header_fails_closed(self) -> None:
        raw = b"a,a\n1,2\n"
        size, sha256 = identity(raw)
        with self.assertRaises(profile.MappingProfileError):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_empty_header_fails_closed(self) -> None:
        raw = b"a,\n1,2\n"
        size, sha256 = identity(raw)
        with self.assertRaises(profile.MappingProfileError):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_ragged_row_fails_closed(self) -> None:
        raw = b"a,b\n1,2\n3\n"
        size, sha256 = identity(raw)
        with self.assertRaises(profile.MappingProfileError):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_utf8_bom_is_explicit_not_silently_part_of_header(self) -> None:
        raw = b"\xef\xbb\xbfa,b\r\n1,2\r\n"
        size, sha256 = identity(raw)
        result = profile.profile_verified_mapping_bytes(
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
        result = profile.profile_verified_mapping_bytes(
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
                result = profile.profile_verified_mapping_bytes(
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
        with self.assertRaises(profile.MappingProfileError):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_frozen_receipt_constants_match_trusted_mapping_result(self) -> None:
        self.assertEqual(profile.SOURCE_ISSUE, 283)
        self.assertEqual(profile.DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(profile.PROJECT_ID, 269)
        self.assertEqual(profile.PROJECT_PATH, "efehr/esrm20")
        self.assertEqual(
            profile.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(
            profile.REPOSITORY_PATH,
            "Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
        )
        self.assertEqual(profile.RECEIPT_COMMENT_ID, 5303466667)
        self.assertEqual(
            profile.RECEIPT_EXECUTION_SHA,
            "9b1bb7127138247cf613dbf444d139c189c9b13a",
        )
        self.assertEqual(profile.EXPECTED_BYTE_COUNT, 83_585)
        self.assertEqual(
            profile.EXPECTED_SHA256,
            "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c",
        )

    def _assert_alias_drift_fails_before_opener(self, name: str, drifted) -> None:
        original = getattr(profile, name)
        opener_calls = 0

        def opener(request, timeout):
            nonlocal opener_calls
            opener_calls += 1
            raise AssertionError("opener must not run after authority drift")

        setattr(profile, name, drifted)
        try:
            with self.assertRaisesRegex(profile.MappingProfileError, "authority drifted"):
                profile.acquire_and_profile_esrm20_mapping(opener=opener)
        finally:
            setattr(profile, name, original)
        self.assertEqual(opener_calls, 0)

    def test_public_authority_alias_drift_fails_before_network(self) -> None:
        drifts = (
            ("SCHEMA_VERSION", "oc-esrm20-mapping-content-profile-v999"),
            ("SOURCE_ISSUE", True),
            ("DATASET_ID", "efehr.esrm20.risk-inputs.v999"),
            ("PROJECT_ID", True),
            ("PROJECT_PATH", "efehr/drifted"),
            ("COMMIT_SHA", "0" * 40),
            ("REPOSITORY_PATH", "Vulnerability/drifted.csv"),
            ("RECEIPT_COMMENT_ID", True),
            ("RECEIPT_EXECUTION_SHA", "0" * 40),
            ("EXPECTED_BYTE_COUNT", True),
            ("EXPECTED_SHA256", "0" * 64),
            ("DELIMITER_CANDIDATES", (",",)),
            ("MIN_COLUMNS", True),
            ("MAX_COLUMNS", 127),
            ("MAX_HEADER_UTF8_BYTES", 255),
        )
        for name, drifted in drifts:
            with self.subTest(name=name):
                self._assert_alias_drift_fails_before_opener(name, drifted)

    def test_acquisition_constructs_only_the_frozen_mapping_target(self) -> None:
        captured: list[str] = []

        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            captured.append(request.full_url)
            raise OSError("synthetic stop before provider bytes")

        with self.assertRaisesRegex(profile.MappingProfileError, "OSError"):
            profile.acquire_and_profile_esrm20_mapping(opener=opener)

        self.assertEqual(len(captured), 1)
        self.assertIn("/api/v4/projects/269/", captured[0])
        self.assertIn(
            "Vulnerability%2Fesrm20_exposure_vulnerability_mapping.csv",
            captured[0],
        )
        self.assertIn(
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
            captured[0],
        )


if __name__ == "__main__":
    unittest.main()
