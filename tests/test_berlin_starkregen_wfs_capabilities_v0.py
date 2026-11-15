# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only negative and provenance tests for two pluvial WFS products."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import unittest

from research_runners.berlin_starkregen_wfs_capabilities_v0 import (
    MAX_BYTES, SOURCES, TIMEOUT, StarkregenError, inspect, probe,
)


def xml(name="ua_srhk:waterdepth", version="2.0.0"):
    return (
        '<?xml version="1.0"?>'
        '<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0" '
        f'version="{version}"><wfs:FeatureTypeList>'
        f'<wfs:FeatureType><wfs:Name>{name}</wfs:Name>'
        '<wfs:DefaultCRS>urn:ogc:def:crs:EPSG::25832</wfs:DefaultCRS>'
        '<wfs:OtherCRS>urn:ogc:def:crs:EPSG::25833</wfs:OtherCRS>'
        '</wfs:FeatureType></wfs:FeatureTypeList></wfs:WFS_Capabilities>'
    ).encode()


class Response(io.BytesIO):
    status = 200
    def __init__(self, data, *, url, media="text/xml; charset=UTF-8"):
        super().__init__(data)
        self.url = url
        self.headers = {"Content-Type": media}
    def geturl(self):
        return self.url


class BerlinPluvialMetadataTests(unittest.TestCase):
    def test_two_distinct_exact_official_source_ids_and_rights_labels(self):
        self.assertEqual(set(SOURCES), {"hinweiskarte", "gefahrenkarte"})
        self.assertNotEqual(SOURCES["hinweiskarte"]["source_id"],
                            SOURCES["gefahrenkarte"]["source_id"])
        self.assertNotEqual(SOURCES["hinweiskarte"]["url"],
                            SOURCES["gefahrenkarte"]["url"])
        self.assertEqual(SOURCES["hinweiskarte"]["published_licence_label"], "dl-de-by-2.0")
        self.assertEqual(SOURCES["gefahrenkarte"]["published_licence_label"], "cc-by-4.0")
        self.assertIn("/ua_srhk?request=GetCapabilities&service=WFS",
                      SOURCES["hinweiskarte"]["url"])
        self.assertIn("/ua_srgk?request=GetCapabilities&service=WFS",
                      SOURCES["gefahrenkarte"]["url"])

    def test_metadata_is_not_a_model_grid_or_a_feature_read(self):
        out = inspect(xml(), "hinweiskarte")
        self.assertEqual(out["advertised_feature_count"], 1)
        self.assertTrue(out["epsg25832_advertised"])
        self.assertTrue(out["epsg25833_advertised"])
        for key in ("actual_water_depth_values_retrieved", "actual_depth_units_verified",
                    "rasters_or_atom_feeds_downloaded",
                    "specific_berlin_bld4_box_coverage_verified",
                    "scientific_model_input_approved"):
            self.assertFalse(out[key])
        self.assertTrue(out["wfs_service_not_geo_tiff_raster"])

    def test_rejects_malformed_unreviewed_xml_and_source_alias(self):
        for original in (b"", b"<ExceptionReport/>", b" " * (MAX_BYTES + 1),
                         b'<!DOCTYPE a [<!ENTITY x "secret">]><WFS_Capabilities/>',
                         xml(version="1.1.0"), xml(version="3.0.0"),
                         xml().replace(b"WFS_Capabilities", b"SomeOtherRoot")):
            with self.subTest(original=original[:30]), self.assertRaises(StarkregenError):
                inspect(original, "hinweiskarte")
        with self.assertRaises(StarkregenError):
            inspect(xml(), "unknown")

    def test_duplicate_and_unbounded_feature_metadata_blocks(self):
        a = xml()
        duplicate = a.replace(b"</wfs:FeatureTypeList>", (
            b"<wfs:FeatureType><wfs:Name>ua_srhk:waterdepth</wfs:Name>"
            b"<wfs:DefaultCRS>EPSG:25832</wfs:DefaultCRS>"
            b"</wfs:FeatureType></wfs:FeatureTypeList>"
        ))
        with self.assertRaisesRegex(StarkregenError, "duplicate"):
            inspect(duplicate, "hinweiskarte")
        bad = a.replace(b"<wfs:DefaultCRS>urn:ogc:def:crs:EPSG::25832</wfs:DefaultCRS>", b"")
        bad = bad.replace(b"<wfs:OtherCRS>urn:ogc:def:crs:EPSG::25833</wfs:OtherCRS>", b"")
        with self.assertRaisesRegex(StarkregenError, "coordinate reference"):
            inspect(bad, "hinweiskarte")

    def test_exact_url_and_no_external_feature_bytes(self):
        for source, config in SOURCES.items():
            with self.subTest(source=source):
                def opener(req, timeout):
                    self.assertEqual(req.full_url, config["url"])
                    self.assertEqual(req.get_method(), "GET")
                    self.assertEqual(timeout, TIMEOUT)
                    return Response(xml(), url=config["url"])
                p = probe(source, opener=opener,
                          clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
                self.assertEqual(p["source_id"], config["source_id"])
                self.assertEqual(p["original_response_byte_count"], len(xml()))
                self.assertEqual(len(p["original_response_sha256"]), 64)
                self.assertFalse(p["original_xml_bytes_persisted"])
                self.assertFalse(p["automated_feature_acquisition_authorized_by_this_probe"])
                self.assertFalse(p["scientific_model_input_approved"])
                self.assertNotIn("building_values", p)

    def test_redirect_wrong_media_http_failure_and_bad_clock(self):
        cfg = SOURCES["hinweiskarte"]
        wrong = (
            Response(xml(), url="https://elsewhere.invalid/fake"),
            Response(xml(), url=cfg["url"], media="text/html"),
            Response(xml(), url=cfg["url"], media="application/json"),
        )
        for obj in wrong:
            with self.subTest(media=obj.headers["Content-Type"]), self.assertRaises(StarkregenError):
                probe("hinweiskarte", opener=lambda req, timeout: obj)
        class BadStatus(Response):
            status = 503
        with self.assertRaises(StarkregenError):
            probe("hinweiskarte", opener=lambda req, timeout: BadStatus(xml(), url=cfg["url"]))
        with self.assertRaisesRegex(StarkregenError, "clock"):
            probe("hinweiskarte", opener=lambda req, timeout: Response(xml(), url=cfg["url"]),
                  clock=lambda: datetime(2026, 11, 1))


if __name__ == "__main__":
    unittest.main()
