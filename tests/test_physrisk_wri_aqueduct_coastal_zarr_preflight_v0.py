# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression coverage for the exact-source WRI coastal Zarr gate."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.physrisk_wri_aqueduct_coastal_zarr_preflight_v0 import (
    SourceGateError, inspect_metadata, RETURN_PERIODS, TRANSFORM,
)


def array():
    return {"zarr_format": 2, "shape": [9, 21600, 43200],
            "chunks": [9, 1000, 1000], "dtype": "<f4", "order": "C",
            "compressor": {"id": "blosc", "cname": "lz4", "clevel": 5,
                           "shuffle": 1, "blocksize": 0},
            "filters": None, "fill_value": 0.0}


def attrs():
    return {"crs": "+init=epsg:4326",
            "dimensions": ["index", "latitude", "longitude"],
            "index_name": "return period (years)",
            "index_values": RETURN_PERIODS[:],
            "transform_mat3x3": TRANSFORM[:]}


def encoded(d):
    return (json.dumps(d, sort_keys=True) + "\n").encode("utf-8")


def inspect(a=None, b=None):
    x, y = encoded(array() if a is None else a), encoded(attrs() if b is None else b)
    return inspect_metadata(x, y, hashlib.sha256(x).hexdigest(), hashlib.sha256(y).hexdigest())


class SourceMetadataTests(unittest.TestCase):
    def test_good_metadata_still_blocks_cat_admission(self):
        r = inspect()
        self.assertEqual(r["array_shape_return_period_lat_lon"], [9, 21600, 43200])
        self.assertEqual(r["return_period_years"], RETURN_PERIODS)
        self.assertFalse(r["return_period_levels_are_independent_events"])
        self.assertFalse(r["annual_event_catalogue_present"])
        self.assertFalse(r["array_chunks_read"])
        self.assertFalse(r["model_input_admitted"])
        self.assertFalse(r["flood_protection_modelled"])

    def test_wrong_array_encoding_fails(self):
        for field, wrong in [("zarr_format", 3), ("dtype", ">f4"),
                             ("shape", [1, 21600, 43200]),
                             ("chunks", [1, 1000, 1000]),
                             ("fill_value", 99), ("fill_value", True),
                             ("compressor", None), ("filters", ["scale"])]:
            with self.subTest(field=field):
                doc = array()
                doc[field] = wrong
                with self.assertRaises(SourceGateError):
                    inspect(doc, None)

    def test_wrong_index_or_crs_or_transform_fails(self):
        for field, wrong in [("index_values", [2, 5, 10, 25, 50, 100, 250, 500, 500]),
                             ("index_values", [2, 5, 10, 25, 50, 100, 250, 500, True]),
                             ("index_name", "event_id"),
                             ("dimensions", ["event", "latitude", "longitude"]),
                             ("crs", "EPSG:3857")]:
            with self.subTest(field=field):
                doc = attrs()
                doc[field] = wrong
                with self.assertRaises(SourceGateError):
                    inspect(None, doc)
        for wrong in ([0] * 9, TRANSFORM[:8], TRANSFORM[:3] + [float("inf")] + TRANSFORM[4:]):
            doc = attrs()
            doc["transform_mat3x3"] = wrong
            with self.assertRaises(SourceGateError):
                inspect(None, doc)

    def test_source_sha_duplicate_keys_and_metadata_size(self):
        a, b = encoded(array()), encoded(attrs())
        with self.assertRaisesRegex(SourceGateError, "SHA-256 mismatch"):
            inspect_metadata(a, b, "0" * 64, hashlib.sha256(b).hexdigest())
        for broken in (b'{"shape":[],"shape":[]}', b'NaN', b'\xff', b'X' * 4097):
            with self.subTest(broken=broken[:10]):
                with self.assertRaises(SourceGateError):
                    inspect_metadata(broken, b, hashlib.sha256(broken).hexdigest(),
                                     hashlib.sha256(b).hexdigest())

    def test_cli_blocks_source_overwrite(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            rootdir = Path(tmp)
            a = rootdir / "zarray.json"
            b = rootdir / "zattrs.json"
            out = rootdir / "report.json"
            a.write_bytes(encoded(array()))
            b.write_bytes(encoded(attrs()))
            cmd = [sys.executable, str(root / "research_runners/physrisk_wri_aqueduct_coastal_zarr_preflight_v0.py"),
                   str(a), str(b),
                   "--expected-zarray-sha256", hashlib.sha256(a.read_bytes()).hexdigest(),
                   "--expected-zattrs-sha256", hashlib.sha256(b.read_bytes()).hexdigest(),
                   "--out", str(out)]
            valid = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertFalse(json.loads(out.read_text())["model_input_admitted"])
            invalid = subprocess.run(cmd[:-1] + [str(a)], capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertEqual(a.read_bytes(), encoded(array()))


if __name__ == "__main__":
    unittest.main()
