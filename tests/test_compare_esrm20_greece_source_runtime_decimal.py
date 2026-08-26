# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest

from scripts import compare_esrm20_greece_exposure_runtime as target


def _source_row(
    index: int, *, total: str | None = None, component: str = "60"
) -> dict[str, str]:
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
        "COST_STRUCTURAL_EUR": component,
        "COST_NONSTRUCTURAL_EUR": "20",
        "COST_CONTENTS_EUR": "20",
        "OCCUPANTS_PER_ASSET": f"{8 + index}",
        "OCCUPANTS_PER_ASSET_DAY": f"{4 + index}.00",
        "OCCUPANTS_PER_ASSET_NIGHT": f"{8 + index}.0",
        "OCCUPANTS_PER_ASSET_TRANSIT": f"{2 + index}.000",
        "OCCUPANTS_PER_ASSET_AVERAGE": f"{6 + index}",
        "ID_2": f"GR00{index}",
        "NAME_2": f"SECRET-PLACE-{index}",
        "ID_1": f"GR0{index}",
        "NAME_1": f"SECRET-REGION-{index}",
    }


def _runtime_row(
    source: dict[str, str], index: int, *, structural: str | None = None
) -> dict[str, str]:
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
        "id_3": f"GR3-{index}",
        "id_3_left": f"L-{index}",
        "name_3": f"SECRET-LEVEL3-{index}",
        "id_3_right": f"R-{index}",
        "id_1": source["ID_1"],
        "name_1": source["NAME_1"],
        "id_2": source["ID_2"],
        "name_2": source["NAME_2"],
    }


def _csv_bytes(header: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([row[field] for field in header])
    return stream.getvalue().encode("utf-8")


def _compare(
    source_rows: list[dict[str, str]], runtime_rows: list[dict[str, str]]
) -> dict:
    source_raw = _csv_bytes(target.SOURCE_HEADER, source_rows)
    runtime_raw = _csv_bytes(target.RUNTIME_HEADER, runtime_rows)
    return target.compare_verified_sector_bytes(
        source_raw,
        runtime_raw,
        sector="residential",
        source_expected_byte_count=len(source_raw),
        source_expected_sha256=hashlib.sha256(source_raw).hexdigest(),
        runtime_expected_byte_count=len(runtime_raw),
        runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
        expected_record_count=len(source_rows),
    )


class GreeceSourceRuntimeDecimalComparatorTests(unittest.TestCase):
    def test_total_candidate_matches_while_component_candidate_is_falsified(
        self,
    ) -> None:
        source_rows = [_source_row(index) for index in range(3)]
        runtime_rows = [
            _runtime_row(source_rows[index], index) for index in range(3)
        ]

        result = _compare(source_rows, runtime_rows)

        total = next(
            item
            for item in result["numeric_comparisons"]
            if item["source_field"] == "TOTAL_REPL_COST_EUR"
        )
        component = next(
            item
            for item in result["numeric_comparisons"]
            if item["source_field"] == "COST_STRUCTURAL_EUR"
        )
        self.assertTrue(total["all_exact_decimal_equal"])
        self.assertEqual(total["non_equal_count"], 0)
        self.assertEqual(total["maximum_absolute_difference"], "0")
        self.assertEqual(
            total["role"], "total_replacement_cost_lineage_candidate"
        )
        self.assertFalse(component["all_exact_decimal_equal"])
        self.assertEqual(
            component["role"], "structural_component_falsification_candidate"
        )
        self.assertEqual(component["non_equal_count"], 3)
        self.assertFalse(result["canonical_receipt_pair_verified"])
        self.assertFalse(result["source_runtime_lineage_verified"])
        self.assertFalse(result["total_replacement_cost_to_structural_verified"])
        self.assertFalse(result["cost_structural_to_structural_verified"])

        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("SECRET-TAXONOMY", encoded)
        self.assertNotIn("SECRET-PLACE", encoded)
        self.assertNotIn("SECRET-REGION", encoded)
        self.assertNotIn("SECRET-LEVEL3", encoded)
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_lexical_decimal_format_does_not_create_difference(self) -> None:
        source_rows = [_source_row(0, total="100.000")]
        runtime_rows = [_runtime_row(source_rows[0], 0, structural="1E+2")]
        result = _compare(source_rows, runtime_rows)
        total = next(
            item
            for item in result["numeric_comparisons"]
            if item["source_field"] == "TOTAL_REPL_COST_EUR"
        )
        self.assertTrue(total["all_exact_decimal_equal"])
        self.assertEqual(total["maximum_absolute_difference"], "0")
        self.assertEqual(len(total["relation_sha256"]), 64)

    def test_total_replacement_mismatch_is_measured_without_tolerance(self) -> None:
        source_rows = [_source_row(index) for index in range(2)]
        runtime_rows = [
            _runtime_row(source_rows[index], index) for index in range(2)
        ]
        runtime_rows[1]["structural"] = "100.5"

        result = _compare(source_rows, runtime_rows)
        total = next(
            item
            for item in result["numeric_comparisons"]
            if item["source_field"] == "TOTAL_REPL_COST_EUR"
        )
        self.assertFalse(total["all_exact_decimal_equal"])
        self.assertEqual(total["exact_decimal_equal_count"], 1)
        self.assertEqual(total["non_equal_count"], 1)
        self.assertEqual(total["maximum_absolute_difference"], "0.5")
        self.assertNotIn("tolerance", total)
        self.assertFalse(result["source_runtime_lineage_verified"])

    def test_duplicate_literal_comparison_key_fails_closed(self) -> None:
        first = _source_row(0)
        duplicate = dict(first)
        duplicate["BUILDINGS"] = "99"
        runtime_first = _runtime_row(first, 0)
        runtime_second_source = _source_row(1)
        runtime_second = _runtime_row(runtime_second_source, 1)
        with self.assertRaisesRegex(
            target.GreeceExposureRuntimeComparisonError,
            "source comparison key is not unique",
        ):
            _compare([first, duplicate], [runtime_first, runtime_second])

    def test_key_set_mismatch_fails_closed_without_normalization(self) -> None:
        source_rows = [_source_row(index) for index in range(2)]
        runtime_rows = [
            _runtime_row(source_rows[index], index) for index in range(2)
        ]
        runtime_rows[1]["taxonomy"] = source_rows[1]["TAXONOMY"].lower()
        with self.assertRaisesRegex(
            target.GreeceExposureRuntimeComparisonError,
            "source/runtime comparison key sets differ",
        ):
            _compare(source_rows, runtime_rows)

    def test_byte_identity_is_checked_before_csv_comparison(self) -> None:
        source = _source_row(0)
        runtime = _runtime_row(source, 0)
        source_raw = _csv_bytes(target.SOURCE_HEADER, [source])
        runtime_raw = _csv_bytes(target.RUNTIME_HEADER, [runtime])
        with self.assertRaisesRegex(
            target.GreeceExposureRuntimeComparisonError,
            "source exposure receipt/structure gate failed",
        ):
            target.compare_verified_sector_bytes(
                source_raw,
                runtime_raw,
                sector="residential",
                source_expected_byte_count=len(source_raw),
                source_expected_sha256="0" * 64,
                runtime_expected_byte_count=len(runtime_raw),
                runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
                expected_record_count=1,
            )

    def test_runtime_header_drift_fails_closed(self) -> None:
        source = _source_row(0)
        runtime = _runtime_row(source, 0)
        source_raw = _csv_bytes(target.SOURCE_HEADER, [source])
        drifted_header = tuple(
            "structural_total" if name == "structural" else name
            for name in target.RUNTIME_HEADER
        )
        runtime["structural_total"] = runtime.pop("structural")
        runtime_raw = _csv_bytes(drifted_header, [runtime])
        with self.assertRaisesRegex(
            target.GreeceExposureRuntimeComparisonError,
            "runtime exposure header drifted",
        ):
            target.compare_verified_sector_bytes(
                source_raw,
                runtime_raw,
                sector="residential",
                source_expected_byte_count=len(source_raw),
                source_expected_sha256=hashlib.sha256(source_raw).hexdigest(),
                runtime_expected_byte_count=len(runtime_raw),
                runtime_expected_sha256=hashlib.sha256(runtime_raw).hexdigest(),
                expected_record_count=1,
            )

    def test_bundle_requires_exact_three_sector_key_set_before_any_parse(self) -> None:
        with self.assertRaisesRegex(
            target.GreeceExposureRuntimeComparisonError,
            "source bundle left frozen sector set",
        ):
            target.compare_verified_bundle_bytes(
                {"residential": b"not-provider-bytes"},
                {sector: b"not-provider-bytes" for sector in target.SECTOR_SPECS},
            )

    def test_unknown_sector_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            target.GreeceExposureRuntimeComparisonError,
            "sector left frozen Greece comparison set",
        ):
            target.compare_verified_sector_bytes(b"x", b"y", sector="all")


if __name__ == "__main__":
    unittest.main()
