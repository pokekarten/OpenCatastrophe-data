# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only GUGiK WFS original metadata contract tests; no remote access."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import parse_qs, urlsplit

from scripts.probe_pl_egib_buildings_wfs_v0 import (
    EXPECTED_CRS,
    EXPECTED_FIELDS,
    ProviderMetadataError,
    inspect_original_xml,
    provider_requests,
)

ROOT = Path(__file__).resolve().parents[1]

CAPS = b"""<?xml version="1.0"?>
<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0" version="2.0.0">
  <wfs:FeatureTypeList>
    <wfs:FeatureType><wfs:Name>ms:dzialki</wfs:Name>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::2180</wfs:DefaultCRS></wfs:FeatureType>
    <wfs:FeatureType><wfs:Name>ms:budynki</wfs:Name>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::2180</wfs:DefaultCRS></wfs:FeatureType>
  </wfs:FeatureTypeList>
</wfs:WFS_Capabilities>"""

SCHEMA = b"""<?xml version="1.0"?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" xmlns:gml="http://www.opengis.net/gml/3.2">
 <complexType name="budynkiType"><complexContent><extension base="gml:AbstractFeatureType">
  <sequence>
    <element name="geom" type="gml:SurfacePropertyType" minOccurs="0"/>
    <element name="ID_BUDYNKU" type="string" minOccurs="0"/>
    <element name="RODZAJ" type="string" minOccurs="0"/>
    <element name="KONDYGNACJE_NADZIEMNE" type="string" minOccurs="0"/>
    <element name="KONDYGNACJE_PODZIEMNE" type="string" minOccurs="0"/>
  </sequence>
 </extension></complexContent></complexType>
</schema>"""

HITS = b"""<?xml version="1.0"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
 timeStamp="2026-11-08T23:03:58" numberMatched="1" numberReturned="0" />"""


class PlEgibNativeWfsTests(unittest.TestCase):
    def test_pinned_requests_only_and_bounded_hits(self):
        urls = provider_requests()
        self.assertEqual(set(urls), {"capabilities", "schema", "hits"})
        for url in urls.values():
            p = urlsplit(url)
            self.assertEqual(p.scheme, "https")
            self.assertEqual(p.hostname, "mapy.geoportal.gov.pl")
            self.assertEqual(p.path, "/wss/service/PZGIK/EGIB/WFS/UslugaZbiorcza")
        self.assertEqual(parse_qs(urlsplit(urls["schema"]).query)["TYPENAMES"], ["ms:budynki"])
        self.assertEqual(parse_qs(urlsplit(urls["hits"]).query)["RESULTTYPE"], ["hits"])
        self.assertEqual(parse_qs(urlsplit(urls["hits"]).query)["COUNT"], ["1"])

    def test_success_is_metadata_only_and_sha_reproducible(self):
        report = inspect_original_xml(CAPS, SCHEMA, HITS)
        self.assertEqual(report["capabilities"]["layer"], "ms:budynki")
        self.assertEqual(report["capabilities"]["declared_crs"], EXPECTED_CRS)
        self.assertEqual(report["schema"]["advertised_fields_only"], list(EXPECTED_FIELDS))
        self.assertEqual(report["hits"]["records_returned"], 0)
        self.assertFalse(report["hits"]["nationwide_feature_count_known"])
        self.assertEqual(report["original_xml_byte_receipts"]["DescribeFeatureType"]["sha256"],
                         hashlib.sha256(SCHEMA).hexdigest())
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["commercial_redistribution_rights_verified"])
        self.assertFalse(report["original_source_geometry_downloaded"])
        self.assertEqual(report, inspect_original_xml(CAPS, SCHEMA, HITS))

    def test_reject_wrong_layer_and_crs(self):
        variants = [
            CAPS.replace(b"ms:budynki", b"ms:other"),
            CAPS.replace(b"EPSG::2180", b"EPSG::4326"),
            CAPS.replace(b'version="2.0.0"', b'version="1.1.0"'),
            CAPS.replace(b"<wfs:FeatureTypeList>", b'<wfs:FeatureTypeList><wfs:FeatureType>'
                         b'<wfs:Name>ms:budynki</wfs:Name>'
                         b'<wfs:DefaultCRS>urn:ogc:def:crs:EPSG::2180</wfs:DefaultCRS>'
                         b'</wfs:FeatureType>'),
        ]
        for raw in variants:
            with self.subTest(raw=raw[:60]), self.assertRaises(ProviderMetadataError):
                inspect_original_xml(raw, SCHEMA, HITS)

    def test_reject_missing_attribute_or_nonpolygon_geometry(self):
        for raw in [
            SCHEMA.replace(b"KONDYGNACJE_PODZIEMNE", b"FIELD_MISSING"),
            SCHEMA.replace(b"gml:SurfacePropertyType", b"gml:PointPropertyType"),
            SCHEMA.replace(b'budynkiType', b'invalidType'),
        ]:
            with self.subTest(raw=raw[:60]), self.assertRaises(ProviderMetadataError):
                inspect_original_xml(CAPS, raw, HITS)

    def test_reject_fetched_feature_or_exception_report(self):
        for raw in [
            HITS.replace(b'numberReturned="0"', b'numberReturned="1"'),
            HITS.replace(b'numberReturned="0"', b'numberReturned="5"'),
            b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows/1.1" />',
            b'<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" '
            b'numberReturned="0" xmlns:ms="http://mapserver.gis.umn.edu/mapserver">'
            b'<ms:budynki/></wfs:FeatureCollection>',
        ]:
            with self.subTest(raw=raw[:80]), self.assertRaises(ProviderMetadataError):
                inspect_original_xml(CAPS, SCHEMA, raw)

    def test_reject_dtd_entity_and_broken_xml(self):
        for raw in [
            b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>' + HITS,
            b'<!ENTITY sneaky "X">' + HITS,
            b'<wfs:FeatureCollection',
            b"",
        ]:
            with self.subTest(raw=raw[:80]), self.assertRaises(ProviderMetadataError):
                inspect_original_xml(CAPS, SCHEMA, raw)

    def test_offline_cli_and_no_feature_identity(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {}
            for kind, value in (("capabilities", CAPS), ("schema", SCHEMA), ("hits", HITS)):
                dest = root / (kind + ".xml")
                dest.write_bytes(value)
                files[kind] = dest
            cmd = [sys.executable, "scripts/probe_pl_egib_buildings_wfs_v0.py",
                   "--offline",
                   "--capabilities-file", str(files["capabilities"]),
                   "--schema-file", str(files["schema"]),
                   "--hits-file", str(files["hits"])]
            run = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True,
                                 timeout=20, check=True)
            self.assertIn('"layer": "ms:budynki"', run.stdout)
            self.assertIn('"model_input_admitted": false', run.stdout)
            self.assertNotIn("PRIVATE-INSURER-ADDRESS", run.stdout)
            again = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True,
                                   timeout=20, check=True)
            self.assertEqual(run.stdout, again.stdout)
            denied = subprocess.run([sys.executable, cmd[1], "--offline"],
                                    cwd=ROOT, text=True, capture_output=True, timeout=20)
            self.assertEqual(denied.returncode, 2)
            self.assertIn("BLOCKED", denied.stderr)


if __name__ == "__main__":
    unittest.main()
