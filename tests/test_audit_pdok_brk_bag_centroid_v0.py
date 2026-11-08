# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully synthetic-only tests for bounded PDOK parcel ↔ BAG candidate QA."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_pdok_brk_bag_centroid_v0 import ParcelBagError, audit, load, main

BBOX = [5.0, 52.0, 5.005, 52.005]


def square(w, s, e, n):
    return {"type": "Polygon", "coordinates": [[
        [w, s], [e, s], [e, n], [w, n], [w, s]
    ]]}


def feature(identity, kind, geometry, status):
    if kind == "parcel":
        props = {"identificatie_lokaal_id": identity, "status_historie_waarde": status}
    else:
        props = {"identificatie": identity, "status": status, "bouwjaar": 1980}
    return {"type": "Feature", "properties": props, "geometry": geometry}


def collection(features, *, timestamp, with_next=False):
    return {"type": "FeatureCollection", "timeStamp": timestamp,
            "numberReturned": len(features), "features": features,
            "links": [{"rel": "next", "href": "https://example.org/next"}] if with_next else []}


def fixtures():
    p = collection([
        feature("P1", "parcel", square(5.0002, 52.0002, 5.002, 52.002), "Geldig"),
        feature("P2", "parcel", square(5.003, 52.003, 5.004, 52.004), "Geldig"),
    ], timestamp="2026-11-04T20:00:00Z")
    b = collection([
        feature("B1", "building", square(5.0003, 52.0003, 5.0005, 52.0005), "Pand in gebruik"),
        feature("B2", "building", square(5.001, 52.001, 5.00102, 52.00102), "Pand in gebruik"),
        feature("B3", "building", square(5.0032, 52.0032, 5.0035, 52.0035), "Pand in gebruik"),
        feature("B4", "building", square(5.0022, 52.0022, 5.0027, 52.0027), "Pand in gebruik"),
        feature("B5", "building", square(5.0014, 52.0014, 5.0018, 52.0018), "Niet gerealiseerd pand"),
    ], timestamp="2026-11-04T20:00:04Z")
    return p, b


class PdokParcelBagTests(unittest.TestCase):
    def test_conserves_active_counts_and_many_buildings_per_parcel(self):
        p, b = fixtures()
        r = audit(p, b, bbox=BBOX)
        self.assertEqual(r["parcel_feature_count"], 2)
        self.assertEqual(r["bag_building_feature_count"], 5)
        self.assertEqual(r["active_building_count"], 4)
        self.assertEqual(r["active_centroid_in_one_parcel_candidate"], 3)
        self.assertEqual(r["active_centroid_no_parcel_candidate"], 1)
        self.assertEqual(r["eligible_parcels_with_multiple_active_building_centroids"], 1)
        self.assertTrue(r["conservation_check_passed"])
        for flag in ("source_admitted", "model_input_approved",
                     "exact_polygon_intersection_verified",
                     "legal_property_or_insurer_identity_verified"):
            self.assertFalse(r[flag])
        self.assertNotIn("B1", json.dumps(r))
        self.assertNotIn("P1", json.dumps(r))

    def test_recentered_shoelace_handles_tiny_footprints(self):
        p, b = fixtures()
        b["features"] = [b["features"][1]]
        b["numberReturned"] = 1
        r = audit(p, b, bbox=BBOX)
        self.assertEqual(r["active_centroid_in_one_parcel_candidate"], 1)
        self.assertEqual(r["active_centroid_outside_own_geometry"], 0)

    def test_rejects_all_sensitive_owner_address_title_fields(self):
        for field in ("eigenaar", "owner_name", "address", "postcode",
                      "grundbuchblattnummer", "title_number", "huisnummer"):
            with self.subTest(field=field):
                p, b = fixtures()
                p["features"][0]["properties"][field] = "secret"
                with self.assertRaises(ParcelBagError):
                    audit(p, b, bbox=BBOX)

    def test_pagination_or_missing_counts_not_complete(self):
        p, b = fixtures()
        p["links"].append({"rel": "next", "href": "https://example.org"})
        with self.assertRaisesRegex(ParcelBagError, "pagination"):
            audit(p, b, bbox=BBOX)
        p, b = fixtures()
        b["numberReturned"] = 4
        with self.assertRaisesRegex(ParcelBagError, "numberReturned"):
            audit(p, b, bbox=BBOX)

    def test_rejects_old_source_snapshots_and_non_timezone_timestamp(self):
        p, b = fixtures()
        b["timeStamp"] = "2026-11-02T20:00:00Z"
        with self.assertRaisesRegex(ParcelBagError, "more than a day"):
            audit(p, b, bbox=BBOX)
        p, b = fixtures()
        b["timeStamp"] = "2026-11-04T20:00:00"
        with self.assertRaises(ParcelBagError):
            audit(p, b, bbox=BBOX)

    def test_rejects_duplicate_source_identity_and_bad_geometry(self):
        p, b = fixtures()
        p["features"].append(copy.deepcopy(p["features"][0]))
        p["numberReturned"] += 1
        with self.assertRaisesRegex(ParcelBagError, "duplicate"):
            audit(p, b, bbox=BBOX)
        p, b = fixtures()
        b["features"][0]["geometry"]["coordinates"][0].pop()
        with self.assertRaisesRegex(ParcelBagError, "not closed"):
            audit(p, b, bbox=BBOX)

    def test_rejects_oversized_or_reversed_bbox(self):
        p, b = fixtures()
        for bbox in ([5, 52, 5.1, 52.1], [5.1, 52, 5, 52.1],
                     [5, 52, 5.001], [float("nan"), 52, 5.01, 52.01]):
            with self.subTest(bbox=bbox), self.assertRaises(ParcelBagError):
                audit(p, b, bbox=bbox)

    def test_rejects_unlocated_feature_and_unknown_status_field(self):
        p, b = fixtures()
        b["features"][0]["geometry"] = square(7, 53, 7.001, 53.001)
        with self.assertRaisesRegex(ParcelBagError, "outside requested bbox"):
            audit(p, b, bbox=BBOX)
        p, b = fixtures()
        del b["features"][0]["properties"]["status"]
        with self.assertRaisesRegex(ParcelBagError, "no status"):
            audit(p, b, bbox=BBOX)

    def test_cli_and_strict_duplicate_json_keys(self):
        p, b = fixtures()
        with tempfile.TemporaryDirectory() as temp:
            pf, bf = Path(temp) / "parcels.json", Path(temp) / "buildings.json"
            pf.write_text(json.dumps(p), encoding="utf-8")
            bf.write_text(json.dumps(b), encoding="utf-8")
            self.assertEqual(main(["--parcels", str(pf), "--buildings", str(bf),
                                   "--bbox", "5,52,5.005,52.005"]), 0)
            pf.write_text('{"type":"FeatureCollection","type":"FeatureCollection"}', encoding="utf-8")
            with self.assertRaises(ParcelBagError):
                load(pf)
            self.assertEqual(main(["--parcels", str(pf), "--buildings", str(bf),
                                   "--bbox", "5,52,5.005,52.005"]), 1)


if __name__ == "__main__":
    unittest.main()
