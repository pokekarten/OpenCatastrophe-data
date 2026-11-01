# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only EUBUCCO original LU00 Parquet lineage preflight tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HAS_ARROW = importlib.util.find_spec("pyarrow") is not None

if HAS_ARROW:
    import pyarrow as pa
    import pyarrow.parquet as pq
    from research_runners.eubucco_lu00_lineage_preflight_v0 import (
        inspect, EubuccoPreflightError,
    )

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(HAS_ARROW, "requires pinned optional pyarrow v0.20 profile")
class LuxembourgEubuccoTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "LU00.parquet"
        self.fields = {
            "id": ["SYN-LU-A", "SYN-LU-B", "SYN-LU-C"],
            "region_id": ["LU000"] * 3,
            "geometry": [b"\x01\x03\x00\x00\x00", b"\x01\x03\x00\x00\x00", b"\x01\x03\x00\x00\x00"],
            "geometry_source": ["gov-luxembourg", "osm", "msft"],
            "type_source": ["gov-luxembourg", "estimated", None],
            "height_source": ["estimated", "estimated", "msft"],
        }

    def write(self):
        table = pa.table({
            key: pa.array(value, type=(
                pa.binary() if key == "geometry" else
                pa.float64() if key == "height" else
                pa.int64() if key in ("floors", "construction_year") else pa.string()
            ))
            for key, value in self.fields.items()
        })
        pq.write_table(table, self.path, compression="NONE")
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def report(self, **options):
        digest = self.write()
        return inspect(self.path, digest, **options)

    def test_valid_lu00_counts_are_aggregate_and_non_admitted(self):
        report = self.report()
        self.assertEqual(report["total_buildings"], 3)
        self.assertEqual(report["provider_nuts2_partition"], "LU00")
        self.assertEqual(report["provider_nuts3_region"], "LU000")
        self.assertEqual(report["geometry_source_families"], {
            "government_label_unverified": 1, "msft": 1, "osm": 1,
        })
        self.assertEqual(report["attribute_provenance_families"]["height_source"]["model_estimated"], 2)
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["independence_from_luxembourg_act2023_established"])
        self.assertNotIn("SYN-LU-A", json.dumps(report))

    def test_actual_value_presence_is_separate_from_provenance(self):
        self.fields.update({
            "type": ["residential", "", None],
            "subtype": ["apartment", "industrial", " "],
            "height": [7.5, None, float("nan")],
            "floors": [3, 0, None],
            "construction_year": [None, 1970, None],
        })
        report = self.report()
        stats = report["attribute_value_availability"]
        self.assertEqual(stats["type"], {
            "present": 1, "null": 1, "blank": 1, "nonfinite": 0
        })
        self.assertEqual(stats["subtype"]["present"], 2)
        self.assertEqual(stats["subtype"]["blank"], 1)
        self.assertEqual(stats["height"]["present"], 1)
        self.assertEqual(stats["height"]["null"], 1)
        self.assertEqual(stats["height"]["nonfinite"], 1)
        self.assertEqual(stats["floors"]["present"], 2)
        self.assertEqual(stats["construction_year"]["present"], 1)
        self.assertEqual(stats["construction_year"]["null"], 2)
        self.assertEqual(report["missing_attribute_value_columns"], [])
        self.assertEqual(report["total_buildings"], 3)
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("SYN-LU-A", json.dumps(report))

    def test_missing_optional_values_only_reported_not_filled(self):
        report = self.report()
        self.assertEqual(report["attribute_value_availability"], {})
        self.assertEqual(sorted(report["missing_attribute_value_columns"]), [
            "construction_year", "floors", "height", "subtype", "type"
        ])

    def test_pinned_original_digest_mismatch_fails(self):
        digest = self.write()
        with self.assertRaisesRegex(EubuccoPreflightError, "SHA-256 mismatch"):
            inspect(self.path, "0" * 64 if digest != "0" * 64 else "1" * 64)

    def test_bad_partition_and_id_fails(self):
        with self.assertRaisesRegex(EubuccoPreflightError, "LU00"):
            self.report(partition_id="LU01")
        with self.assertRaisesRegex(EubuccoPreflightError, "v0.2"):
            self.report(source_id="eubucco.buildings.v0.1")

    def test_wrong_nuts3_region_blocks_aggregation(self):
        self.fields["region_id"][1] = "DE212"
        with self.assertRaisesRegex(EubuccoPreflightError, "non-LU000"):
            self.report()

    def test_duplicate_id_is_not_a_unique_building(self):
        self.fields["id"][2] = "SYN-LU-A"
        with self.assertRaisesRegex(EubuccoPreflightError, "duplicate"):
            self.report()

    def test_missing_source_provenance_column_blocks(self):
        del self.fields["geometry_source"]
        with self.assertRaisesRegex(EubuccoPreflightError, "missing EUBUCCO"):
            self.report()

    def test_missing_optional_column_is_reported_but_no_fill_inferred(self):
        report = self.report()
        self.assertIn("floors_source", report["missing_attribute_provenance_columns"])
        self.assertIn("construction_year_source", report["missing_attribute_provenance_columns"])
        self.assertNotIn("SYN-LU-A", json.dumps(report))
        self.assertFalse(report["building_identifiers_or_geometries_exported"])

    def test_malformed_parquet_magic_is_rejected_before_decoding(self):
        self.path.write_bytes(b"other local file")
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(EubuccoPreflightError, "Parquet header/footer"):
            inspect(self.path, digest)

    def test_nonbinary_geometry_column_is_rejected(self):
        table = pa.table({
            key: pa.array(value, type=pa.string())
            for key, value in self.fields.items()
            if key != "geometry"
        }).append_column("geometry", pa.array(["polygon"] * 3, type=pa.string()))
        pq.write_table(table, self.path, compression="NONE")
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(EubuccoPreflightError, "not WKB binary"):
            inspect(self.path, digest)

    def test_cli_emits_only_aggregate_and_blocks_output_overwrite(self):
        digest = self.write()
        args = [sys.executable, str(ROOT / "research_runners/eubucco_lu00_lineage_preflight_v0.py"),
                "--original", str(self.path), "--expected-sha256", digest]
        one = subprocess.run(args, text=True, capture_output=True, check=False)
        self.assertEqual(one.returncode, 0, one.stderr)
        two = subprocess.run(args, text=True, capture_output=True, check=False)
        self.assertEqual(one.stdout, two.stdout)
        self.assertEqual(json.loads(one.stdout)["total_buildings"], 3)
        self.assertNotIn("SYN-LU-A", one.stdout)
        output = self.path.parent / "receipt.json"
        exists = args + ["--out", str(output)]
        self.assertEqual(subprocess.run(exists, text=True, capture_output=True).returncode, 0)
        again = subprocess.run(exists, text=True, capture_output=True)
        self.assertEqual(again.returncode, 2)


if __name__ == "__main__":
    unittest.main()
