# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only negative and positive cases; never access original WFS."""
import unittest
from urllib.parse import parse_qs, urlsplit

from scripts.probe_hr_dgu_buildings_gml_window_v0 import (
    BBOX, BuildingGmlError, NoRedirect, fixed_url, inspect_gml, validate_content_length,
)


def sample(
    *, points="459100 5074600 459140 5074600 459140 5074640 459100 5074640 459100 5074600",
    crs="EPSG:3765", geom=True, number="1", feature="Building",
    duplicate=False, dim="2",
):
    polygon = (
        '<bu:geometry2D><bu:BuildingGeometry2D><bu:geometry>'
        '<gml:Polygon srsName="' + crs + '" srsDimension="' + dim + '">'
        '<gml:exterior><gml:LinearRing><gml:posList>' + points +
        '</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon>'
        '</bu:geometry></bu:BuildingGeometry2D></bu:geometry2D>'
    ) if geom else ""
    member = '<wfs:member><bu:' + feature + '>' + polygon + '</bu:' + feature + '></wfs:member>'
    raw = (
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" '
        'xmlns:gml="http://www.opengis.net/gml/3.2" '
        'xmlns:bu="http://inspire.ec.europa.eu/schemas/bu-core2d/4.0" '
        'numberReturned="' + number + '" numberMatched="unknown">'
        + member + (member if duplicate else "") + "</wfs:FeatureCollection>"
    )
    return raw.encode("utf-8")


class CroatianGmlWindowTest(unittest.TestCase):
    def test_fixed_provider_count_and_window(self):
        u = urlsplit(fixed_url())
        self.assertEqual(u.scheme, "https")
        self.assertEqual(u.hostname, "api.uredjenazemlja.hr")
        self.assertEqual(u.path, "/services/inspire/bu/wfs")
        q = parse_qs(u.query)
        self.assertEqual(q["TYPENAMES"], ["bu:Building"])
        self.assertEqual(q["COUNT"], ["1"])
        self.assertEqual(q["SRSNAME"], ["EPSG:3765"])
        self.assertEqual(q["BBOX"], [",".join(str(v) for v in BBOX) + ",EPSG:3765"])
        self.assertLess((600**2 + 600**2) ** .5, 2000)

    def test_one_synthetic_original_shape_profile(self):
        raw = sample()
        receipt = inspect_gml(raw)
        self.assertEqual(receipt["feature_records_checked"], 1)
        self.assertEqual(receipt["declared_crs"], "EPSG:3765")
        self.assertEqual(receipt["original_xml_bytes"], len(raw))
        self.assertFalse(receipt["model_input_admitted"])
        self.assertFalse(receipt["nationwide_completeness_verified"])
        self.assertNotIn("459100", str(receipt))
        self.assertNotIn("ID", str(receipt).split("original_xml_sha256")[0])

    def test_reject_missing_or_wrong_geometry_type(self):
        for raw in (sample(geom=False), sample(feature="BuildingPart")):
            with self.subTest(raw=raw[:75]), self.assertRaises(BuildingGmlError):
                inspect_gml(raw)

    def test_reject_wrong_crs_and_3d(self):
        for raw in (sample(crs="EPSG:4326"), sample(crs=""), sample(dim="3")):
            with self.subTest(raw=raw[:80]), self.assertRaises(BuildingGmlError):
                inspect_gml(raw)

    def test_reject_swapped_axes_and_outside_window(self):
        for coords in (
            "5074600 459100 5074600 459140 5074640 459140 5074640 459100 5074600 459100",
            "500100 5084600 500140 5084600 500140 5084640 500100 5084640 500100 5084600",
        ):
            with self.assertRaises(BuildingGmlError):
                inspect_gml(sample(points=coords))

    def test_reject_crossing_exterior_with_nonzero_signed_area(self):
        # The shoelace sum is nonzero, so an area-only test would pass.
        crossing = (
            "459100 5074600 459140 5074640 459100 5074650 "
            "459140 5074600 459160 5074640 459100 5074600"
        )
        with self.assertRaisesRegex(BuildingGmlError, "self-intersecting"):
            inspect_gml(sample(points=crossing))

    def test_reject_nonadjacent_repeated_vertex_and_zero_length_edge(self):
        for points in (
            "459100 5074600 459140 5074600 459140 5074640 "
            "459100 5074640 459140 5074600 459100 5074600",
            "459100 5074600 459140 5074600 459140 5074600 "
            "459140 5074640 459100 5074600",
        ):
            with self.subTest(points=points), self.assertRaises(BuildingGmlError):
                inspect_gml(sample(points=points))

    def test_reject_unreviewed_interior_ring(self):
        raw = sample().replace(b"</gml:Polygon>", b"<gml:interior/>" + b"</gml:Polygon>")
        with self.assertRaisesRegex(BuildingGmlError, "interior rings"):
            inspect_gml(raw)

    def test_allow_simple_nonconvex_exterior(self):
        concave = (
            "459100 5074600 459160 5074600 459160 5074660 "
            "459130 5074630 459100 5074660 459100 5074600"
        )
        result = inspect_gml(sample(points=concave))
        self.assertTrue(result["polygon_envelope_overlaps_fixed_window"])

    def test_reject_nonfinite_open_degenerate_or_oversize(self):
        for coords in (
            "NaN 5074600 459140 5074600 459140 5074640 459100 5074640 459100 5074600",
            "459100 5074600 459140 5074600 459140 5074640 459100 5074640 459101 5074600",
            "459100 5074600 459110 5074600 459120 5074600 459130 5074600 459100 5074600",
        ):
            with self.assertRaises(BuildingGmlError):
                inspect_gml(sample(points=coords))
        with self.assertRaises(BuildingGmlError):
            inspect_gml(sample() + b" " * (512 * 1024))

    def test_reject_multi_member_and_incorrect_count(self):
        for raw in (sample(duplicate=True), sample(number="0"), sample(number="2")):
            with self.assertRaises(BuildingGmlError):
                inspect_gml(raw)

    def test_reject_xml_entities_and_exception(self):
        with self.assertRaises(BuildingGmlError):
            inspect_gml(b'<!DOCTYPE a [<!ENTITY b "unsafe">]>' + sample())
        with self.assertRaises(BuildingGmlError):
            inspect_gml(b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows/1.1"/>')

    def test_content_length_declared_bounded_before_integer_conversion(self):
        validate_content_length(None, 12)
        validate_content_length("12", 12)
        for declared in ("9" * 5000, True, 12, "-1", "+12", "12x", "１２",
                         "0", str(512 * 1024 + 1), "11", ""):
            with self.subTest(declared=str(declared)[:24]), self.assertRaises(BuildingGmlError):
                validate_content_length(declared, 12)

    def test_redirect_never_followed(self):
        with self.assertRaises(BuildingGmlError):
            NoRedirect().redirect_request(None, None, 302, "moved", {}, "https://elsewhere.test")


if __name__ == "__main__":
    unittest.main()
