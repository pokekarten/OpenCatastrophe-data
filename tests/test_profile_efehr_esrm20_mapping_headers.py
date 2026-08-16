# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import unittest
from unittest import mock

from scripts import profile_efehr_esrm20_mapping_headers as disclosure
from scripts import profile_efehr_esrm20_mapping_structure as structure


def structural_result(raw: bytes, *, header: list[str], delimiter: str = ","):
    fingerprint = disclosure._length_prefixed_sha256(header)
    return {
        "source_issue": structure.SOURCE_ISSUE,
        "profile_issue": structure.PROFILE_ISSUE,
        "dataset_id": structure.DATASET_ID,
        "project_id": structure.PROJECT_ID,
        "project_path": structure.PROJECT_PATH,
        "commit_sha": structure.COMMIT_SHA,
        "repository_path": structure.REPOSITORY_PATH,
        "receipt_comment_id": structure.RECEIPT_COMMENT_ID,
        "receipt_run_id": structure.RECEIPT_RUN_ID,
        "receipt_execution_sha": structure.RECEIPT_EXECUTION_SHA,
        "byte_count": structure.EXPECTED_BYTE_COUNT,
        "sha256": structure.EXPECTED_SHA256,
        "profile": {
            "schema_version": "oc-esrm20-mapping-structure-profile-v0",
            "parser": {
                "encoding": "utf-8",
                "bom_present": False,
                "delimiter": delimiter,
                "line_endings": {
                    "crlf_count": 0,
                    "lf_count": raw.count(b"\n"),
                    "cr_count": 0,
                },
            },
            "column_count": len(header),
            "record_count": 1,
            "ordered_header_sha256": fingerprint,
            "header_utf8_byte_count": sum(
                len(value.encode("utf-8")) for value in header
            ),
            "columns": [],
            "header_strings_returned": False,
            "cell_values_returned": False,
            "raw_rows_returned": False,
            "normalization_applied": False,
            "mapping_interpretation_authorized": False,
            "vulnerability_selection_authorized": False,
            "external_bytes_persisted": False,
            "derived_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        },
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "mapping_interpretation_authorized": False,
        "vulnerability_selection_authorized": False,
        "model_use_authorized": False,
    }


class MappingHeaderDisclosureTests(unittest.TestCase):
    def test_discloses_only_exact_ordered_headers_after_structure_authority(self) -> None:
        raw = b"alpha,beta,gamma\nx,y,z\n"
        expected_headers = ["alpha", "beta", "gamma"]
        calls: list[bytes] = []

        def authority(candidate: bytes):
            calls.append(candidate)
            return structural_result(candidate, header=expected_headers)

        result = disclosure._disclose_headers(raw, structure_profiler=authority)

        self.assertEqual(calls, [raw])
        self.assertEqual(result["headers"], expected_headers)
        self.assertEqual(result["column_count"], 3)
        self.assertEqual(
            result["ordered_header_sha256"],
            disclosure._length_prefixed_sha256(expected_headers),
        )
        self.assertEqual(result["disclosure_scope"], "exact_header_strings_only")
        self.assertTrue(result["header_strings_returned"])

        rendered = repr(result)
        self.assertNotIn("'x'", rendered)
        self.assertNotIn("'y'", rendered)
        self.assertNotIn("'z'", rendered)
        for field in (
            "cell_values_returned",
            "raw_rows_returned",
            "normalization_applied",
            "mapping_interpretation_authorized",
            "taxonomy_join_authorized",
            "vulnerability_selection_authorized",
            "external_bytes_persisted",
            "derived_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_structure_authority_runs_before_header_decode(self) -> None:
        raw = b"\xff"

        def reject(_: bytes):
            raise RuntimeError("not exact trusted bytes")

        with self.assertRaisesRegex(
            disclosure.MappingHeaderDisclosureError,
            "structure authority rejected",
        ):
            disclosure._disclose_headers(raw, structure_profiler=reject)

    def test_production_entry_rejects_synthetic_untrusted_bytes(self) -> None:
        with self.assertRaisesRegex(
            disclosure.MappingHeaderDisclosureError,
            "structure authority rejected",
        ):
            disclosure.disclose_verified_mapping_headers(b"a,b\n1,2\n")

    def test_public_entry_has_only_raw_bytes_input(self) -> None:
        signature = inspect.signature(disclosure.disclose_verified_mapping_headers)
        self.assertEqual(tuple(signature.parameters), ("raw",))

    def test_header_fingerprint_drift_fails_closed(self) -> None:
        raw = b"alpha,beta\nx,y\n"
        result = structural_result(raw, header=["alpha", "beta"])
        result["profile"]["ordered_header_sha256"] = "0" * 64

        with self.assertRaisesRegex(
            disclosure.MappingHeaderDisclosureError,
            "ordered-header fingerprint drifted",
        ):
            disclosure._disclose_headers(raw, structure_profiler=lambda _: result)

    def test_header_width_drift_fails_closed(self) -> None:
        raw = b"alpha,beta\nx,y\n"
        result = structural_result(raw, header=["alpha", "beta"])
        result["profile"]["column_count"] = 3

        with self.assertRaisesRegex(
            disclosure.MappingHeaderDisclosureError,
            "header width drifted",
        ):
            disclosure._disclose_headers(raw, structure_profiler=lambda _: result)

    def test_duplicate_empty_and_control_headers_fail_closed(self) -> None:
        cases = (
            (b"a,a\n1,2\n", ["a", "a"], "header is invalid"),
            (b"a,\n1,2\n", ["a", ""], "header is invalid"),
            (b'a,"b\t"\n1,2\n', ["a", "b\t"], "control"),
        )
        for raw, header, message in cases:
            with self.subTest(message=message):
                result = structural_result(raw, header=header)
                with self.assertRaisesRegex(
                    disclosure.MappingHeaderDisclosureError,
                    message,
                ):
                    disclosure._disclose_headers(
                        raw,
                        structure_profiler=lambda _, result=result: result,
                    )

    def test_wrong_structure_provenance_and_authority_ceiling_fail_closed(self) -> None:
        raw = b"alpha,beta\nx,y\n"

        for field, bad_value in (
            ("commit_sha", "0" * 40),
            ("byte_count", True),
            ("sha256", "0" * 64),
        ):
            with self.subTest(field=field):
                result = structural_result(raw, header=["alpha", "beta"])
                result[field] = bad_value
                with self.assertRaisesRegex(
                    disclosure.MappingHeaderDisclosureError,
                    "provenance drifted",
                ):
                    disclosure._disclose_headers(
                        raw,
                        structure_profiler=lambda _, result=result: result,
                    )

        widened = structural_result(raw, header=["alpha", "beta"])
        widened["publication_authorized"] = True
        with self.assertRaisesRegex(
            disclosure.MappingHeaderDisclosureError,
            "widened authority",
        ):
            disclosure._disclose_headers(raw, structure_profiler=lambda _: widened)

        nested_widened = structural_result(raw, header=["alpha", "beta"])
        nested_widened["profile"]["mapping_interpretation_authorized"] = True
        with self.assertRaisesRegex(
            disclosure.MappingHeaderDisclosureError,
            "widened authority",
        ):
            disclosure._disclose_headers(
                raw,
                structure_profiler=lambda _: nested_widened,
            )

    def test_parser_metadata_drift_fails_closed(self) -> None:
        raw = b"alpha,beta\nx,y\n"

        bad_encoding = structural_result(raw, header=["alpha", "beta"])
        bad_encoding["profile"]["parser"]["encoding"] = "latin-1"
        with self.assertRaisesRegex(
            disclosure.MappingHeaderDisclosureError,
            "encoding is invalid",
        ):
            disclosure._disclose_headers(
                raw,
                structure_profiler=lambda _: bad_encoding,
            )

        bad_delimiter = structural_result(raw, header=["alpha", "beta"])
        bad_delimiter["profile"]["parser"]["delimiter"] = ":"
        with self.assertRaisesRegex(
            disclosure.MappingHeaderDisclosureError,
            "delimiter is invalid",
        ):
            disclosure._disclose_headers(
                raw,
                structure_profiler=lambda _: bad_delimiter,
            )

    def test_structure_profiler_identity_cannot_be_monkeypatched(self) -> None:
        with mock.patch.object(
            disclosure.mapping_structure,
            "profile_verified_mapping_bytes",
            lambda raw: {},
        ):
            with self.assertRaisesRegex(
                disclosure.MappingHeaderDisclosureError,
                "profiler identity drifted",
            ):
                disclosure.disclose_verified_mapping_headers(b"x")

    def test_result_binds_frozen_receipt_identity_without_semantic_authority(self) -> None:
        raw = b"alpha,beta\nx,y\n"
        result = disclosure._disclose_headers(
            raw,
            structure_profiler=lambda candidate: structural_result(
                candidate,
                header=["alpha", "beta"],
            ),
        )

        self.assertEqual(result["decision_issue"], 410)
        self.assertEqual(result["source_issue"], 283)
        self.assertEqual(result["profile_issue"], 404)
        self.assertEqual(result["project_id"], 269)
        self.assertEqual(
            result["commit_sha"],
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(result["byte_count"], 83_585)
        self.assertEqual(
            result["sha256"],
            "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c",
        )
        self.assertFalse(result["mapping_interpretation_authorized"])
        self.assertFalse(result["taxonomy_join_authorized"])
        self.assertFalse(result["vulnerability_selection_authorized"])


if __name__ == "__main__":
    unittest.main()
