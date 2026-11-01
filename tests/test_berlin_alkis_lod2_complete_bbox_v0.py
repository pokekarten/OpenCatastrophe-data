# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic full-in-box original Berlin ALKIS vs LoD2 source regressions."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import io
import importlib.util
import json
import unittest

from research_runners.berlin_alkis_lod2_complete_bbox_v0 import (
    COUNT_LIMIT, URLS, MIN_IOU, CompleteBboxError, evaluate, probe,
)
from tests.test_berlin_alkis_gebaeude_five_feature_join_v0 import fixture, raw

HAS_SPATIAL = importlib.util.find_spec('shapely') is not None


def pair():
    a=fixture(n=3)
    h=copy.deepcopy(a)
    for i,f in enumerate(h["features"]):
        f["id"]=f"other-independent-original-source-{i}"
        f["properties"]={
            "role_txt":"Gebäude" if i<2 else "Bauteil",
            "hoehe":3.0 if i==0 else 9.0+i,
            "dachart":f"source-roof-class-{i}",
            "geschosse":2+i,
            "grundrissaktualitaet":"2022-04-07",
        }
    for obj in (a,h):
        obj["numberMatched"]=len(obj["features"])
        obj["numberReturned"]=len(obj["features"])
    return a,h


class Response(io.BytesIO):
    status=200
    def __init__(self,b,url):
        super().__init__(b)
        self.url=url
        self.headers={"Content-Type":"application/json"}
    def geturl(self):return self.url


class CompletenessAndMatchingTests(unittest.TestCase):
    def test_fixed_50_cap_no_broad_source_recursion(self):
        self.assertEqual(COUNT_LIMIT,50)
        self.assertEqual(MIN_IOU,0.95)
        self.assertEqual(len(URLS),2)
        self.assertNotEqual(*list(URLS.values()))
        for url in URLS.values():
            self.assertIn("count=50",url)
            self.assertIn("391700",url)
            self.assertIn("EPSG%3A25833",url)

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_realistic_bijective_geometry_must_not_map_by_id(self):
        a,h=pair()
        result=evaluate(raw(a),raw(h))
        self.assertEqual(result["alkis_in_bbox"],3)
        self.assertEqual(result["loD2_2022_in_bbox"],3)
        self.assertEqual(result["unambiguous_one_to_one_footprints"],3)
        self.assertEqual(result["height_positive_numeric_count"],3)
        self.assertEqual(result["three_metre_possible_placeholder_count"],1)
        self.assertEqual(result["height_role_text_counts"]["Bauteil"],1)
        self.assertEqual(result["matched_height_source_role_counts"],{
            "Gebäude":2,"Bauteil":1,"Gebäudeteil":0,"unknown":0,
        })
        self.assertEqual(result["matched_positive_numeric_height_count"],3)
        self.assertEqual(result["matched_exact_3m_possible_placeholder_count"],1)
        self.assertEqual(result["matched_positive_non3m_height_count_not_proven_measured"],2)
        self.assertEqual(result["matched_recognized_building_role_positive_non3m_count_research_only"],1)
        self.assertEqual(result["matched_source_method_field_non_null_counts"],{
            "quellebodenhoehe":0,"quelledachhoehe":0,"quellelage":0,
        })
        self.assertEqual(result["matched_source_height_admitted_to_insurer_exposure"],0)
        self.assertFalse(result["model_input_admitted"])
        self.assertNotIn("source-roof-class",str(result))

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_unknown_role_and_missing_matched_height_remain_unadmitted(self):
        a,h=pair()
        h["features"][1]["properties"]["role_txt"]="unreviewed provider role"
        h["features"][1]["properties"]["hoehe"]=None
        report=evaluate(raw(a),raw(h))
        self.assertEqual(report["unambiguous_one_to_one_footprints"],3)
        self.assertEqual(report["matched_height_source_role_counts"]["unknown"],1)
        self.assertEqual(report["matched_positive_numeric_height_count"],2)
        self.assertEqual(report["matched_exact_3m_possible_placeholder_count"],1)
        self.assertEqual(report["matched_positive_non3m_height_count_not_proven_measured"],1)
        self.assertEqual(report["matched_recognized_building_role_positive_non3m_count_research_only"],0)
        self.assertEqual(report["matched_source_height_admitted_to_insurer_exposure"],0)
        self.assertNotIn("unreviewed provider role",str(report))

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_role_vocabulary_hypotheses_never_reclassify_unknown_source_roles(self):
        a,h=pair()
        h["features"][0]["properties"]["role_txt"]="Building"
        h["features"][1]["properties"]["role_txt"]="BuildingPart"
        h["features"][2]["properties"]["role_txt"]="UNKNOWN-PRIVATE@example.org / 123"
        result=evaluate(raw(a),raw(h))
        self.assertEqual(result["matched_height_source_role_counts"]["unknown"],3)
        self.assertTrue(result["role_domain_candidate_terms_not_provider_approved"])
        vocab=result["height_role_literal_domain_probe_counts"]
        self.assertEqual(vocab["all_height_features"]["citygml_building_literal_hypothesis"],1)
        self.assertEqual(vocab["all_height_features"]["citygml_buildingpart_literal_hypothesis"],1)
        self.assertEqual(vocab["all_height_features"]["unrecognized_not_echoed"],1)
        self.assertEqual(vocab["uniquely_matched_height_features"]["unrecognized_not_echoed"],1)
        self.assertFalse(result["model_input_admitted"])
        self.assertEqual(result["matched_source_height_admitted_to_insurer_exposure"],0)
        self.assertNotIn("UNKNOWN-PRIVATE",str(result))
        self.assertNotIn("example.org",str(result))
        self.assertNotIn("BuildingPart",str(result))

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_duplicate_quarantine_role_domain_count_never_enters_matched_subset(self):
        a,h=pair()
        h["features"][1]["geometry"]=copy.deepcopy(h["features"][0]["geometry"])
        h["features"][1]["properties"]["role_txt"]="BuildingPart"
        result=evaluate(raw(a),raw(h))
        domains=result["height_role_literal_domain_probe_counts"]
        self.assertEqual(result["unambiguous_one_to_one_footprints"],1)
        self.assertEqual(domains["duplicate_footprint_quarantined_height_features"]["citygml_buildingpart_literal_hypothesis"],1)
        self.assertEqual(sum(domains["uniquely_matched_height_features"].values()),1)
        self.assertEqual(sum(domains["all_height_features"].values()),3)
        self.assertEqual(result["matched_height_source_role_counts"],{
            "Gebäude":0,"Bauteil":1,"Gebäudeteil":0,"unknown":0
        })
        self.assertFalse(result["model_input_admitted"])

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_original_gebaeudeteil_is_a_distinct_non_insured_literal(self):
        a,h=pair()
        for item in h["features"]:
            item["properties"]["role_txt"]="Gebäudeteil"
        report=evaluate(raw(a),raw(h))
        self.assertEqual(report["height_role_text_counts"]["Gebäudeteil"],3)
        self.assertEqual(report["height_role_text_counts"]["unknown"],0)
        self.assertEqual(report["matched_height_source_role_counts"]["Gebäudeteil"],3)
        self.assertEqual(report["matched_source_gebaeudeteil_not_whole_building_count"],3)
        self.assertEqual(report["matched_recognized_building_role_positive_non3m_count_research_only"],0)
        self.assertTrue(report["source_role_label_not_equivalent_to_insured_building"])
        self.assertFalse(report["model_input_admitted"])

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_gebaeudeteil_in_duplicate_group_is_never_a_matched_unit(self):
        a,h=pair()
        for item in h["features"]:
            item["properties"]["role_txt"]="Gebäudeteil"
        h["features"][1]["geometry"]=copy.deepcopy(h["features"][0]["geometry"])
        report=evaluate(raw(a),raw(h))
        self.assertEqual(report["height_role_text_counts"]["Gebäudeteil"],3)
        self.assertEqual(report["matched_source_gebaeudeteil_not_whole_building_count"],1)
        self.assertEqual(report["duplicate_source_features_quarantined_by_source"]["loD2_2022"],2)
        self.assertEqual(report["unambiguous_one_to_one_footprints"],1)
        self.assertEqual(report["matched_source_height_admitted_to_insurer_exposure"],0)

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_missing_or_unbounded_source_population_refused(self):
        a,h=pair()
        h["numberMatched"]=4
        with self.assertRaisesRegex(CompleteBboxError,"count/pagination"):
            evaluate(raw(a),raw(h))
        a,h=pair()
        del h["numberMatched"]
        with self.assertRaises(CompleteBboxError):
            evaluate(raw(a),raw(h))
        a,h=pair()
        h["crs"]["properties"]["name"]="EPSG:4326"
        with self.assertRaises(CompleteBboxError):
            evaluate(raw(a),raw(h))
        a,h=pair()
        a["features"][1]["id"]=a["features"][0]["id"]
        with self.assertRaises(CompleteBboxError):
            evaluate(raw(a),raw(h))

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_polygon_wrong_or_bbox_false_positives_rejected(self):
        a,h=pair()
        h["features"][0]["geometry"]["type"]="Point"
        with self.assertRaises(CompleteBboxError):
            evaluate(raw(a),raw(h))
        a,h=pair()
        for row in h["features"][0]["geometry"]["coordinates"][0]:
            row[0]+=400
        with self.assertRaises(CompleteBboxError):
            evaluate(raw(a),raw(h))

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_shifted_current_source_no_invented_matches(self):
        a,h=pair()
        # 50 metres shift inside reviewed 200m bbox.
        for feat in h["features"]:
            for ring in feat["geometry"]["coordinates"]:
                for xy in ring:xy[0]+=50
        report=evaluate(raw(a),raw(h))
        self.assertEqual(report["unambiguous_one_to_one_footprints"],0)
        self.assertEqual(report["height_positive_numeric_count"],3)

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_both_sources_must_explicitly_declare_projected_crs(self):
        a,h=pair()
        for source in ("alkis","height"):
            with self.subTest(source=source):
                aa,hh=copy.deepcopy(a),copy.deepcopy(h)
                (aa if source=="alkis" else hh).pop("crs")
                with self.assertRaisesRegex(CompleteBboxError,"explicitly declare"):
                    evaluate(raw(aa),raw(hh))
        a,h=pair()
        h["crs"]={"type":"name","properties":{"name":"EPSG:4326"}}
        with self.assertRaisesRegex(CompleteBboxError,"explicitly declare"):
            evaluate(raw(a),raw(h))

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_distinct_source_ids_cannot_hide_duplicate_original_geometries(self):
        a,h=pair()
        h["features"][1]["geometry"]=copy.deepcopy(h["features"][0]["geometry"])
        h["features"][1]["id"]="different-source-id-same-footprint"
        result=evaluate(raw(a),raw(h))
        self.assertTrue(result["duplicate_footprints_quarantined"])
        self.assertEqual(result["duplicate_footprint_groups_by_source"]["loD2_2022"],1)
        self.assertEqual(result["duplicate_source_features_quarantined_by_source"]["loD2_2022"],2)
        self.assertEqual(result["unambiguous_one_to_one_footprints"],1)
        self.assertEqual(result["unmatched_height_product_count"],2)
        self.assertEqual(result["matched_positive_numeric_height_count"],1)
        self.assertEqual(result["confirmed_height_values_assigned_to_CAT4"],0)
        a,h=pair()
        a["features"][1]["geometry"]=copy.deepcopy(a["features"][0]["geometry"])
        a["features"][1]["id"]="different-alkis-id-same-footprint"
        result=evaluate(raw(a),raw(h))
        self.assertEqual(result["duplicate_footprint_groups_by_source"]["alkis"],1)
        self.assertEqual(result["duplicate_source_features_quarantined_by_source"]["alkis"],2)
        self.assertEqual(result["unambiguous_one_to_one_footprints"],1)
        self.assertFalse(result["model_input_admitted"])

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_three_identical_polygon_members_all_quarantined_independent_of_ids(self):
        a,h=pair()
        for i in (1,2):
            h["features"][i]["geometry"]=copy.deepcopy(h["features"][0]["geometry"])
        r=evaluate(raw(a),raw(h))
        self.assertEqual(r["duplicate_source_features_quarantined_by_source"]["loD2_2022"],3)
        self.assertEqual(r["duplicate_footprint_groups_by_source"]["loD2_2022"],1)
        self.assertEqual(r["unambiguous_one_to_one_footprints"],0)
        self.assertEqual(r["loD2_2022_in_bbox"],3)
        self.assertEqual(r["matched_positive_numeric_height_count"],0)
        self.assertFalse(r["model_input_admitted"])

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed Shapely spatial job required")
    def test_two_exact_original_requests_and_no_serialized_source_values(self):
        a,h=pair()
        calls=[]
        def fake(req,timeout):
            calls.append(req.full_url)
            return Response(raw(a) if req.full_url==URLS["alkis"] else raw(h),
                            req.full_url)
        report=probe(opener=fake,clock=lambda:datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(calls,[URLS["alkis"],URLS["loD2_2022"]])
        self.assertEqual(report["unambiguous_one_to_one_footprints"],3)
        self.assertFalse(report["original_provider_geometry_persisted"])
        self.assertFalse(report["CAT_or_other_persistent_db_modified"])
        self.assertNotIn("other-independent-original-source",str(report))


if __name__=="__main__":
    unittest.main()
