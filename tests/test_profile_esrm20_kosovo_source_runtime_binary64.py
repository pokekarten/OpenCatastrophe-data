# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest
from unittest.mock import patch

from scripts import compare_esrm20_kosovo_exposure_runtime as comparison
from scripts import profile_esrm20_kosovo_source_runtime_binary64 as target


def _source_row(
    index: int,
    *,
    buildings: str | None = None,
    total: str | None = None,
    day: str | None = None,
    night: str | None = None,
    transit: str | None = None,
) -> dict[str, str]:
    return {
        "LONGITUDE": f"20.{index}",
        "LATITUDE": f"42.{index}",
        "TAXONOMY": f"SECRET-TAXONOMY-{index}",
        "MACRO_TAXONOMY": "SECRET-MACRO",
        "BUILDINGS": buildings or f"{index + 1}.0",
        "DWELLINGS": f"{index + 2}",
        "OCCUPANCY": "RES",
        "OCCUPANCY_TYPE": "All",
        "SETTLEMENT_TYPE": "URBAN",
        "AREA_PER_DWELLING_SQM": "80",
        "COST_PER_AREA_EUR": "1000",
        "TOTAL_REPL_COST_EUR": total or f"{100 + index}.00",
        "COST_STRUCTURAL_EUR": "60",
        "COST_NONSTRUCTURAL_EUR": "20",
        "COST_CONTENTS_EUR": "20",
        "OCCUPANTS_PER_ASSET": f"{8 + index}",
        "OCCUPANTS_PER_ASSET_DAY": day or f"{4 + index}.00",
        "OCCUPANTS_PER_ASSET_NIGHT": night or f"{8 + index}.0",
        "OCCUPANTS_PER_ASSET_TRANSIT": transit or f"{2 + index}.000",
        "OCCUPANTS_PER_ASSET_AVERAGE": f"{6 + index}",
        "ID_2": f"KS00{index}",
        "NAME_2": f"SECRET-PLACE-{index}",
        "ID_1": f"KS0{index}",
        "NAME_1": f"SECRET-REGION-{index}",
    }


def _runtime_row(
    source: dict[str, str],
    index: int,
    *,
    number: str | None = None,
    structural: str | None = None,
    day: str | None = None,
    night: str | None = None,
    transit: str | None = None,
) -> dict[str, str]:
    return {
        "id": f"asset-{index}",
        "lon": source["LONGITUDE"],
        "lat": source["LATITUDE"],
        "taxonomy": source["TAXONOMY"],
        "number": number or str(index + 1),
        "structural": structural or str(100 + index),
        "night": night or str(8 + index),
        "day": day or str(4 + index),
        "transit": transit or str(2 + index),
        "occupancy": source["OCCUPANCY"],
        "name_2": source["NAME_2"],
        "id_2": source["ID_2"],
        "id_1": source["ID_1"],
        "name_1": source["NAME_1"],
    }


def _csv_bytes(header: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([row[field] for field in header])
    return stream.getvalue().encode("utf-8")


def _profile(
    source_rows: list[dict[str, str]], runtime_rows: list[dict[str, str]]
) -> dict:
    source_raw = _csv_bytes(comparison.SOURCE_HEADER, source_rows)
    runtime_raw = _csv_bytes(comparison.RUNTIME_HEADER, runtime_rows)
    with patch.object(comparison, "EXPECTED_RECORD_COUNT", len(source_rows)):
        return target.profile_verified_exposure_binary64_projection(
            source_raw,
            runtime_raw,
            source_expected_byte_count=len(source_raw),
            source_expected_sha256=hashlib.sha256(source_raw).hexdigest(),
            runtime_expected_byte_count=len(runtime_raw),
            runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
        )


class KosovoSourceRuntimeBinary64ProjectionTests(unittest.TestCase):
    def test_exact_decimal_values_are_consistent_without_authority_uplift(self) -> None:
        source_rows = [_source_row(index) for index in range(3)]
        runtime_rows = [_runtime_row(source_rows[index], index) for index in range(3)]

        result = _profile(source_rows, runtime_rows)

        self.assertEqual(result["record_count"], 3)
        self.assertTrue(result["all_fields_numerically_consistent_with_hypothesis"])
        self.assertFalse(result["canonical_receipt_pair_verified"])
        self.assertFalse(result["hypothesis"]["provider_transform_claimed"])
        for field in result["numeric_fields"]:
            self.assertEqual(field["source_runtime_exact_equal_count"], 3)
            self.assertEqual(field["binary64_projection_match_count"], 3)
            self.assertEqual(field["binary64_projection_mismatch_count"], 0)
            self.assertTrue(field["all_runtime_values_match_binary64_projection"])
            self.assertEqual(len(field["projection_relation_sha256"]), 64)

        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("SECRET-TAXONOMY", encoded)
        self.assertNotIn("SECRET-PLACE", encoded)
        self.assertNotIn("SECRET-REGION", encoded)
        self.assertFalse(result["source_to_runtime_transform_lineage_verified"])
        self.assertFalse(result["provider_generator_identity_verified"])
        self.assertFalse(result["runtime_values_substitutable_with_source_values"])
        self.assertFalse(result["source_runtime_semantic_equivalence_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_binary64_shortest_roundtrip_can_explain_exact_decimal_mismatch(self) -> None:
        source = _source_row(0, total="1000000.0000000004")
        runtime = _runtime_row(source, 0, structural="1000000.0000000003")

        result = _profile([source], [runtime])
        structural = next(
            item for item in result["numeric_fields"] if item["runtime_field"] == "structural"
        )

        self.assertEqual(structural["source_runtime_exact_equal_count"], 0)
        self.assertEqual(structural["binary64_projection_match_count"], 1)
        self.assertEqual(structural["binary64_projection_mismatch_count"], 0)
        self.assertTrue(structural["all_runtime_values_match_binary64_projection"])
        self.assertTrue(result["all_fields_numerically_consistent_with_hypothesis"])
        self.assertFalse(result["source_to_runtime_transform_lineage_verified"])

    def test_unexplained_numeric_change_remains_explicit_mismatch(self) -> None:
        source = _source_row(0, total="100.0000000004")
        runtime = _runtime_row(source, 0, structural="100.0000000003")

        result = _profile([source], [runtime])
        structural = next(
            item for item in result["numeric_fields"] if item["runtime_field"] == "structural"
        )

        self.assertEqual(structural["source_runtime_exact_equal_count"], 0)
        self.assertEqual(structural["binary64_projection_match_count"], 0)
        self.assertEqual(structural["binary64_projection_mismatch_count"], 1)
        self.assertFalse(structural["all_runtime_values_match_binary64_projection"])
        self.assertFalse(result["all_fields_numerically_consistent_with_hypothesis"])

    def test_projection_uses_shortest_roundtrip_binary64_representation(self) -> None:
        projected, binary64_hex = target._project_source_token(
            "12345678.123456789", field="probe"
        )
        self.assertEqual(str(projected), "12345678.12345679")
        self.assertRegex(binary64_hex, r"^0x[0-9a-f]+\.[0-9a-f]+p[+-][0-9]+$")

    def test_nonfinite_or_negative_projection_input_fails_closed(self) -> None:
        for value in ("NaN", "Infinity", "-1"):
            with self.subTest(value=value):
                with self.assertRaises(target.KosovoBinary64ProjectionError):
                    target._project_source_token(value, field="probe")

    def test_byte_identity_is_checked_before_projection(self) -> None:
        source = _source_row(0)
        runtime = _runtime_row(source, 0)
        source_raw = _csv_bytes(comparison.SOURCE_HEADER, [source])
        runtime_raw = _csv_bytes(comparison.RUNTIME_HEADER, [runtime])

        with patch.object(comparison, "EXPECTED_RECORD_COUNT", 1):
            with self.assertRaisesRegex(
                comparison.ExposureRuntimeComparisonError,
                "source exposure receipt/structure gate failed",
            ):
                target.profile_verified_exposure_binary64_projection(
                    source_raw,
                    runtime_raw,
                    source_expected_byte_count=len(source_raw),
                    source_expected_sha256="0" * 64,
                    runtime_expected_byte_count=len(runtime_raw),
                    runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
                )


if __name__ == "__main__":
    unittest.main()
