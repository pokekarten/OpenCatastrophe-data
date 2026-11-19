# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only negative and conservation tests of NHSL -> OED staging."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.nhsl_oed_staging_preflight_v0 import (
    NHSLStagingError, MAX_JSON_BYTES, examine_row, inspect_file,
)

ROOT = Path(__file__).resolve().parents[1]


def example() -> dict[str, object]:
    """Invented values; source-shaped keys, zero actual NHSL records."""
    return {
        "Sauid": "SYNTH-SAUID-001",
        "E_SauidLat": "49.25",
        "E_SauidLon": "-123.10",
        "Et_BldgNum": "2.5",
        "Et_BldgArea": "2000",
        "Et_StrValue": "150000.00",
        "Et_NStrValue": "50000.00",
        "Et_BldgValue": "200000.00",
        "Et_ContValue": "40000.00",
        "Et_AssetValue": "240000.00",
        "E_LandUse": "synthetic mixed use (untrusted auxiliary field)",
    }


class TestNHSLStaging(unittest.TestCase):
    def test_synthetic_crosswalk_is_non_admission_and_no_oed_export(self) -> None:
        o = examine_row(example())
        self.assertEqual(o["aggregated_buildings_estimated"], "2.5")
        self.assertTrue(o["aggregated_building_count_nonintegral"])
        self.assertEqual(o["monetary_unit"], "CAD")
        self.assertEqual(o["monetary_base_year"], 2019)
        self.assertEqual(o["replacement_cost_components_cad_2019"]["assets_total"], "240000.00")
        self.assertIn("centroid", o["settled_area_centroid"]["spatial_role"])
        self.assertFalse(o["can_export_oed_loc_or_account"])
        self.assertFalse(o["model_input_approved"])
        self.assertFalse(o["source_rights_reviewed"])
        self.assertFalse(o["source_bytes_acquired_by_this_program"])
        self.assertEqual(o["admission_status"], "not_admitted")
        self.assertIn("BuildingTIV", o["oed_candidate_field_lineage"])
        self.assertNotIn("BuildingTIV", o)
        self.assertIn("LocPerilsCovered", o["unavailable_from_nhsl"])

    def test_rounded_cents_allowed_not_arbitrary_disagreement(self) -> None:
        d = example()
        d["Et_AssetValue"] = "240000.01"
        self.assertEqual(examine_row(d)["admission_status"], "not_admitted")
        d["Et_AssetValue"] = "240000.03"
        with self.assertRaisesRegex(NHSLStagingError, "asset value"):
            examine_row(d)
        d = example()
        d["Et_BldgValue"] = "199999.90"
        d["Et_AssetValue"] = "239999.90"
        with self.assertRaisesRegex(NHSLStagingError, "building value"):
            examine_row(d)

    def test_missing_and_mixed_insurance_fields_rejected(self) -> None:
        d = example()
        d.pop("Et_BldgValue")
        with self.assertRaisesRegex(NHSLStagingError, "missing"):
            examine_row(d)
        for key, value in (
            ("BuildingTIV", "200000"),
            ("AccNumber", "FAKE-ACCOUNT"),
            ("LocPerilsCovered", "AA1"),
            ("OEDVersion", "5.0.0"),
        ):
            d = example()
            d[key] = value
            with self.subTest(field=key), self.assertRaisesRegex(NHSLStagingError, "insurance/OED"):
                examine_row(d)

    def test_missing_insurer_terms_cannot_be_inferred(self) -> None:
        d = example()
        d["Et_BldgNum"] = "3"
        receipt = examine_row(d)
        self.assertEqual(receipt["aggregated_buildings_estimated"], "3")
        self.assertFalse(receipt["aggregated_building_count_nonintegral"])
        for value in receipt["unavailable_from_nhsl"]:
            self.assertTrue(value)
        self.assertNotIn("PortNumber", receipt)
        self.assertNotIn("AccNumber", receipt)
        self.assertNotIn("LocNumber", receipt)

    def test_coordinate_issues_rejected(self) -> None:
        for key, value in (
            ("E_SauidLat", "-123.1"),
            ("E_SauidLon", "49.25"),
            ("E_SauidLon", "-181"),
            ("E_SauidLat", "NaN"),
            ("E_SauidLat", "Infinity"),
            ("E_SauidLon", False),
        ):
            d = example()
            d[key] = value
            with self.subTest(field=key, value=value), self.assertRaises(NHSLStagingError):
                examine_row(d)

    def test_negative_missing_unbounded_or_non_finite_values_rejected(self) -> None:
        for key, value in (
            ("Et_AssetValue", "-1"),
            ("Et_StrValue", "NaN"),
            ("Et_ContValue", "Infinity"),
            ("Et_BldgNum", -2),
            ("Et_BldgArea", "-3"),
            ("Et_AssetValue", "1000000000000000000"),
            ("Et_NStrValue", True),
            ("Et_BldgNum", "x" * 50),
        ):
            d = example()
            d[key] = value
            with self.subTest(field=key), self.assertRaises(NHSLStagingError):
                examine_row(d)

    def test_no_asset_value_or_area_with_zero_buildings(self) -> None:
        d = example()
        d["Et_BldgNum"] = "0"
        with self.assertRaisesRegex(NHSLStagingError, "zero estimated buildings"):
            examine_row(d)
        d = example()
        d["Et_BldgArea"] = "0"
        with self.assertRaisesRegex(NHSLStagingError, "missing finished floor area"):
            examine_row(d)

    def test_zero_aggregate_is_non_admitted(self) -> None:
        d = example()
        for name in ("Et_BldgNum", "Et_BldgArea", "Et_StrValue", "Et_NStrValue",
                     "Et_BldgValue", "Et_ContValue", "Et_AssetValue"):
            d[name] = "0"
        self.assertFalse(examine_row(d)["can_export_oed_loc_or_account"])

    def test_id_must_remain_nonempty_string(self) -> None:
        for id_value in ("", 1234, "contains a space", "x" * 49):
            d = example()
            d["Sauid"] = id_value
            with self.subTest(id=id_value), self.assertRaisesRegex(NHSLStagingError, "Sauid"):
                examine_row(d)

    def test_duplicate_json_nonfinite_and_invalid_utf8_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "row.json"
            p.write_text('{"Sauid":"A","Sauid":"B"}', encoding="utf-8")
            with self.assertRaisesRegex(NHSLStagingError, "duplicate"):
                inspect_file(p)
            p.write_text(json.dumps(example()).replace('"2.5"', 'NaN'), encoding="utf-8")
            with self.assertRaisesRegex(NHSLStagingError, "non-finite"):
                inspect_file(p)
            p.write_bytes(b"\xff")
            with self.assertRaisesRegex(NHSLStagingError, "UTF-8"):
                inspect_file(p)
            p.write_bytes(b"a" * (MAX_JSON_BYTES + 1))
            with self.assertRaisesRegex(NHSLStagingError, "oversized"):
                inspect_file(p)

    def test_cli_success_is_only_local_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.json"
            p.write_text(json.dumps(example()), encoding="utf-8")
            command = [
                sys.executable, str(ROOT / "scripts/nhsl_oed_staging_preflight_v0.py"),
                "--row-json", str(p),
            ]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["source_candidate_id"], "can.nrcan.nhsl.physical-exposure.2016-2020")
            self.assertFalse(receipt["can_export_oed_loc_or_account"])
            self.assertFalse(receipt["model_input_approved"])
            self.assertFalse(receipt["source_bytes_acquired_by_this_program"])


if __name__ == "__main__":
    unittest.main()
