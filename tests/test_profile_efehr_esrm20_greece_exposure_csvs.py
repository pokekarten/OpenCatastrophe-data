# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import profile_efehr_esrm20_greece_exposure_csvs as worker


def _identity(raw: bytes) -> tuple[int, str]:
    return len(raw), hashlib.sha256(raw).hexdigest()


def _profile(raw: bytes) -> dict[str, object]:
    byte_count, sha256 = _identity(raw)
    return worker._profile_receipt_verified_csv(
        raw,
        expected_byte_count=byte_count,
        expected_sha256=sha256,
    )


class GreeceExposureCsvProfileTests(unittest.TestCase):
    def test_frozen_receipts_match_trusted_main_terminal(self) -> None:
        self.assertEqual(worker.SOURCE_ISSUE, 285)
        self.assertEqual(worker.PARENT_CONSUMER_ISSUE, 287)
        self.assertEqual(worker.RECEIPT_COMMENT_ID, 5397480571)
        self.assertEqual(
            worker.RECEIPT_EXECUTION_SHA,
            "4b1d3c41a5df739b9686303eb753577ca39ec58e",
        )
        self.assertEqual(
            worker.RECEIPTS,
            (
                (
                    "Exposure/OQ_Exposure_Input_Greece_Com.csv",
                    7_672_810,
                    "2281f079a6e0b2215fab696d442f9d98b9b0ba94a2b4b24f23f1fff4018d1b57",
                ),
                (
                    "Exposure/OQ_Exposure_Input_Greece_Ind.csv",
                    2_822_653,
                    "ad6698199d84002d017b41668dc204a2d53835a4b2429bc7e8eea56b328549c7",
                ),
                (
                    "Exposure/OQ_Exposure_Input_Greece_Res.csv",
                    5_263_604,
                    "928ac7f069dfc3181a936f73caafb951a5c2437f70379fa29518c002bbd3ef28",
                ),
            ),
        )
        self.assertEqual(len(worker._receipt_map()), 3)

    def test_structure_profile_is_deterministic_and_value_free(self) -> None:
        raw = (
            b"id,taxonomy,structural\n"
            b"A,CR/LWAL,100000\n"
            b"B,MUR/LWAL,200000\n"
            b"C,CR/LWAL,\n"
        )
        profile = _profile(raw)
        self.assertEqual(profile["record_count"], 3)
        self.assertEqual(profile["header"], ["id", "taxonomy", "structural"])
        self.assertIs(profile["raw_rows_returned"], False)
        self.assertIs(profile["exact_field_values_returned"], False)
        self.assertIs(profile["external_bytes_persisted"], False)
        self.assertIs(profile["publication_authorized"], False)

        columns = {column["name"]: column for column in profile["columns"]}
        self.assertEqual(columns["taxonomy"]["distinct_count"], 2)
        self.assertEqual(columns["taxonomy"]["empty_count"], 0)
        self.assertEqual(columns["structural"]["empty_count"], 1)
        self.assertEqual(
            columns["structural"]["decimal_summary"]["finite_decimal_count"],
            2,
        )
        serialized = repr(profile)
        self.assertNotIn("CR/LWAL", serialized)
        self.assertNotIn("MUR/LWAL", serialized)
        self.assertNotIn("100000", serialized)

    def test_value_set_fingerprint_is_independent_of_row_order(self) -> None:
        one = _profile(b"id,taxonomy\n1,B\n2,A\n3,B\n")
        two = _profile(b"id,taxonomy\n3,B\n1,B\n2,A\n")
        one_columns = {column["name"]: column for column in one["columns"]}
        two_columns = {column["name"]: column for column in two["columns"]}
        self.assertEqual(
            one_columns["taxonomy"]["exact_value_set_sha256"],
            two_columns["taxonomy"]["exact_value_set_sha256"],
        )
        self.assertEqual(one_columns["taxonomy"]["distinct_count"], 2)
        self.assertEqual(two_columns["taxonomy"]["distinct_count"], 2)

    def test_byte_identity_is_checked_before_decode_or_csv_parse(self) -> None:
        raw = b"\xff,not,csv"
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvProfileError,
            "byte count does not match trusted receipt",
        ):
            worker._profile_receipt_verified_csv(
                raw,
                expected_byte_count=len(raw) + 1,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

        with self.assertRaisesRegex(
            worker.GreeceExposureCsvProfileError,
            "SHA-256 does not match trusted receipt",
        ):
            worker._profile_receipt_verified_csv(
                raw,
                expected_byte_count=len(raw),
                expected_sha256="0" * 64,
            )

        byte_count, sha256 = _identity(raw)
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvProfileError,
            "not valid UTF-8",
        ):
            worker._profile_receipt_verified_csv(
                raw,
                expected_byte_count=byte_count,
                expected_sha256=sha256,
            )

    def test_nul_duplicate_empty_header_and_ragged_rows_fail_closed(self) -> None:
        cases = (
            (b"id,taxonomy\n1,A\x00B\n", "NUL characters"),
            (b"id,id\n1,2\n", "duplicate headers"),
            (b"id,\n1,2\n", "empty header"),
            (b"id,taxonomy\n1\n", "ragged row"),
            (b"id,taxonomy\n", "no data records"),
        )
        for raw, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(worker.GreeceExposureCsvProfileError, message):
                    _profile(raw)

    def test_nonfinite_numeric_text_is_not_counted_as_finite_decimal(self) -> None:
        profile = _profile(b"id,value\n1,NaN\n2,Infinity\n3,4.5\n")
        columns = {column["name"]: column for column in profile["columns"]}
        summary = columns["value"]["decimal_summary"]
        self.assertEqual(summary["finite_decimal_count"], 1)
        self.assertIs(summary["all_nonempty_decimal"], False)

    def test_public_profiler_is_closed_to_frozen_paths_and_receipts(self) -> None:
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvProfileError,
            "left frozen three-object receipt set",
        ):
            worker.profile_verified_csv_bytes(
                b"id,taxonomy\n1,A\n",
                repository_path="Exposure/Other.csv",
            )

        canonical_path = worker.RECEIPTS[0][0]
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvProfileError,
            "byte count does not match trusted receipt",
        ):
            worker.profile_verified_csv_bytes(
                b"id,taxonomy\n1,A\n",
                repository_path=canonical_path,
            )

    def test_bundle_requires_exact_three_paths(self) -> None:
        paths = [path for path, _, _ in worker.RECEIPTS]
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvProfileError,
            "does not match frozen three-object receipt set",
        ):
            worker.profile_verified_bundle({paths[0]: b"x", paths[1]: b"y"})

        with self.assertRaisesRegex(
            worker.GreeceExposureCsvProfileError,
            "does not match frozen three-object receipt set",
        ):
            worker.profile_verified_bundle(
                {
                    paths[0]: b"x",
                    paths[1]: b"y",
                    paths[2]: b"z",
                    "Exposure/Other.csv": b"q",
                }
            )

    def test_bundle_authority_flags_remain_fail_closed(self) -> None:
        expected_false = (
            "content_semantics_verified",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        )
        source = worker.profile_verified_csv_bytes
        try:
            worker.profile_verified_csv_bytes = lambda raw, *, repository_path: {
                "repository_path": repository_path,
                "byte_count": 1,
                "sha256": "0" * 64,
                "profile": {"raw_rows_returned": False},
            }
            bundle = worker.profile_verified_bundle(
                {path: b"x" for path, _, _ in worker.RECEIPTS}
            )
        finally:
            worker.profile_verified_csv_bytes = source

        self.assertIs(bundle["provider_file_content_profiled"], True)
        self.assertIs(bundle["raw_rows_returned"], False)
        self.assertIs(bundle["exact_field_values_returned"], False)
        self.assertIs(bundle["external_bytes_persisted"], False)
        for field in expected_false:
            with self.subTest(field=field):
                self.assertIs(bundle[field], False)


if __name__ == "__main__":
    unittest.main()
