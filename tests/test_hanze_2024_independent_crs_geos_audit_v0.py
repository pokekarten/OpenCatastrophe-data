# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only independent CRS and GEOS proof; no original region polygons."""
from __future__ import annotations

import importlib.util
import hashlib
import unittest
from unittest.mock import patch

from research_runners import hanze_regions2024_geometry_zip_audit_v0 as zipmod
from research_runners.hanze_2024_independent_crs_geos_audit_v0 import (
    audit_independent_crs_and_topology, RegionArchiveError, _invalid_family,
)
from tests.test_hanze_2024_original_polygon_integrity_v0 import (
    polygon_record, shapefile_fixture,
)

HAS_ENGINE = all(importlib.util.find_spec(x) for x in ("shapefile", "pyproj", "shapely"))
OFFICIAL_ESRI_WKT = (
    'PROJCS["ETRS_1989_LAEA",GEOGCS["GCS_ETRS_1989",'
    'DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137.0,298.257222101]],'
    'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],'
    'PROJECTION["Lambert_Azimuthal_Equal_Area"],'
    'PARAMETER["False_Easting",4321000.0],'
    'PARAMETER["False_Northing",3210000.0],'
    'PARAMETER["Central_Meridian",10.0],'
    'PARAMETER["Latitude_Of_Origin",52.0],UNIT["Meter",1.0]]'
)
CLOCKWISE = [(0.,0.),(0.,1.),(1.,1.),(1.,0.),(0.,0.)]
BOWTIE = [(0.,0.),(1.,1.),(0.,1.),(1.,0.),(0.,0.)]


def check(blob):
    with patch.object(zipmod, "PUBLISHER_BYTES", len(blob)), \
         patch.object(zipmod, "PUBLISHER_MD5",
                      hashlib.md5(blob, usedforsecurity=False).hexdigest()):
        return audit_independent_crs_and_topology(
            blob, expected_sha256=hashlib.sha256(blob).hexdigest())


class OriginalHANZEIndependentEngineTests(unittest.TestCase):
    def test_invalid_reason_never_contains_coordinates(self):
        self.assertEqual(_invalid_family("Self-intersection[12.4 35.8]"),
                         "Self-intersection")
        self.assertEqual(_invalid_family("Ring Self-intersection[100 200]"),
                         "Ring Self-intersection")

    def test_original_source_geos_distribution_frozen_and_never_automatically_repaired(self):
        from research_runners.hanze_2024_independent_geometry_source_receipt_v0 import (
            HANZE_2024_INDEPENDENT_GEOMETRY_RECEIPT_V0 as e,
        )
        from research_runners.hanze_regions2024_zip_original_receipt_v0 import PINNED_ZIP_SHA256
        self.assertEqual(e["original_region_zip_sha256"], PINNED_ZIP_SHA256)
        self.assertEqual(e["identified_epsg_by_proj"], 3035)
        self.assertTrue(e["epsg3035_projection_parameters_ellipsoid_axes_match"])
        self.assertFalse(e["strict_source_to_modern_epsg_crs_equals"])
        self.assertEqual(e["source_feature_count"], 1449)
        self.assertEqual(e["geos_valid_geometries"], 555)
        self.assertEqual(e["geos_invalid_geometries"], 894)
        self.assertEqual(sum(e["invalid_reason_families"].values()), 894)
        self.assertEqual(e["interpreted_feature_types"]["polygon"] +
                         e["interpreted_feature_types"]["multipolygon"], 1449)
        for key in ("independent_gdal_ogr_geometry_interpretation_verified",
                    "invalidity_is_conclusive_source_geometry_defect",
                    "geometry_auto_repair_or_topology_simplification_performed",
                    "cross_feature_overlap_and_gap_validation_complete",
                    "original_geometry_or_feature_id_reproduced",
                    "underlying_geographic_commercial_rights_approved",
                    "all_geometry_features_eligible_for_model_input",
                    "model_input_admitted"):
            self.assertFalse(e[key])

    @unittest.skipUnless(HAS_ENGINE, "pyproj/shapely/pyshp only in geo-source CI")
    def test_official_epsg3035_reference_equal_projected_and_simple_valid_polygon(self):
        blob = shapefile_fixture(records=[polygon_record([CLOCKWISE])],
                                 prj=OFFICIAL_ESRI_WKT.encode("ascii"))
        a = check(blob)
        self.assertTrue(a["source_projected_crs"])
        self.assertFalse(a["equals_official_epsg3035_ignoring_axis_order"])
        self.assertTrue(a["epsg3035_projection_parameters_ellipsoid_axes_match"])
        self.assertTrue(a["legacy_wkt_datum_and_modern_epsg_ensemble_equivalence_not_proven"])
        self.assertEqual(a["epsg_code_identified_by_pyproj"], 3035)
        self.assertEqual(a["source_feature_count"], 1)
        self.assertEqual(a["validity"]["geos_valid_geometries"], 1)
        self.assertEqual(a["validity"]["geos_invalid_geometries"], 0)
        self.assertFalse(a["cross_feature_topology_or_spatial_gaps_verified"])
        self.assertFalse(a["original_coordinates_or_region_id_exported"])
        self.assertFalse(a["model_input_admitted"])
        self.assertNotIn("DATUM", str(a))
        self.assertNotIn("0.,1.", str(a))

    @unittest.skipUnless(HAS_ENGINE, "pyproj/shapely/pyshp only in geo-source CI")
    def test_bowtie_is_aggregate_invalid_geometry_not_false_validated_region(self):
        blob = shapefile_fixture(records=[polygon_record([BOWTIE])],
                                 prj=OFFICIAL_ESRI_WKT.encode("ascii"))
        a = check(blob)
        self.assertEqual(a["source_feature_count"], 1)
        self.assertEqual(a["validity"]["geos_invalid_geometries"], 1)
        self.assertEqual(sum(a["invalid_reason_family_counts"].values()), 1)
        self.assertNotIn("[", str(a["invalid_reason_family_counts"]))

    @unittest.skipUnless(HAS_ENGINE, "pyproj/shapely/pyshp only in geo-source CI")
    def test_source_lonlat_cannot_be_assumed_laea(self):
        wkt=b'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],UNIT["degree",0.0174532925199433]]'
        blob=shapefile_fixture(records=[polygon_record([CLOCKWISE])],prj=wkt)
        with self.assertRaisesRegex(RegionArchiveError, "not projected"):
            check(blob)

    @unittest.skipUnless(HAS_ENGINE, "pyproj/shapely/pyshp only in geo-source CI")
    def test_original_zip_sha_drift_rejected_before_geometry(self):
        b=shapefile_fixture(records=[polygon_record([CLOCKWISE])],
                            prj=OFFICIAL_ESRI_WKT.encode("ascii"))
        with self.assertRaisesRegex(RegionArchiveError, "original archive provider-byte"):
            audit_independent_crs_and_topology(b,expected_sha256=hashlib.sha256(b).hexdigest())


if __name__ == "__main__":
    unittest.main()
