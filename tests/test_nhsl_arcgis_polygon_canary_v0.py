# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic-only tests; no real NHSL feature rows are committed."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.nhsl_arcgis_polygon_canary_v0 import (
    FIELDS, MAX_SAMPLE_BYTES, NHSLServiceError, SAMPLE_URL,
    audit_pair, inspect_files,
)

ROOT = Path(__file__).resolve().parents[1]


def layer() -> dict:
    typed = [{"name": k, "type": t} for k, t in FIELDS.items()]
    # 53 fictional fields to recreate the observed 64-field contract, no provider bytes.
    typed += [{"name": f"SYNTH_{i}", "type": "esriFieldTypeString"} for i in range(53)]
    return {
        "id": 1, "name": "Landuse", "type": "Feature Layer",
        "geometryType": "esriGeometryPolygon",
        "sourceSpatialReference": {"wkid": 102100, "latestWkid": 3857},
        "capabilities": "Map,Data,Query",
        "fields": typed,
    }


def sample() -> dict:
    records = []
    for i in range(1, 4):
        # Entirely invented numbers, NOT Quebec/GitHub original source records.
        building = 10000 * i
        contents = 2000 * i
        row = {
            "Sauid": f"SYNTH-SAUID-{i}",
            "E_SauidLat": 49 + i / 10,
            "E_SauidLon": -123 - i / 10,
            "Et_BldgNum": i,
            "Et_BldgArea": i * 1000,
            "Et_StrValue": building / 4,
            "Et_NStrValue": building * 3 / 4,
            "Et_BldgValue": building,
            "Et_ContValue": contents,
            "Et_AssetValue": building + contents,
            "OBJECTID": i,
        }
        records.append({"attributes": row})
    return {
        "displayFieldName": "Sauid",
        "fields": [{"name": k, "type": v} for k, v in FIELDS.items()],
        "features": records,
        "exceededTransferLimit": True,
    }


class TestNHSLArcGISPolygonCanary(unittest.TestCase):
    def test_three_synthetic_aggregates_never_admit_oed(self) -> None:
        receipt = audit_pair(layer(), sample(), "a" * 64, "b" * 64)
        self.assertEqual(receipt["observed_feature_count"], 3)
        self.assertEqual(receipt["sample_only_totals"]["estimated_buildings"], "6")
        self.assertEqual(receipt["sample_only_totals"]["modeled_total_replacement_cad_2019"], "72000")
        self.assertEqual(receipt["sample_only_totals"]["modeled_building_replacement_cad_2019"], "60000")
        self.assertEqual(receipt["sample_only_totals"]["modeled_contents_replacement_cad_2019"], "12000")
        self.assertEqual(receipt["official_sample_query_url"], SAMPLE_URL)
        self.assertEqual(receipt["live_polygon_field_count"], 64)
        self.assertEqual(receipt["source_dictionary_yaml_field_count"], 66)
        for blocked in (
            "can_export_oed_loc_or_account", "model_input_approved",
            "original_GPKG_v1_bytes_or_excel_dictionary_compared",
            "offline_json_origin_authenticated", "source_rights_independently_reviewed",
        ):
            self.assertIs(receipt[blocked], False, blocked)
        self.assertEqual(receipt["admission_status"], "not_admitted")

    def test_wrong_polygon_layer_and_incorrect_geometry_or_crs_fail(self) -> None:
        for field, value in (
            ("id", 0),
            ("name", "Building archetypes"),
            ("geometryType", "esriGeometryMultipoint"),
            ("capabilities", "Edit"),
            ("type", "Raster Layer"),
        ):
            with self.subTest(field=field):
                bad = layer()
                bad[field] = value
                with self.assertRaises(NHSLServiceError):
                    audit_pair(bad, sample(), "a" * 64, "b" * 64)
        bad = layer()
        bad["sourceSpatialReference"]["latestWkid"] = 4326
        with self.assertRaisesRegex(NHSLServiceError, "CRS"):
            audit_pair(bad, sample(), "a" * 64, "b" * 64)

    def test_layer_field_schema_drift_rejected(self) -> None:
        for modification in ("count", "type", "missing", "duplicate"):
            with self.subTest(modification=modification):
                bad = layer()
                fields = bad["fields"]
                if modification == "count":
                    fields.pop()
                elif modification == "type":
                    fields[0]["type"] = "esriFieldTypeDouble"
                elif modification == "missing":
                    fields[0]["name"] = "RENAMED"
                else:
                    fields[0]["name"] = fields[1]["name"]
                with self.assertRaises(NHSLServiceError):
                    audit_pair(bad, sample(), "a" * 64, "b" * 64)

    def test_wrong_query_projection_and_too_many_features_fail(self) -> None:
        for modification in ("missing_field", "type", "duplicate", "wrong_length"):
            with self.subTest(modification=modification):
                q = sample()
                if modification == "missing_field":
                    q["fields"][0]["name"] = "different"
                elif modification == "type":
                    q["fields"][0]["type"] = "esriFieldTypeDouble"
                elif modification == "duplicate":
                    q["fields"][0]["name"] = q["fields"][1]["name"]
                else:
                    q["features"].append(copy.deepcopy(q["features"][0]))
                with self.assertRaises(NHSLServiceError):
                    audit_pair(layer(), q, "a" * 64, "b" * 64)

    def test_sample_dedup_order_and_geometry_fail(self) -> None:
        for modification in ("duplicate_oid", "duplicate_sauid", "reverse", "geometry", "unexpected_field"):
            with self.subTest(modification=modification):
                q = sample()
                rows = q["features"]
                if modification == "duplicate_oid":
                    rows[1]["attributes"]["OBJECTID"] = rows[0]["attributes"]["OBJECTID"]
                elif modification == "duplicate_sauid":
                    rows[1]["attributes"]["Sauid"] = rows[0]["attributes"]["Sauid"]
                elif modification == "reverse":
                    q["features"] = list(reversed(rows))
                elif modification == "geometry":
                    rows[0]["geometry"] = {"x": -1, "y": 1}
                else:
                    rows[0]["attributes"]["BuildingTIV"] = 123
                with self.assertRaises(NHSLServiceError):
                    audit_pair(layer(), q, "a" * 64, "b" * 64)

    def test_bad_financial_units_fail_through_base_preflight(self) -> None:
        for field, value in (
            ("Et_BldgValue", -1),
            ("Et_NStrValue", 999999),
            ("Et_AssetValue", 5),
            ("E_SauidLat", -35),
            ("Et_BldgNum", False),
            ("Et_BldgArea", 0),
        ):
            with self.subTest(field=field):
                q = sample()
                q["features"][0]["attributes"][field] = value
                with self.assertRaisesRegex(NHSLServiceError, "scientific"):
                    audit_pair(layer(), q, "a" * 64, "b" * 64)

    def test_service_error_missing_limit_and_digest_fail(self) -> None:
        with self.assertRaises(NHSLServiceError):
            audit_pair(layer(), {"error": {"code": 403}}, "a" * 64, "b" * 64)
        q = sample()
        del q["exceededTransferLimit"]
        with self.assertRaisesRegex(NHSLServiceError, "transfer limit"):
            audit_pair(layer(), q, "a" * 64, "b" * 64)
        with self.assertRaisesRegex(NHSLServiceError, "SHA-256"):
            audit_pair(layer(), sample(), "not-a-hash", "b" * 64)

    def test_bounded_local_input_and_command_line_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            source = d / "layer.json"
            rows = d / "three-synthetic-rows.json"
            source.write_text(json.dumps(layer()), encoding="utf-8")
            rows.write_text(json.dumps(sample()), encoding="utf-8")
            receipt = inspect_files(source, rows)
            self.assertEqual(receipt["sample_only_totals"]["estimated_buildings"], "6")
            output = subprocess.run(
                [sys.executable, str(ROOT / "scripts/nhsl_arcgis_polygon_canary_v0.py"),
                 "--layer-json", str(source), "--sample-json", str(rows)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(output.returncode, 0, output.stderr)
            self.assertFalse(json.loads(output.stdout)["can_export_oed_loc_or_account"])
            rows.write_bytes(b"x" * (MAX_SAMPLE_BYTES + 1))
            with self.assertRaisesRegex(NHSLServiceError, "oversized"):
                inspect_files(source, rows)

    def test_duplicate_json_and_nonfinite_numbers_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            first, second = d / "first.json", d / "second.json"
            first.write_text(json.dumps(layer()), encoding="utf-8")
            second.write_text('{"features":[],"features":[]}', encoding="utf-8")
            with self.assertRaisesRegex(NHSLServiceError, "duplicate"):
                inspect_files(first, second)
            second.write_text(json.dumps(sample()).replace('"E_SauidLat": 49.1', '"E_SauidLat": NaN'), encoding="utf-8")
            with self.assertRaisesRegex(NHSLServiceError, "non-finite"):
                inspect_files(first, second)


if __name__ == "__main__":
    unittest.main()
