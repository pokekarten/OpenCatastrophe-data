# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only NYC OTI geometry structural preflight regressions."""

import json
import unittest
from urllib.parse import parse_qs, urlsplit

from research_runners.nyc_oti_geometry_smoke_v0 import (
    GeometryProbeError, TransportFailure, _parse, footprint_url, geometry_screen,
    ll84_url, main, run_live, summarize,
)


def polygon(x=-74.010, y=40.710):
    return {"type": "MultiPolygon", "coordinates": [[[
        [x, y], [x + 0.001, y], [x + 0.001, y + 0.001],
        [x, y + 0.001], [x, y],
    ]]]}


def fixtures():
    ll = [
        {
            "property_id": str(1000 + i), "report_year": "2024",
            "nyc_borough_block_and_lot": f"1000{i:06d}",
            "nyc_building_identification": f"100{i+1:04d}",
            "parent_property_id": "Not Applicable: Standalone Property",
            "number_of_buildings": "1",
        }
        for i in range(30)
    ]
    fp = [
        {
            "bin": f"100{i+1:04d}",
            "doitt_id": str(80001 + i),
            "base_bbl": f"1000{i if i < 22 else i + 1000:06d}",
            "mappluto_bbl": f"1000{i:06d}",
            "feature_code": "2100",
            "the_geom": polygon(-74.020 + i * 0.002, 40.710),
            "geom_source": "Photogrammetric" if i < 20 else "Other (Manual)",
            "construction_year": "0" if i == 29 else "1979",
            "last_edited_date": "2020-01-20T15:33:00.000Z",
        }
        for i in range(30)
    ]
    return ll, fp


class TestNYCOTIGeometrySmoke(unittest.TestCase):
    def test_synthetic_smoke_with_all_fail_closed_flags(self):
        ll, fp = fixtures()
        result = summarize(ll, fp)
        self.assertEqual(result["footprints"], 30)
        self.assertEqual(result["ring_structure_and_bbox_passed"], 30)
        self.assertEqual(result["geometry_source_counts"],
                         {"Other (Manual)": 10, "Photogrammetric": 20})
        self.assertEqual(result["physical_base_bbl_vs_billing_mappluto_bbl"],
                         {"different": 8, "equal": 22})
        self.assertEqual(result["construction_year_missing_or_zero"], 1)
        self.assertEqual(result["vertices"], {"total": 150, "min": 5, "max": 5})
        self.assertEqual(result["multipart_features"], 0)
        self.assertFalse(result["historical_2024_presence_proven"])
        self.assertFalse(result["topology_survey_or_equal_area_crs_proven"])
        self.assertFalse(result["source_rights_or_model_admission_approved"])
        self.assertFalse(result["insurance_tiv_or_loss_calculated"])
        self.assertFalse(result["raw_property_ids_bin_bbl_or_geometry_exported"])
        self.assertNotIn("coordinates", str(result))
        self.assertNotIn("80001", str(result))

    def test_structural_screen_not_true_topological_intersection(self):
        vertices, approx, parts, holes = geometry_screen(polygon())
        self.assertEqual((vertices, parts, holes), (5, 1, 0))
        self.assertGreater(approx, 1000)
        self.assertLess(approx, 20_000)

    def test_multipart_and_hole_are_reported_without_geojson_export(self):
        ll, fp = fixtures()
        shape = polygon()
        shape["coordinates"][0].append([
            [-74.0098, 40.7102], [-74.0098, 40.7104],
            [-74.0096, 40.7104], [-74.0096, 40.7102],
            [-74.0098, 40.7102],
        ])
        shape["coordinates"].append(polygon(-74.007, 40.714)["coordinates"][0])
        fp[0]["the_geom"] = shape
        res = summarize(ll, fp)
        self.assertEqual(res["multipart_features"], 1)
        self.assertEqual(res["features_with_inner_rings"], 1)

    def test_reject_bad_rings_and_fake_wgs84(self):
        for kind in ("unclosed", "wrong_crs", "nan", "three_dims", "missing",
                     "flat", "point", "wrong_type", "nonlist", "too_many_parts"):
            g = polygon()
            if kind == "unclosed":
                g["coordinates"][0][0][-1] = [-74.011, 40.710]
            elif kind == "wrong_crs":
                g["coordinates"][0][0][1] = [300000, 450000]
            elif kind == "nan":
                g["coordinates"][0][0][1] = [float("nan"), 40.710]
            elif kind == "three_dims":
                g["coordinates"][0][0][1] = [-74.009, 40.710, 15]
            elif kind == "missing":
                g["coordinates"] = []
            elif kind == "flat":
                g["coordinates"][0][0][1][1] = 40.710
                g["coordinates"][0][0][2][1] = 40.710
                g["coordinates"][0][0][3][1] = 40.710
            elif kind == "point":
                g = {"type": "Point", "coordinates": [-74.01, 40.71]}
            elif kind == "wrong_type":
                g["type"] = "Polygon"
            elif kind == "nonlist":
                g["coordinates"][0][0][0] = (-74.01, 40.71)
            elif kind == "too_many_parts":
                g["coordinates"] *= 101
            with self.subTest(kind=kind), self.assertRaises(GeometryProbeError):
                geometry_screen(g)

    def test_request_is_bounded_and_excludes_sensitive_columns(self):
        ll = urlsplit(ll84_url())
        q = parse_qs(ll.query)
        self.assertEqual(q["$limit"], ["30"])
        self.assertEqual(q["$order"], ["property_id ASC"])
        self.assertEqual(ll.hostname, "data.cityofnewyork.us")
        fs = footprint_url(tuple(f"100{i+1:04d}" for i in range(5)))
        parsed = urlsplit(fs)
        query = parse_qs(parsed.query)
        self.assertEqual(query["$limit"], ["100"])
        self.assertEqual(query["$select"], [
            "bin,doitt_id,base_bbl,mappluto_bbl,feature_code,the_geom,"
            "geom_source,construction_year,last_edited_date"
        ])
        self.assertNotIn("insured", fs)
        self.assertNotIn("address", fs)
        self.assertEqual(parse_qs(urlsplit(footprint_url(("1000001",))).query)["$limit"], ["20"])

    def test_invalid_bin_and_identifier_injection_blocked(self):
        for batch in ((), ("1000001",) * 2,
                      tuple(f"100{i+1:04d}" for i in range(6)),
                      ("1000000",), ("1000001); drop table",),
                      ("1000001.000",), (1000001,)):
            with self.subTest(batch=batch), self.assertRaises(GeometryProbeError):
                footprint_url(batch)

    def test_mocked_offline_full_run(self):
        ll, fp = fixtures()
        by_bin = {r["bin"]: r for r in fp}
        calls = []
        def fake_fetch(url):
            calls.append(url)
            if url == ll84_url():
                return json.dumps(ll).encode()
            query = parse_qs(urlsplit(url).query)
            ids = query["$where"][0].split("(")[1].rstrip(")").split(",")
            return json.dumps([by_bin[x] for x in ids]).encode()
        out = run_live(fake_fetch)
        self.assertEqual(out["footprints"], 30)
        self.assertEqual(len(calls), 7)
        self.assertTrue(all(urlsplit(c).hostname == "data.cityofnewyork.us" for c in calls))

    def test_timeout_fallback_only_for_transport_exception(self):
        ll, fp = fixtures()
        by_bin = {r["bin"]: r for r in fp}
        calls = {"single": 0, "failed": 0}
        def fake_fetch(url):
            if url == ll84_url():
                return json.dumps(ll).encode()
            ids = parse_qs(urlsplit(url).query)["$where"][0].split("(")[1].rstrip(")").split(",")
            if len(ids) == 5 and ids[0] == "1000006":
                calls["failed"] += 1
                raise TransportFailure("simulated batch timeout")
            if len(ids) == 1:
                calls["single"] += 1
            return json.dumps([by_bin[x] for x in ids]).encode()
        self.assertEqual(run_live(fake_fetch)["footprints"], 30)
        self.assertEqual(calls, {"single": 5, "failed": 1})

    def test_persistent_single_bin_transport_failure_blocks_all(self):
        ll, _ = fixtures()
        def mock(url):
            if url == ll84_url():
                return json.dumps(ll).encode()
            raise TransportFailure("simulated persistent failure")
        with self.assertRaises(TransportFailure):
            run_live(mock)

    def test_bad_source_framing_or_cardinality_fails_closed(self):
        for data in (b"{}", b"null", b"bad", b"[1]", b"[{}]" + b" " * 300000):
            with self.subTest(data=data[:20]), self.assertRaises(GeometryProbeError):
                _parse(data, 20)
        with self.assertRaises(GeometryProbeError):
            _parse(b'[{}, {}]', 2)

    def test_identity_and_revision_flags_block_false_geometry_proof(self):
        for kind in ("duplicate_ll84", "missing_bin", "wrong_year", "multi_bbl",
                     "duplicate_footprint", "wrong_mappluto", "wrong_doitt",
                     "nonbuilding", "wrong_row_count", "bad_geom_source"):
            ll, fp = fixtures()
            if kind == "duplicate_ll84":
                ll[1]["property_id"] = ll[0]["property_id"]
            elif kind == "missing_bin":
                ll[0]["nyc_building_identification"] = "1000000"
            elif kind == "wrong_year":
                ll[0]["report_year"] = "2023"
            elif kind == "multi_bbl":
                ll[0]["nyc_borough_block_and_lot"] += ";1000009999"
            elif kind == "duplicate_footprint":
                fp[1]["bin"] = fp[0]["bin"]
            elif kind == "wrong_mappluto":
                fp[0]["mappluto_bbl"] = "1000009999"
            elif kind == "wrong_doitt":
                fp[1]["doitt_id"] = fp[0]["doitt_id"]
            elif kind == "nonbuilding":
                fp[0]["feature_code"] = "1003"
            elif kind == "wrong_row_count":
                fp.pop()
            elif kind == "bad_geom_source":
                fp[0]["geom_source"] = "Unknown vendor"
            with self.subTest(kind=kind), self.assertRaises(GeometryProbeError):
                summarize(ll, fp)

    def test_post_2024_features_get_flagged_not_automatically_admitted(self):
        ll, fp = fixtures()
        fp[0]["construction_year"] = "2026"
        fp[0]["last_edited_date"] = "2026-01-02T09:00:00.000Z"
        report = summarize(ll, fp)
        self.assertEqual(report["construction_year_after_2024"], 1)
        self.assertEqual(report["last_edit_year_after_2024"], 1)
        self.assertFalse(report["historical_2024_presence_proven"])

    def test_without_live_does_not_call_network(self):
        with self.assertRaises(SystemExit) as cm:
            main([])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
