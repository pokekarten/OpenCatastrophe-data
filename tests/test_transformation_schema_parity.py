# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "transformation-contract-v0.schema.json"


class TransformationSchemaParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_has_durable_versioned_identity(self) -> None:
        self.assertEqual(
            self.schema["$id"],
            "urn:opencatastrophe:schema:transformation-contract:0.2.0",
        )
        self.assertIn("semantic acceptance", self.schema["description"].lower())
        self.assertIn("validate_transformation_contract.py", self.schema["description"])

    def test_version_schema_rejects_known_mutable_identities(self) -> None:
        pattern = re.compile(self.schema["$defs"]["version"]["pattern"])
        for value in ("latest", "Stable", "MAIN", "master", "DeVeLoP"):
            with self.subTest(value=value):
                self.assertIsNone(pattern.fullmatch(value))
        self.assertIsNotNone(pattern.fullmatch("1.2.3"))

    def test_rule_schema_rejects_lossy_and_reversible_together(self) -> None:
        for name in ("copy_rule", "rename_rule", "code_map_rule", "unit_conversion_rule"):
            rule = self.schema["$defs"][name]
            guard = rule["allOf"][0]["not"]
            self.assertEqual(guard["properties"]["lossy"]["const"], True, name)
            self.assertEqual(guard["properties"]["reversible"]["const"], True, name)
            self.assertEqual(guard["required"], ["lossy", "reversible"], name)

    def test_comparison_schema_has_exactly_two_closed_shapes(self) -> None:
        branches = self.schema["$defs"]["comparison"]["oneOf"]
        self.assertEqual(len(branches), 2)
        equal, tolerance = branches
        self.assertFalse(equal["additionalProperties"])
        self.assertEqual(equal["properties"]["method"]["const"], "equal")
        self.assertEqual(equal["required"], ["method"])
        self.assertFalse(tolerance["additionalProperties"])
        self.assertEqual(
            tolerance["properties"]["method"]["const"], "absolute_tolerance"
        )
        self.assertEqual(tolerance["required"], ["method", "tolerance"])

    def test_unit_conversion_schema_rejects_zero_factor(self) -> None:
        factor = self.schema["$defs"]["unit_conversion_rule"]["properties"]["factor"]
        self.assertEqual(factor["not"]["const"], 0)

    def test_v02_declares_one_to_one_rows_and_two_sided_reconciliation(self) -> None:
        self.assertEqual(
            self.schema["properties"]["row_semantics"]["const"], "one_to_one"
        )
        reconciliation = self.schema["$defs"]["reconciliation_check"]
        self.assertIn("source_group_by", reconciliation["required"])
        self.assertIn("target_group_by", reconciliation["required"])
        self.assertIn("relation", reconciliation["required"])
        self.assertIn("source_field", reconciliation["properties"])
        self.assertIn("target_field", reconciliation["properties"])
        self.assertEqual(len(reconciliation["oneOf"]), 3)

    def test_schema_and_validator_share_bounded_text_contracts(self) -> None:
        self.assertEqual(self.schema["$defs"]["bounded_text_64"]["maxLength"], 64)
        self.assertEqual(self.schema["$defs"]["bounded_text_256"]["maxLength"], 256)
        self.assertEqual(self.schema["$defs"]["bounded_text_1000"]["maxLength"], 1000)


if __name__ == "__main__":
    unittest.main()
