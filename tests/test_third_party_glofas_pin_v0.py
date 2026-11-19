# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""GloFAS native-I/O dependency documentation must match the acquisition pin."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ThirdPartyPinTests(unittest.TestCase):
    def test_glofas_dependency_pin_is_documented(self):
        req = (ROOT / "requirements-glofas-acquisition.txt").read_text(encoding="utf-8")
        match = re.search(r"(?m)^netCDF4==([0-9A-Za-z.]+)$", req)
        self.assertIsNotNone(match)
        third_party = (ROOT / "THIRD_PARTY.md").read_text(encoding="utf-8")
        self.assertIn("netCDF4==" + match.group(1), third_party)
        self.assertIn("separate from bounded Oasis/CLIMK research workflows", third_party)


if __name__ == "__main__":
    unittest.main()
