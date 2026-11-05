# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-only source_polygon source_DBf one record integrity tests."""
import importlib.util
import struct
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_nrw_hu_2022_first_polygons_v0 import (
    parse_first_original_records,reproject_first_valid_physical_building,OriginalZipBlocked
)


def invented_single_polygon():
    coords=[(32280450.,5578000.),(32280510.,5578000.),
            (32280510.,5578070.),(32280450.,5578070.),(32280450.,5578000.)]
    body=(struct.pack("<I",5)+struct.pack("<dddd",32280450.,5578000.,32280510.,5578070.)+
          struct.pack("<II",1,len(coords))+struct.pack("<I",0)+
          b"".join(struct.pack("<dd",x,y) for x,y in coords))
    assert len(body)%2==0
    header=bytearray(100)
    struct.pack_into(">I",header,0,9994)
    struct.pack_into(">I",header,24,(100+8+len(body))//2)
    struct.pack_into("<I",header,28,1000)
    struct.pack_into("<I",header,32,5)
    shp=bytes(header)+struct.pack(">II",1,len(body)//2)+body
    dbf=bytearray(161)
    dbf[0]=3
    struct.pack_into("<I",dbf,4,1)
    struct.pack_into("<H",dbf,8,161)
    struct.pack_into("<H",dbf,10,46)
    dbf[160]=0x0d
    row=(b" "+b"05111000"+b"ORIGINAL-MOCK-001".ljust(17,b" ")+
         b"3100".ljust(10,b" ")+b"2022-01-01")
    assert len(row)==46
    return shp,bytes(dbf)+row


class TestOriginalPolygonSmoke(unittest.TestCase):
    def test_first_real_shape_layout_supported_without_mislabeling_insurer(self):
        shp,dbf=invented_single_polygon()
        physical,audit=parse_first_original_records(shp,dbf)
        self.assertEqual(audit["shp_records_inspected"],1)
        self.assertEqual(physical[0]["ags_kreis"],"05111")
        self.assertEqual(physical[0]["gfk"],"3100")
        self.assertEqual(len(physical[0]["coords"]),5)

    def test_missing_or_corrupt_source_does_not_invent_sites(self):
        shp,dbf=invented_single_polygon()
        with self.assertRaises(OriginalZipBlocked):
            parse_first_original_records(b"garbage",dbf)
        with self.assertRaises(OriginalZipBlocked):
            parse_first_original_records(shp,dbf[:20])
        broken=bytearray(shp)
        struct.pack_into(">I",broken,100,9)
        with self.assertRaises(OriginalZipBlocked):
            parse_first_original_records(bytes(broken),dbf)
        deleted=bytearray(dbf)
        deleted[161]=ord("*")
        found,audit=parse_first_original_records(shp,bytes(deleted))
        self.assertEqual(found,[])
        self.assertEqual(audit["nonadmitted_reasons"]["deleted_dbf_record"],1)

    @unittest.skipUnless(
        importlib.util.find_spec("pyproj") is not None and importlib.util.find_spec("shapely") is not None,
        "optional pinned geospatial libraries not installed")
    def test_optional_pinned_etrs89_to_wgs84_interior_point(self):
        shp,dbf=invented_single_polygon()
        physical,_=parse_first_original_records(shp,dbf)
        receipt=reproject_first_valid_physical_building(physical)
        self.assertTrue(receipt["actual_source_geometry_reprojected_to_wgs84"])
        self.assertFalse(receipt["actual_RV_insured_site_location_verified"])
        self.assertFalse(receipt["source_original_zip_sha256_verified"])
        self.assertEqual(len(receipt["physical_source_only_sample_wgs84_coordinates"]),1)
        pt=receipt["physical_source_only_sample_wgs84_coordinates"][0]
        self.assertTrue(5.7<pt["lon"]<9.9 and 50.0<pt["lat"]<52.8)

if __name__=="__main__":
    unittest.main()
