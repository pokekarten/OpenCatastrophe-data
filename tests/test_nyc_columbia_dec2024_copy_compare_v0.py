# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only regressions for dated third-party NYC ArcGIS-copy comparison."""

from collections import Counter
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from research_runners.nyc_columbia_dec2024_copy_compare_v0 import (
    CopyProbeError, CopyTransportError, N, count_url, feature_urls,
    item_url, layer_url, ll84_url, main, parse_ll84, run_live,
    summarize, validate_provider,
)

CREATED = 1733607935000  # 2024-12-07 21:45:35 UTC (synthetic test receipt)
MODIFIED = 1733608920000  # 2024-12-07 22:02:00 UTC (synthetic test receipt)
EDITED = 1733608913896
FIELDS = ("BIN", "DOITT_ID", "BASE_BBL", "MPLUTO_BBL", "FEAT_CODE", "CNSTRCT_YR", "LSTMODDATE")


def ring(i=0):
    x = -74.01 + i * 0.002
    y = 40.70
    return [[x, y], [x + .001, y], [x + .001, y + .001],
            [x, y + .001], [x, y]]


def fixture():
    item = {
        "id": "66e3c725ad9843569da25ce1059a3807",
        "owner": "rm4068_columbia", "access": "public",
        "created": CREATED, "modified": MODIFIED,
    }
    layer = {
        "serviceItemId": item["id"], "name": "building",
        "editingInfo": {
            "lastEditDate": EDITED, "dataLastEditDate": EDITED,
            "schemaLastEditDate": EDITED,
        },
        "extent": {"spatialReference": {"wkid": 102718, "latestWkid": 2263}},
        "fields": [{"name": f} for f in FIELDS],
    }
    count = {"count": 1082964}
    ll84, old, now = [], [], []
    for i in range(N):
        b = f"100{i+1:04d}"
        billing = f"1000{i:06d}"
        physical = f"1000{i if i < 22 else i+1000:06d}"
        doitt = str(100000 + i)
        ll84.append({
            "property_id": str(2000 + i),
            "nyc_borough_block_and_lot": billing,
            "nyc_building_identification": b,
            "parent_property_id": "Not Applicable: Standalone Property",
            "number_of_buildings": "1",
            "report_year": "2024",
        })
        old.append({
            "attributes": {
                "BIN": int(b), "DOITT_ID": int(doitt),
                "BASE_BBL": physical, "MPLUTO_BBL": billing,
                "FEAT_CODE": 2100, "CNSTRCT_YR": 1979,
                "LSTMODDATE": 1610000000000,
            },
            "geometry": {"rings": [ring(i)]},
        })
        now.append({
            "bin": b, "doitt_id": doitt, "base_bbl": physical,
            "mappluto_bbl": billing, "feature_code": "2100",
            "the_geom": {"type": "MultiPolygon", "coordinates": [[[pt[:] for pt in ring(i)]]]},
        })
    old_groups, current_groups = [], []
    for start in range(0, N, 5):
        old_groups.append({"spatialReference": {"wkid": 4326, "latestWkid": 4326},
                           "features": old[start:start+5]})
        current_groups.append(now[start:start+5])
    return item, layer, count, ll84, old_groups, current_groups


def dumps(x):
    return json.dumps(x, separators=(",", ":")).encode("utf-8")


class NYCDec2024CopyTests(unittest.TestCase):
    def test_complete_synthetic_thirty_comparison_and_no_admission(self):
        source = fixture()
        out = summarize(*source)
        self.assertEqual(out["cohort_size"], 30)
        self.assertEqual(out["provider_copy_feature_count"], 1082964)
        self.assertEqual(out["provider_copy_item_created_utc"], "2024-12-07")
        for key in (
            "both_provider_buildings", "stable_doitt", "stable_base_bbl",
            "stable_billing_bbl", "old_billing_matches_ll84_bbl",
            "same_number_of_ring_vertices", "bbox_within_1e_9_degrees",
            "bbox_within_1e_5_degrees",
        ):
            self.assertEqual(out["original_source_comparison"][key], 30)
        self.assertEqual(out["original_source_comparison"]["old_base_bbl_matches_ll84_bbl"], 22)
        for k in (
            "official_nyc_oti_archive_release_attested",
            "original_source_2024_full_snapshot_sha256_known",
            "authenticated_original_nyc_asof_2024_stock",
            "external_replica_reuse_rights_approved",
            "worldwide_exposure_or_insured_tiv_calculated",
            "raw_external_source_rows_ids_or_geometries_exported",
        ):
            self.assertFalse(out[k])
        self.assertNotIn("coordinates", str(out))
        self.assertNotIn("1000001", str(out))
        self.assertNotIn("-74.01", str(out))

    def test_synthetic_single_submeter_bbox_delta_is_not_false_exact_match(self):
        item, layer, count, ll84, old, now = fixture()
        for point in now[0][0]["the_geom"]["coordinates"][0][0]:
            point[0] += 1.48e-7
        out = summarize(item, layer, count, ll84, old, now)
        sums = out["original_source_comparison"]
        self.assertEqual(sums["same_number_of_ring_vertices"], 30)
        self.assertEqual(sums["bbox_within_1e_9_degrees"], 29)
        self.assertEqual(sums["bbox_within_1e_5_degrees"], 30)
        self.assertGreater(out["max_bbox_abs_delta_degrees"], 1e-7)
        self.assertTrue(out["bbox_diagnostics_are_not_geometric_equivalence"])

    def test_reject_undated_or_revised_columbia_copy(self):
        for defect in ("owner", "access", "item_id", "created", "modified",
                       "lastEditDate", "dataLastEditDate", "schemaLastEditDate",
                       "wrong_crs", "wrong_feature_count", "missing_field",
                       "service_id"):
            item, layer, count, *_ = fixture()
            if defect == "owner":
                item["owner"] = "unknown"
            elif defect == "access":
                item["access"] = "private"
            elif defect == "item_id":
                item["id"] = "not_the_same_source"
            elif defect in ("created", "modified"):
                item[defect] += 40 * 86400 * 1000
            elif defect in ("lastEditDate", "dataLastEditDate", "schemaLastEditDate"):
                layer["editingInfo"][defect] += 40 * 86400 * 1000
            elif defect == "wrong_crs":
                layer["extent"]["spatialReference"]["latestWkid"] = 3857
            elif defect == "wrong_feature_count":
                count["count"] = 1082965
            elif defect == "missing_field":
                layer["fields"].pop()
            elif defect == "service_id":
                layer["serviceItemId"] = "different"
            with self.subTest(defect=defect), self.assertRaises(CopyProbeError):
                validate_provider(item, layer, count)

    def test_30_original_ll84_cohort_ambiguity_blocked(self):
        for defect in ("missing", "wrong_year", "campus", "two_buildings",
                       "multi_bin", "dummy_bin", "duplicate_bin", "duplicate_property",
                       "wrong_bbl_prefix"):
            item, layer, count, ll, old, curr = fixture()
            if defect == "missing":
                ll.pop()
            elif defect == "wrong_year":
                ll[0]["report_year"] = "2025"
            elif defect == "campus":
                ll[0]["parent_property_id"] = "12345"
            elif defect == "two_buildings":
                ll[0]["number_of_buildings"] = "2"
            elif defect == "multi_bin":
                ll[0]["nyc_building_identification"] += ";1009999"
            elif defect == "dummy_bin":
                ll[0]["nyc_building_identification"] = "1000000"
            elif defect == "duplicate_bin":
                ll[0]["nyc_building_identification"] = ll[1]["nyc_building_identification"]
            elif defect == "duplicate_property":
                ll[0]["property_id"] = ll[1]["property_id"]
            elif defect == "wrong_bbl_prefix":
                ll[0]["nyc_borough_block_and_lot"] = "2000000001"
            with self.subTest(defect=defect), self.assertRaises(CopyProbeError):
                parse_ll84(ll)

    def test_source_query_pinning_and_no_sensitive_fields(self):
        for name, url in (
            ("item", item_url()), ("layer", layer_url()),
            ("count", count_url()), ("ll84", ll84_url()),
        ):
            with self.subTest(name=name):
                p = urlsplit(url)
                self.assertEqual(p.scheme, "https")
                self.assertIn(p.hostname, ("www.arcgis.com", "services2.arcgis.com", "data.cityofnewyork.us"))
                self.assertNotIn("owner_name", url)
                self.assertNotIn("address", url)
        old, current = feature_urls(tuple(f"100{i+1:04d}" for i in range(5)))
        self.assertEqual(parse_qs(urlsplit(old).query)["returnGeometry"], ["true"])
        self.assertEqual(parse_qs(urlsplit(old).query)["outSR"], ["4326"])
        self.assertEqual(parse_qs(urlsplit(current).query)["$limit"], ["100"])
        self.assertIn("the_geom", current)

    def test_invalid_batch_or_dummy_id_blocked(self):
        for b in ((), ("1000000",), ("1000001", "1000001"),
                  ("1000001 OR 1=1",), ("1000001.0",),
                  tuple(f"100{i+1:04d}" for i in range(6)), (1000001,)):
            with self.subTest(b=b), self.assertRaises(CopyProbeError):
                feature_urls(b)

    def test_arcgis_feature_errors_fail_closed(self):
        for defect in ("duplicate_bin", "invalid_doitt", "nonbuilding",
                       "wrong_arc_crs", "unclosed_ring", "wrong_geometry_coords",
                       "missing_arc_feature", "extra_arc_feature"):
            item, layer, count, ll, old, curr = fixture()
            if defect == "duplicate_bin":
                old[0]["features"][1]["attributes"]["BIN"] = old[0]["features"][0]["attributes"]["BIN"]
            elif defect == "invalid_doitt":
                old[0]["features"][0]["attributes"]["DOITT_ID"] = 0
            elif defect == "nonbuilding":
                old[0]["features"][0]["attributes"]["FEAT_CODE"] = 1003
            elif defect == "wrong_arc_crs":
                old[0]["spatialReference"]["latestWkid"] = 2263
            elif defect == "unclosed_ring":
                old[0]["features"][0]["geometry"]["rings"][0][-1] = [-74.009, 40.72]
            elif defect == "wrong_geometry_coords":
                old[0]["features"][0]["geometry"]["rings"][0][1] = [500000, 456000]
            elif defect == "missing_arc_feature":
                old[0]["features"].pop()
            elif defect == "extra_arc_feature":
                old[0]["exceededTransferLimit"] = True
            with self.subTest(defect=defect), self.assertRaises(CopyProbeError):
                summarize(item, layer, count, ll, old, curr)

    def test_current_city_feature_errors_fail_closed(self):
        for defect in ("missing", "wrong_bin", "wrong_doitt", "not_multipolygon",
                       "ring_not_closed", "geometry_not_nyc", "not_standard_building"):
            item, layer, count, ll, old, curr = fixture()
            if defect == "missing":
                curr[0].pop()
            elif defect == "wrong_bin":
                curr[0][0]["bin"] = "2001023"
            elif defect == "wrong_doitt":
                curr[0][0]["doitt_id"] = "0"
            elif defect == "not_multipolygon":
                curr[0][0]["the_geom"]["type"] = "Point"
            elif defect == "ring_not_closed":
                curr[0][0]["the_geom"]["coordinates"][0][0][0] = [-74.001, 40.70]
            elif defect == "geometry_not_nyc":
                curr[0][0]["the_geom"]["coordinates"][0][0][1] = [-80, 30]
            elif defect == "not_standard_building":
                curr[0][0]["feature_code"] = "1003"
            with self.subTest(defect=defect), self.assertRaises(CopyProbeError):
                summarize(item, layer, count, ll, old, curr)

    def test_current_city_copy_disagreement_is_diagnostic_not_false_source_admission(self):
        item, layer, count, ll, old, curr = fixture()
        curr[0][0]["base_bbl"] = "1000009999"
        curr[0][0]["doitt_id"] = "999999"
        out = summarize(item, layer, count, ll, old, curr)
        self.assertEqual(out["original_source_comparison"]["stable_base_bbl"], 29)
        self.assertEqual(out["original_source_comparison"]["stable_doitt"], 29)
        self.assertFalse(out["authenticated_original_nyc_asof_2024_stock"])

    def test_full_offline_network_mock_for_30_using_only_pinned_queries(self):
        item, layer, count, ll, old, curr = fixture()
        response_map = {
            item_url(): item, layer_url(): layer, count_url(): count,
            ll84_url(): ll,
        }
        for i in range(6):
            arr = tuple(f"100{j+1:04d}" for j in range(i*5, i*5+5))
            o, c = feature_urls(arr)
            response_map[o] = old[i]
            response_map[c] = curr[i]
        calls = []
        def fetch(url):
            calls.append(url)
            return dumps(response_map[url])
        out = run_live(fetch)
        self.assertEqual(out["original_source_comparison"]["stable_doitt"], 30)
        self.assertEqual(len(calls), 16)
        self.assertTrue(all(urlsplit(c).scheme == "https" for c in calls))

    def test_batch_transport_failure_fallback_both_sources(self):
        item, layer, count, ll, old, curr = fixture()
        initial = {
            item_url(): item, layer_url(): layer, count_url(): count,
            ll84_url(): ll,
        }
        single = {}
        for i in range(6):
            arr = tuple(f"100{j+1:04d}" for j in range(i*5, i*5+5))
            o, c = feature_urls(arr)
            initial[o] = old[i]
            initial[c] = curr[i]
            for j, b in enumerate(arr):
                u, v = feature_urls((b,))
                single[u] = {
                    "spatialReference": {"wkid": 4326, "latestWkid": 4326},
                    "features": [old[i]["features"][j]],
                }
                single[v] = [curr[i][j]]
        first = tuple(f"100{j+1:04d}" for j in range(5))
        failure_urls = set(feature_urls(first))
        calls = Counter()
        def fetch(url):
            calls[url] += 1
            if url in failure_urls:
                raise CopyTransportError("simulated original transport issue")
            return dumps(initial[url] if url in initial else single[url])
        # Regression checks both bounded five-BIN fallbacks.
        result = run_live(fetch)
        self.assertEqual(result["original_source_comparison"]["stable_doitt"], 30)
        self.assertEqual(sum(v for k, v in calls.items() if k in single), 10)

    def test_failed_single_bin_response_blocks_instead_of_counting_missing(self):
        item, layer, count, ll, old, curr = fixture()
        cache = {item_url(): item, layer_url(): layer, count_url(): count, ll84_url(): ll}
        def fetch(url):
            if url in cache:
                return dumps(cache[url])
            raise CopyTransportError("persistent failure")
        with self.assertRaises(CopyTransportError):
            run_live(fetch)

    def test_no_network_without_explicit_optin(self):
        with self.assertRaises(SystemExit) as ctx:
            main([])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
