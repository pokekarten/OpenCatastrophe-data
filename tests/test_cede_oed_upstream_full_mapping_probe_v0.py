# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic, synthetic-only guards for upstream Oasis research mapping probes."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from scripts.cede_oed_upstream_full_mapping_probe_v0 import (
    MAPPING_PATH, _source_row, duplicate_type_keys, probe,
)


def example_mapping() -> str:
    return (
        "types:\n"
        "  ContractID:\n    type: string\n"
        "  LocationID:\n    type: string\n"
        "null_values:\n  - NULL\n"
        "transform:\n"
        "  AccNumber:\n    - transformation: ContractID\n"
    )


class UpstreamComprehensiveResearchTests(unittest.TestCase):
    def test_fictional_values_only_and_closed_primitive_types(self):
        row = _source_row({"ContractID": {"type": "string"},
                           "LocationID": {"type": "string"},
                           "BuildingValue": {"type": "float"},
                           "NumberOfStories": {"type": "int"},
                           "UnknownField": {"type": "ODTF Data Type"}})
        self.assertEqual(row["ContractID"], "1")
        self.assertEqual(row["BuildingValue"], "100.10")
        self.assertEqual(row["NumberOfStories"], "0")
        self.assertEqual(row["UnknownField"], "")

    def test_duplicate_source_type_keys_detected_before_yaml_loader(self):
        raw = (
            "types:\n"
            "  LocationID:\n    type: string\n"
            "  MinDeduct:\n    type: float\n"
            "  MinDeduct:\n    type: float\n"
            "null_values:\n  - NULL\ntransform: {}\n"
        )
        self.assertEqual(duplicate_type_keys(raw), ["MinDeduct"])
        self.assertEqual(duplicate_type_keys(example_mapping()), [])

    def test_zero_exit_without_generated_csv_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / MAPPING_PATH
            root.mkdir(parents=True)
            for filename in ("mapping_loc_Cede-OED.yaml", "mapping_acc_Cede-OED.yaml"):
                (root / filename).write_text(example_mapping(), encoding="utf-8")
            proc = SimpleNamespace(returncode=0, stderr="ERROR synthetic mapping failure")
            with patch("scripts.cede_oed_upstream_full_mapping_probe_v0.subprocess.run",
                       return_value=proc) as mocked:
                outcome = probe(Path(tmp))
            self.assertEqual(mocked.call_count, 2)
            self.assertFalse(outcome["full_mapping_executed_both"])
            self.assertTrue(all(row["transform_exit_code"] == 0 for row in outcome["runs"]))
            self.assertTrue(all(not row["generated_csv"] for row in outcome["runs"]))
            self.assertFalse(outcome["full_mapping_compatible"])
            self.assertFalse(outcome["model_input_admitted"])

    def test_missing_upstream_mapping_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                probe(Path(tmp))


if __name__ == "__main__":
    unittest.main()
