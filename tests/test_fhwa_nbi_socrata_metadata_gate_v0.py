# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic NBI metadata contract tests (no official API retrieved)."""
from __future__ import annotations

from hashlib import sha256
import json
import unittest

from research_runners import fhwa_nbi_socrata_metadata_gate_v0 as gate


def fixture() -> dict:
    required = list(gate.REQUIRED)
    columns = [{"fieldName": key, "dataTypeName": gate.REQUIRED[key] or "text"}
               for key in required]
    columns.extend({"fieldName": f"unreviewed_{i:03}", "dataTypeName": "text"}
                   for i in range(gate.PUBLISHED_COLUMNS_AT_REVIEW - len(required)))
    return {"id": gate.DATASET_ID, "name": "National Bridge Inventory", "viewType": "tabular",
            "columns": columns, "rowsUpdatedAt": 1793550000,
            "sourcePrivateRawBridgeCoordinates": "should not escape in receipt"}


def wire(document: dict) -> bytes:
    return json.dumps(document, separators=(",", ":")).encode("utf-8")


class FHWAOriginalMetadataGateTests(unittest.TestCase):
    def test_exact_offline_metadata_shape_receipt(self):
        original = wire(fixture())
        receipt = gate.audit_metadata(original, expected_sha256=sha256(original).hexdigest())
        self.assertEqual(receipt["published_column_count"], 124)
        self.assertEqual(receipt["required_field_types"]["structure_number_008"], "text")
        self.assertEqual(receipt["original_metadata_sha256"], sha256(original).hexdigest())
        self.assertFalse(receipt["model_input_admitted"])
        self.assertFalse(receipt["all_source_rows_obtained"])
        self.assertFalse(receipt["lat_lon_encoding_and_crs_verified"])
        self.assertNotIn("should not escape", json.dumps(receipt))

    def test_socrata_internal_fields_do_not_change_published_column_count(self):
        f = fixture()
        f["columns"].append({"fieldName": ":id", "dataTypeName": "meta_data"})
        result = gate.audit_metadata(wire(f))
        self.assertEqual(result["socrata_internal_column_count"], 1)
        self.assertEqual(result["published_column_count"], 124)

    def test_missing_core_schema_fails_closed(self):
        for field in gate.REQUIRED:
            f = fixture()
            for col in f["columns"]:
                if col["fieldName"] == field:
                    col["fieldName"] = "replaced_" + field
                    break
            with self.subTest(field=field), self.assertRaisesRegex(gate.Blocked, "required original"):
                gate.audit_metadata(wire(f))

    def test_changed_public_column_count_fails_closed(self):
        f = fixture()
        f["columns"].append({"fieldName": "unexpected_new_field", "dataTypeName": "text"})
        with self.assertRaisesRegex(gate.Blocked, "124-column"):
            gate.audit_metadata(wire(f))
        f = fixture()
        f["columns"].pop()
        with self.assertRaises(gate.Blocked):
            gate.audit_metadata(wire(f))

    def test_duplicate_fields_and_duplicate_json_keys_fail_closed(self):
        f = fixture()
        f["columns"][-1]["fieldName"] = "year"
        with self.assertRaisesRegex(gate.Blocked, "duplicate NBI"):
            gate.audit_metadata(wire(f))
        original = wire(fixture()).replace(b'"id":"pced-83j4"',
                                          b'"id":"pced-83j4","id":"pced-83j4"')
        with self.assertRaisesRegex(gate.Blocked, "duplicate JSON"):
            gate.audit_metadata(original)

    def test_wrong_dataset_type_and_hash_fail_closed(self):
        f = fixture()
        f["id"] = "other-id"
        with self.assertRaisesRegex(gate.Blocked, "identity"):
            gate.audit_metadata(wire(f))
        f = fixture()
        f["viewType"] = "blobby"
        with self.assertRaisesRegex(gate.Blocked, "non-tabular"):
            gate.audit_metadata(wire(f))
        with self.assertRaisesRegex(gate.Blocked, "SHA-256"):
            gate.audit_metadata(wire(fixture()), expected_sha256="0" * 64)
        f = fixture()
        next(col for col in f["columns"] if col["fieldName"] == "year")["dataTypeName"] = "text"
        with self.assertRaisesRegex(gate.Blocked, "type changed"):
            gate.audit_metadata(wire(f))

    def test_invalid_bytes_and_nonfinite_json_rejected(self):
        for original in (b"", b"<html>Error</html>" * 5, b"\xff" * 100,
                         b'{"x": NaN, "y": 4}' * 5, None):
            with self.subTest(original=str(original)[:15]), self.assertRaises(gate.Blocked):
                gate.audit_metadata(original)


if __name__ == "__main__":
    unittest.main()
