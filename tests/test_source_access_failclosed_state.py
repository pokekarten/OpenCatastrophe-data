# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_source_access import SourceAccessError, load_strict_json_bytes, validate_contract


ROOT = Path(__file__).resolve().parents[1]


class SourceAccessFailClosedStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pegel = load_strict_json_bytes(
            (ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json").read_bytes()
        )

    def mutated(self) -> dict:
        return copy.deepcopy(self.pegel)

    def test_documented_only_cannot_carry_active_probe(self) -> None:
        contract = self.mutated()
        contract["status"] = "documented_only"
        contract["implementation_decision"] = "document_only"
        with self.assertRaisesRegex(SourceAccessError, "requires probe mode none"):
            validate_contract(contract)

    def test_blocked_credentials_cannot_carry_active_probe(self) -> None:
        contract = self.mutated()
        contract["status"] = "blocked_credentials"
        contract["implementation_decision"] = "document_only"
        with self.assertRaisesRegex(SourceAccessError, "requires probe mode none"):
            validate_contract(contract)

    def test_verified_authenticated_requires_authenticated_access(self) -> None:
        contract = self.mutated()
        contract["status"] = "verified_authenticated"
        with self.assertRaisesRegex(SourceAccessError, "requires authenticated access"):
            validate_contract(contract)

    def test_verified_anonymous_requires_active_probe(self) -> None:
        contract = self.mutated()
        contract["status"] = "verified_anonymous"
        contract["probe_contract"] = {
            "mode": "none",
            "operation": None,
            "requires_credentials": False,
            "expected_evidence": [],
        }
        contract["implementation_decision"] = "document_only"
        with self.assertRaisesRegex(SourceAccessError, "requires an active probe"):
            validate_contract(contract)

    def test_active_probe_requires_expected_evidence(self) -> None:
        contract = self.mutated()
        contract["probe_contract"]["expected_evidence"] = []
        with self.assertRaisesRegex(SourceAccessError, "requires non-empty expected evidence"):
            validate_contract(contract)

    def test_legacy_numeric_loopback_spellings_fail_closed(self) -> None:
        for host in ("2130706433", "127.1", "0177.0.0.1", "0x7f000001"):
            with self.subTest(host=host):
                contract = self.mutated()
                contract["service_root"] = f"https://{host}"
                with self.assertRaisesRegex(SourceAccessError, "ambiguous numeric host"):
                    validate_contract(contract)

    def test_dwd_active_recipe_is_probe_ready(self) -> None:
        dwd = load_strict_json_bytes(
            (ROOT / "access" / "dwd.cdc.extreme-wind.http-file.json").read_bytes()
        )
        self.assertEqual(dwd["status"], "probe_ready")
        validate_contract(dwd)

    def test_schema_mirrors_portable_verification_states(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "source-access-v1.schema.json").read_text(encoding="utf-8")
        )
        rules = schema["allOf"]
        serialized = json.dumps(rules, sort_keys=True)
        for marker in (
            "documented_only",
            "blocked_registration",
            "blocked_credentials",
            "verified_anonymous",
            "verified_authenticated",
            "expected_evidence",
        ):
            self.assertIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
