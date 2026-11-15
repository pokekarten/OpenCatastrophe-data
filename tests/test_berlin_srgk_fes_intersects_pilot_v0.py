# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only source-locked Berlin SRGK FES Intersects tests."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from unittest.mock import patch
import unittest

from research_runners.berlin_srgk_fes_intersects_pilot_v0 import (
    BASE, FEATURE_URL, FILTER, SCHEMA_URL, FesBlocked,
    _fetch, assess_feature, validate_original_schema, probe,
)


def xsd():
    return b'''<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
      xmlns:gml="http://www.opengis.net/gml/3.2">
      <xs:element name="a_modellgebiete" type="t:Feature"/>
      <xs:element name="geom" type="gml:MultiSurfacePropertyType"/>
      </xs:schema>'''


def feature(poly=None, *, matched=1):
    rows = ([] if poly is None else [{
        "type": "Feature", "id": "private-id-never-log",
        "properties": {"address": "PRIVATE must not export"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [poly[0], poly[1]], [poly[2], poly[1]],
                [poly[2], poly[3]], [poly[0], poly[3]],
                [poly[0], poly[1]],
            ]],
        },
    }])
    return json.dumps({
        "type": "FeatureCollection", "numberMatched": matched,
        "numberReturned": len(rows),
        "crs": {"type": "name", "properties": {"name": "EPSG:25833"}},
        "features": rows,
    }).encode()


class Fake(BytesIO):
    def __init__(self, url, raw, *, media, status=200, encoding="identity"):
        super().__init__(raw)
        self._url = url
        self.status = status
        self.headers = {"Content-Type": media, "Content-Length": str(len(raw)),
                        "Content-Encoding": encoding}
    def geturl(self):
        return self._url


class BerlinFesIntersectsSourceTests(unittest.TestCase):
    def test_filter_is_fixed_exact_spatial_envelope_and_property(self):
        self.assertIn("<fes:Intersects>", FILTER)
        self.assertIn("<fes:ValueReference>geom</fes:ValueReference>", FILTER)
        self.assertIn("<gml:lowerCorner>391700 5819950</gml:lowerCorner>", FILTER)
        self.assertIn("<gml:upperCorner>391900 5820150</gml:upperCorner>", FILTER)
        self.assertIn("typeNames=ua_srgk%3Aa_modellgebiete", FEATURE_URL)
        self.assertIn("filter=", FEATURE_URL)
        self.assertNotIn("private", FEATURE_URL)

    def test_synthetic_schema_requires_exact_pinned_original_bytes(self):
        with self.assertRaisesRegex(FesBlocked, "SHA changed"):
            validate_original_schema(xsd())
        with patch(
            "research_runners.berlin_srgk_fes_intersects_pilot_v0.SCHEMA_SHA256",
            sha256(xsd()).hexdigest(),
        ):
            got=validate_original_schema(xsd())
            self.assertEqual(got["geometry_property_name_candidates"], ["geom"])
            self.assertFalse(got["filter_capabilities_and_server_bbox_behavior_proven"])
            tampered = xsd().replace(b'name="geom"',b'name="other"')
            with patch(
                "research_runners.berlin_srgk_fes_intersects_pilot_v0.SCHEMA_SHA256",
                sha256(tampered).hexdigest(),
            ):
                with self.assertRaisesRegex(FesBlocked, "source property"):
                    validate_original_schema(tampered)

    def test_valid_polygon_covered_area_but_no_flood_or_cat_admission(self):
        out=assess_feature(feature((391725,5819975,391740,5819990)))
        self.assertEqual(out["model_area_result"],
                         "EXACT_SAMPLED_MODEL_AREA_INTERSECTION_PROVEN")
        self.assertEqual(out["source_pilot_model_intersection_m2"],225.0)
        self.assertFalse(out["hazard_depth_or_insurer_loss_admitted"])
        self.assertFalse(out["any_noncoverage_or_dryness_proven"])
        self.assertNotIn("private-id-never-log",str(out))

    def test_unrelated_or_wrong_crs_geometry_still_blocked(self):
        with self.assertRaisesRegex(FesBlocked,"does not intersect"):
            assess_feature(feature((370000,5790000,371000,5791000)))
        raw=feature((391725,5819975,391740,5819990))
        with self.assertRaisesRegex(FesBlocked,"feature/CRS"):
            assess_feature(raw.replace(b"EPSG:25833",b"EPSG:4326"))

    def test_empty_source_is_not_proven_no_model_or_dry(self):
        out=assess_feature(feature(None,matched=0))
        self.assertEqual(out["model_area_result"],
                         "EMPTY_FES_RESPONSE_COVERAGE_UNRESOLVED")
        self.assertIsNone(out["source_pilot_model_intersection_m2"])
        self.assertFalse(out["any_noncoverage_or_dryness_proven"])
        self.assertFalse(out["hazard_depth_or_insurer_loss_admitted"])

    def test_exact_original_sources_and_no_geometry_or_id_exfiltration(self):
        urls=[]
        data={SCHEMA_URL:xsd(),FEATURE_URL:feature((391725,5819975,391740,5819990))}
        def op(req):
            urls.append(req.full_url)
            return Fake(req.full_url,data[req.full_url],
                        media="application/xml" if req.full_url==SCHEMA_URL
                              else "application/json")
        with patch(
            "research_runners.berlin_srgk_fes_intersects_pilot_v0.SCHEMA_SHA256",
            sha256(xsd()).hexdigest()
        ):
            out=probe(opener=op,
                      clock=lambda:datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(urls,[SCHEMA_URL,FEATURE_URL])
        self.assertTrue(all(u.startswith(BASE+"?") for u in urls))
        self.assertFalse(out["original_feature_ids_geometries_or_attributes_exported"])
        self.assertFalse(out["detail_pluvial_flood_raster_cells_verified"])
        self.assertFalse(out["annual_flood_event_model_or_CAT_loss_admitted"])
        self.assertNotIn("PRIVATE",json.dumps(out))
        self.assertNotIn("private-id-never-log",json.dumps(out))
        self.assertNotIn('"coordinates"',json.dumps(out))

    def test_wrong_source_response_or_oversize_fails_closed(self):
        with self.assertRaisesRegex(FesBlocked,"not explicitly approved"):
            _fetch("https://other.invalid/wfs")
        with self.assertRaisesRegex(FesBlocked,"media type"):
            _fetch(SCHEMA_URL,opener=lambda req:
                   Fake(req.full_url,xsd(),media="image/png"))
        with self.assertRaises(FesBlocked):
            _fetch(FEATURE_URL,opener=lambda req:
                   Fake(req.full_url,b"x"*786433,media="application/json"))
        with self.assertRaisesRegex(FesBlocked,"status"):
            _fetch(FEATURE_URL,opener=lambda req:
                   Fake(req.full_url,feature(None),media="application/json",
                        status=206))

    def test_feature_count_crs_and_provider_json_are_challenged(self):
        with self.assertRaises(FesBlocked):
            assess_feature(b'<ServiceExceptionReport/>')
        with self.assertRaises(FesBlocked):
            assess_feature(b"not-json")
        with self.assertRaises(FesBlocked):
            assess_feature(
                feature((391725,5819975,391740,5819990)).replace(
                    b'"numberReturned": 1',b'"numberReturned": 0'
                )
            )


if __name__=="__main__":
    unittest.main()
