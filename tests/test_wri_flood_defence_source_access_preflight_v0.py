# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for flood-defence sources. Never network/real asset data."""
from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from research_runners.wri_flood_defence_source_access_preflight_v0 import (
    BAVARIA_ZIPS,
    DefenceSourceGateError,
    INPUT_LIMITS,
    NL_CRS,
    NL_FEATURE,
    NL_STALE_CATALOGUE_URL,
    NL_WFS,
    audit,
    inspect_bavaria_atom,
    inspect_bavaria_zip_start,
    inspect_bavaria_zip_end,
    inspect_nl_capabilities,
    inspect_nl_hits,
    inspect_nl_one_feature,
    inspect_nl_schema,
    read_bounded,
)

ROOT = Path(__file__).resolve().parents[1]
WFS = "http://www.opengis.net/wfs"
XSD = "http://www.w3.org/2001/XMLSchema"
ATOM = "http://www.w3.org/2005/Atom"


def make_wfs_caps():
    return (f'<wfs:WFS_Capabilities xmlns:wfs="{WFS}" version="1.1.0">'
            "<wfs:FeatureTypeList><wfs:FeatureType>"
            f"<wfs:Name>{NL_FEATURE}</wfs:Name>"
            "</wfs:FeatureType></wfs:FeatureTypeList>"
            "</wfs:WFS_Capabilities>").encode()


def make_wfs_schema():
    fields = {
        "TRAJECT_ID": "xsd:string",
        "VERSIE": "xsd:string",
        "NORM_SW": "xsd:int",
        "NORM_OG": "xsd:int",
        "NORM_THB": "xsd:int",
        "NORM_NS": "xsd:int",
        "geom": "gml:MultiLineStringPropertyType",
    }
    xml = "".join(f'<xsd:element name="{name}" type="{kind}"/>'
                  for name, kind in fields.items())
    return (f'<xsd:schema xmlns:xsd="{XSD}"'
            ' xmlns:gml="http://www.opengis.net/gml">'
            + xml + "</xsd:schema>").encode()


def make_wfs_hits(n=237):
    return (f'<wfs:FeatureCollection xmlns:wfs="{WFS}"'
            f' numberOfFeatures="{n}"/>').encode()


def make_feature(crs=NL_CRS, geom="MultiLineString",
                 nsw=300, nog=100, normtyp="Overstromingskans"):
    return json.dumps({
        "type": "FeatureCollection",
        "totalFeatures": 237,
        "features": [{
            "type": "Feature",
            "id": "nbpw_dijktrajecten_formeel.1",
            "geometry": {"type": geom, "coordinates": [
                [[199623.5042, 364129.9971], [199634.52, 364142.90]]
            ]},
            "properties": {
                "TRAJECT_ID": "73-1",
                "VERSIE": "3",
                "NORM_SW": nsw,
                "NORM_OG": nog,
                "NORM_THB": 0,
                "NORM_NS": 0,
                "NORMTYP_O": normtyp
            },
        }],
        "crs": {"type": "name", "properties": {"name": crs}},
    }).encode()


def make_bavaria_atom(license_text="CC BY-SA 4.0", include_both=True):
    links = [BAVARIA_ZIPS["25832"]]
    if include_both:
        links.append(BAVARIA_ZIPS["4258"])
    links_xml = "".join(f'<link href="{url}"/>' for url in links)
    return (f'<feed xmlns="{ATOM}"><rights>{license_text}</rights>'
            f"{links_xml}</feed>").encode()


def make_zip_head(epsg="25832"):
    name = f"deich_epsg{epsg}.dbf".encode()
    out = bytearray(512)
    out[:4] = b"PK\x03\x04"
    struct.pack_into("<HH", out, 26, len(name), 0)
    out[30:30+len(name)] = name
    return bytes(out)


def make_zip_tail(epsg="25832"):
    """Invented ZIP central directory in an exact 2048-byte suffix."""
    index_bytes = {"deich": 17468, "hwschutzwand": 6508, "hwschutzsystem": 7228}
    central = bytearray()
    for kind in ("deich", "hwschutzwand", "hwschutzsystem"):
        for extension in ("dbf", "prj", "shp", "shx"):
            name = f"{kind}_epsg{epsg}.{extension}".encode("ascii")
            head = bytearray(46)
            head[:4] = b"PK\x01\x02"
            struct.pack_into("<H", head, 10, 8)  # DEFLATE
            struct.pack_into("<II", head, 20, 100, (
                index_bytes[kind] if extension == "shx" else 300))
            struct.pack_into("<HHH", head, 28, len(name), 0, 0)
            struct.pack_into("<I", head, 42, 64)
            central.extend(head)
            central.extend(name)
    eocd = bytearray(22)
    eocd[:4] = b"PK\x05\x06"
    struct.pack_into("<HHHHIIH", eocd, 4, 0, 0, 12, 12, len(central), 10000, 0)
    assert len(central) + 22 < 2048
    return bytes(2048 - len(central) - 22) + bytes(central) + bytes(eocd)


def make_inputs():
    return {
        "nl_capabilities": make_wfs_caps(),
        "nl_schema": make_wfs_schema(),
        "nl_hits": make_wfs_hits(),
        "nl_one_feature": make_feature(),
        "bavaria_atom": make_bavaria_atom(),
        "bavaria_zip_25832_head": make_zip_head("25832"),
        "bavaria_zip_4258_head": make_zip_head("4258"),
        "bavaria_zip_25832_tail": make_zip_tail("25832"),
        "bavaria_zip_4258_tail": make_zip_tail("4258"),
    }


class FloodDefenceSourceAccessTests(unittest.TestCase):
    def test_source_endpoint_is_precise_not_broken_ows_alias(self):
        self.assertNotEqual(NL_WFS, NL_STALE_CATALOGUE_URL)
        self.assertIn("/wvp/wvp/wfs", NL_WFS)
        self.assertIn("/wvp/ows/wfs", NL_STALE_CATALOGUE_URL)
        self.assertEqual(NL_FEATURE, "wvp:nbpw_dijktrajecten_formeel")

    def test_synthetic_exact_protected_source_contract_succeeds_non_admission(self):
        receipt = audit(make_inputs())
        self.assertEqual(
            receipt["netherlands"]["hits"]["observed_formal_trajectory_count_at_probe_time"],
            237,
        )
        self.assertEqual(receipt["netherlands"]["one_feature"]["native_crs"], "EPSG:28992")
        self.assertEqual(
            receipt["bavaria"]["epsg_25832_first_512_bytes"]["first_zip_member_name"],
            "deich_epsg25832.dbf",
        )
        self.assertFalse(receipt["protection_factor_or_return_period_threshold_inferred"])
        self.assertFalse(receipt["spatial_inside_dike_or_protected_area_identified"])
        self.assertFalse(receipt["model_input_admitted"])
        self.assertFalse(receipt["individual_dike_crest_elevation_verified"])
        self.assertFalse(receipt["source_and_scientific_admission_complete"])
        self.assertEqual(set(receipt["original_response_sha256_at_run"]), set(INPUT_LIMITS))

    def test_wrong_nl_service_path_exception_is_not_availability(self):
        exception = (b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows">'
                     b'<ows:Exception>global services are off</ows:Exception>'
                     b"</ows:ExceptionReport>")
        with self.assertRaises(DefenceSourceGateError):
            inspect_nl_capabilities(exception)
        with self.assertRaises(DefenceSourceGateError):
            inspect_nl_hits(exception)
        with self.assertRaises(DefenceSourceGateError):
            inspect_nl_schema(exception)

    def test_schema_or_wrong_crs_never_passes(self):
        with self.assertRaisesRegex(DefenceSourceGateError, "schema changed"):
            inspect_nl_schema(
                make_wfs_schema().replace(b"NORM_OG", b"MISSING_OG")
            )
        for wrong in ("urn:ogc:def:crs:EPSG::4326", "", "EPSG:28992"):
            with self.subTest(wrong=wrong):
                with self.assertRaisesRegex(DefenceSourceGateError, "CRS"):
                    inspect_nl_one_feature(make_feature(crs=wrong))
        with self.assertRaises(DefenceSourceGateError):
            inspect_nl_one_feature(make_feature(geom="Point"))
        self.assertEqual(
            inspect_nl_one_feature(make_feature())["observed_norm_og_example"], 100
        )

    def test_naive_norm_to_return_period_semantics_disallowed(self):
        for bad_norm, bad_type in ((-1, "Overstromingskans"),
                                   ("1/100", "Overstromingskans"),
                                   (100, "Overtoppingskans")):
            with self.subTest(norm=bad_norm, name=bad_type):
                with self.assertRaises(DefenceSourceGateError):
                    inspect_nl_one_feature(make_feature(nog=bad_norm, normtyp=bad_type))
        one = inspect_nl_one_feature(make_feature())
        self.assertTrue(one["norms_not_interpreted_as_hazard_return_periods"])

    def test_no_mass_fetch_for_nl_formal_trajectory_count(self):
        with self.assertRaises(DefenceSourceGateError):
            inspect_nl_hits(make_wfs_hits(0))
        with self.assertRaises(DefenceSourceGateError):
            inspect_nl_hits(make_wfs_hits(-1))
        n = inspect_nl_hits(make_wfs_hits(237))
        self.assertEqual(n["observed_formal_trajectory_count_at_probe_time"], 237)
        self.assertTrue(n["count_is_live_and_not_globally_pinned"])

    def test_bavaria_missing_license_or_zip_link_blocks(self):
        self.assertEqual(
            inspect_bavaria_atom(make_bavaria_atom())["provider_declared_license"],
            "CC-BY-SA-4.0",
        )
        for atom in (make_bavaria_atom(license_text="copyright - all rights reserved"),
                     make_bavaria_atom(include_both=False)):
            with self.assertRaises(DefenceSourceGateError):
                inspect_bavaria_atom(atom)

    def test_zip_header_only_no_false_full_archive_validation(self):
        for epsg in ("25832", "4258"):
            result = inspect_bavaria_zip_start(make_zip_head(epsg), epsg)
            self.assertTrue(result["zip_signature_verified"])
            self.assertFalse(result["full_zip_central_directory_verified"])
            self.assertFalse(result["full_shapefile_geometry_verified"])
        bad = bytearray(make_zip_head())
        bad[0] = 0x00
        with self.assertRaises(DefenceSourceGateError):
            inspect_bavaria_zip_start(bytes(bad), "25832")
        with self.assertRaises(DefenceSourceGateError):
            inspect_bavaria_zip_start(make_zip_head("4258"), "25832")

    def test_bavarian_tail_proves_three_classes_but_not_full_file_integrity(self):
        for epsg in ("25832", "4258"):
            result = inspect_bavaria_zip_end(make_zip_tail(epsg), epsg)
            self.assertEqual(result["expected_shapefile_component_count"], 12)
            self.assertEqual(result["expected_asset_classes"],
                             ["deich", "hwschutzwand", "hwschutzsystem"])
            self.assertEqual(
                result["index_record_slots_inferred_from_uncompressed_shx_sizes"]["deich"],
                2171,
            )
            self.assertFalse(result["index_records_or_geometries_actually_decoded"])
            self.assertFalse(result["full_zip_crc_or_member_integrity_verified"])
        with self.assertRaises(DefenceSourceGateError):
            inspect_bavaria_zip_end(make_zip_tail("4258"), "25832")
        with self.assertRaises(DefenceSourceGateError):
            inspect_bavaria_zip_end(make_zip_tail("25832")[:-1], "25832")
        broken = bytearray(make_zip_tail("25832"))
        broken[-22:-18] = b"FAIL"
        with self.assertRaises(DefenceSourceGateError):
            inspect_bavaria_zip_end(bytes(broken), "25832")

    def test_malformed_xml_entity_and_wrong_original_http_range_rejected(self):
        with self.assertRaises(DefenceSourceGateError):
            inspect_bavaria_atom(b'<!DOCTYPE feed [<!ENTITY bad "x">]><feed/>')
        with self.assertRaises(DefenceSourceGateError):
            inspect_nl_capabilities(b"<notreallyXML>")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "provider-response"
            for data in (b"", b"x" * (INPUT_LIMITS["nl_capabilities"] + 1)):
                path.write_bytes(data)
                with self.assertRaises(DefenceSourceGateError):
                    read_bounded(path, "nl_capabilities")
            with self.assertRaises(DefenceSourceGateError):
                read_bounded(path, "unknown-source")

    def test_cli_refuses_output_overwrite_original_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "input"
            original.write_bytes(b"synthetic-only")
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wri_flood_defence_source_access_preflight_v0.py"),
            ]
            for key in INPUT_LIMITS:
                cmd.extend(("--"+key.replace("_", "-"), str(original)))
            cmd.extend(("--out", str(original)))
            p = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(original.read_bytes(), b"synthetic-only")


if __name__ == "__main__":
    unittest.main()
