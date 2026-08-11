# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_source_access import SourceAccessError, load_strict_json_bytes, validate_contract


ROOT = Path(__file__).resolve().parents[1]


class SourceAccessTermsIdentityTests(unittest.TestCase):
    def test_separate_reviewed_terms_require_authoritative_url(self) -> None:
        path = ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json"
        contract = load_strict_json_bytes(path.read_bytes())
        self.assertEqual(contract["rights_and_policy"]["api_terms_status"], "separate_reviewed")
        self.assertIsNotNone(contract["rights_and_policy"]["terms_url"])

        contract["rights_and_policy"]["terms_url"] = None
        with self.assertRaisesRegex(SourceAccessError, "separate_reviewed API terms require an authoritative terms_url"):
            validate_contract(contract)

    def test_schema_mirrors_separate_reviewed_terms_identity(self) -> None:
        schema = json.loads((ROOT / "schemas" / "source-access-v1.schema.json").read_text(encoding="utf-8"))
        rules = schema["properties"]["rights_and_policy"].get("allOf", [])
        matching = [
            rule
            for rule in rules
            if rule.get("if", {}).get("properties", {}).get("api_terms_status")
            == {"const": "separate_reviewed"}
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(
            matching[0]["then"]["properties"]["terms_url"],
            {"$ref": "#/$defs/httpsUrl"},
        )


if __name__ == "__main__":
    unittest.main()
