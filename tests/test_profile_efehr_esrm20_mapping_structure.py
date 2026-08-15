# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from scripts import profile_efehr_esrm20_mapping_structure as profile


def identity(raw: bytes) -> tuple[int, str]:
    return len(raw), hashlib.sha256(raw).hexdigest()


def run_profile(raw: bytes):
    size, sha256 = identity(raw)
    return profile._profile_verified_csv_bytes(
        raw,
        expected_byte_count=size,
        expected_sha256=sha256,
    )


class MappingStructureProfileTests(unittest.TestCase):
    def test_profiles_only_value_free_structure(self) -> None:
        raw = (
            b"source,target,condition\n"
            b"A,V1,x\n"
            b"a,V2, x\n"
            b" A,V3,\n"
        )
        result = run_profile(raw)

        self.assertEqual(result["column_count"], 3)
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["parser"]["delimiter"], ",")
        self.assertFalse(result["parser"]["bom_present"])
        self.assertEqual([column["index"] for column in result["columns"]], [0, 1, 2])
        self.assertEqual(result["columns"][0]["distinct_count"], 3)
        self.assertEqual(result["columns"][2]["empty_count"], 1)
        self.assertEqual(
            result["columns"][0]["leading_or_trailing_whitespace_count"], 1
        )
        self.assertEqual(
            result["columns"][2]["leading_or_trailing_whitespace_count"], 1
        )

        rendered = repr(result)
        for forbidden in (
            "source",
            "target",
            "condition",
            "'A'",
            "'a'",
            "' A'",
            "V1",
            "V2",
            "V3",
        ):
            self.assertNotIn(forbidden, rendered)

        for ceiling in (
            "header_strings_returned",
            "cell_values_returned",
            "raw_rows_returned",
            "normalization_applied",
            "mapping_interpretation_authorized",
            "vulnerability_selection_authorized",
            "external_bytes_persisted",
            "derived_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[ceiling], False)

    def test_byte_count_mismatch_fails_before_invalid_utf8_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "byte count"):
            profile._profile_verified_csv_bytes(
                raw,
                expected_byte_count=2,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_hash_mismatch_fails_before_invalid_utf8_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "SHA-256"):
            profile._profile_verified_csv_bytes(
                raw,
                expected_byte_count=1,
                expected_sha256="0" * 64,
            )

    def test_invalid_utf8_fails_after_valid_identity(self) -> None:
        raw = b"\xff"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "UTF-8"):
            profile._profile_verified_csv_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_unique_delimiter_is_selected_from_closed_set(self) -> None:
        result = run_profile(b"a;b\r\n1;2\r\n")
        self.assertEqual(result["parser"]["delimiter"], ";")
        self.assertEqual(
            result["parser"]["line_endings"],
            {"crlf_count": 2, "lf_count": 0, "cr_count": 0},
        )

    def test_ambiguous_delimiter_fails_closed(self) -> None:
        raw = b"a,b;c\n1,2;3\n"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "exactly one"):
            run_profile(raw)

    def test_duplicate_empty_control_and_oversized_headers_fail_closed(self) -> None:
        cases = (
            (b"a,a\n1,2\n", "duplicate"),
            (b"a,\n1,2\n", "empty header"),
            (b'a,"b\t"\n1,2\n', "control"),
            (
                (
                    "a,"
                    + ("x" * (profile.MAX_HEADER_UTF8_BYTES + 1))
                    + "\n1,2\n"
                ).encode(),
                "bounded policy",
            ),
        )
        for raw, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(profile.MappingStructureProfileError, message):
                    run_profile(raw)

    def test_total_header_size_is_bounded(self) -> None:
        with mock.patch.object(profile, "_CANONICAL_MAX_TOTAL_HEADER_UTF8_BYTES", 1):
            with self.assertRaisesRegex(profile.MappingStructureProfileError, "total header"):
                run_profile(b"a,b\n1,2\n")

    def test_ragged_duplicate_blank_and_control_bearing_rows_fail_closed(self) -> None:
        cases = (
            (b"a,b\n1,2\n3\n", "delimiter|ragged"),
            (b"a,b\n1,2\n1,2\n", "duplicate rows"),
            (b"a,b\n1,2\n\n", "delimiter|ragged"),
            (b"a,b\n,\n", "blank record"),
            (b'a,b\n"1\t",2\n', "control-bearing"),
        )
        for raw, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(profile.MappingStructureProfileError, message):
                    run_profile(raw)

    def test_whitespace_only_record_is_not_normalized_to_blank(self) -> None:
        result = run_profile(b"a,b\n ,\n")
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["columns"][0]["distinct_count"], 1)
        self.assertEqual(
            result["columns"][0]["leading_or_trailing_whitespace_count"], 1
        )
        self.assertFalse(result["normalization_applied"])

    def test_record_count_is_bounded_during_candidate_parse(self) -> None:
        with mock.patch.object(profile, "_CANONICAL_MAX_RECORDS", 1):
            with self.assertRaisesRegex(profile.MappingStructureProfileError, "exactly one"):
                run_profile(b"a,b\n1,2\n3,4\n")

    def test_nul_fails_closed(self) -> None:
        raw = b"a,b\n1,\x00\n"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "NUL"):
            run_profile(raw)

    def test_value_set_fingerprint_preserves_exact_identity(self) -> None:
        result = run_profile(b"h1,h2\nA,1\na,2\n A,3\n")
        values = sorted({"A", "a", " A"})
        expected = hashlib.sha256()
        expected.update(len(values).to_bytes(8, "big"))
        for value in values:
            encoded = value.encode("utf-8")
            expected.update(len(encoded).to_bytes(8, "big"))
            expected.update(encoded)
        self.assertEqual(
            result["columns"][0]["exact_value_set_sha256"], expected.hexdigest()
        )

    def test_ordered_header_fingerprint_is_order_sensitive_and_collision_safe(self) -> None:
        first = run_profile(b"a,bc\n1,2\n")
        second = run_profile(b"ab,c\n1,2\n")
        swapped = run_profile(b"bc,a\n1,2\n")
        self.assertNotEqual(
            first["ordered_header_sha256"], second["ordered_header_sha256"]
        )
        self.assertNotEqual(
            first["ordered_header_sha256"], swapped["ordered_header_sha256"]
        )
        self.assertEqual(first["header_utf8_byte_count"], 3)

    def test_whitespace_is_counted_but_not_normalized(self) -> None:
        result = run_profile(b"a,b\n x,1\nx,2\n")
        self.assertEqual(result["columns"][0]["distinct_count"], 2)
        self.assertEqual(
            result["columns"][0]["leading_or_trailing_whitespace_count"], 1
        )
        self.assertFalse(result["normalization_applied"])

    def test_utf8_bom_is_explicit(self) -> None:
        result = run_profile(b"\xef\xbb\xbfa,b\n1,2\n")
        self.assertTrue(result["parser"]["bom_present"])
        self.assertEqual(result["parser"]["encoding"], "utf-8-sig")

    def test_public_profiler_is_pinned_to_trusted_mapping_identity(self) -> None:
        raw = b"a,b\n1,2\n"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "byte count"):
            profile.profile_verified_mapping_bytes(raw)
        self.assertEqual(profile.RECEIPT_COMMENT_ID, 5303466667)
        self.assertEqual(profile.RECEIPT_RUN_ID, 31899242278)
        self.assertEqual(
            profile.RECEIPT_EXECUTION_SHA,
            "9b1bb7127138247cf613dbf444d139c189c9b13a",
        )

    def test_public_authority_alias_drift_fails_before_content_processing(self) -> None:
        raw = b"a,b\n1,2\n"
        for name, replacement in (
            ("EXPECTED_BYTE_COUNT", len(raw)),
            ("MAX_RECORDS", profile.MAX_RECORDS + 1),
            ("DELIMITER_CANDIDATES", (",",)),
        ):
            with self.subTest(name=name), mock.patch.object(profile, name, replacement):
                with self.assertRaisesRegex(profile.MappingStructureProfileError, "drifted"):
                    profile.profile_verified_mapping_bytes(raw)


if __name__ == "__main__":
    unittest.main()
