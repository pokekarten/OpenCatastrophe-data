# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only offline point-to-footprint diagnostic tests."""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.point_footprint_linkage_diagnostic_v0 import (
    LinkageDiagnosticError, evaluate, main,
)

HAS_SHAPELY = importlib.util.find_spec("shapely") is not None


def rect(x1, y1, x2, y2):
    return {"type": "Polygon", "coordinates": [
        [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]],
    ]}


def example():
    return {
        "schema_version": "oc-point-footprint-linkage-synthetic-v0",
        "synthetic_only": True, "crs": "EPSG:4326",
        "event_as_of": "2026-01-01",
        "address_source": {"family": "synthetic_addresses", "release": "v1", "as_of": "2025-01-01"},
        "building_source": {"family": "synthetic_buildings", "release": "v2", "as_of": "2025-01-01"},
        "addresses": [{"case_id": "synthetic:A", "lon": 6.01, "lat": 49.61}],
        "buildings": [{"building_id": "synthetic:B", "geometry": rect(6, 49.6, 6.02, 49.62)}],
    }


@unittest.skipUnless(HAS_SHAPELY, "requires optional Shapely dependency")
class PointFootprintTests(unittest.TestCase):
    def test_one_containing_building_is_never_verified_insured_asset(self):
        a = evaluate(example())
        self.assertEqual(a["status_counts"], {"one_containing_footprint_candidate": 1})
        self.assertFalse(a["physical_building_identity_proven"])
        self.assertFalse(a["insured_exposure_admitted"])
        self.assertFalse(a["cat_model_input_admitted"])

    def test_no_containing_building(self):
        s = example(); s["addresses"][0]["lon"] = 6.04
        self.assertEqual(evaluate(s)["status_counts"], {"no_containing_footprint": 1})

    def test_on_boundary_is_ambiguous(self):
        s = example(); s["addresses"][0]["lon"] = 6.0
        self.assertEqual(evaluate(s)["status_counts"], {"boundary_only_ambiguous": 1})

    def test_duplicate_geometry_other_building_id_ambiguous(self):
        s = example(); t = copy.deepcopy(s["buildings"][0])
        t["building_id"] = "synthetic:C"; s["buildings"].append(t)
        self.assertEqual(evaluate(s)["status_counts"], {"multiple_containing_footprints": 1})

    def test_intersection_and_boundary_neighbor_ambiguous(self):
        s = example()
        s["buildings"].append({"building_id": "synthetic:C",
                               "geometry": rect(6.01, 49.61, 6.03, 49.63)})
        self.assertEqual(evaluate(s)["status_counts"], {"interior_plus_boundary_ambiguity": 1})

    def test_hole_excludes_interior(self):
        s = example()
        s["buildings"][0]["geometry"]["coordinates"].append([
            [6.005,49.605],[6.005,49.615],[6.015,49.615],
            [6.015,49.605],[6.005,49.605]])
        self.assertEqual(evaluate(s)["status_counts"], {"no_containing_footprint": 1})

    def test_multipolygon_disconnected_parts(self):
        s = example(); g = s["buildings"][0]["geometry"]
        before = g["coordinates"]
        g["type"] = "MultiPolygon"
        g["coordinates"] = [before, rect(6.1,49.6,6.2,49.62)["coordinates"]]
        self.assertEqual(evaluate(s)["status_counts"], {"one_containing_footprint_candidate": 1})

    def test_post_event_source_blocks_historic_claim(self):
        s = example(); s["building_source"]["as_of"] = "2026-02-01"
        self.assertEqual(evaluate(s)["status_counts"], {"post_event_source_snapshot": 1})

    def test_same_family_is_not_independent_holdout(self):
        s = example(); s["building_source"]["family"] = "synthetic_addresses"
        r = evaluate(s)
        self.assertTrue(r["same_declared_source_family"])
        self.assertFalse(r["source_lineage_independence_proven"])

    def test_no_real_id_or_unsupported_crs(self):
        for key, value in [("crs", "EPSG:2169"), ("synthetic_only", False)]:
            s = example(); s[key] = value
            with self.assertRaises(LinkageDiagnosticError): evaluate(s)
        s = example(); s["addresses"][0]["case_id"] = "private_customer_id"
        with self.assertRaises(LinkageDiagnosticError): evaluate(s)

    def test_duplicate_identity_and_invalid_geometry(self):
        s = example(); s["addresses"].append(copy.deepcopy(s["addresses"][0]))
        with self.assertRaises(LinkageDiagnosticError): evaluate(s)
        s = example()
        s["buildings"][0]["geometry"]["coordinates"] = [[
            [6,49.6],[6.02,49.62],[6,49.62],[6.02,49.6],[6,49.6]]]
        with self.assertRaises(LinkageDiagnosticError): evaluate(s)

    def test_bad_3d_bool_nonfinite_and_out_of_bounds(self):
        for value in (True, 181, float("nan"), "6.01"):
            s = example(); s["addresses"][0]["lon"] = value
            with self.assertRaises(LinkageDiagnosticError): evaluate(s)
        s = example()
        s["buildings"][0]["geometry"]["coordinates"][0][0] = [6,49.6,10]
        with self.assertRaises(LinkageDiagnosticError): evaluate(s)
        s = example()
        s["buildings"][0]["geometry"]["coordinates"][0][0] = [True,49.6]
        with self.assertRaises(LinkageDiagnosticError): evaluate(s)

    def test_cli_is_aggregate_only_and_rejects_duplicate_json_fields(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "example.json"
            p.write_text(json.dumps(example()), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["--input", str(p)]), 0)
            self.assertNotIn("synthetic:A", out.getvalue())
            self.assertNotIn("6.01", out.getvalue())
            p.write_text('{"a":1,"a":2}', encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--input", str(p)]), 2)


if __name__ == "__main__":
    unittest.main()
