# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest
from unittest.mock import patch

from scripts import compare_esrm20_kosovo_source_runtime_decimal as target


def _source_row(index: int, *, total: str | None = None) -> dict[str, str]:
    return {
        "LONGITUDE": f"20.{index}",
        "LATITUDE": f"42.{index}",
        "TAXONOMY": f"SECRET-TAXONOMY-{index}",
        "MACRO_TAXONOMY": "SECRET-MACRO",
        "BUILDINGS": f"{index + 1}.0",
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
        "OCCUPANTS_PER_ASSET_DAY": f"{4 + index}.00",
        "OCCUPANTS_PER_ASSET_NIGHT": f"{8 + index}.0",
        "OCCUPANTS_PER_ASSET_TRANSIT": f"{2 + index}.000",
        "OCCUPANTS_PER_ASSET_AVERAGE": f"{6 + index}",
        "ID_2": f"KS00{index}",
        "NAME_2": f"SECRET-PLACE-{index}",
        "ID_1": f"KS0{index}",
        "NAME_1": f"SECRET-REGION-{index}",
    }


def _runtime_row(source: dict[str, str], index: int, *, structural: str | None = None) -> dict[str, str]:
    return {
        "id": f"asset-{index}",
        "lon": source["LONGITUDE"],
        "lat": source["LATITUDE"],
        "taxonomy": source["TAXONOMY"],
        "number": str(index + 1),
        "structural": structural or str(100 + index),
        "night": str(8 + index),
        "day": str(4 + index),
        "transit": str(2 + index),
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


def _compare(source_rows: list[dict[str, str]], runtime_rows: list[dict[str, str]]) -> dict:
    source_raw = _csv_bytes(target.SOURCE_HEADER, source_rows)
    runtime_raw = _csv_bytes(target.RUNTIME_HEADER, runtime_rows)
    with patch.object(target, "EXPECTED_RECORD_COUNT", len(source_rows)):
        return target.compare_verified_exposure_bytes(
            source_raw,
            runtime_raw,
            source_expected_byte_count=len(source_raw),
            source_expected_sha256=hashlib.sha256(source_raw).hexdigest(),
            runtime_expected_byte_count=len(runtime_raw),
            runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
        )


class KosovoSourceRuntimeDecimalComparatorTests(unittest.TestCase):
    def test_exact_decimal_equality_survives_lexical_format_changes_without_raw_output(self) -> None:
        source_rows = [_source_row(index) for index in range(3)]
        runtime_rows = [_runtime_row(source_rows[index], index) for index in range(3)]

        result = _compare(source_rows, runtime_rows)

        self.assertEqual(result["record_count"], 3)
        self.assertTrue(result["comparison_key"]["exact_key_set_equal"])
        self.assertEqual(result["comparison_key"]["source_unique_count"], 3)
        self.assertFalse(result["comparison_key"]["provider_business_key_authorized"])
        self.assertEqual(len(result["numeric_comparisons"]), len(target.NUMERIC_FIELD_PAIRS))
        for comparison in result["numeric_comparisons"]:
            self.assertTrue(comparison["all_exact_decimal_equal"])
            self.assertEqual(comparison["non_equal_count"], 0)
            self.assertEqual(comparison["maximum_absolute_difference"], "0")
            self.assertEqual(len(comparison["relation_sha256"]), 64)

        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("SECRET-TAXONOMY", encoded)
        self.assertNotIn("SECRET-PLACE", encoded)
        self.assertNotIn("SECRET-REGION", encoded)
        self.assertFalse(result["project186_equivalence_verified"])
        self.assertFalse(result["value_structural_wiring_verified"])
        self.assertFalse(result["source_crs_datum_epsg_verified"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_numeric_mismatch_is_measured_not_promoted_to_semantic_conclusion(self) -> None:
        source_rows = [_source_row(index) for index in range(2)]
        runtime_rows = [_runtime_row(source_rows[index], index) for index in range(2)]
        runtime_rows[1]["structural"] = "100.5"

        result = _compare(source_rows, runtime_rows)
        structural = next(
            comparison
            for comparison in result["numeric_comparisons"]
            if comparison["runtime_field"] == "structural"
        )

        self.assertFalse(structural["all_exact_decimal_equal"])
        self.assertEqual(structural["exact_decimal_equal_count"], 1)
        self.assertEqual(structural["non_equal_count"], 1)
        self.assertEqual(structural["maximum_absolute_difference"], "0.5")
        self.assertFalse(result["value_structural_wiring_verified"])

    def test_duplicate_comparison_key_fails_closed(self) -> None:
        first = _source_row(0)
        duplicate = dict(first)
        duplicate["BUILDINGS"] = "99"
        runtime_first = _runtime_row(first, 0)
        runtime_second_source = _source_row(1)
        runtime_second = _runtime_row(runtime_second_source, 1)

        source_raw = _csv_bytes(target.SOURCE_HEADER, [first, duplicate])
        runtime_raw = _csv_bytes(target.RUNTIME_HEADER, [runtime_first, runtime_second])
        with patch.object(target, "EXPECTED_RECORD_COUNT", 2):
            with self.assertRaisesRegex(target.ExposureRuntimeComparisonError, "source comparison key is not unique"):
                target.compare_verified_exposure_bytes(
                    source_raw,
                    runtime_raw,
                    source_expected_byte_count=len(source_raw),
                    source_expected_sha256=hashlib.sha256(source_raw).hexdigest(),
                    runtime_expected_byte_count=len(runtime_raw),
                    runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
                )

    def test_key_set_mismatch_fails_closed(self) -> None:
        source_rows = [_source_row(index) for index in range(2)]
        runtime_rows = [_runtime_row(source_rows[index], index) for index in range(2)]
        runtime_rows[1]["taxonomy"] = "DIFFERENT-TAXONOMY"

        source_raw = _csv_bytes(target.SOURCE_HEADER, source_rows)
        runtime_raw = _csv_bytes(target.RUNTIME_HEADER, runtime_rows)
        with patch.object(target, "EXPECTED_RECORD_COUNT", 2):
            with self.assertRaisesRegex(target.ExposureRuntimeComparisonError, "comparison key sets differ"):
                target.compare_verified_exposure_bytes(
                    source_raw,
                    runtime_raw,
                    source_expected_byte_count=len(source_raw),
                    source_expected_sha256=hashlib.sha256(source_raw).hexdigest(),
                    runtime_expected_byte_count=len(runtime_raw),
                    runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
                )

    def test_byte_identity_is_checked_before_comparison(self) -> None:
        source = _source_row(0)
        runtime = _runtime_row(source, 0)
        source_raw = _csv_bytes(target.SOURCE_HEADER, [source])
        runtime_raw = _csv_bytes(target.RUNTIME_HEADER, [runtime])

        with patch.object(target, "EXPECTED_RECORD_COUNT", 1):
            with self.assertRaisesRegex(target.ExposureRuntimeComparisonError, "source exposure receipt/structure gate failed"):
                target.compare_verified_exposure_bytes(
                    source_raw,
                    runtime_raw,
                    source_expected_byte_count=len(source_raw),
                    source_expected_sha256="0" * 64,
                    runtime_expected_byte_count=len(runtime_raw),
                    runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
                )


if __name__ == "__main__":
    unittest.main()
