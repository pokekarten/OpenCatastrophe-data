# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_source_access import SourceAccessError, load_strict_json_bytes, validate_contract


ROOT = Path(__file__).resolve().parents[1]


class SourceAccessNetworkBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pegel = load_strict_json_bytes(
            (ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json").read_bytes()
        )

    def mutated(self) -> dict:
        return copy.deepcopy(self.pegel)

    def test_unicode_idna_loopback_spellings_fail_closed(self) -> None:
        for host in ("ⓛⓞⓒⓐⓛⓗⓞⓢⓣ", "ｌｏｃａｌｈｏｓｔ", "127。0。0。1"):
            with self.subTest(host=host):
                contract = self.mutated()
                contract["service_root"] = f"https://{host}"
                with self.assertRaisesRegex(SourceAccessError, "ASCII/IDNA-canonical"):
                    validate_contract(contract)

    def test_active_probe_requires_concrete_service_root(self) -> None:
        contract = self.mutated()
        contract["service_root"] = None
        with self.assertRaisesRegex(SourceAccessError, "concrete HTTPS service_root"):
            validate_contract(contract)

    def test_build_adapter_now_requires_concrete_service_root_even_without_probe(self) -> None:
        contract = self.mutated()
        contract["service_root"] = None
        contract["status"] = "documented_only"
        contract["probe_contract"] = {
            "mode": "none",
            "operation": None,
            "requires_credentials": False,
            "expected_evidence": [],
        }
        # documented_only is independently non-executable, but endpoint identity
        # must fail first for an explicit adapter-now claim.
        contract["implementation_decision"] = "build_adapter_now"
        with self.assertRaisesRegex(SourceAccessError, "concrete HTTPS service_root"):
            validate_contract(contract)

    def test_ftp_interface_cannot_be_active_in_https_only_v1_execution_model(self) -> None:
        contract = self.mutated()
        contract["interface_type"] = "ftp_or_ftps"
        with self.assertRaisesRegex(SourceAccessError, "documentation-only"):
            validate_contract(contract)

    def test_invalid_utf8_percent_encoded_path_fails_closed(self) -> None:
        contract = self.mutated()
        contract["request_contract"]["path_templates"] = ["/safe/%ff"]
        with self.assertRaisesRegex(SourceAccessError, "bounded percent-encoding"):
            validate_contract(contract)

    def test_portable_schema_mirrors_endpoint_state_boundaries(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "source-access-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertIn("\\x21-\\x7E", schema["$defs"]["httpsUrl"]["pattern"])
        rules = json.dumps(schema["allOf"], sort_keys=True)
        self.assertIn("service_root", rules)
        self.assertIn("ftp_or_ftps", rules)
        self.assertIn("build_adapter_now", rules)


if __name__ == "__main__":
    unittest.main()
