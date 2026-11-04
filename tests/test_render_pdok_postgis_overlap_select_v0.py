# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic source snapshots only: no real property locations or ownership."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_pdok_brk_bag_centroid_v0 import ParcelBagError
from scripts.render_pdok_postgis_overlap_select_v0 import ROOT, render, main

BBOX = [5.0, 52.0, 5.005, 52.005]
STAMP = "2026-11-04T23:00:00Z"


def sq(x, y, w=0.0002):
    return {"type": "Polygon", "coordinates": [[
        [x, y], [x + w, y], [x + w, y + w], [x, y + w], [x, y]
    ]]}


def item(id_, kind, geo, status=""):
    if kind == "parcel":
        p = {"identificatie_lokaal_id": id_, "status_historie_waarde": status}
    elif kind == "bgt":
        p = {"identificatie_lokaal_id": id_, "identificatie_bag_pnd": "bag-1",
             "bgt_status": status}
    else:
        p = {"identificatie": id_, "status": status}
    return {"type": "Feature", "properties": p, "geometry": geo}


def collect(*features, timestamp=STAMP):
    return {"type": "FeatureCollection", "timeStamp": timestamp,
            "numberReturned": len(features), "features": list(features), "links": []}


def fixture():
    parcels = collect(item("parcel-A", "parcel", sq(5.0001, 52.0001), "Geldig"),
                      item("parcel-B", "parcel", sq(5.0003, 52.0001), "Geldig"))
    bgt = collect(item("footprint-A", "bgt", sq(5.0002, 52.00015, 0.0002), "bestaand"))
    bag = collect(item("bag-1", "bag", sq(5.0002, 52.00015), "Pand in gebruik"))
    return parcels, bgt, bag


class PostGISQueryGenerationTests(unittest.TestCase):
    def test_strict_readonly_metric_overlay_with_realistic_identity_fields(self):
        p, b, a = fixture()
        sql = render(p, b, a, bbox=BBOX)
        self.assertIn("ST_Transform(geo,28992)", sql)
        self.assertIn("ST_Intersection(b.geom,p.geom)", sql)
        self.assertIn("ST_Union(e.overlap_geom)", sql)
        self.assertIn("parcel_self_overlap_doublecount_sqm", sql)
        self.assertIn("union_intersection_area_sqm", sql)
        self.assertIn("ST_Area", sql)
        self.assertIn("ROW_NUMBER() OVER", sql)
        self.assertIn("source_status='Geldig'", sql)
        self.assertIn("source_status='bestaand'", sql)
        self.assertIn("source_status='Pand in gebruik'", sql)
        self.assertIn("multiple_parcel_overlap_over_one_sqm", sql)
        self.assertIn("multiple_parcel_overlap_over_five_pct", sql)
        self.assertIn("double_count_risk_buildings", sql)
        self.assertIn("FALSE AS model_input_approved", sql)
        self.assertTrue(sql.lstrip().startswith("-- RESEARCH ONLY"))
        for unsafe in ("CREATE TABLE", "INSERT INTO", "UPDATE ", "DROP TABLE", "DELETE FROM"):
            self.assertNotIn(unsafe, sql)

    def test_rejects_owner_and_identifying_address_property_fields(self):
        for key in ("owner_name", "eigenaar", "postcode", "address",
                    "grundbuchblattnummer", "title_number"):
            with self.subTest(key=key):
                p, b, a = fixture()
                p["features"][0]["properties"][key] = "forbidden"
                with self.assertRaises(ParcelBagError):
                    render(p, b, a, bbox=BBOX)

    def test_rejects_unbounded_page_and_stale_source(self):
        p, b, a = fixture()
        p["links"] = [{"rel": "next", "href": "https://example.org/next"}]
        with self.assertRaisesRegex(ParcelBagError, "pagination"):
            render(p, b, a, bbox=BBOX)
        p, b, a = fixture()
        a["timeStamp"] = "2026-11-02T20:00:00Z"
        with self.assertRaises(ParcelBagError):
            render(p, b, a, bbox=BBOX)

    def test_rejects_missing_bag_id_and_non_ascii_sql_ids(self):
        p, b, a = fixture()
        del b["features"][0]["properties"]["identificatie_bag_pnd"]
        with self.assertRaises(ParcelBagError):
            render(p, b, a, bbox=BBOX)
        p, b, a = fixture()
        b["features"][0]["properties"]["identificatie_lokaal_id"] = "bad'quote"
        with self.assertRaises(ParcelBagError):
            render(p, b, a, bbox=BBOX)

    def test_rejects_invalid_geometries_and_wrong_bbox(self):
        p, b, a = fixture()
        b["features"][0]["geometry"]["coordinates"][0].pop()
        with self.assertRaises(ParcelBagError):
            render(p, b, a, bbox=BBOX)
        p, b, a = fixture()
        with self.assertRaises(ParcelBagError):
            render(p, b, a, bbox=[5, 52, 5.05, 52.05])

    def test_cli_outputs_only_to_private_local_file(self):
        p, b, a = fixture()
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for name, payload in (("parcels", p), ("bgt", b), ("bag", a)):
                (folder / (name + ".json")).write_text(json.dumps(payload), encoding="utf-8")
            dest = folder / "private-overlap.sql"
            argv = ["--parcels", str(folder / "parcels.json"),
                    "--bgt", str(folder / "bgt.json"),
                    "--bag", str(folder / "bag.json"),
                    "--bbox", "5,52,5.005,52.005", "--out", str(dest)]
            self.assertEqual(main(argv), 0)
            self.assertIn("ST_Intersection", dest.read_text(encoding="utf-8"))
            self.assertEqual(main([*argv[:-1], str(ROOT / "forbidden-generated.sql")]), 2)
            self.assertFalse((ROOT / "forbidden-generated.sql").exists())


if __name__ == "__main__":
    unittest.main()
