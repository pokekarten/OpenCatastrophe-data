# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest
from decimal import localcontext

from scripts import profile_efehr_kosovo_exposure_value_spatial as target


def _base_row() -> dict[str, str]:
    return {
        "LONGITUDE": "20.5",
        "LATITUDE": "42.5",
        "TAXONOMY": "TEST-TAXONOMY",
        "MACRO_TAXONOMY": "TEST-MACRO",
        "BUILDINGS": "2",
        "DWELLINGS": "4",
        "OCCUPANCY": "RES",
        "OCCUPANCY_TYPE": "RESIDENTIAL",
        "SETTLEMENT_TYPE": "URBAN",
        "AREA_PER_DWELLING_SQM": "80",
        "COST_PER_AREA_EUR": "1000",
        "TOTAL_REPL_COST_EUR": "100",
        "COST_STRUCTURAL_EUR": "60",
        "COST_NONSTRUCTURAL_EUR": "20",
        "COST_CONTENTS_EUR": "20",
        "OCCUPANTS_PER_ASSET": "8",
        "OCCUPANTS_PER_ASSET_DAY": "4",
        "OCCUPANTS_PER_ASSET_NIGHT": "8",
        "OCCUPANTS_PER_ASSET_TRANSIT": "2",
        "OCCUPANTS_PER_ASSET_AVERAGE": "6",
        "ID_2": "KS001",
        "NAME_2": "SECRET_PLACE_TOKEN",
        "ID_1": "KS01",
        "NAME_1": "SECRET_REGION_TOKEN",
    }


def _csv_bytes(
    rows: list[dict[str, str]],
    *,
    header: tuple[str, ...] = target.EXPECTED_HEADER,
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([row.get(field, "") for field in header])
    return stream.getvalue().encode("utf-8")


def _profile(raw: bytes) -> dict:
    return target.profile_verified_exposure_value_spatial(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


class ExposureValueSpatialProfileTests(unittest.TestCase):
    def test_summary_measures_duplicates_ranges_and_cost_residual_without_rows(self) -> None:
        first = _base_row()
        duplicate = dict(first)
        residual = dict(first)
        residual["LONGITUDE"] = "21.25"
        residual["LATITUDE"] = "95"
        residual["TOTAL_REPL_COST_EUR"] = "101"
        residual["BUILDINGS"] = "0"
        residual["DWELLINGS"] = "-1"
        raw = _csv_bytes([first, duplicate, residual])

        profile = _profile(raw)

        self.assertEqual(profile["record_count"], 3)
        self.assertEqual(profile["full_row_duplicates"]["duplicate_record_count"], 1)
        self.assertEqual(
            profile["candidate_key_diagnostics"]["duplicate_record_count"],
            1,
        )
        self.assertFalse(
            profile["candidate_key_diagnostics"]["provider_business_key_authorized"]
        )
        self.assertEqual(
            profile["coordinate_range_diagnostics"][
                "latitude_outside_minus90_plus90_count"
            ],
            1,
        )
        self.assertEqual(profile["numeric_fields"]["BUILDINGS"]["zero_count"], 1)
        self.assertEqual(profile["numeric_fields"]["DWELLINGS"]["negative_count"], 1)
        self.assertEqual(
            profile["replacement_cost_component_diagnostic"]["nonzero_residual_count"],
            1,
        )
        self.assertEqual(
            profile["replacement_cost_component_diagnostic"][
                "maximum_absolute_residual_eur"
            ],
            "1",
        )

        encoded = json.dumps(profile, sort_keys=True)
        self.assertNotIn("SECRET_PLACE_TOKEN", encoded)
        self.assertNotIn("SECRET_REGION_TOKEN", encoded)
        self.assertNotIn("TEST-TAXONOMY", encoded)
        self.assertFalse(profile["raw_rows_returned"])
        self.assertFalse(profile["external_bytes_persisted"])
        self.assertFalse(profile["publication_authorized"])
        self.assertFalse(profile["model_use_authorized"])
        self.assertFalse(profile["crs_identifier_verified"])
        self.assertFalse(profile["valuation_vintage_verified"])
        self.assertFalse(profile["sentinel_semantics_verified"])
        self.assertFalse(profile["row_business_key_verified"])

    def test_high_precision_diagnostics_are_independent_of_ambient_decimal_context(self) -> None:
        exact_total = "123456789012345678901234567890123456789"
        row = _base_row()
        row["TOTAL_REPL_COST_EUR"] = exact_total
        row["COST_STRUCTURAL_EUR"] = "0"
        row["COST_NONSTRUCTURAL_EUR"] = "0"
        row["COST_CONTENTS_EUR"] = "0"
        raw = _csv_bytes([row])

        with localcontext() as context:
            context.prec = 7
            profile = _profile(raw)

        total_summary = profile["numeric_fields"]["TOTAL_REPL_COST_EUR"]
        self.assertEqual(total_summary["minimum"], exact_total)
        self.assertEqual(total_summary["maximum"], exact_total)
        self.assertEqual(
            profile["replacement_cost_component_diagnostic"][
                "maximum_absolute_residual_eur"
            ],
            exact_total,
        )
        self.assertEqual(
            profile["replacement_cost_component_diagnostic"]["nonzero_residual_count"],
            1,
        )

    def test_synthetic_caller_receipt_cannot_assert_frozen_dataset_identity(self) -> None:
        raw = _csv_bytes([_base_row()])
        profile = _profile(raw)

        self.assertNotIn("source_issue", profile)
        self.assertNotIn("dataset_id", profile)
        self.assertNotEqual(profile.get("dataset_id"), target.DATASET_ID)

    def test_receipt_identity_fails_before_invalid_utf8_decode(self) -> None:
        raw = b"\xff"
        with self.assertRaisesRegex(
            target.ExposureValueSpatialProfileError,
            "receipt/structure gate",
        ):
            target.profile_verified_exposure_value_spatial(
                raw,
                expected_byte_count=2,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_exact_header_contract_rejects_drift(self) -> None:
        row = _base_row()
        drifted = list(target.EXPECTED_HEADER)
        drifted[0] = "LON"
        raw = _csv_bytes([row], header=tuple(drifted))
        with self.assertRaisesRegex(
            target.ExposureValueSpatialProfileError,
            "header drifted",
        ):
            _profile(raw)

    def test_nonfinite_and_extreme_exponent_numeric_values_fail_closed(self) -> None:
        row = _base_row()
        row["BUILDINGS"] = "NaN"
        with self.assertRaisesRegex(
            target.ExposureValueSpatialProfileError,
            "non-finite",
        ):
            _profile(_csv_bytes([row]))

        row = _base_row()
        row["BUILDINGS"] = "1e1000"
        with self.assertRaisesRegex(
            target.ExposureValueSpatialProfileError,
            "exponent",
        ):
            _profile(_csv_bytes([row]))

    def test_row_identity_is_length_framed(self) -> None:
        self.assertNotEqual(
            target._row_identity(["ab", "c"]),
            target._row_identity(["a", "bc"]),
        )


if __name__ == "__main__":
    unittest.main()
