# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_transformation_contract", ROOT / "scripts" / "validate_transformation_contract.py"
)
assert SPEC and SPEC.loader
vt = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vt)


def valid_contract() -> dict:
    return {
        "profile_version": "0.1.0",
        "mapping_id": "synthetic-exposure-to-canonical",
        "mapping_version": "0.1.0",
        "source_profile": {"name": "synthetic-exposure", "version": "1.0.0"},
        "target_profile": {"name": "opencat-exposure", "version": "0.1.0"},
        "rules": [
            {
                "rule_id": "location-id",
                "operation": "rename",
                "source_field": "site_code",
                "target_field": "location_id",
                "lossy": False,
                "reversible": True,
            },
            {
                "rule_id": "occupancy-taxonomy",
                "operation": "code_map",
                "source_field": "occupancy",
                "target_field": "taxonomy_code",
                "lossy": False,
                "reversible": True,
                "mapping": [
                    {"from": "R", "to": "RES"},
                    {"from": "C", "to": "COM"},
                ],
            },
            {
                "rule_id": "area-units",
                "operation": "unit_conversion",
                "source_field": "area_ft2",
                "target_field": "area_m2",
                "lossy": False,
                "reversible": True,
                "from_unit": "ft2",
                "to_unit": "m2",
                "factor": 0.09290304,
                "offset": 0.0,
            },
        ],
        "unsupported_fields": ["free_text_note"],
        "semantics": {
            "lossy": True,
            "notes": "free_text_note is intentionally unsupported in v0; all mapped fields preserve declared meaning.",
        },
        "reconciliation_checks": [
            {
                "check_id": "location-count",
                "metric": "count",
                "group_by": [],
                "comparison": {"method": "equal"},
            },
            {
                "check_id": "area-by-taxonomy",
                "metric": "sum",
                "field": "area_m2",
                "group_by": ["taxonomy_code"],
                "comparison": {"method": "absolute_tolerance", "tolerance": 1e-9},
            },
        ],
    }


class TransformationContractTests(unittest.TestCase):
    def test_valid_contract_and_identity(self) -> None:
        payload = valid_contract()
        vt.validate_contract(payload)
        identity = vt.contract_identity(payload)
        self.assertRegex(identity, r"^[a-f0-9]{64}$")

    def test_identity_is_independent_of_json_key_order(self) -> None:
        payload = valid_contract()
        reordered = {key: payload[key] for key in reversed(payload)}
        self.assertEqual(vt.contract_identity(payload), vt.contract_identity(reordered))

    def test_material_mapping_change_changes_identity(self) -> None:
        payload = valid_contract()
        changed = copy.deepcopy(payload)
        changed["rules"][2]["factor"] = 0.1
        self.assertNotEqual(vt.contract_identity(payload), vt.contract_identity(changed))

    def test_top_level_contract_is_closed(self) -> None:
        payload = valid_contract()
        payload["surprise"] = True
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_duplicate_rule_ids_and_targets_fail_closed(self) -> None:
        duplicate_id = valid_contract()
        duplicate_id["rules"][1]["rule_id"] = duplicate_id["rules"][0]["rule_id"]
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(duplicate_id)

        duplicate_target = valid_contract()
        duplicate_target["rules"][1]["target_field"] = duplicate_target["rules"][0]["target_field"]
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(duplicate_target)

    def test_latest_profile_version_is_rejected(self) -> None:
        payload = valid_contract()
        payload["source_profile"]["version"] = "latest"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_bool_is_not_numeric_conversion_or_tolerance(self) -> None:
        payload = valid_contract()
        payload["rules"][2]["factor"] = True
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][1]["comparison"]["tolerance"] = False
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_unit_conversion_requires_declared_unit_change_and_nonzero_factor(self) -> None:
        same_unit = valid_contract()
        same_unit["rules"][2]["to_unit"] = "ft2"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(same_unit)

        zero_factor = valid_contract()
        zero_factor["rules"][2]["factor"] = 0
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(zero_factor)

    def test_reversible_code_map_must_be_one_to_one(self) -> None:
        payload = valid_contract()
        payload["rules"][1]["mapping"][1]["to"] = "RES"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_unsupported_fields_cannot_also_be_mapped(self) -> None:
        payload = valid_contract()
        payload["unsupported_fields"] = ["site_code"]
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_lossiness_cannot_disappear_silently(self) -> None:
        payload = valid_contract()
        payload["semantics"]["lossy"] = False
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_reconciliation_references_only_declared_target_fields(self) -> None:
        payload = valid_contract()
        payload["reconciliation_checks"][1]["group_by"] = ["unknown_target"]
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][1]["field"] = "unknown_target"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_count_check_forbids_field_and_tolerance_contract_is_explicit(self) -> None:
        payload = valid_contract()
        payload["reconciliation_checks"][0]["field"] = "location_id"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][1]["comparison"] = {"method": "absolute_tolerance"}
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text('{"profile_version":"0.1.0","profile_version":"0.1.0"}', encoding="utf-8")
            with self.assertRaises(vt.TransformationContractError):
                vt.load_strict_json(duplicate)

            nonfinite = Path(directory) / "nonfinite.json"
            nonfinite.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaises(vt.TransformationContractError):
                vt.load_strict_json(nonfinite)

    def test_schema_declares_closed_draft_2020_12_contract(self) -> None:
        schema = json.loads((ROOT / "schemas" / "transformation-contract-v0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["profile_version"]["const"], "0.1.0")
        for name in ("profile", "semantics", "copy_rule", "rename_rule", "code_map_rule", "unit_conversion_rule", "comparison", "reconciliation_check"):
            self.assertFalse(schema["$defs"][name]["additionalProperties"], name)


if __name__ == "__main__":
    unittest.main()
