# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
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
            "urn:opencatastrophe:schema:transformation-contract:0.1.0",
        )
        self.assertIn("semantic acceptance", self.schema["description"].lower())
        self.assertIn("validate_transformation_contract.py", self.schema["description"])

    def test_version_schema_rejects_mutable_latest_identity(self) -> None:
        version = self.schema["$defs"]["version"]
        self.assertEqual(version["maxLength"], 64)
        self.assertEqual(version["not"]["pattern"], "^[Ll][Aa][Tt][Ee][Ss][Tt]$")

    def test_rule_schema_rejects_lossy_and_reversible_together(self) -> None:
        for name in ("copy_rule", "rename_rule", "code_map_rule", "unit_conversion_rule"):
            rule = self.schema["$defs"][name]
            guard = rule["allOf"][0]["not"]
            self.assertEqual(guard["properties"]["lossy"]["const"], True, name)
            self.assertEqual(guard["properties"]["reversible"]["const"], True, name)
            self.assertEqual(guard["required"], ["lossy", "reversible"], name)

    def test_comparison_schema_matches_tolerance_shape(self) -> None:
        comparison = self.schema["$defs"]["comparison"]
        clauses = comparison["allOf"]
        self.assertEqual(len(clauses), 2)
        self.assertEqual(
            clauses[0]["if"]["properties"]["method"]["const"],
            "equal",
        )
        self.assertEqual(clauses[0]["then"]["not"]["required"], ["tolerance"])
        self.assertEqual(
            clauses[1]["if"]["properties"]["method"]["const"],
            "absolute_tolerance",
        )
        self.assertEqual(clauses[1]["then"]["required"], ["tolerance"])

    def test_unit_conversion_schema_rejects_zero_factor(self) -> None:
        factor = self.schema["$defs"]["unit_conversion_rule"]["properties"]["factor"]
        self.assertEqual(factor["not"]["const"], 0)

    def test_reconciliation_schema_matches_metric_field_shape(self) -> None:
        reconciliation = self.schema["$defs"]["reconciliation_check"]
        clauses = reconciliation["allOf"]
        self.assertEqual(len(clauses), 2)
        self.assertEqual(
            clauses[0]["if"]["properties"]["metric"]["const"],
            "count",
        )
        self.assertEqual(clauses[0]["then"]["not"]["required"], ["field"])
        self.assertEqual(
            clauses[1]["if"]["properties"]["metric"]["enum"],
            ["sum", "null_count", "unique_count"],
        )
        self.assertEqual(clauses[1]["then"]["required"], ["field"])

    def test_reconciliation_semantics_are_explicitly_projected_target_space(self) -> None:
        top_level = self.schema["properties"]["reconciliation_checks"]["description"].lower()
        check = self.schema["$defs"]["reconciliation_check"]["description"].lower()
        self.assertIn("source-to-target", top_level)
        self.assertIn("target-space", top_level)
        self.assertIn("source-to-target", check)
        self.assertIn("projected target-space", check)


if __name__ == "__main__":
    unittest.main()
