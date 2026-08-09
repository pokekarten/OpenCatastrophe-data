# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_transformation_contract", ROOT / "scripts" / "validate_transformation_contract.py"
)
assert SPEC and SPEC.loader
vt = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = vt
SPEC.loader.exec_module(vt)


def valid_contract() -> dict:
    return {
        "profile_version": "0.2.0",
        "mapping_id": "synthetic-exposure-to-canonical",
        "mapping_version": "0.2.0",
        "source_profile": {"name": "synthetic-exposure", "version": "1.0.0"},
        "target_profile": {"name": "opencat-exposure", "version": "0.2.0"},
        "row_semantics": "one_to_one",
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
            "notes": "free_text_note is intentionally unsupported; mapped fields preserve declared meaning.",
        },
        "reconciliation_checks": [
            {
                "check_id": "location-count",
                "metric": "count",
                "source_group_by": [],
                "target_group_by": [],
                "relation": {"kind": "equal"},
                "comparison": {"method": "equal"},
            },
            {
                "check_id": "area-by-taxonomy",
                "metric": "sum",
                "source_field": "area_ft2",
                "target_field": "area_m2",
                "source_group_by": ["occupancy"],
                "target_group_by": ["taxonomy_code"],
                "relation": {
                    "kind": "affine",
                    "factor": 0.09290304,
                    "offset_per_record": 0.0,
                },
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

    def test_material_mapping_change_changes_identity_when_reconciliation_changes_with_it(self) -> None:
        payload = valid_contract()
        changed = copy.deepcopy(payload)
        changed["rules"][2]["factor"] = 0.1
        changed["reconciliation_checks"][1]["relation"]["factor"] = 0.1
        self.assertNotEqual(vt.contract_identity(payload), vt.contract_identity(changed))

    def test_top_level_contract_is_closed_and_row_semantics_are_explicit(self) -> None:
        payload = valid_contract()
        payload["surprise"] = True
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["row_semantics"] = "filtering_allowed"
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

    def test_mutable_versions_are_rejected_everywhere(self) -> None:
        for alias in ("latest", "stable", "main", "master", "develop", "LaTeSt"):
            for location in ("mapping", "source", "target"):
                payload = valid_contract()
                if location == "mapping":
                    payload["mapping_version"] = alias
                elif location == "source":
                    payload["source_profile"]["version"] = alias
                else:
                    payload["target_profile"]["version"] = alias
                with self.subTest(alias=alias, location=location), self.assertRaises(
                    vt.TransformationContractError
                ):
                    vt.validate_contract(payload)

    def test_version_format_rejects_whitespace_and_control_characters(self) -> None:
        for value in (" 1.0.0", "1.0.0 ", "1.0\n0"):
            payload = valid_contract()
            payload["source_profile"]["version"] = value
            with self.subTest(value=value), self.assertRaises(vt.TransformationContractError):
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

    def test_numeric_overflow_fails_closed(self) -> None:
        payload = valid_contract()
        payload["rules"][2]["factor"] = 10**10000
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

    def test_lossy_rule_cannot_claim_reversibility(self) -> None:
        payload = valid_contract()
        payload["rules"][0]["lossy"] = True
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_reversible_code_map_must_be_one_to_one(self) -> None:
        payload = valid_contract()
        payload["rules"][1]["mapping"][1]["to"] = "RES"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_code_values_units_and_notes_follow_schema_bounds(self) -> None:
        payload = valid_contract()
        payload["rules"][1]["mapping"][0]["from"] = "x" * 257
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["rules"][2]["from_unit"] = "u" * 65
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["semantics"]["notes"] = "n" * 1001
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

    def test_count_reconciliation_is_two_sided_and_row_preserving(self) -> None:
        payload = valid_contract()
        payload["reconciliation_checks"][0]["source_field"] = "site_code"
        payload["reconciliation_checks"][0]["target_field"] = "location_id"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][0]["relation"] = {
            "kind": "affine",
            "factor": 1.0,
            "offset_per_record": 0.0,
        }
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_sum_reconciliation_requires_explicit_source_and_target_fields(self) -> None:
        payload = valid_contract()
        del payload["reconciliation_checks"][1]["source_field"]
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        del payload["reconciliation_checks"][1]["target_field"]
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_unit_sum_relation_must_match_declared_conversion(self) -> None:
        payload = valid_contract()
        payload["reconciliation_checks"][1]["relation"]["factor"] = 1.0
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][1]["relation"]["offset_per_record"] = 1.0
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][1]["relation"] = {"kind": "equal"}
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_sum_is_not_defined_for_code_mapping(self) -> None:
        payload = valid_contract()
        check = payload["reconciliation_checks"][1]
        check["source_field"] = "occupancy"
        check["target_field"] = "taxonomy_code"
        check["source_group_by"] = []
        check["target_group_by"] = []
        check["relation"] = {"kind": "equal"}
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_grouped_reconciliation_requires_aligned_lossless_mapping(self) -> None:
        payload = valid_contract()
        payload["reconciliation_checks"][1]["target_group_by"] = []
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][1]["target_group_by"] = ["location_id"]
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["rules"][1]["reversible"] = False
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_non_count_field_metrics_require_lossless_reversible_mapping(self) -> None:
        payload = valid_contract()
        check = payload["reconciliation_checks"][1]
        check["metric"] = "unique_count"
        check["source_field"] = "occupancy"
        check["target_field"] = "taxonomy_code"
        check["source_group_by"] = []
        check["target_group_by"] = []
        check["relation"] = {"kind": "equal"}
        vt.validate_contract(payload)

        payload["rules"][1]["reversible"] = False
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_comparison_tolerance_shape_is_unambiguous(self) -> None:
        payload = valid_contract()
        payload["reconciliation_checks"][0]["comparison"] = {
            "method": "equal",
            "tolerance": 0.0,
        }
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][1]["comparison"] = {
            "method": "absolute_tolerance"
        }
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_reconciliation_references_only_declared_source_and_target_fields(self) -> None:
        payload = valid_contract()
        payload["reconciliation_checks"][1]["source_field"] = "unknown_source"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

        payload = valid_contract()
        payload["reconciliation_checks"][1]["target_field"] = "unknown_target"
        with self.assertRaises(vt.TransformationContractError):
            vt.validate_contract(payload)

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text(
                '{"profile_version":"0.2.0","profile_version":"0.2.0"}',
                encoding="utf-8",
            )
            with self.assertRaises(vt.TransformationContractError):
                vt.load_strict_json(duplicate)

            nonfinite = Path(directory) / "nonfinite.json"
            nonfinite.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaises(vt.TransformationContractError):
                vt.load_strict_json(nonfinite)

    def test_schema_declares_closed_draft_2020_12_contract_and_v02_semantics(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "transformation-contract-v0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(
            schema["$id"], "urn:opencatastrophe:schema:transformation-contract:0.2.0"
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["profile_version"]["const"], "0.2.0")
        self.assertEqual(schema["properties"]["row_semantics"]["const"], "one_to_one")
        self.assertEqual(len(schema["$defs"]["comparison"]["oneOf"]), 2)
        self.assertEqual(len(schema["$defs"]["reconciliation_check"]["oneOf"]), 3)
        for name in (
            "profile",
            "semantics",
            "copy_rule",
            "rename_rule",
            "code_map_rule",
            "unit_conversion_rule",
            "reconciliation_check",
        ):
            self.assertFalse(schema["$defs"][name]["additionalProperties"], name)
        for branch in schema["$defs"]["comparison"]["oneOf"]:
            self.assertFalse(branch["additionalProperties"])

    def test_schema_version_pattern_rejects_mutable_aliases(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "transformation-contract-v0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        pattern = re.compile(schema["$defs"]["version"]["pattern"])
        for alias in ("latest", "Stable", "MAIN", "master", "DeVeLoP"):
            with self.subTest(alias=alias):
                self.assertIsNone(pattern.fullmatch(alias))
        self.assertIsNotNone(pattern.fullmatch("1.2.3"))


if __name__ == "__main__":
    unittest.main()
