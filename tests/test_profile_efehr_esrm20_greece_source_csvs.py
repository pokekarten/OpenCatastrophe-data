# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import profile_efehr_esrm20_greece_source_csvs as subject


class GreeceSourceCsvProfileTests(unittest.TestCase):
    @staticmethod
    def _nested_profile(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "schema_version": subject.generic_csv.SCHEMA_VERSION,
            "parser": {
                "encoding": "utf-8",
                "bom_present": False,
                "delimiter": ",",
                "line_endings": {"crlf_count": 1, "lf_count": 1, "cr_count": 0},
            },
            "record_count": 1,
            "header": ["FIELD"],
            "columns": [
                {
                    "name": "FIELD",
                    "record_count": 1,
                    "empty_count": 0,
                    "nonempty_count": 1,
                    "distinct_count": 1,
                    "exact_value_set_sha256": "0" * 64,
                    "decimal_summary": None,
                }
            ],
            "raw_rows_returned": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }

    def test_receipts_bind_exact_trusted_main_terminal(self) -> None:
        self.assertEqual(subject.RECEIPT_COMMENT_ID, 5423879080)
        self.assertEqual(
            subject.RECEIPT_EXECUTION_SHA,
            "0babfcf9aa9b6f6ede911217f99e2252428e95db",
        )
        self.assertEqual(
            subject.RECEIPTS,
            (
                (
                    "_exposure_models/Exposure_Model_Greece_Com.csv",
                    12_578_244,
                    "54c689673ba7160a2cf116af44cae20fe4c74c69ebf3bf192c7dd1bccfc94125",
                ),
                (
                    "_exposure_models/Exposure_Model_Greece_Ind.csv",
                    4_600_971,
                    "491fe2b4dfbb36418582c41818a41c8e521e64b5a4b6c369816d175469b55165",
                ),
                (
                    "_exposure_models/Exposure_Model_Greece_Res.csv",
                    9_011_434,
                    "1104b73d2d4e5b5b89d8c3a9575fe1f348662dd7f706c7a322c70a3240dc4e3b",
                ),
            ),
        )
        subject._require_contract()

    def test_profile_for_test_passes_only_frozen_receipt_to_generic_profiler(self) -> None:
        calls: list[tuple[bytes, int, str]] = []

        def profiler(
            raw: bytes,
            *,
            expected_byte_count: int,
            expected_sha256: str,
        ) -> dict[str, object]:
            calls.append((raw, expected_byte_count, expected_sha256))
            return self._nested_profile()

        path, byte_count, sha256 = subject.RECEIPTS[0]
        result = subject._profile_for_test(b"fixture", repository_path=path, profiler=profiler)

        self.assertEqual(calls, [(b"fixture", byte_count, sha256)])
        self.assertEqual(result["repository_path"], path)
        self.assertEqual(result["byte_count"], byte_count)
        self.assertEqual(result["sha256"], sha256)
        self.assertFalse(result["profile"]["raw_rows_returned"])

    def test_bundle_is_complete_canonical_and_keeps_scientific_ceilings_false(self) -> None:
        raw_by_path = {path: path.encode("ascii") for path, _count, _sha in subject.RECEIPTS}
        result = subject._profile_bundle_for_test(
            raw_by_path,
            profiler=self._nested_profile,
        )

        self.assertEqual(
            [item["repository_path"] for item in result["files"]],
            [path for path, _count, _sha in subject.RECEIPTS],
        )
        self.assertTrue(result["provider_file_content_profiled"])
        for field in (
            "source_runtime_lineage_verified",
            "content_semantics_verified",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "raw_rows_returned",
            "exact_field_values_returned",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False, field)

    def test_bundle_rejects_missing_or_extra_source_object(self) -> None:
        raw_by_path = {path: b"x" for path, _count, _sha in subject.RECEIPTS}
        missing = dict(raw_by_path)
        missing.pop(subject.RECEIPTS[-1][0])
        with self.assertRaisesRegex(subject.GreeceSourceCsvProfileError, "does not match"):
            subject._profile_bundle_for_test(missing, profiler=self._nested_profile)

        extra = dict(raw_by_path)
        extra["_exposure_models/not-authorized.csv"] = b"x"
        with self.assertRaisesRegex(subject.GreeceSourceCsvProfileError, "does not match"):
            subject._profile_bundle_for_test(extra, profiler=self._nested_profile)

    def test_profile_rejects_unreceipted_path_before_profiler_call(self) -> None:
        profiler = mock.Mock(return_value=self._nested_profile())
        with self.assertRaisesRegex(subject.GreeceSourceCsvProfileError, "left frozen"):
            subject._profile_for_test(
                b"fixture",
                repository_path="_exposure_models/Exposure_Model_Greece_All.csv",
                profiler=profiler,
            )
        profiler.assert_not_called()

    def test_nested_profile_cannot_widen_raw_persistence_or_publication_authority(self) -> None:
        path = subject.RECEIPTS[0][0]
        for field in (
            "raw_rows_returned",
            "external_bytes_persisted",
            "publication_authorized",
        ):
            nested = self._nested_profile()
            nested[field] = True
            with self.subTest(field=field):
                with self.assertRaises(subject.GreeceSourceCsvProfileError):
                    subject._profile_for_test(
                        b"fixture",
                        repository_path=path,
                        profiler=lambda *_args, value=nested, **_kwargs: value,
                    )

    def test_production_profile_rejects_mutated_generic_profiler_identity(self) -> None:
        path = subject.RECEIPTS[0][0]
        with mock.patch.object(
            subject.generic_csv,
            "profile_verified_csv_bytes",
            return_value=self._nested_profile(),
        ):
            with self.assertRaisesRegex(subject.GreeceSourceCsvProfileError, "identity drifted"):
                subject.profile_verified_csv_bytes(b"fixture", repository_path=path)

    def test_contract_rejects_source_target_drift(self) -> None:
        drifted = list(subject.source_receipts.TARGETS)
        path, blob, size = drifted[0]
        drifted[0] = (path, blob, size + 1)
        with mock.patch.object(subject.source_receipts, "TARGETS", tuple(drifted)):
            with self.assertRaisesRegex(subject.GreeceSourceCsvProfileError, "no longer match"):
                subject._require_contract()


if __name__ == "__main__":
    unittest.main()
