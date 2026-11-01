# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ESRI polygon integrity contracts; never ship real polygons."""
from __future__ import annotations

import hashlib
import io
import math
import struct
import unittest
from unittest.mock import patch
import zipfile

from research_runners import hanze_regions2024_geometry_zip_audit_v0 as archive_module
from research_runners.hanze_2024_original_polygon_integrity_v0 import (
    inspect_polygon_records, RegionArchiveError,
)

RING = [(0.,0.), (1.,0.), (1.,1.), (0.,0.)]
CRS = b'GEOGCS["WGS 84",DATUM["WGS_1984"],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'


def header(length):
    b=bytearray(100)
    struct.pack_into(">I",b,0,9994)
    struct.pack_into(">I",b,24,length//2)
    struct.pack_into("<I",b,28,1000)
    struct.pack_into("<I",b,32,5)
    struct.pack_into("<4d",b,36,-10.,-10.,20.,20.)
    return bytes(b)


def polygon_record(rings):
    points=[xy for ring in rings for xy in ring]
    offsets=[]
    consumed=0
    for ring in rings:
        offsets.append(consumed)
        consumed+=len(ring)
    x=[p[0] for p in points]; y=[p[1] for p in points]
    return (struct.pack("<I4dII",5,min(x),min(y),max(x),max(y),len(rings),len(points))
            +struct.pack("<"+"I"*len(rings),*offsets)
            +b"".join(struct.pack("<2d",*p) for p in points))


def shapefile_fixture(records=None, prj=CRS):
    if records is None:
        records=[polygon_record([RING]),polygon_record([RING,RING])]
    shp_records=[]
    shx_records=[]
    offset_words=50
    for i,raw in enumerate(records,1):
        assert len(raw)%2==0
        shp_records.append(struct.pack(">II",i,len(raw)//2)+raw)
        shx_records.append(struct.pack(">II",offset_words,len(raw)//2))
        offset_words+=(8+len(raw))//2
    shpbody=b"".join(shp_records)
    shxbody=b"".join(shx_records)
    shp=header(100+len(shpbody))+shpbody
    shx=header(100+len(shxbody))+shxbody
    # DBF declaration with one five-character synthetic Code
    dbf=bytearray(65+6*len(records))
    dbf[0]=3
    struct.pack_into("<IHH",dbf,4,len(records),65,6)
    dbf[32:36]=b"Code"
    dbf[43]=ord("C")
    dbf[48]=5
    dbf[64]=13
    for i in range(len(records)):
        dbf[65+6*i:65+6*(i+1)]=b" DE111"
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("region.shp",shp)
        z.writestr("region.shx",shx)
        z.writestr("region.dbf",bytes(dbf))
        z.writestr("region.prj",prj)
    return out.getvalue()


def verified(blob):
    with patch.object(archive_module,"PUBLISHER_BYTES",len(blob)), \
         patch.object(archive_module,"PUBLISHER_MD5",
                      hashlib.md5(blob,usedforsecurity=False).hexdigest()):
        return inspect_polygon_records(blob,expected_sha256=hashlib.sha256(blob).hexdigest())


class OriginalPolygonIntegrityTests(unittest.TestCase):
    def test_polygon_parts_shx_and_projection_aggregate_only(self):
        out=verified(shapefile_fixture())
        self.assertEqual(out["polygon_records"],2)
        self.assertEqual(out["null_shape_records"],0)
        self.assertEqual(out["polygon_rings"],3)
        self.assertEqual(out["polygon_vertices"],12)
        self.assertEqual(out["exactly_closed_ring_count"],3)
        self.assertEqual(out["open_ring_count"],0)
        self.assertTrue(out["shp_shx_record_count_exactly_reconciled"])
        self.assertEqual(out["projection_declaration"]["wkt_header_family"],"GEOGCS")
        self.assertEqual(out["projection_declaration"]["wkt_authority_epsg_codes_reported"],["4326"])
        for key in ("original_polygon_coordinates_or_wkt_exported",
                    "polygon_topology_or_self_intersections_verified",
                    "historical_hazard_footprint_observed",
                    "underlying_geometry_rights_reviewed_for_commercial_use",
                    "model_source_admitted"):
            self.assertFalse(out[key])
        self.assertNotIn("region.shp",str(out))
        self.assertEqual(out["projection_declaration"]["declared_crs_name_unverified"],"WGS 84")
        self.assertIn("degree",out["projection_declaration"]["declared_unit_names_unverified"])
        self.assertNotIn("DATUM",str(out))

    def test_source_sha_and_wkt_syntax_fail_closed(self):
        blob=shapefile_fixture()
        with self.assertRaisesRegex(RegionArchiveError,"original archive provider-byte"):
            inspect_polygon_records(blob,expected_sha256=hashlib.sha256(blob).hexdigest())
        with self.assertRaisesRegex(RegionArchiveError,"source SHA256"):
            with patch.object(archive_module,"PUBLISHER_BYTES",len(blob)), \
                 patch.object(archive_module,"PUBLISHER_MD5",hashlib.md5(blob,usedforsecurity=False).hexdigest()):
                inspect_polygon_records(blob,expected_sha256="0"*64)
        with self.assertRaisesRegex(RegionArchiveError,"WKT projection syntax"):
            verified(shapefile_fixture(prj=b"not a WKT projection"))

    def test_polygon_open_ring_is_observed_not_pretended_valid(self):
        ring=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)]
        out=verified(shapefile_fixture(records=[polygon_record([ring])]))
        self.assertEqual(out["open_ring_count"],1)
        self.assertEqual(out["exactly_closed_ring_count"],0)
        self.assertFalse(out["polygon_topology_or_self_intersections_verified"])

    def test_null_shape_does_not_count_as_polygon(self):
        out=verified(shapefile_fixture(records=[polygon_record([RING]),struct.pack("<I",0)]))
        self.assertEqual(out["null_shape_records"],1)
        self.assertEqual(out["polygon_records"],1)
        self.assertEqual(out["polygon_rings"],1)

    def test_nonfinite_vertex_and_invalid_ring_length_rejected(self):
        bad=list(RING); bad[1]=(math.nan,1.)
        with self.assertRaisesRegex(RegionArchiveError,"bounds, parts or point structure|nonfinite polygon vertex"):
            verified(shapefile_fixture(records=[polygon_record([bad])]))
        short=[(0.,0.),(1.,0.),(0.,0.)]
        with self.assertRaisesRegex(RegionArchiveError,"parts or point structure"):
            verified(shapefile_fixture(records=[polygon_record([short])]))

    def test_untrusted_zip_member_record_offset_and_trailing_data_rejected(self):
        base=polygon_record([RING])
        tampered=bytearray(base)
        struct.pack_into("<I",tampered,44,1)
        with self.assertRaisesRegex(RegionArchiveError,"ring part indices"):
            verified(shapefile_fixture(records=[bytes(tampered)]))


if __name__=="__main__":
    unittest.main()
