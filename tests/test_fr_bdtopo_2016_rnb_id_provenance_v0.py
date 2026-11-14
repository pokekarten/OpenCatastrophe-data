# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only; test 2016 v2.1 DBF ID provenance without ID/geometry publication."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pyproj import CRS, Transformer
import shapefile
from shapely.geometry import Polygon, mapping

from research_runners.fr_bdtopo_2016_rnb_id_provenance_v0 import (
    bounded_historical_attribute_receipts, research_id_crosscheck,
    rnb_external_id_receipts, RNB_IDS, BridgeError,
)


class HistoricalDbfIdTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        t=Transformer.from_crs(4326,2154,always_xy=True)
        self.points=[t.transform(*p) for p in (
            (2.54700,48.53663),(2.54762,48.53673),(2.54830,48.53715))]
        for family in ("BATI_INDIFFERENCIE","BATI_INDUSTRIEL","BATI_REMARQUABLE"):
            with shapefile.Writer(str(self.folder/family),shapeType=shapefile.POLYGON) as w:
                w.field("ID","C",size=35)
                w.field("DATE_CREAT","C",size=16)
                w.field("ORIGIN_BAT","C",size=20)
                w.field("HAUTEUR","N",size=8,decimal=1)
                if family=="BATI_INDIFFERENCIE":
                    for i,(x,y) in enumerate(self.points):
                        # Proper clockwise ESRI outer ring; no real data.
                        w.poly([[(x-5,y-5),(x-5,y+5),(x+5,y+5),
                                 (x+5,y-5),(x-5,y-5)]])
                        w.record("SYNTHETIC-2016-{}".format(i),"2016-03-24","CADASTRE",9.5)
            (self.folder/(family+".prj")).write_text(
                CRS.from_epsg(2154).to_wkt(),encoding="utf8")

    def payload(self,rnb_id):
        lon,lat=(2.54700,48.53663) if rnb_id==RNB_IDS[0] else (2.54762,48.53673)
        rect=Polygon([(lon-0.00003,lat-0.00003),(lon+0.00003,lat-0.00003),
                      (lon+0.00003,lat+0.00003),(lon-0.00003,lat+0.00003)])
        return json.dumps({
            "rnb_id":rnb_id,"status":"constructed","is_active":True,
            "shape":mapping(rect),
            "ext_ids":[
                {"source":"bdtopo","source_version":"bdtopo_2023_09",
                 "id":"SYNTHETIC-2016-0" if rnb_id==RNB_IDS[0] else "NEW-2023-ID"},
                {"source":"bdnb","source_version":"2023_01","id":"OTHER-ID"}
            ],
        }).encode("utf8")

    def test_original_dbf_source_fields_and_hashes(self):
        items,schema=bounded_historical_attribute_receipts(self.folder)
        self.assertEqual(len(items),3)
        self.assertIn("ID",schema["BATI_INDIFFERENCIE"])
        self.assertIn("DATE_CREAT",schema["BATI_INDIFFERENCIE"])
        self.assertEqual(items[0]["original_temporal_field_values"]["DATE_CREAT"],"2016-03-24")
        self.assertEqual(items[0]["original_id_sha256_by_field"]["ID"]["sha256"],
                         hashlib.sha256(b"SYNTHETIC-2016-0").hexdigest())
        self.assertNotIn("SYNTHETIC-2016-0",json.dumps(items))
        quality=items[0]["original_source_quality_attributes"]
        self.assertEqual(quality["original_origin_bat_category"],"CADASTRE")
        self.assertEqual(
            quality["historic_numeric_fields_as_stored_not_verified_exposure"]["HAUTEUR"],9.5)
        self.assertTrue(quality["fields_are_not_2016_construction_or_insured_values"])

    def test_cross_version_literal_id_hash_is_not_identity(self):
        receipt=research_id_crosscheck(self.folder,fetch=self.payload)
        self.assertEqual(receipt["historical_bounded_aoi_candidate_count"],3)
        self.assertEqual(receipt["rnb_modern_bdtopo_mapping_versions_observed"],
                         ["bdtopo_2023_09"])
        self.assertEqual(
            receipt["original_bounded_attribute_receipts"][0]
            ["literal_2016_id_matches_2023_bdtopo_external_id_by_rnb"][RNB_IDS[0]],
            ["ID"])
        self.assertFalse(receipt["historic_current_same_physical_building_identity_proven"])
        self.assertFalse(receipt["original_v21_identifiers_version_stable_proven"])
        self.assertFalse(receipt["cat_model_admitted"])
        self.assertFalse(receipt["raw_historic_or_current_source_ids_logged"])
        self.assertNotIn("SYNTHETIC-2016-0",json.dumps(receipt))

    def test_source_version_exactly_preserved(self):
        ext,ids=rnb_external_id_receipts(self.payload(RNB_IDS[1]),RNB_IDS[1])
        self.assertEqual(len(ext),2)
        self.assertEqual(ids,["NEW-2023-ID"])
        self.assertNotIn("NEW-2023-ID",json.dumps(ext))

    def test_wrong_source_identity_rejected(self):
        with self.assertRaisesRegex(BridgeError,"identity/status"):
            rnb_external_id_receipts(self.payload(RNB_IDS[1]),RNB_IDS[0])

    def test_missing_shapefile_component_rejected(self):
        (self.folder/"BATI_INDUSTRIEL.dbf").unlink()
        with self.assertRaisesRegex(BridgeError,"missing or unsafe"):
            bounded_historical_attribute_receipts(self.folder)


if __name__=="__main__":
    unittest.main()
