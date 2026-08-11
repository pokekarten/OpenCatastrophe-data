# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest

from scripts.build_source_access_inventory import ROOT
from scripts.validate_source_access import SourceAccessError, validate_contract


class NestedPathEncodingTests(unittest.TestCase):
    def setUp(self) -> None:
        path = ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json"
        self.contract = json.loads(path.read_text(encoding="utf-8"))

    def assert_path_rejected(self, path: str) -> None:
        contract = copy.deepcopy(self.contract)
        contract["request_contract"]["path_templates"] = [path]
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_triple_encoded_traversal_fails_closed(self) -> None:
        self.assert_path_rejected("/safe/%25252e%25252e/secret")

    def test_excessively_nested_traversal_fails_closed(self) -> None:
        encoded = ".."
        for _ in range(12):
            encoded = encoded.replace("%", "%25").replace(".", "%2e")
        self.assert_path_rejected(f"/safe/{encoded}/secret")


if __name__ == "__main__":
    unittest.main()
