# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No provider bytes: source provenance coherence tests with synthetic parquet."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.eubucco_lu00_source_coherence_v0 import (
    CrossSourceError, PROVENANCE, audit, classify, family,
)

ARROW = importlib.util.find_spec("pyarrow") is not None
if ARROW:
    import pyarrow as pa
    import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]


class ClassificationTests(unittest.TestCase):
    def test_missing_and_estimated_never_ground_truth(self):
        self.assertEqual(classify("gov-luxembourg", "estimated")[2], "estimated")
        self.assertEqual(classify("osm", None)[2], "missing")
        self.assertEqual(classify("gov-luxembourg", "gov-luxembourg")[2],
                         "same_label_not_independent_proof")
        self.assertEqual(classify("gov-luxembourg", "osm")[2],
                         "different_label_independence_unverified")

    def test_family_unverified_not_scientifically_authoritative(self):
        self.assertEqual(family("gov-luxembourg"), "gov_unverified")
        self.assertEqual(family("unexpected-source"), "other_unverified")
        with self.assertRaises(CrossSourceError):
            family("X" * 129)


@unittest.skipUnless(ARROW, "requires optional pinned pyarrow")
class SourceCoherenceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "synthetic-LU00.parquet"
        self.data = {
            "id": ["SYN-1", "SYN-2", "SYN-3", "SYN-4"],
            "region_id": ["LU000"] * 4,
            "geometry_source": ["gov-luxembourg", "gov-luxembourg", "osm", "msft"],
            "type_source": ["estimated", "gov-luxembourg", "osm", "estimated"],
            "subtype_source": ["estimated", "osm", "estimated", "msft"],
            "height_source": ["gov-luxembourg", "estimated", "osm", "msft"],
            "floors_source": ["estimated", "osm", "estimated", "estimated"],
            "construction_year_source": [None, None, None, None],
        }

    def write(self):
        pq.write_table(pa.table(self.data), self.path, compression="NONE")
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def report(self):
        return audit(self.path, self.write())

    def test_coherent_original_source_relationships(self):
        report = self.report()
        self.assertEqual(report["rows"], 4)
        self.assertEqual(report["geometry_families"],
                         {"gov_unverified": 2, "msft": 1, "osm": 1})
        self.assertEqual(report["attribute_source_label_relations"]["height_source"],
                         {"estimated": 1, "same_label_not_independent_proof": 3})
        self.assertEqual(report["attribute_source_label_relations"]["floors_source"],
                         {"different_label_independence_unverified": 1, "estimated": 3})
        self.assertEqual(report["attribute_source_label_relations"]["construction_year_source"],
                         {"missing": 4})
        self.assertEqual(sum(x["count"] for x in
                             report["source_family_matrices"]["type_source"]), 4)
        self.assertFalse(report["independent_from_luxembourg_act2023_established"])
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("SYN-1", json.dumps(report))

    def test_original_byte_sha_mismatch_rejected(self):
        self.write()
        with self.assertRaisesRegex(CrossSourceError, "SHA256 mismatch"):
            audit(self.path, "f" * 64)

    def test_missing_attribute_source_column_fails(self):
        del self.data["height_source"]
        with self.assertRaisesRegex(CrossSourceError, "mandatory"):
            self.report()

    def test_region_mismatch_fails(self):
        self.data["region_id"][0] = "BE100"
        with self.assertRaisesRegex(CrossSourceError, "regional code"):
            self.report()

    def test_duplicate_building_ids_fail(self):
        self.data["id"][0] = "SYN-2"
        with self.assertRaisesRegex(CrossSourceError, "duplicate"):
            self.report()

    def test_empty_government_label_is_not_verified(self):
        self.data["geometry_source"][0] = None
        report = self.report()
        self.assertEqual(report["geometry_families"]["missing"], 1)
        self.assertEqual(report["attribute_source_label_relations"]["height_source"]["unresolved_geometry_origin"], 1)

    def test_cli_only_aggregate_repeatable(self):
        sha = self.write()
        cmd = [sys.executable, str(ROOT / "research_runners/eubucco_lu00_source_coherence_v0.py"),
               "--original", str(self.path), "--sha256", sha]
        one = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        self.assertEqual(one.returncode, 0, one.stderr)
        again = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        self.assertEqual(one.stdout, again.stdout)
        self.assertEqual(json.loads(one.stdout)["rows"], 4)
        self.assertNotIn("SYN-1", one.stdout)

    def test_malformed_parquet_rejected_without_output(self):
        self.path.write_text("fake fixture", encoding="utf-8")
        sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(CrossSourceError, "invalid or oversized"):
            audit(self.path, sha)


if __name__ == "__main__":
    unittest.main()
