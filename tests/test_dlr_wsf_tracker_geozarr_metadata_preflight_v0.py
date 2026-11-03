# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original WSF Tracker GeoZarr metadata/epoch safety tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.dlr_wsf_tracker_geozarr_metadata_preflight_v0 import (
    WSFGateError, earliest_detection_epoch, inspect_wsf_metadata_bytes,
)

ROOT = Path(__file__).resolve().parents[1]


def level_meta(group):
    return {
        "zarr_format": 3, "node_type": "array",
        "data_type": "int8", "fill_value": 0,
        "shape": ([1536433, 4007502] if group == 0 else [375, 978]),
        "dimension_names": ["y", "x"],
        "chunk_grid": {"name": "regular", "configuration": {"chunk_shape": [8192, 8192]}},
        "codecs": [{"name": "sharding_indexed",
                    "configuration": {"chunk_shape": [256, 256]}}],
        "storage_transformers": [],
        "attributes": {
            "_ARRAY_DIMENSIONS": ["y", "x"],
            "grid_mapping": "spatial_ref",
            "valid_min": 0, "valid_max": 20,
            "description": "Integer index (int8) encoding earliest detection; "
                           "0 no settlement/nodata; 1-20 biannual half-year "
                           "epochs. Levels 1-12 overviews use min aggregation.",
        },
    }


def encoded(doc):
    return (json.dumps(doc, sort_keys=True) + "\n").encode("utf-8")


def inspect(a=None, b=None):
    first = encoded(level_meta(0) if a is None else a)
    second = encoded(level_meta(12) if b is None else b)
    return inspect_wsf_metadata_bytes(
        first, second, hashlib.sha256(first).hexdigest(),
        hashlib.sha256(second).hexdigest(),
    )


class WSFTrackerMetadataTests(unittest.TestCase):
    def test_native_and_overview_are_distinct_and_inadmissible(self):
        got = inspect()
        self.assertEqual(got["native_shape_yx"], [1536433, 4007502])
        self.assertEqual(got["overview_shape_yx"], [375, 978])
        self.assertEqual(got["source_data_type"], "int8")
        self.assertEqual(got["source_index_zero_meaning"],
                         "NO_SETTLEMENT_OR_NODATA_NOT_A_BUILDING_COUNT")
        self.assertTrue(got["overview_aggregates_with_minimum"])
        self.assertFalse(got["overview_valid_for_area_count_or_vintage_statistics"])
        self.assertFalse(got["building_footprints_observed"])
        self.assertFalse(got["building_values_observed"])
        self.assertFalse(got["demolition_events_observed"])
        self.assertFalse(got["model_input_admitted"])
        self.assertNotIn("construction_year", json.dumps(got))

    def test_epoch_translation_preserves_first_detection_not_construction(self):
        self.assertIsNone(earliest_detection_epoch(0))
        self.assertEqual(earliest_detection_epoch(1), "2016-07-01")
        self.assertEqual(earliest_detection_epoch(2), "2017-01-01")
        self.assertEqual(earliest_detection_epoch(3), "2017-07-01")
        self.assertEqual(earliest_detection_epoch(19), "2025-07-01")
        self.assertEqual(earliest_detection_epoch(20), "2026-01-01")
        for bad in (-1, 21, None, True, 1.0, "3"):
            with self.subTest(bad=bad):
                with self.assertRaises(WSFGateError):
                    earliest_detection_epoch(bad)

    def test_source_format_shape_and_semantics_drift_block(self):
        cases = []
        for level, field, value in [
            (0, "zarr_format", 2), (0, "zarr_format", True),
            (0, "data_type", "uint8"), (0, "fill_value", 1),
            (0, "shape", [1536433, 4000000]),
            (0, "dimension_names", ["x", "y"]),
            (12, "shape", [376, 979]),
            (12, "node_type", "group"),
        ]:
            a, b = level_meta(0), level_meta(12)
            target = a if level == 0 else b
            target[field] = value
            cases.append((a, b))
        for a, b in cases:
            with self.assertRaises(WSFGateError):
                inspect(a, b)
        for field, value in [
            ("valid_max", 21), ("valid_min", 1),
            ("description", "values 1-20 are just classes"),
            ("grid_mapping", "alternative_CRS"),
        ]:
            a = level_meta(0)
            a["attributes"][field] = value
            with self.assertRaises(WSFGateError):
                inspect(a, None)
        a = level_meta(0)
        a["chunk_grid"]["configuration"]["chunk_shape"] = [128, 128]
        with self.assertRaises(WSFGateError):
            inspect(a, None)
        a = level_meta(0)
        a["codecs"][0]["configuration"]["chunk_shape"] = [128, 128]
        with self.assertRaises(WSFGateError):
            inspect(a, None)

    def test_hash_duplicate_json_and_source_byte_limits(self):
        data = encoded(level_meta(0))
        other = encoded(level_meta(12))
        with self.assertRaisesRegex(WSFGateError, "SHA256 mismatch"):
            inspect_wsf_metadata_bytes(data, other, "0" * 64,
                                       hashlib.sha256(other).hexdigest())
        duplicate = b'{"node_type":"array","node_type":"array"}'
        with self.assertRaisesRegex(WSFGateError, "duplicate"):
            inspect_wsf_metadata_bytes(duplicate, other,
                                       hashlib.sha256(duplicate).hexdigest(),
                                       hashlib.sha256(other).hexdigest())
        for broken in (b"", b"\xff", b"Z" * 32769):
            with self.assertRaises(WSFGateError):
                inspect_wsf_metadata_bytes(broken, other,
                                           hashlib.sha256(broken).hexdigest(),
                                           hashlib.sha256(other).hexdigest())

    def test_cli_never_overwrites_original_source(self):
        native = encoded(level_meta(0))
        overview = encoded(level_meta(12))
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            src = p / "source-0.json"
            coarse = p / "source-12.json"
            out = p / "receipt.json"
            src.write_bytes(native)
            coarse.write_bytes(overview)
            args = [sys.executable,
                str(ROOT / "research_runners/dlr_wsf_tracker_geozarr_metadata_preflight_v0.py"),
                str(src), str(coarse),
                "--expected-level0-sha256", hashlib.sha256(native).hexdigest(),
                "--expected-level12-sha256", hashlib.sha256(overview).hexdigest(),
                "--out", str(out)]
            valid = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertFalse(report["overview_valid_for_area_count_or_vintage_statistics"])
            blocked = subprocess.run(args[:-1] + [str(src)],
                                     capture_output=True, text=True)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertEqual(src.read_bytes(), native)
            self.assertEqual(coarse.read_bytes(), overview)


if __name__ == "__main__":
    unittest.main()
