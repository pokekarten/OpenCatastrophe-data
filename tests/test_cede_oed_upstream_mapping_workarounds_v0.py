# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic regression guards for pinned legacy Oasis example workarounds."""
from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

import yaml

from scripts.cede_oed_upstream_full_mapping_probe_v0 import BASELINE, MAPPING_PATH, _source_row
from scripts.cede_oed_upstream_mapping_workarounds_v0 import (
    BOOLEAN_WHEN, PLACEHOLDER, UNSAFE_WHEN, VERSION_OLD, VERSION_VALID,
    _verify_synthetic_core_values, probe
)


class LegacyExampleWorkaroundTests(unittest.TestCase):
    def test_explicit_legacy_to_oed_occupancy_value(self):
        self.assertEqual(BASELINE["OccupancyCode"], "301")
        self.assertEqual(_source_row({"OccupancyCode": {"type": "int"}})["OccupancyCode"], "301")

    def test_version_substitution_is_oed_semver_literal(self):
        raw = "types:\n  LocationID:\n    type: string\ntransform:\n" + VERSION_OLD
        modified = raw.replace(VERSION_OLD, VERSION_VALID)
        parsed = yaml.safe_load(modified)
        self.assertEqual(parsed["transform"]["OEDVersion"][0]["transformation"], "'3.0.2'")
        self.assertEqual(raw.count(VERSION_OLD), 1)
        self.assertNotIn(VERSION_OLD, modified)

    def test_nonboolean_when_is_replaced_only_at_exact_anchor(self):
        self.assertIn("when: ExposureSetName\n", UNSAFE_WHEN)
        self.assertIn("is not in", BOOLEAN_WHEN)
        self.assertEqual(UNSAFE_WHEN.count("when: "), 1)

    def test_core_synthetic_values_detect_tiv_and_identity_mutations(self):
        loc = {
            "PortNumber": "SYNTHETIC-ONLY", "AccNumber": "1", "LocNumber": "1",
            "CountryCode": "DE", "LocCurrency": "EUR", "OEDVersion": "3.0.2",
            "BuildingTIV": "100.1", "ContentsTIV": "20.05", "OccupancyCode": "1050",
        }
        acc = {
            "PortNumber": "SYNTHETIC-ONLY", "AccNumber": "1",
            "PolNumber": "1", "AccCurrency": "EUR", "LayerNumber": "1",
        }
        with tempfile.TemporaryDirectory() as tmp:
            p1, p2 = Path(tmp) / "loc.csv", Path(tmp) / "acc.csv"
            def write(path, record):
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(record))
                    writer.writeheader()
                    writer.writerow(record)
            write(p1, loc)
            write(p2, acc)
            valid = _verify_synthetic_core_values(p1, p2)
            self.assertTrue(valid["passed"])
            self.assertFalse(valid["scientific_lossless_mapping_proven"])
            write(p1, {**loc, "BuildingTIV": "100.11", "OccupancyCode": "0"})
            changed = _verify_synthetic_core_values(p1, p2)
            self.assertFalse(changed["passed"])
            self.assertIn("location:BuildingTIV", changed["mismatched_field_names"])
            self.assertIn("location:OccupancyCode", changed["mismatched_field_names"])
            write(p1, loc)
            write(p2, {**acc, "PolNumber": "EXTRA"})
            self.assertIn("account:PolNumber", _verify_synthetic_core_values(p1, p2)["mismatched_field_names"])

    def test_upstream_schema_drift_fails_closed_before_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / MAPPING_PATH
            folder.mkdir(parents=True)
            location_yaml = (
                "types:\n  LocationID:\n    type: string\n"
                + PLACEHOLDER + "null_values:\n  - NULL\ntransform:\n"
                + "  PortNumber:\n    - transformation: ExposureSetName\n"
                + UNSAFE_WHEN
                + "  OEDVersion:\n    - transformation: \"999\"\n"
            )
            (folder / "mapping_loc_Cede-OED.yaml").write_text(location_yaml, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "OEDVersion 302 expression changed"):
                probe(Path(tmp))


if __name__ == "__main__":
    unittest.main()
