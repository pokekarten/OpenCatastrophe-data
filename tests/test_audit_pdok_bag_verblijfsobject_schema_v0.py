# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic JSON Schema metadata fixture only; no BAG feature/address records."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_pdok_bag_verblijfsobject_schema_v0 import (
    BagSchemaError, SCHEMA_ID, SCHEMA_VERSION, audit, main, read_schema,
)


def schema_fixture():
    props = {
        "identificatie": {"type": "string"},
        "oppervlakte": {"type": "integer"},
        "pand": {
            "type": "array",
            "items": {
                "type": "string",
                "x-ogc-role": "reference",
                "x-ogc-collectionId": "pand",
            },
        },
        "status": {"type": "string"},
        "gebruiksdoel": {"type": "string"},
    }
    for field in (
        "postcode", "huisnummer", "huisletter", "toevoeging",
        "hoofdadres_identificatie", "hoofdadres_status",
        "openbare_ruimte_naam", "openbare_ruimte_naam_kort",
        "woonplaats_naam", "provincie_naam",
    ):
        props[field] = {"type": "integer" if field == "huisnummer" else "string"}
    return {
        "$schema": SCHEMA_VERSION,
        "$id": SCHEMA_ID,
        "title": "Verblijfsobject",
        "type": "object",
        "required": ["id"],
        "properties": props,
    }


class BagSchemaContractTests(unittest.TestCase):
    def test_recognises_official_semantics_and_blocks_address_exports(self):
        result = audit(schema_fixture())
        self.assertTrue(result["source_schema_verified"])
        self.assertTrue(result["source_contains_address_fields"])
        self.assertFalse(result["address_fields_permitted_in_exposure_export"])
        self.assertEqual(result["unit_area_type"], "integer")
        self.assertEqual(result["pand_relation"],
                         "array of reference strings to BAG pand collection")
        self.assertFalse(result["building_id_identity_or_mapping_verified"])
        for name in ("source_admitted", "insured_tiv_verified",
                     "replacement_cost_verified", "original_feature_records_queried"):
            self.assertFalse(result[name])
        text = json.dumps(result)
        self.assertNotIn("postcode", text)
        self.assertNotIn("huisnummer", text)

    def test_wrong_provider_or_object_class_rejected(self):
        for field, val in (
            ("$id", "https://evil.example/schema"),
            ("$schema", "http://json-schema.org/draft-07/schema"),
            ("title", "Adres"),
            ("type", "array"),
        ):
            with self.subTest(field=field), self.assertRaises(BagSchemaError):
                item = schema_fixture()
                item[field] = val
                audit(item)

    def test_area_must_be_integer_and_pand_array_reference(self):
        for mutation in ("float-area", "scalar-pand", "wrong-relation", "wrong-collection"):
            item = schema_fixture()
            if mutation == "float-area":
                item["properties"]["oppervlakte"]["type"] = "number"
            elif mutation == "scalar-pand":
                item["properties"]["pand"]["type"] = "string"
            elif mutation == "wrong-relation":
                item["properties"]["pand"]["items"]["x-ogc-role"] = "feature"
            elif mutation == "wrong-collection":
                item["properties"]["pand"]["items"]["x-ogc-collectionId"] = "adres"
            with self.subTest(mutation=mutation), self.assertRaises(BagSchemaError):
                audit(item)

    def test_required_keys_and_sensitive_field_contract_cannot_silently_change(self):
        item = schema_fixture()
        del item["properties"]["postcode"]
        with self.assertRaises(BagSchemaError):
            audit(item)
        item = schema_fixture()
        item["required"] = ["id", "pand"]
        with self.assertRaises(BagSchemaError):
            audit(item)

    def test_cli_on_schema_only_and_duplicate_metadata_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "schema-only.json"
            path.write_text(json.dumps(schema_fixture()), encoding="utf-8")
            self.assertEqual(main(["--schema", str(path)]), 0)
            self.assertTrue(audit(read_schema(path))["source_schema_verified"])
            path.write_text('{"title":"A","title":"B"}', encoding="utf-8")
            with self.assertRaises(BagSchemaError):
                read_schema(path)
            self.assertEqual(main(["--schema", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
