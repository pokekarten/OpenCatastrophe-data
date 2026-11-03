# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Prevent accidental numerical GEOS-version drift in publisher AGE tests.

The generic Python matrix uses Shapely 2.2.0, while the original research
polygon/repair challenge must be evaluated under the exact 2.1.2 pin in its
own GitHub Actions workflows. A generic skip is not scientific equivalence.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GeoVersionBoundaryTests(unittest.TestCase):
    def test_generic_matrix_and_pinned_source_are_explicitly_distinct(self):
        generic = (ROOT / "requirements-validation.txt").read_text(encoding="utf-8")
        source = (ROOT / "research_runners/luxembourg_age_hq2021_geojson_group_ogc_v0.py").read_text(encoding="utf-8")
        # Parallel main updates may restore the generic 2.1.2 pin.
        # Under 2.1.2 the OGC tests execute; under 2.2.0 their
        # version-sensitive subsets skip, while specialist jobs still run.
        self.assertTrue(
            "shapely==2.1.2" in generic or "shapely==2.2.0" in generic,
            "generic CI must pin one reviewed Shapely version",
        )
        self.assertEqual(
            sum(s in generic for s in ("shapely==2.1.2", "shapely==2.2.0")), 1,
        )
        self.assertIn('shapely.__version__ != "2.1.2"', source)
        self.assertIn('raise GroupTopologyError("Unpinned Shapely', source)

    def test_original_specialist_workflows_still_execute_pinned_ogc_tests(self):
        for workflow in (
            ".github/workflows/luxembourg-age-hq100-2021-megagroup-ogc.yml",
            ".github/workflows/luxembourg-age-hq2021-original-geojson.yml",
        ):
            with self.subTest(workflow=workflow):
                s = (ROOT / workflow).read_text(encoding="utf-8")
                self.assertIn("shapely==2.1.2", s)
                self.assertIn("test_luxembourg_age_hq2021_geojson_group_ogc_v0", s)
        repair = (ROOT / ".github/workflows/luxembourg-age-hq2021-original-geojson.yml").read_text(encoding="utf-8")
        self.assertIn("test_luxembourg_age_hq2021_group_repair_sensitivity_v0", repair)

    def test_both_research_classes_skip_unpinned_generic_ci_but_not_pinned_ci(self):
        for relative in (
            "tests/test_luxembourg_age_hq2021_geojson_group_ogc_v0.py",
            "tests/test_luxembourg_age_hq2021_group_repair_sensitivity_v0.py",
        ):
            with self.subTest(file=relative):
                s = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn('shapely.__version__ == "2.1.2"', s)
                self.assertIn("@unittest.skipUnless(HAS_PINNED_SHAPELY", s)
                self.assertNotIn("@unittest.skipUnless(HAS_SHAPELY", s)


if __name__ == "__main__":
    unittest.main()
