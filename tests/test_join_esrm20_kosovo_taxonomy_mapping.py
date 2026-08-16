# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from scripts import join_esrm20_kosovo_taxonomy_mapping as subject


def _raw(rows: list[str]) -> bytes:
    return ("taxonomy,conversion,weight\n" + "\n".join(rows) + "\n").encode()


def _join(taxonomies: list[str], rows: list[str]):
    raw = _raw(rows)
    return subject._join_exact_taxonomies(
        sorted(taxonomies),
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


class ExactKosovoMappingJoinTests(unittest.TestCase):
    def test_exact_one_to_one_and_one_to_many_are_resolved(self):
        records = _join(
            ["A", "B"],
            [
                "A,RISK_A,1",
                "B,RISK_B2,0.6",
                "B,RISK_B1,0.4",
            ],
        )
        self.assertEqual(records[0]["status"], "resolved")
        self.assertEqual(records[0]["targets"], [{"risk_id": "RISK_A", "weight": "1"}])
        self.assertEqual(records[1]["status"], "resolved")
        self.assertEqual(
            records[1]["targets"],
            [
                {"risk_id": "RISK_B1", "weight": "0.4"},
                {"risk_id": "RISK_B2", "weight": "0.6"},
            ],
        )

    def test_openquake_weight_precision_is_applied(self):
        [within] = _join(["A"], ["A,R1,0.5", "A,R2,0.50000005"])
        self.assertEqual(within["status"], "resolved")

        [outside] = _join(["A"], ["A,R1,0.5", "A,R2,0.5000002"])
        self.assertEqual(outside["status"], "ambiguous")
        self.assertEqual(outside["reason_code"], "weights_outside_openquake_precision")

    def test_zero_exact_rows_is_unsupported_without_case_or_whitespace_fallback(self):
        records = _join(["Exact"], ["exact,RISK_LOWER,1", " Exact,RISK_SPACE,1"])
        self.assertEqual(
            records,
            [
                {
                    "taxonomy": "Exact",
                    "status": "unsupported",
                    "reason_code": "no_exact_mapping_row",
                    "targets": [],
                }
            ],
        )

    def test_duplicate_target_semantics_is_ambiguous(self):
        [record] = _join(["A"], ["A,RISK_A,0.5", "A,RISK_A,0.5"])
        self.assertEqual(record["status"], "ambiguous")
        self.assertEqual(record["reason_code"], "duplicate_risk_id_semantics")
        self.assertEqual(record["targets"], [])

    def test_weights_outside_openquake_precision_are_ambiguous(self):
        [record] = _join(["A"], ["A,R1,0.4", "A,R2,0.5"])
        self.assertEqual(record["status"], "ambiguous")
        self.assertEqual(record["reason_code"], "weights_outside_openquake_precision")

    def test_nonfinite_nonpositive_whitespace_or_overlong_weight_is_ambiguous(self):
        for value in ("NaN", "Infinity", "0", "-0.1", " 1", "1" * 129):
            with self.subTest(value=value):
                [record] = _join(["A"], [f"A,RISK_A,{value}"])
                self.assertEqual(record["status"], "ambiguous")
                self.assertEqual(record["reason_code"], "matched_row_not_canonical")

    def test_conversion_is_not_trimmed_or_normalized(self):
        [record] = _join(["A"], ["A, RISK_A,1"])
        self.assertEqual(record["status"], "ambiguous")
        self.assertEqual(record["targets"], [])

    def test_conversion_controls_or_overlong_values_are_not_emitted(self):
        raw_control = b'taxonomy,conversion,weight\nA,"RISK\x01A",1\n'
        [control] = subject._join_exact_taxonomies(
            ["A"],
            raw_control,
            expected_byte_count=len(raw_control),
            expected_sha256=hashlib.sha256(raw_control).hexdigest(),
        )
        self.assertEqual(control["status"], "ambiguous")
        self.assertEqual(control["targets"], [])

        overlong = "R" * (subject.MAX_RISK_ID_UTF8_BYTES + 1)
        [long_value] = _join(["A"], [f"A,{overlong},1"])
        self.assertEqual(long_value["status"], "ambiguous")
        self.assertEqual(long_value["targets"], [])

    def test_admitted_taxonomy_controls_or_overlong_values_fail_before_output(self):
        for taxonomy in ("A\x01", "A" * (subject.MAX_TAXONOMY_UTF8_BYTES + 1)):
            with self.subTest(taxonomy=taxonomy):
                raw = _raw(["OTHER,RISK,1"])
                with self.assertRaisesRegex(
                    subject.KosovoMappingJoinError, "bounded literals"
                ):
                    subject._join_exact_taxonomies(
                        [taxonomy],
                        raw,
                        expected_byte_count=len(raw),
                        expected_sha256=hashlib.sha256(raw).hexdigest(),
                    )

    def test_ragged_mapping_fails_closed_even_if_unrelated(self):
        raw = b"taxonomy,conversion,weight\nOTHER,RISK\n"
        with self.assertRaisesRegex(subject.KosovoMappingJoinError, "ragged row"):
            subject._join_exact_taxonomies(
                ["A"],
                raw,
                expected_byte_count=len(raw),
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_byte_identity_precedes_mapping_decode(self):
        raw = b"\xfftaxonomy,conversion,weight\nA,RISK_A,1\n"
        with self.assertRaisesRegex(subject.KosovoMappingJoinError, "SHA-256"):
            subject._join_exact_taxonomies(
                ["A"],
                raw,
                expected_byte_count=len(raw),
                expected_sha256="0" * 64,
            )

    def test_public_result_is_exhaustive_and_keeps_authority_ceiling_false(self):
        mapping_raw = _raw(["A,RISK_A,1", "B,R1,0.25", "B,R2,0.75"])
        exposure_identity = {
            "dataset_id": "test.exposure",
            "project_id": 186,
            "project_path": "efehr/esrm20_exposure",
            "commit_sha": "9" * 40,
            "repository_path": "exposure.csv",
            "byte_count": 10,
            "sha256": "a" * 64,
            "taxonomy_count": 2,
            "taxonomy_value_set_sha256": "b" * 64,
            "taxonomies": ["A", "B"],
            "normalization_applied": False,
        }
        digest = hashlib.sha256(mapping_raw).hexdigest()
        with (
            patch.object(subject.taxonomy_source, "extract_verified_kosovo_taxonomy", return_value=exposure_identity),
            patch.object(subject.taxonomy_source, "EXPECTED_DISTINCT_COUNT", 2),
            patch.object(subject, "_MAPPING_BYTE_COUNT", len(mapping_raw)),
            patch.object(subject, "_MAPPING_SHA256", digest),
            patch.object(subject.mapping_source, "EXPECTED_BYTE_COUNT", len(mapping_raw)),
            patch.object(subject.mapping_source, "EXPECTED_SHA256", digest),
        ):
            result = subject.join_verified_kosovo_taxonomy_mapping(b"synthetic", mapping_raw)

        self.assertEqual(result["classification_counts"], {"resolved": 2, "unsupported": 0, "ambiguous": 0})
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(
            result["mapping_weight_rule"],
            "positive_finite_float_sum_within_openquake_1e-7",
        )
        self.assertFalse(result["normalization_applied"])
        self.assertFalse(result["wildcard_or_fallback_matching_applied"])
        self.assertFalse(result["vulnerability_file_selection_authorized"])
        self.assertFalse(result["raw_mapping_rows_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])


if __name__ == "__main__":
    unittest.main()
