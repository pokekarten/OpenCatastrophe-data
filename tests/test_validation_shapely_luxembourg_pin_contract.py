# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Prevent dependency bot from silently invalidating pinned GEOS topology evidence."""
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-validation.txt"
SOURCE = ROOT / "research_runners/luxembourg_age_hq2021_geojson_group_ogc_v0.py"


class GeometryValidationVersionContractTests(unittest.TestCase):
    def test_required_shapely_version_matches_frozen_geometry_probe(self):
        req = REQUIREMENTS.read_text(encoding="utf-8")
        source = SOURCE.read_text(encoding="utf-8")
        req_pin = re.findall(r"^shapely==([0-9]+(?:\.[0-9]+){2})$", req, re.MULTILINE)
        probe_pin = re.findall(r'if shapely\.__version__ != "([0-9]+(?:\.[0-9]+){2})":', source)
        self.assertEqual(len(req_pin), 1, "exactly one reviewed validation Shapely pin required")
        self.assertEqual(len(probe_pin), 1, "frozen source diagnostic version must be explicit")
        self.assertEqual(req_pin, probe_pin,
            "validation environment cannot run a different Shapely than the frozen geometry diagnostic")


if __name__ == "__main__":
    unittest.main()
