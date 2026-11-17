# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only negative and positive cases; never access original WFS."""
import hashlib
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from scripts.probe_hr_dgu_buildings_gml_window_v0 import (
    BBOX, BuildingGmlError, FOOTPRINT_URI, COMBINED_URI, NoRedirect, _signed_twice_area,
    fixed_url, inspect_gml, inspect_semantic_label, live_one_original, validate_content_length,
)


def sample(
    *, points="459100 5074600 459140 5074600 459140 5074640 459100 5074640 459100 5074600",
    crs="EPSG:3765", geom=True, number="1", feature="Building",
    duplicate=False, dim="2", ref="true", href=FOOTPRINT_URI,
    geometry_type="Polygon",
):
    if geometry_type == "Polygon":
        shape = (
            '<gml:Polygon srsName="' + crs + '" srsDimension="' + dim + '">'
            '<gml:exterior><gml:LinearRing><gml:posList>' + points +
            '</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon>'
        )
    elif geometry_type == "Point":
        shape = '<gml:Point srsName="' + crs + '"><gml:pos>459100 5074600</gml:pos></gml:Point>'
    else:
        raise ValueError("unknown synthetic geometry fixture")
    polygon = (
        '<bu:geometry2D><base:BuildingGeometry2D><base:geometry>' + shape +
        '</base:geometry><base:referenceGeometry>' + ref +
        '</base:referenceGeometry><base:horizontalGeometryReference xlink:href="' +
        href + '"/></base:BuildingGeometry2D></bu:geometry2D>'
    ) if geom else ""
    member = '<wfs:member><bu:' + feature + '>' + polygon + '</bu:' + feature + '></wfs:member>'
    raw = (
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" '
        'xmlns:gml="http://www.opengis.net/gml/3.2" '
        'xmlns:bu="http://inspire.ec.europa.eu/schemas/bu-core2d/4.0" '
        'xmlns:base="http://inspire.ec.europa.eu/schemas/bu-base/4.0" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
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
        self.assertTrue(receipt["inspire_reference_geometry_verified"])
        self.assertEqual(receipt["inspire_horizontal_geometry_reference"], "footPrint")
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

    def test_reject_wrong_insPIRE_namespace_and_nested_decoy(self):
        raw = sample().replace(b"base:BuildingGeometry2D", b"bu:BuildingGeometry2D")
        with self.assertRaisesRegex(BuildingGmlError, "bu-base"):
            inspect_gml(raw)
        # A Polygon nested in the wrong member of the base data type must not
        # be promoted to referenceGeometry by broad descendant searches.
        raw = sample().replace(
            b"<base:geometry>", b"<base:geometry><gml:Point/>"
        )
        with self.assertRaises(BuildingGmlError):
            inspect_gml(raw)

    def test_reject_unreviewed_extra_base_geometry_properties(self):
        # Fail closed when extra direct property children could carry a second
        # geometry or introduce coordinate metadata outside the reviewed scope.
        original = sample()
        insertion_point = b"</base:BuildingGeometry2D>"
        for extra in (
            b"<base:geometry><gml:Point/></base:geometry>",
            b"<base:unreviewedExtension><gml:pos>0 0</gml:pos></base:unreviewedExtension>",
            b"<base:horizontalGeometryEstimatedAccuracy>1</base:horizontalGeometryEstimatedAccuracy>",
        ):
            with self.subTest(extra=extra), self.assertRaisesRegex(
                BuildingGmlError, "unexpected or duplicated"
            ):
                inspect_gml(original.replace(insertion_point, extra + insertion_point, 1))
        # The exact reviewed three-property fixture remains valid.
        self.assertEqual(inspect_gml(original)["feature_records_checked"], 1)

    def test_reject_missing_or_false_insPIRE_reference_geometry(self):
        for raw in (
            sample(ref="false"),
            sample(ref="1"),
            sample(ref=""),
            sample().replace(
                b"<base:referenceGeometry>true</base:referenceGeometry>", b""
            ),
            sample().replace(
                b"</base:referenceGeometry>",
                b"</base:referenceGeometry><base:referenceGeometry>true</base:referenceGeometry>",
            ),
        ):
            with self.subTest(raw=raw[:150]), self.assertRaisesRegex(
                BuildingGmlError, "referenceGeometry"
            ):
                inspect_gml(raw)

    def test_reject_unreviewed_geometry_horizontal_reference(self):
        for raw in (
            sample(href="http://inspire.ec.europa.eu/codelist/HorizontalGeometryReferenceValue/roofEdge"),
            sample(href="http://inspire.ec.europa.eu/codelist/HorizontalGeometryReferenceValue/combined"),
            sample(href="https://example.test/footPrint"),
            sample(href=""),
            sample().replace(
                b'<base:horizontalGeometryReference xlink:href="' + FOOTPRINT_URI.encode() + b'"/>',
                b'<base:horizontalGeometryReference/>',
            ),
        ):
            with self.subTest(raw=raw[:150]), self.assertRaisesRegex(
                BuildingGmlError, "footPrint"
            ):
                inspect_gml(raw)

    def test_native_combined_semantics_audited_but_footprint_rejected(self):
        # Source-observed combination: old OGC EPSG URI + combined reference.
        native_crs = "http://www.opengis.net/gml/srs/epsg.xml#3765"
        # Inject only a synthetic string to prove the receipt never echoes IDs.
        raw = sample(crs=native_crs, href=COMBINED_URI).replace(
            b"<bu:Building>",
            b'<bu:Building sourceIdentifier="synthetic-DO-NOT-PRINT">',
            1,
        )
        receipt = inspect_semantic_label(raw)
        self.assertEqual(receipt["inspire_horizontal_geometry_reference"], "combined")
        self.assertEqual(receipt["original_xml_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(receipt["original_xml_bytes"], len(raw))
        for key in (
            "actual_polygon_geometry_verified", "ground_footprint_verified",
            "reusable_source_rights_fully_reviewed", "model_input_admitted",
        ):
            self.assertFalse(receipt[key])
        self.assertNotIn("synthetic-DO-NOT-PRINT", json.dumps(receipt))
        self.assertNotIn("459100", json.dumps(receipt))
        with self.assertRaisesRegex(BuildingGmlError, "footPrint"):
            inspect_gml(raw)
        self.assertEqual(
            inspect_semantic_label(sample())["inspire_horizontal_geometry_reference"],
            "footPrint"
        )

    def test_semantic_audit_fail_closed_on_unreviewed_inputs(self):
        clean = sample()
        for raw in (
            sample(duplicate=True),
            sample(number="2"),
            sample(geometry_type="Point"),
            sample(crs="EPSG:4326"),
            sample(href="https://example.test/not-reviewed"),
            sample(ref="false"),
            sample(geom=False),
            b'<!DOCTYPE x [<!ENTITY leak "secret">]>' + clean,
            clean.replace(
                b"</base:BuildingGeometry2D>",
                b"<base:geometry><gml:Point/></base:geometry>"
                b"</base:BuildingGeometry2D>", 1
            ),
        ):
            with self.subTest(raw_length=len(raw)), self.assertRaises(BuildingGmlError):
                inspect_semantic_label(raw)

    def test_semantic_audit_error_reports_only_bounded_schema_field_names(self):
        # Diagnose provider schema drift without disclosing data or attributes.
        bad = sample().replace(
            b"</base:BuildingGeometry2D>",
            b'<base:horizontalGeometryEstimatedAccuracy secret="PRIVATE-DO-NOT-PRINT">'
            b'459100 5074600 PRIVATE-DO-NOT-PRINT'
            b'</base:horizontalGeometryEstimatedAccuracy>'
            b"</base:BuildingGeometry2D>",
            1,
        )
        with self.assertRaises(BuildingGmlError) as caught:
            inspect_semantic_label(bad)
        message = str(caught.exception)
        self.assertIn("horizontalGeometryEstimatedAccuracy", message)
        self.assertIn("count=4", message)
        self.assertNotIn("PRIVATE-DO-NOT-PRINT", message)
        self.assertNotIn("459100", message)
        self.assertLess(len(message), 260)

    def test_reject_non_polygon_geometry_profile(self):
        with self.assertRaisesRegex(BuildingGmlError, "unsupported"):
            inspect_gml(sample(geometry_type="Point"))

    def test_reject_wrong_crs_and_3d(self):
        for raw in (sample(crs="EPSG:4326"), sample(crs=""), sample(dim="3")):
            with self.subTest(raw=raw[:80]), self.assertRaises(BuildingGmlError):
                inspect_gml(raw)

    def test_exact_original_legacy_ogc_http_crs_alias(self):
        # An anonymous, bounded provider GML intermediary response on
        # 2026-11-17 declared this exact legacy OGC URI directly on its
        # Polygon; a strict EPSG-only preflight otherwise rejected it.
        native = "http://www.opengis.net/gml/srs/epsg.xml#3765"
        receipt = inspect_gml(sample(crs=native))
        self.assertEqual(receipt["declared_crs"], "EPSG:3765")
        self.assertEqual(receipt["feature_records_checked"], 1)
        self.assertFalse(receipt["model_input_admitted"])

        # Exact provider evidence does not authorize nearby CRS IDs,
        # URI schemes or opportunistic alias expansion.
        for other in (
            "http://www.opengis.net/gml/srs/epsg.xml#3766",
            "https://www.opengis.net/gml/srs/epsg.xml#3765",
            "http://www.opengis.net/gml/srs/epsg.xml#4326",
            "http://www.opengis.net/gml/srs/epsg.xml",
        ):
            with self.subTest(other=other):
                with self.assertRaisesRegex(
                    BuildingGmlError, "must directly declare reviewed EPSG:3765"
                ):
                    inspect_gml(sample(crs=other))

    def test_reject_only_nested_crs_without_polygon_crs(self):
        # GML srsName on a LinearRing/posList does not establish the polygon's
        # own source CRS. Such nested-only metadata used to pass because a
        # descendant-wide union contained the expected EPSG:3765 value.
        original = sample()
        without_polygon_crs = original.replace(
            b'<gml:Polygon srsName="EPSG:3765"',
            b'<gml:Polygon', 1,
        )
        self.assertNotEqual(original, without_polygon_crs)
        nested_crs_cases = [without_polygon_crs]
        for tag in ("LinearRing", "posList"):
            before = ("<gml:" + tag + ">").encode("ascii")
            after = ('<gml:' + tag + ' srsName="EPSG:3765">').encode("ascii")
            self.assertIn(before, without_polygon_crs)
            nested_crs_cases.append(
                without_polygon_crs.replace(before, after, 1)
            )
        for raw in nested_crs_cases:
            with self.subTest(raw=raw[:250]):
                with self.assertRaisesRegex(
                    BuildingGmlError, "polygon must directly declare"
                ):
                    inspect_gml(raw)
        # The original single-footprint explicit polygon CRS remains accepted.
        self.assertEqual(inspect_gml(original)["feature_records_checked"], 1)

    def test_reject_swapped_axes_and_outside_window(self):
        for coords in (
            "5074600 459100 5074600 459140 5074640 459140 5074640 459100 5074600 459100",
            "500100 5084600 500140 5084600 500140 5084640 500100 5084640 500100 5084600",
        ):
            with self.assertRaises(BuildingGmlError):
                inspect_gml(sample(points=coords))

    def test_reject_disjoint_concave_polygon_despite_envelope_overlap(self):
        # A valid L-shaped ring wraps around the lower-left search-window
        # corner. Its envelope overlaps the BBOX, but no geometry does.
        outside_l = (
            "458900 5074600 458900 5074400 459100 5074400 "
            "459100 5074450 458950 5074450 458950 5074600 "
            "458900 5074600"
        )
        with self.assertRaisesRegex(BuildingGmlError, "polygon itself"):
            inspect_gml(sample(points=outside_l))

    def test_accept_window_fully_enclosed_by_polygon(self):
        # None of the corners of the outer polygon lies inside the window,
        # and no polygon edge crosses the window. A corner-in-polygon check
        # is needed to prove actual intersection.
        enclosing = (
            "458900 5074400 459700 5074400 459700 5075200 "
            "458900 5075200 458900 5074400"
        )
        receipt = inspect_gml(sample(points=enclosing))
        self.assertTrue(receipt["actual_polygon_intersects_fixed_window"])
        self.assertFalse(receipt["model_input_admitted"])

    def test_accept_crossing_and_boundary_touch_without_area_claim(self):
        # Polygon vertices all outside BBOX, its edges cross the BBOX.
        crossing = (
            "459250 5074400 459350 5074400 459350 5075200 "
            "459250 5075200 459250 5074400"
        )
        # A zero-area boundary contact is geometric intersection, but is
        # NOT evidence that a building has positive area inside the window.
        touching = (
            "458900 5074600 459000 5074600 459000 5074650 "
            "458900 5074650 458900 5074600"
        )
        for points in (crossing, touching):
            with self.subTest(points=points):
                result = inspect_gml(sample(points=points))
                self.assertTrue(result["actual_polygon_intersects_fixed_window"])
                self.assertNotIn("positive_area_inside_window", result)

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

    def test_reject_mixed_linear_ring_coordinate_encodings(self):
        # A single posList is insufficient if the same LinearRing also
        # contains an incompatible second encoding or another GML child.
        clean = sample()
        for extra in (
            b"<gml:pos>459120 5074620</gml:pos>",
            b"<gml:pointProperty/>",
            b"<gml:coordinates>459100,5074600</gml:coordinates>",
        ):
            with self.subTest(extra=extra), self.assertRaisesRegex(
                BuildingGmlError, "ambiguous GML exterior posList"
            ):
                inspect_gml(clean.replace(
                    b"</gml:posList>", b"</gml:posList>" + extra, 1
                ))

    def test_reject_unreviewed_polygon_and_nested_position_content(self):
        clean = sample()
        unreviewed = (
            (clean.replace(
                b"</gml:exterior>",
                b"</gml:exterior><gml:posList>459120 5074620</gml:posList>", 1
            ), "unexpected GML Polygon"),
            (clean.replace(
                b"</gml:posList>",
                b"<gml:pos>459120 5074620</gml:pos></gml:posList>", 1
            ), "nested coordinate elements"),
            (clean.replace(
                b"<gml:posList>",
                b"459120 5074620<gml:posList>", 1
            ), "mixed coordinate text"),
            (clean.replace(
                b"</gml:posList>",
                b"</gml:posList>459120 5074620", 1
            ), "mixed coordinate text"),
        )
        for raw, expected in unreviewed:
            with self.subTest(expected=expected, raw_length=len(raw)):
                with self.assertRaisesRegex(BuildingGmlError, expected):
                    inspect_gml(raw)
        self.assertEqual(inspect_gml(clean)["feature_records_checked"], 1)

    def test_translated_shoelace_area_near_degeneracy_gate(self):
        x0, y0 = 459100.0, 5074600.0

        def square(side):
            xy = [
                (x0, y0), (x0 + side, y0),
                (x0 + side, y0 + side), (x0, y0 + side), (x0, y0),
            ]
            return xy, sample(points=" ".join(f"{x:.8f} {y:.8f}" for x, y in xy))

        accepted_xy, accepted_xml = square(0.0225)
        self.assertAlmostEqual(
            _signed_twice_area(accepted_xy), 2 * 0.0225 ** 2, places=8
        )
        self.assertEqual(inspect_gml(accepted_xml)["feature_records_checked"], 1)
        self.assertFalse(inspect_gml(accepted_xml)["model_input_admitted"])
        _, rejected_xml = square(0.0223)
        with self.assertRaisesRegex(BuildingGmlError, "degenerate"):
            inspect_gml(rejected_xml)

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

    def test_original_http_vs_network_failures_are_sanitized(self):
        class RefusingOpener:
            def __init__(self, exc):
                self.exc = exc

            def open(self, *args, **kwargs):
                raise self.exc

        for status in (400, 403, 429, 500):
            # Deliberately embed a sensitive-looking error reason to confirm
            # that only numeric HTTP status can leave the source runner.
            exc = HTTPError(fixed_url(), status, "SECRET-NEVER-PRINT", {}, None)
            with patch(
                "scripts.probe_hr_dgu_buildings_gml_window_v0.request.build_opener",
                return_value=RefusingOpener(exc)
            ):
                with self.assertRaises(BuildingGmlError) as caught:
                    live_one_original()
            error_text = str(caught.exception)
            self.assertIn(f"original WFS HTTP {status}", error_text)
            self.assertNotIn("SECRET-NEVER-PRINT", error_text)
            self.assertNotIn("api.uredjenazemlja.hr", error_text)

        with patch(
            "scripts.probe_hr_dgu_buildings_gml_window_v0.request.build_opener",
            return_value=RefusingOpener(URLError("SECRET-NEVER-PRINT"))
        ):
            with self.assertRaisesRegex(
                BuildingGmlError, "original WFS network unavailable"
            ) as caught:
                live_one_original()
        self.assertNotIn("SECRET-NEVER-PRINT", str(caught.exception))

    def test_redirect_never_followed(self):
        with self.assertRaises(BuildingGmlError):
            NoRedirect().redirect_request(None, None, 302, "moved", {}, "https://elsewhere.test")


if __name__ == "__main__":
    unittest.main()
