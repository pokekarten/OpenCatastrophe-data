# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from scripts import profile_efehr_esrm20_mapping_structure as profile


class Esrm20MappingStructureProfileTests(unittest.TestCase):
    def profile_synthetic(self, raw: bytes) -> dict[str, object]:
        digest = hashlib.sha256(raw).hexdigest()
        with (
            mock.patch.object(profile, "_CANONICAL_EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(profile, "_CANONICAL_EXPECTED_SHA256", digest),
            mock.patch.object(profile, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(profile, "EXPECTED_SHA256", digest),
        ):
            return profile.profile_verified_mapping_bytes(raw)

    def assert_synthetic_rejected(self, raw: bytes, pattern: str | None = None) -> None:
        digest = hashlib.sha256(raw).hexdigest()
        with (
            mock.patch.object(profile, "_CANONICAL_EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(profile, "_CANONICAL_EXPECTED_SHA256", digest),
            mock.patch.object(profile, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(profile, "EXPECTED_SHA256", digest),
        ):
            if pattern is None:
                with self.assertRaises(profile.MappingStructureProfileError):
                    profile.profile_verified_mapping_bytes(raw)
            else:
                with self.assertRaisesRegex(profile.MappingStructureProfileError, pattern):
                    profile.profile_verified_mapping_bytes(raw)

    def test_valid_profile_is_value_free_and_preserves_whitespace_identity(self) -> None:
        raw = (
            b"SYNTH_SOURCE_HEADER,SYNTH_TARGET_HEADER,SYNTH_WEIGHT_HEADER\r\n"
            b"SYNTH_A,SYNTH_V1,1\r\n"
            b" SYNTH_B,SYNTH_V2,2\r\n"
            b"SYNTH_C,SYNTH_V3,\r\n"
        )
        result = self.profile_synthetic(raw)

        self.assertEqual(result["schema_version"], profile.SCHEMA_VERSION)
        self.assertEqual(result["source_issue"], 283)
        self.assertEqual(result["control_issue"], 404)
        self.assertEqual(result["dataset_id"], "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(result["project_id"], 269)
        self.assertEqual(result["receipt_comment_id"], 5303466667)
        self.assertEqual(result["receipt_run_id"], 31899242278)
        self.assertEqual(result["parser"]["delimiter"], ",")  # type: ignore[index]
        self.assertEqual(result["parser"]["encoding"], "utf-8")  # type: ignore[index]
        self.assertEqual(result["parser"]["line_endings"]["crlf_count"], 4)  # type: ignore[index]
        self.assertEqual(result["column_count"], 3)
        self.assertEqual(result["record_count"], 3)

        columns = result["columns"]  # type: ignore[assignment]
        self.assertEqual(columns[0]["distinct_count"], 3)  # type: ignore[index]
        self.assertEqual(columns[0]["leading_or_trailing_whitespace_count"], 1)  # type: ignore[index]
        self.assertEqual(columns[2]["empty_count"], 1)  # type: ignore[index]

        rendered = repr(result)
        for forbidden in (
            "SYNTH_SOURCE_HEADER",
            "SYNTH_TARGET_HEADER",
            "SYNTH_WEIGHT_HEADER",
            "SYNTH_A",
            "SYNTH_V1",
            "SYNTH_V2",
            "SYNTH_V3",
            " SYNTH_B",
        ):
            self.assertNotIn(forbidden, rendered)
        self.assertNotIn("name", columns[0])  # type: ignore[operator]
        self.assertNotIn("values", columns[0])  # type: ignore[operator]

    def test_byte_identity_fails_before_decode_or_parser(self) -> None:
        invalid_utf8 = b"\xff"
        with self.assertRaisesRegex(profile.MappingStructureProfileError, "byte count"):
            profile.profile_verified_mapping_bytes(invalid_utf8)

        with (
            mock.patch.object(profile, "_CANONICAL_EXPECTED_BYTE_COUNT", 1),
            mock.patch.object(profile, "EXPECTED_BYTE_COUNT", 1),
        ):
            with self.assertRaisesRegex(profile.MappingStructureProfileError, "SHA-256"):
                profile.profile_verified_mapping_bytes(invalid_utf8)

        digest = hashlib.sha256(invalid_utf8).hexdigest()
        with (
            mock.patch.object(profile, "_CANONICAL_EXPECTED_BYTE_COUNT", 1),
            mock.patch.object(profile, "_CANONICAL_EXPECTED_SHA256", digest),
            mock.patch.object(profile, "EXPECTED_BYTE_COUNT", 1),
            mock.patch.object(profile, "EXPECTED_SHA256", digest),
        ):
            with self.assertRaisesRegex(profile.MappingStructureProfileError, "UTF-8"):
                profile.profile_verified_mapping_bytes(invalid_utf8)

    def test_public_alias_drift_fails_before_content_processing(self) -> None:
        with mock.patch.object(profile, "DATASET_ID", "efehr.other"):
            with self.assertRaisesRegex(
                profile.MappingStructureProfileError,
                "dataset id drifted",
            ):
                profile.profile_verified_mapping_bytes(b"not the mapping")

    def test_delimiter_selection_is_unique_and_ambiguous_input_fails_closed(self) -> None:
        semicolon = self.profile_synthetic(b"a;b;c\n1;2;3\n4;5;6\n")
        self.assertEqual(semicolon["parser"]["delimiter"], ";")  # type: ignore[index]

        ambiguous = b"a,b;c\n1,2;3\n4,5;6\n"
        self.assert_synthetic_rejected(ambiguous, "exactly one.*delimiter")

    def test_header_failures_are_closed_without_echoing_values(self) -> None:
        cases = (
            (b"a,,c\n1,2,3\n", "empty header"),
            (b"a,a\n1,2\n", "duplicate headers"),
            (b'"a\nb",c\n1,2\n', "control characters"),
            (("a" * (profile.MAX_HEADER_UTF8_BYTES + 1) + ",b\n1,2\n").encode(), "header exceeds"),
        )
        for raw, pattern in cases:
            with self.subTest(pattern=pattern):
                self.assert_synthetic_rejected(raw, pattern)

    def test_row_failures_are_closed(self) -> None:
        cases = (
            b"a,b\n1,2\n3\n",
            b"a,b\n1,2\n\n3,4\n",
            b'a,b\n"1,2\n',
        )
        for raw in cases:
            with self.subTest(raw=raw):
                self.assert_synthetic_rejected(raw)

        self.assert_synthetic_rejected(
            b"a,b\n1,2\n1,2\n",
            "duplicate exact record",
        )
        self.assert_synthetic_rejected(
            b'a,b\n1,"x\ty"\n',
            "control-bearing cell",
        )

    def test_fingerprints_are_deterministic_and_order_sensitive(self) -> None:
        first_raw = b"a,b\nx,y\nz,w\n"
        first = self.profile_synthetic(first_raw)
        repeated = self.profile_synthetic(first_raw)
        reordered = self.profile_synthetic(b"b,a\ny,x\nw,z\n")

        self.assertEqual(first["ordered_header_sha256"], repeated["ordered_header_sha256"])
        self.assertNotEqual(first["ordered_header_sha256"], reordered["ordered_header_sha256"])
        self.assertEqual(first["columns"][0]["exact_value_set_sha256"], repeated["columns"][0]["exact_value_set_sha256"])  # type: ignore[index]
        self.assertNotEqual(first["columns"][0]["exact_value_set_sha256"], reordered["columns"][0]["exact_value_set_sha256"])  # type: ignore[index]

    def test_bom_and_line_endings_are_profiled_without_text_output(self) -> None:
        raw = b"\xef\xbb\xbfa,b\r\n1,2\r\n"
        result = self.profile_synthetic(raw)
        self.assertTrue(result["parser"]["bom_present"])  # type: ignore[index]
        self.assertEqual(result["parser"]["encoding"], "utf-8-sig")  # type: ignore[index]
        self.assertEqual(result["parser"]["line_endings"]["crlf_count"], 2)  # type: ignore[index]
        self.assertNotIn("name", result["columns"][0])  # type: ignore[operator,index]

    def test_all_authority_ceilings_remain_exact_false(self) -> None:
        result = self.profile_synthetic(b"a,b\n1,2\n3,4\n")
        for field in (
            "header_values_returned",
            "cell_values_returned",
            "raw_rows_returned",
            "normalization_applied",
            "external_bytes_persisted",
            "derived_artifact_persisted",
            "publication_authorized",
            "mapping_interpretation_authorized",
            "vulnerability_selection_authorized",
        ):
            with self.subTest(field=field):
                self.assertIs(result[field], False)


if __name__ == "__main__":
    unittest.main()
