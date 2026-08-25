# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from scripts import profile_efehr_esrm20_greece_exposure_csvs as worker


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

    def test_adapter_reuses_receipt_first_parser_without_returning_values(self) -> None:
        raw = b"id,taxonomy,structural\nA,CR/LWAL,100000\nB,MUR/LWAL,200000\n"
        path = worker.RECEIPTS[0][0]
        receipt = {path: (len(raw), hashlib.sha256(raw).hexdigest())}
        with mock.patch.object(worker, "_receipt_map", return_value=receipt):
            result = worker.profile_verified_csv_bytes(raw, repository_path=path)

        self.assertEqual(result["repository_path"], path)
        self.assertEqual(result["byte_count"], len(raw))
        profile = result["profile"]
        self.assertEqual(profile["record_count"], 2)
        self.assertEqual(profile["header"], ["id", "taxonomy", "structural"])
        self.assertIs(profile["raw_rows_returned"], False)
        self.assertIs(profile["external_bytes_persisted"], False)
        serialized = repr(profile)
        self.assertNotIn("CR/LWAL", serialized)
        self.assertNotIn("MUR/LWAL", serialized)
        self.assertNotIn("100000", serialized)

    def test_real_public_path_still_requires_exact_trusted_receipt(self) -> None:
        canonical_path = worker.RECEIPTS[0][0]
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvProfileError,
            "byte count does not match trusted receipt",
        ):
            worker.profile_verified_csv_bytes(
                b"id,taxonomy\n1,A\n",
                repository_path=canonical_path,
            )

    def test_parser_failure_is_wrapped_without_semantic_fallback(self) -> None:
        raw = b"\xff,not,csv"
        path = worker.RECEIPTS[0][0]
        receipt = {path: (len(raw), hashlib.sha256(raw).hexdigest())}
        with mock.patch.object(worker, "_receipt_map", return_value=receipt):
            with self.assertRaisesRegex(
                worker.GreeceExposureCsvProfileError,
                "not valid UTF-8",
            ):
                worker.profile_verified_csv_bytes(raw, repository_path=path)

    def test_unknown_path_is_rejected_before_parser(self) -> None:
        with mock.patch.object(
            worker.generic_csv,
            "profile_verified_csv_bytes",
            side_effect=AssertionError("parser must not run for an unknown path"),
        ):
            with self.assertRaisesRegex(
                worker.GreeceExposureCsvProfileError,
                "left frozen three-object receipt set",
            ):
                worker.profile_verified_csv_bytes(
                    b"id,taxonomy\n1,A\n",
                    repository_path="Exposure/Other.csv",
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

    def test_bundle_preserves_canonical_order_and_authority_ceiling(self) -> None:
        calls: list[str] = []

        def fake_profile(raw: bytes, *, repository_path: str) -> dict[str, object]:
            self.assertEqual(raw, b"x")
            calls.append(repository_path)
            return {
                "repository_path": repository_path,
                "byte_count": 1,
                "sha256": "0" * 64,
                "profile": {"raw_rows_returned": False},
            }

        with mock.patch.object(
            worker,
            "profile_verified_csv_bytes",
            side_effect=fake_profile,
        ):
            bundle = worker.profile_verified_bundle(
                {path: b"x" for path, _, _ in worker.RECEIPTS}
            )

        self.assertEqual(calls, [path for path, _, _ in worker.RECEIPTS])
        self.assertIs(bundle["provider_file_content_profiled"], True)
        self.assertIs(bundle["raw_rows_returned"], False)
        self.assertIs(bundle["exact_field_values_returned"], False)
        self.assertIs(bundle["external_bytes_persisted"], False)
        for field in (
            "content_semantics_verified",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field):
                self.assertIs(bundle[field], False)

    def test_receipt_table_drift_fails_closed(self) -> None:
        with mock.patch.object(worker, "RECEIPTS", worker.RECEIPTS[:2]):
            with self.assertRaisesRegex(
                worker.GreeceExposureCsvProfileError,
                "receipt set drifted",
            ):
                worker._receipt_map()

        duplicate = (worker.RECEIPTS[0], worker.RECEIPTS[0], worker.RECEIPTS[2])
        with mock.patch.object(worker, "RECEIPTS", duplicate):
            with self.assertRaisesRegex(
                worker.GreeceExposureCsvProfileError,
                "duplicate frozen Greece exposure CSV path",
            ):
                worker._receipt_map()


if __name__ == "__main__":
    unittest.main()
