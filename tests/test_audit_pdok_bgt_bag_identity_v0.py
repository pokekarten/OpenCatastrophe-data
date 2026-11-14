# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, not actual property, ID-linkage QA for BGT to BAG."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_pdok_bgt_bag_identity_v0 import audit, main, ParcelBagError

BBOX = [5, 52, 5.005, 52.005]


def square(x, y):
    return {"type": "Polygon", "coordinates": [[
        [x, y], [x + 0.0001, y], [x + 0.0001, y + 0.0001],
        [x, y + 0.0001], [x, y],
    ]]}


def fixture():
    bag = []
    for i, status in (("1", "Pand in gebruik"), ("2", "Niet gerealiseerd pand"), ("3", "Pand in gebruik")):
        bag.append({"type": "Feature", "properties": {"identificatie": i, "status": status},
                    "geometry": square(5.0002 + int(i) * 0.0002, 52.0002)})
    bgt = []
    for feature_id, bag_id, status, x in (
            ("a", "1", "bestaand", 5.0004),
            ("b", "1", "bestaand", 5.0006),
            ("c", "2", "bestaand", 5.0008),
            ("d", "missing", "bestaand", 5.0010)):
        bgt.append({"type": "Feature", "properties": {
            "identificatie_lokaal_id": feature_id,
            "identificatie_bag_pnd": bag_id, "bgt_status": status,
        }, "geometry": square(x, 52.0004)})
    return (
        {"type": "FeatureCollection", "timeStamp": "2026-11-04T20:00:00Z",
         "numberReturned": len(bgt), "links": [], "features": bgt},
        {"type": "FeatureCollection", "timeStamp": "2026-11-04T20:00:04Z",
         "numberReturned": len(bag), "links": [], "features": bag},
    )


class PdokBgtBagIdentityTests(unittest.TestCase):
    def test_distinct_bag_link_and_multi_geometry(self):
        bgt, bag = fixture()
        out = audit(bgt, bag, bbox=BBOX)
        self.assertEqual(out["bgt_building_feature_count"], 4)
        self.assertEqual(out["bag_building_feature_count"], 3)
        self.assertEqual(out["bgt_direct_id_matched_rows"], 3)
        self.assertEqual(out["matched_distinct_bag_ids"], 2)
        self.assertEqual(out["bag_ids_with_multiple_bgt_geometries"], 1)
        self.assertEqual(out["bag_without_bgt_geometry_in_sample"], 1)
        self.assertEqual(out["bgt_with_bag_id_absent_in_sample"], 1)
        self.assertEqual(out["matched_bag_status_counts"],
                         {"Niet gerealiseerd pand": 1, "Pand in gebruik": 2})
        self.assertTrue(out["conservation_check_passed"])
        for key in ("model_input_approved", "source_admitted",
                    "independent_geometry_source_verified",
                    "legal_parcel_or_insurance_identity_verified"):
            self.assertFalse(out[key])
        self.assertNotIn("missing", json.dumps(out))

    def test_no_bag_reference_is_not_false_positive(self):
        bgt, bag = fixture()
        del bgt["features"][0]["properties"]["identificatie_bag_pnd"]
        out = audit(bgt, bag, bbox=BBOX)
        self.assertEqual(out["bgt_without_bag_reference"], 1)
        self.assertEqual(out["bgt_direct_id_matched_rows"], 2)

    def test_rejects_bad_or_sensitive_identity_fields(self):
        for bad in (123, "", " not-trimmed "):
            with self.subTest(bad=bad):
                bgt, bag = fixture()
                bgt["features"][0]["properties"]["identificatie_bag_pnd"] = bad
                with self.assertRaises(ParcelBagError):
                    audit(bgt, bag, bbox=BBOX)
        bgt, bag = fixture()
        bgt["features"][0]["properties"]["eigenaar"] = "not allowed"
        with self.assertRaises(ParcelBagError):
            audit(bgt, bag, bbox=BBOX)

    def test_rejects_missing_status_pagination_and_old_snapshots(self):
        bgt, bag = fixture()
        del bgt["features"][0]["properties"]["bgt_status"]
        with self.assertRaises(ParcelBagError):
            audit(bgt, bag, bbox=BBOX)
        bgt, bag = fixture()
        bag["links"] = [{"rel": "next", "href": "https://example.org/next"}]
        with self.assertRaises(ParcelBagError):
            audit(bgt, bag, bbox=BBOX)
        bgt, bag = fixture()
        bag["timeStamp"] = "2026-11-01T00:00:00Z"
        with self.assertRaises(ParcelBagError):
            audit(bgt, bag, bbox=BBOX)

    def test_reject_duplicate_bgt_feature_identity(self):
        bgt, bag = fixture()
        bgt["features"].append(copy.deepcopy(bgt["features"][0]))
        bgt["numberReturned"] += 1
        with self.assertRaisesRegex(ParcelBagError, "duplicate"):
            audit(bgt, bag, bbox=BBOX)

    def test_cli_runs_on_toy_snapshots(self):
        bgt, bag = fixture()
        with tempfile.TemporaryDirectory() as temp:
            bg, ba = Path(temp) / "bgt.json", Path(temp) / "bag.json"
            bg.write_text(json.dumps(bgt), encoding="utf-8")
            ba.write_text(json.dumps(bag), encoding="utf-8")
            self.assertEqual(main(["--bgt", str(bg), "--bag", str(ba),
                                   "--bbox", "5,52,5.005,52.005"]), 0)


if __name__ == "__main__":
    unittest.main()
