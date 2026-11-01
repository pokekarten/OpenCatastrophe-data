# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic GDAL/Fiona alternate-reader tests; zero provider coordinates."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import unittest
from unittest.mock import patch
import zipfile

from research_runners import hanze_regions2024_geometry_zip_audit_v0 as arch
from research_runners.hanze_2024_gdal_fiona_geometry_review_v0 import (
    validate_original_with_gdal_fiona, RegionArchiveError,
)

HAS_ENGINE = all(importlib.util.find_spec(m) for m in ("fiona", "shapefile", "shapely"))
PRJ = ('PROJCS["ETRS_1989_LAEA",GEOGCS["GCS_ETRS_1989",'
       'DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137.0,298.257222101]],'
       'UNIT["Degree",0.0174532925199433]],'
       'PROJECTION["Lambert_Azimuthal_Equal_Area"],'
       'PARAMETER["False_Easting",4321000.0],'
       'PARAMETER["False_Northing",3210000.0],'
       'PARAMETER["Central_Meridian",10.0],'
       'PARAMETER["Latitude_Of_Origin",52.0],UNIT["Meter",1.0]]')
REGULAR_RING = [(0.,0.),(0.,1.),(1.,1.),(1.,0.),(0.,0.)]
BOWTIE = [(0.,0.),(1.,1.),(0.,1.),(1.,0.),(0.,0.)]


def original_like_zip(rings):
    import shapefile
    shp,shx,dbf = io.BytesIO(),io.BytesIO(),io.BytesIO()
    w=shapefile.Writer(shp=shp,shx=shx,dbf=dbf,shapeType=5)
    w.field("Code","C",size=5)
    w.field("Name","C",size=20)
    for i,ring in enumerate(rings):
        w.poly([ring])
        w.record("DE111", "synthetic")
    w.close()
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("source.shp",shp.getvalue())
        z.writestr("source.shx",shx.getvalue())
        z.writestr("source.dbf",dbf.getvalue())
        z.writestr("source.prj",PRJ)
    return out.getvalue()


def verify_zip(blob):
    with patch.object(arch,"PUBLISHER_BYTES",len(blob)), \
         patch.object(arch,"PUBLISHER_MD5",
                      hashlib.md5(blob,usedforsecurity=False).hexdigest()):
        return validate_original_with_gdal_fiona(
            blob,expected_sha256=hashlib.sha256(blob).hexdigest())


class HANZEGDALFionaValidationTests(unittest.TestCase):
    def test_real_original_crossreader_receipt_and_cat_admission_gate(self):
        from research_runners.hanze_2024_cross_reader_source_receipt_v0 import (
            HANZE_GDAL_PYSHP_ORIGINAL_CROSSCHECK_V0 as e,
        )
        from research_runners.hanze_regions2024_zip_original_receipt_v0 import PINNED_ZIP_SHA256
        self.assertEqual(e["source_zip_original_sha256"], PINNED_ZIP_SHA256)
        self.assertEqual(e["original_geometries"], 1449)
        self.assertEqual(e["both_readers_valid"], 555)
        self.assertEqual(e["both_readers_flagged_invalid"], 894)
        self.assertEqual(e["both_readers_valid"] + e["both_readers_flagged_invalid"],
                         e["original_geometries"])
        self.assertEqual(e["gdal_valid_pyshp_invalid"], 0)
        self.assertEqual(e["gdal_invalid_pyshp_valid"], 0)
        self.assertEqual(e["geometric_type_disagreements"], 0)
        self.assertEqual(e["identified_invalid_family_counts"]["Ring Self-intersection"], 894)
        self.assertTrue(e["dbf_code_order_consistent_without_export"])
        self.assertTrue(e["same_geos_topological_validity_algorithm_both_readers"])
        for key in ("third_independent_topology_engine_or_manual_region_review_completed",
                    "source_originals_automatically_fixed",
                    "original_geometries_or_region_ids_exported",
                    "historical_hazard_extent_or_insured_loss_proven",
                    "commercial_geometry_use_rights_reviewed",
                    "all_source_regions_model_eligible",
                    "model_data_admitted"):
            self.assertFalse(e[key])

    @unittest.skipUnless(HAS_ENGINE,"Fiona/GDAL/Shapely installed only in source CI")
    def test_original_like_polygon_read_via_gdal_is_valid(self):
        out=verify_zip(original_like_zip([REGULAR_RING]))
        self.assertEqual(out["read_feature_count"],1)
        self.assertEqual(out["validity_counts"]["geos_valid"],1)
        self.assertEqual(out["validity_counts"]["geos_invalid"],0)
        self.assertEqual(out["cross_reader_per_feature_validity_counts"]["both_valid"],1)
        self.assertEqual(out["cross_reader_per_feature_validity_counts"]["both_invalid"],0)
        self.assertTrue(out["original_feature_code_order_agrees_without_emitting_identifiers"])
        self.assertTrue(out["source_wkt_readable_by_gdal"])
        self.assertEqual(out["type_counts"]["Polygon"],1)
        self.assertFalse(out["model_input_admitted"])
        self.assertFalse(out["automatic_geometry_makevalid_performed"])
        self.assertFalse(out["original_geometry_bytes_or_region_ids_exported"])
        self.assertNotIn("DE111",str(out))
        self.assertNotIn("synthetic",str(out))

    @unittest.skipUnless(HAS_ENGINE,"Fiona/GDAL/Shapely installed only in source CI")
    def test_independent_gdal_interpretation_flags_bowtie_only(self):
        out=verify_zip(original_like_zip([REGULAR_RING,BOWTIE]))
        self.assertEqual(out["read_feature_count"],2)
        self.assertEqual(out["validity_counts"]["geos_valid"],1)
        self.assertEqual(out["validity_counts"]["geos_invalid"],1)
        self.assertEqual(out["cross_reader_per_feature_validity_counts"]["both_valid"],1)
        self.assertEqual(out["cross_reader_per_feature_validity_counts"]["both_invalid"],1)
        self.assertEqual(out["cross_reader_per_feature_validity_counts"]["gdal_valid_pyshp_invalid"],0)
        self.assertEqual(out["cross_reader_per_feature_validity_counts"]["gdal_invalid_pyshp_valid"],0)
        self.assertEqual(sum(out["invalid_reason_family_counts"].values()),1)
        self.assertNotIn("[",str(out["invalid_reason_family_counts"]))
        self.assertFalse(out["cross_feature_polygon_coverage_or_gap_validated"])

    @unittest.skipUnless(HAS_ENGINE,"Fiona/GDAL/Shapely installed only in source CI")
    def test_wrong_publisher_bytes_never_open_gdal(self):
        blob=original_like_zip([REGULAR_RING])
        with self.assertRaisesRegex(RegionArchiveError,"original archive provider-byte"):
            validate_original_with_gdal_fiona(
                blob,expected_sha256=hashlib.sha256(blob).hexdigest())


if __name__=="__main__":
    unittest.main()
