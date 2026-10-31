# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only geometry-code matching: presence of polygon code != inundation."""
from __future__ import annotations

import hashlib
import io
import struct
import unittest
from unittest.mock import patch
import zipfile

from research_runners import hanze_regions2024_geometry_zip_audit_v0 as zipmod
from research_runners import hanze_native_regions2024_source_audit_v0 as s2mod
from research_runners.hanze_regions2024_geometry_code_coverage_v0 import (
    compare_hanze_geometry_native_glossary, survey_verified_event_region_geometry_coverage,
    read_original_region_dbf_codes,
)
from research_runners.flood_event_link_candidates_v0 import link_candidates
from research_runners.dfo_floodrecords_csv_preflight_v0 import HEADER as DFO_HEADER
from research_runners.historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS
from tests.test_flood_event_link_candidates_v0 import csv_blob,dfo_row,hanze_row,crosswalk,sha
from tests.test_hanze_regions2024_geometry_zip_audit_v0 import shp_header


def shape_with_codes(codes):
    n=len(codes)
    def head(length):
        return shp_header(shape_type=5,length=length)
    shp=head(100+12*n)+b"".join(
        struct.pack(">II",i+1,2)+b"\x00"*4 for i in range(n))
    shx=head(100+8*n)+b"\x00"*8*n
    dbf=bytearray(65+6*n)
    dbf[0]=3
    struct.pack_into("<IHH",dbf,4,n,65,6)
    dbf[32:36]=b"Code"
    dbf[43]=ord("C")
    dbf[48]=5
    dbf[64]=13
    for i,code in enumerate(codes):
        dbf[65+6*i:65+6*(i+1)]=b" "+code.encode("ascii")
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("Regions.shp",shp)
        z.writestr("Regions.shx",shx)
        z.writestr("Regions.dbf",bytes(dbf))
        z.writestr("Regions.prj",'GEOGCS["WGS 84"]')
    return out.getvalue()


def s2_blob():
    codes=[f"AA{i:03d}" for i in range(999)]+["DE111","DE112"]
    return csv_blob(("Code","Name"),[{"Code":c,"Name":"fictional"} for c in codes])


def source_context(codes=None, admin="DE111;DE112"):
    geo=shape_with_codes(codes if codes is not None else ["DE111","DE112"])
    gloss=s2_blob()
    dfo=csv_blob(DFO_HEADER,[dfo_row()])
    hanze=csv_blob(HANZE_COLUMNS,[hanze_row(**{
        "admin_unit_nomenclature":"NUTS","admin_unit_level":"3",
        "admin_unit_year":"2024","admin_unit_code":admin,
    })])
    cw=crosswalk()
    overlaps=link_candidates(dfo,sha(dfo),hanze,sha(hanze),cw,sha(cw))
    return geo,gloss,hanze,overlaps


def with_mocked_source(geo,gloss,fn):
    with patch.object(zipmod,"PUBLISHER_BYTES",len(geo)), \
         patch.object(zipmod,"PUBLISHER_MD5",hashlib.md5(geo,usedforsecurity=False).hexdigest()), \
         patch.object(s2mod,"PUBLISHER_BYTES",len(gloss)), \
         patch.object(s2mod,"PUBLISHER_MD5",hashlib.md5(gloss,usedforsecurity=False).hexdigest()):
        return fn()


class HANZEGeometryCodeMembershipTests(unittest.TestCase):
    def test_all_glossary_candidate_tokens_are_geometry_attribute_codes(self):
        geo,gloss,hanze,overlaps=source_context()
        def run():
            union=compare_hanze_geometry_native_glossary(geo,gloss,
                    expected_zip_sha256=sha(geo),expected_glossary_sha256=sha(gloss))
            event=survey_verified_event_region_geometry_coverage(
                    geo,gloss,hanze,sha(hanze),overlaps,
                    expected_zip_sha256=sha(geo),expected_glossary_sha256=sha(gloss))
            return union,event
        union,event=with_mocked_source(geo,gloss,run)
        self.assertEqual(union["geometry_codes_not_in_glossary"],0)
        self.assertEqual(union["glossary_codes_not_in_geometry"],999)
        self.assertEqual(union["glossary_codes_also_in_geometry"],2)
        self.assertEqual(event["candidate_pair_count"],1)
        self.assertEqual(event["fully_dbf_code_covered_original_candidate_lists"],1)
        self.assertEqual(event["region_token_occurrences"],2)
        self.assertFalse(event["source_polygon_geometry_intersections_computed"])
        self.assertFalse(event["model_input_admitted"])
        self.assertNotIn("DE111",str(event))
        self.assertNotIn("DE112",str(union))

    def test_missing_geometry_code_does_not_mean_absent_flood(self):
        geo,gloss,hanze,overlaps=source_context(["DE111"])
        result=with_mocked_source(geo,gloss,lambda:
            survey_verified_event_region_geometry_coverage(
                geo,gloss,hanze,sha(hanze),overlaps))
        self.assertEqual(result["glossary_valid_lists_with_missing_geometry_code"],1)
        self.assertEqual(result["fully_dbf_code_covered_original_candidate_lists"],0)
        self.assertFalse(result["common_flood_event_identity_confirmed"])

    def test_repeated_dbf_code_is_detected_as_extra_feature_not_new_region(self):
        geo,gloss,hanze,overlaps=source_context(["DE111","DE111","DE112"])
        counts,report=with_mocked_source(geo,gloss,lambda:read_original_region_dbf_codes(geo))
        self.assertEqual(counts["DE111"],2)
        self.assertEqual(report["dbf_region_feature_records"],3)
        self.assertEqual(report["dbf_distinct_canonical_code_count"],2)
        self.assertEqual(report["dbf_repeated_code_surplus_features"],1)
        self.assertFalse(report["model_input_admitted"])

    def test_corrupt_zip_byte_sha_cannot_be_assumed_geometry(self):
        geo,gloss,hanze,overlaps=source_context()
        with self.assertRaisesRegex(zipmod.RegionArchiveError,"original archive provider-byte"):
            read_original_region_dbf_codes(geo)
        with self.assertRaisesRegex(zipmod.RegionArchiveError,"SHA256"):
            with_mocked_source(geo,gloss,lambda:
                read_original_region_dbf_codes(geo,expected_zip_sha256="0"*64))


if __name__=="__main__":
    unittest.main()
