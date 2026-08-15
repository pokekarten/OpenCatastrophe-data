# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import profile_efehr_esrm20_mapping_structure as profile


def identity(raw: bytes) -> tuple[int, str]:
    return len(raw), hashlib.sha256(raw).hexdigest()


def run_profile(raw: bytes):
    size, sha256 = identity(raw)
    return profile.profile_verified_mapping_bytes(
        raw,
        expected_byte_count=size,
        expected_sha256=sha256,
    )


class ProfileVerifiedMappingBytesTests(unittest.TestCase):
    def test_profiles_only_value_free_structure(self) -> None:
        raw = (
            b"SecretHeaderAlpha,SecretHeaderBeta\n"
            b"valueAlpha,modelOne\n"
            b" valueAlpha ,modelTwo\n"
            b",modelThree\n"
        )
        result = run_profile(raw)

        self.assertEqual(result["column_count"], 2)
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["parser"]["delimiter"], ",")
        self.assertEqual(result["source_identity"]["science_issue"], 283)
        self.assertEqual(result["source_identity"]["control_issue"], 340)
        self.assertEqual(result["source_identity"]["byte_count"], len(raw))
        self.assertEqual([column["index"] for column in result["columns"]], [0, 1])
        self.assertEqual(result["columns"][0]["empty_count"], 1)
        self.assertEqual(result["columns"][0]["nonempty_count"], 2)
        self.assertEqual(result["columns"][0]["distinct_count"], 3)
        self.assertEqual(
            result["columns"][0]["leading_or_trailing_whitespace_count"], 1
        )

        rendered = repr(result)
        for forbidden in (
            "SecretHeaderAlpha",
            "SecretHeaderBeta",
            "valueAlpha",
            "modelOne",
            "modelTwo",
            "modelThree",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_byte_count_mismatch_fails_before_invalid_utf8_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "byte count"):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=2,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_hash_mismatch_fails_before_invalid_utf8_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "SHA-256"):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=1,
                expected_sha256="0" * 64,
            )

    def test_valid_identity_then_invalid_utf8_fails_closed(self) -> None:
        raw = b"\xff"
        size, sha256 = identity(raw)
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "UTF-8"):
            profile.profile_verified_mapping_bytes(
                raw,
                expected_byte_count=size,
                expected_sha256=sha256,
            )

    def test_unique_delimiter_selection_supports_closed_candidate_set(self) -> None:
        for delimiter in (b",", b";", b"\t", b"|"):
            with self.subTest(delimiter=delimiter):
                raw = b"left" + delimiter + b"right\nA" + delimiter + b"B\n"
                result = run_profile(raw)
                self.assertEqual(result["parser"]["delimiter"].encode(), delimiter)
                self.assertEqual(result["column_count"], 2)

    def test_ambiguous_delimiter_fails_closed(self) -> None:
        raw = b"a,b;c\n1,2;3\n"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "ambiguous"):
            run_profile(raw)

    def test_no_valid_multi_column_delimiter_fails_closed(self) -> None:
        raw = b"single\nvalue\n"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "no structurally valid"):
            run_profile(raw)

    def test_invalid_headers_fail_closed(self) -> None:
        cases = {
            "duplicate": b"a,a\n1,2\n",
            "empty header": b"a,\n1,2\n",
            "control": b"a,\x01b\n1,2\n",
            "oversized": (b"a" * (profile.MAX_HEADER_UTF8_BYTES + 1)) + b",b\n1,2\n",
        }
        for expected, raw in cases.items():
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(profile.MappingStructureProfileError, expected):
                    run_profile(raw)

    def test_invalid_rows_fail_closed(self) -> None:
        cases = {
            "ragged": b"a,b\n1,2\n3\n",
            "duplicate exact row": b"a,b\n1,2\n1,2\n",
            "blank row": b"a,b\n1,2\n\n3,4\n",
            "control-bearing cell": b"a,b\n1,2\n3,\x01\n",
        }
        for expected, raw in cases.items():
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(profile.MappingStructureProfileError, expected):
                    run_profile(raw)

    def test_whitespace_is_counted_but_never_normalized(self) -> None:
        raw = b"a,b\n A ,one\nA,two\n"
        result = run_profile(raw)
        column = result["columns"][0]
        self.assertEqual(column["distinct_count"], 2)
        self.assertEqual(column["leading_or_trailing_whitespace_count"], 1)

        expected = hashlib.sha256()
        for value in sorted({" A ", "A"}):
            encoded = value.encode("utf-8")
            expected.update(len(encoded).to_bytes(8, "big"))
            expected.update(encoded)
        self.assertEqual(column["exact_value_set_sha256"], expected.hexdigest())
        self.assertFalse(result["normalization_applied"])
        self.assertNotIn(" A ", repr(result))

    def test_fingerprints_are_deterministic_and_identity_sensitive(self) -> None:
        first = run_profile(b"a,b\nA,X\nB,Y\n")
        same = run_profile(b"a,b\nA,X\nB,Y\n")
        header_reordered = run_profile(b"b,a\nX,A\nY,B\n")
        value_changed = run_profile(b"a,b\nA,X\nC,Y\n")

        self.assertEqual(first["ordered_header_sha256"], same["ordered_header_sha256"])
        self.assertEqual(
            first["columns"][0]["exact_value_set_sha256"],
            same["columns"][0]["exact_value_set_sha256"],
        )
        self.assertNotEqual(
            first["ordered_header_sha256"], header_reordered["ordered_header_sha256"]
        )
        self.assertNotEqual(
            first["columns"][0]["exact_value_set_sha256"],
            value_changed["columns"][0]["exact_value_set_sha256"],
        )

    def test_value_set_hash_is_row_order_independent(self) -> None:
        first = run_profile(b"a,b\nA,X\nB,Y\n")
        reordered = run_profile(b"a,b\nB,Y\nA,X\n")
        self.assertEqual(
            first["columns"][0]["exact_value_set_sha256"],
            reordered["columns"][0]["exact_value_set_sha256"],
        )

    def test_bom_and_line_endings_are_structural_only(self) -> None:
        raw = b"\xef\xbb\xbfa,b\r\n1,2\r\n"
        result = run_profile(raw)
        self.assertTrue(result["parser"]["bom_present"])
        self.assertEqual(result["parser"]["encoding"], "utf-8-sig")
        self.assertEqual(
            result["parser"]["line_endings"],
            {"crlf_count": 2, "lf_count": 0, "cr_count": 0},
        )

    def test_all_authority_ceilings_are_exact_false(self) -> None:
        result = run_profile(b"a,b\n1,2\n")
        for field in (
            "header_strings_returned",
            "cell_values_returned",
            "raw_rows_returned",
            "normalization_applied",
            "external_bytes_persisted",
            "derived_bytes_persisted",
            "publication_authorized",
            "mapping_interpretation_authorized",
            "vulnerability_selection_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False, field)


if __name__ == "__main__":
    unittest.main()
