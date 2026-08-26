# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from scripts import join_esrm20_greece_taxonomy_mapping as subject


def _fingerprint(values: set[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _exposure_csv(taxonomies: list[str]) -> str:
    header = ",".join(subject.EXPECTED_HEADER)
    rows = []
    for index, taxonomy in enumerate(taxonomies, start=1):
        row = [
            str(index),
            "23.7",
            "37.9",
            taxonomy,
            "1",
            "100",
            "1",
            "1",
            "1",
            "Res",
            "1",
            "1",
            "name3",
            "1",
            "1",
            "name1",
            "1",
            "name2",
        ]
        rows.append(",".join(row))
    return header + "\n" + "\n".join(rows) + "\n"


class GreeceTaxonomyMappingJoinTests(unittest.TestCase):
    def test_profiled_text_extracts_literal_sorted_unique_taxonomies(self) -> None:
        text = _exposure_csv(["B", "A", "B"])
        values = subject._extract_taxonomies_from_profiled_text(
            text,
            expected_record_count=3,
            expected_taxonomy_count=2,
            expected_value_set_sha256=_fingerprint({"A", "B"}),
        )
        self.assertEqual(values, ["A", "B"])

    def test_profiled_text_does_not_casefold_or_alias(self) -> None:
        text = _exposure_csv(["Taxonomy", "taxonomy"])
        values = subject._extract_taxonomies_from_profiled_text(
            text,
            expected_record_count=2,
            expected_taxonomy_count=2,
            expected_value_set_sha256=_fingerprint({"Taxonomy", "taxonomy"}),
        )
        self.assertEqual(values, ["Taxonomy", "taxonomy"])

    def test_profiled_text_rejects_empty_control_and_overlong_taxonomies(self) -> None:
        for taxonomy in (
            "",
            "A\x01",
            "A" * (subject.exact_join.MAX_TAXONOMY_UTF8_BYTES + 1),
        ):
            with self.subTest(taxonomy=taxonomy[:20]):
                text = _exposure_csv([taxonomy])
                with self.assertRaisesRegex(
                    subject.GreeceTaxonomyMappingJoinError, "invalid taxonomy"
                ):
                    subject._extract_taxonomies_from_profiled_text(
                        text,
                        expected_record_count=1,
                        expected_taxonomy_count=1,
                        expected_value_set_sha256=_fingerprint({taxonomy}),
                    )

    def test_profiled_text_rejects_count_and_fingerprint_drift(self) -> None:
        text = _exposure_csv(["A", "B"])
        with self.assertRaisesRegex(
            subject.GreeceTaxonomyMappingJoinError, "record count changed"
        ):
            subject._extract_taxonomies_from_profiled_text(
                text,
                expected_record_count=3,
                expected_taxonomy_count=2,
                expected_value_set_sha256=_fingerprint({"A", "B"}),
            )
        with self.assertRaisesRegex(
            subject.GreeceTaxonomyMappingJoinError, "distinct count changed"
        ):
            subject._extract_taxonomies_from_profiled_text(
                text,
                expected_record_count=2,
                expected_taxonomy_count=3,
                expected_value_set_sha256=_fingerprint({"A", "B"}),
            )
        with self.assertRaisesRegex(
            subject.GreeceTaxonomyMappingJoinError, "fingerprint changed"
        ):
            subject._extract_taxonomies_from_profiled_text(
                text,
                expected_record_count=2,
                expected_taxonomy_count=2,
                expected_value_set_sha256="0" * 64,
            )

    def test_receipt_profile_gate_precedes_literal_extraction(self) -> None:
        path = subject._CANONICAL_RECEIPTS[0][0]
        with (
            patch.object(
                subject.greece_source,
                "profile_verified_csv_bytes",
                side_effect=subject.greece_source.GreeceExposureCsvProfileError(
                    "receipt mismatch"
                ),
            ),
            patch.object(subject, "_extract_taxonomies_from_profiled_text") as extract,
        ):
            with self.assertRaisesRegex(
                subject.GreeceTaxonomyMappingJoinError, "receipt/profile gate"
            ):
                subject._extract_verified_taxonomies(
                    b"not trusted", repository_path=path
                )
        extract.assert_not_called()

    def test_profile_drift_fails_before_literal_extraction(self) -> None:
        path, byte_count, sha256 = subject._CANONICAL_RECEIPTS[0]
        facts = subject._FROZEN_PROFILE_FACTS[path]
        profile = {
            "schema_version": subject.greece_source.generic_csv.SCHEMA_VERSION,
            "parser": {"encoding": "utf-8", "bom_present": False, "delimiter": ","},
            "record_count": facts["record_count"],
            "header": list(subject.EXPECTED_HEADER),
            "columns": [
                {
                    "name": "taxonomy",
                    "record_count": facts["record_count"],
                    "empty_count": 0,
                    "nonempty_count": facts["record_count"],
                    "distinct_count": facts["taxonomy_count"],
                    "exact_value_set_sha256": "0" * 64,
                    "decimal_summary": {
                        "leading_or_trailing_whitespace_count": 0
                    },
                }
            ],
            "raw_rows_returned": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
        }
        evidence = {
            "repository_path": path,
            "byte_count": byte_count,
            "sha256": sha256,
            "profile": profile,
        }
        with (
            patch.object(
                subject.greece_source,
                "profile_verified_csv_bytes",
                return_value=evidence,
            ),
            patch.object(subject, "_extract_taxonomies_from_profiled_text") as extract,
        ):
            with self.assertRaisesRegex(
                subject.GreeceTaxonomyMappingJoinError,
                "taxonomy profile drifted",
            ):
                subject._extract_verified_taxonomies(
                    b"already profiled", repository_path=path
                )
        extract.assert_not_called()

    def test_frozen_exposure_authority_drift_fails_closed(self) -> None:
        with patch.object(subject.greece_source, "COMMIT_SHA", "0" * 40):
            with self.assertRaisesRegex(
                subject.GreeceTaxonomyMappingJoinError, "source authority drifted"
            ):
                subject._require_frozen_exposure_authority()
        drifted = list(subject._CANONICAL_RECEIPTS)
        drifted[0] = (drifted[0][0], drifted[0][1] + 1, drifted[0][2])
        with patch.object(subject.greece_source, "RECEIPTS", tuple(drifted)):
            with self.assertRaisesRegex(
                subject.GreeceTaxonomyMappingJoinError, "receipt authority drifted"
            ):
                subject._require_frozen_exposure_authority()

    def test_bundle_must_contain_exact_three_paths(self) -> None:
        paths = [path for path, _, _ in subject._CANONICAL_RECEIPTS]
        with self.assertRaisesRegex(
            subject.GreeceTaxonomyMappingJoinError, "frozen receipt set"
        ):
            subject.join_verified_greece_taxonomy_mapping(
                {paths[0]: b"a", paths[1]: b"b"}, b"mapping"
            )

    def test_mapping_authority_is_checked_before_exposure_extraction(self) -> None:
        bundle = {path: b"x" for path, _, _ in subject._CANONICAL_RECEIPTS}
        with (
            patch.object(
                subject.exact_join,
                "_require_frozen_mapping_authority",
                side_effect=subject.exact_join.KosovoMappingJoinError("drift"),
            ),
            patch.object(subject, "_extract_verified_taxonomies") as extract,
        ):
            with self.assertRaisesRegex(
                subject.GreeceTaxonomyMappingJoinError, "mapping authority drifted"
            ):
                subject.join_verified_greece_taxonomy_mapping(bundle, b"mapping")
        extract.assert_not_called()

    def test_public_result_is_exhaustive_sector_aware_and_keeps_ceiling_false(
        self,
    ) -> None:
        paths = [path for path, _, _ in subject._CANONICAL_RECEIPTS]
        extracted = {
            paths[0]: {
                "repository_path": paths[0],
                "exposure_class": "commercial",
                "record_count": 2,
                "taxonomy_count": 2,
                "taxonomy_value_set_sha256": "a" * 64,
                "taxonomies": ["A", "B"],
            },
            paths[1]: {
                "repository_path": paths[1],
                "exposure_class": "industrial",
                "record_count": 1,
                "taxonomy_count": 1,
                "taxonomy_value_set_sha256": "b" * 64,
                "taxonomies": ["B"],
            },
            paths[2]: {
                "repository_path": paths[2],
                "exposure_class": "residential",
                "record_count": 1,
                "taxonomy_count": 1,
                "taxonomy_value_set_sha256": "c" * 64,
                "taxonomies": ["C"],
            },
        }
        base_records = [
            {
                "taxonomy": "A",
                "status": "resolved",
                "reason_code": "exact_mapping_rows_valid",
                "targets": [{"risk_id": "RISK_A", "weight": "1"}],
            },
            {
                "taxonomy": "B",
                "status": "unsupported",
                "reason_code": "no_exact_mapping_row",
                "targets": [],
            },
            {
                "taxonomy": "C",
                "status": "ambiguous",
                "reason_code": "weights_outside_openquake_precision",
                "targets": [],
            },
        ]
        bundle = {path: b"synthetic" for path in paths}
        with (
            patch.object(
                subject,
                "_extract_verified_taxonomies",
                side_effect=lambda raw, repository_path: extracted[repository_path],
            ),
            patch.object(
                subject.exact_join,
                "_join_exact_taxonomies",
                return_value=base_records,
            ) as join,
        ):
            result = subject.join_verified_greece_taxonomy_mapping(
                bundle, b"mapping"
            )

        join.assert_called_once_with(
            ["A", "B", "C"],
            b"mapping",
            expected_byte_count=subject.exact_join._MAPPING_BYTE_COUNT,
            expected_sha256=subject.exact_join._MAPPING_SHA256,
        )
        self.assertEqual(
            result["classification_counts"],
            {"resolved": 1, "unsupported": 1, "ambiguous": 1},
        )
        self.assertEqual(result["taxonomy_union_count"], 3)
        self.assertFalse(result["all_taxonomies_resolved"])
        self.assertEqual(result["mapping_target_risk_ids"], ["RISK_A"])
        self.assertEqual(
            result["records"][0]["exposure_classes"], ["commercial"]
        )
        self.assertEqual(
            result["records"][1]["exposure_classes"],
            ["commercial", "industrial"],
        )
        self.assertFalse(result["normalization_applied"])
        self.assertFalse(result["wildcard_or_fallback_matching_applied"])
        self.assertFalse(result["taxonomy_semantics_verified"])
        self.assertFalse(result["bounded_derived_disclosure_authorized"])
        self.assertFalse(result["vulnerability_file_selection_authorized"])
        self.assertFalse(result["vulnerability_imt_selection_verified"])
        self.assertFalse(result["hazard_compatibility_verified"])
        self.assertFalse(result["ground_up_loss_executed"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_exact_mapping_join_failure_is_wrapped_without_fallback(self) -> None:
        paths = [path for path, _, _ in subject._CANONICAL_RECEIPTS]
        bundle = {path: b"synthetic" for path in paths}
        extracted = [
            {
                "repository_path": path,
                "exposure_class": subject._FROZEN_PROFILE_FACTS[path][
                    "exposure_class"
                ],
                "record_count": 1,
                "taxonomy_count": 1,
                "taxonomy_value_set_sha256": "a" * 64,
                "taxonomies": [f"T{index}"],
            }
            for index, path in enumerate(paths)
        ]
        with (
            patch.object(
                subject,
                "_extract_verified_taxonomies",
                side_effect=extracted,
            ),
            patch.object(
                subject.exact_join,
                "_join_exact_taxonomies",
                side_effect=subject.exact_join.KosovoMappingJoinError(
                    "bad mapping"
                ),
            ),
        ):
            with self.assertRaisesRegex(
                subject.GreeceTaxonomyMappingJoinError, "failed closed"
            ):
                subject.join_verified_greece_taxonomy_mapping(
                    bundle, b"mapping"
                )


if __name__ == "__main__":
    unittest.main()
