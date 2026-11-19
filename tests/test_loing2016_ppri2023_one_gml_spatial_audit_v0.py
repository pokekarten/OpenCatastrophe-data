# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Network-free GML regression fixtures; not original French publisher bytes."""
import unittest

from research_runners.loing2016_ppri2023_one_gml_spatial_audit_v0 import (
    GMLReviewBlocked, audit_one_gml,
)


def ring(west="680100", south="6766700", east="680300", north="6766800"):
    return (f"{west} {south} {east} {south} {east} {north} "
            f"{west} {north} {west} {south}")


def polygon(outer, inner=None):
    hole = (
        "<gml:interior><gml:LinearRing><gml:posList>"
        + inner + "</gml:posList></gml:LinearRing></gml:interior>"
    ) if inner is not None else ""
    return (
        "<gml:surfaceMember><gml:Polygon>"
        "<gml:exterior><gml:LinearRing><gml:posList>"
        + outer + "</gml:posList></gml:LinearRing></gml:exterior>"
        + hole + "</gml:Polygon></gml:surfaceMember>"
    )


def fixture(members=None, year="", niva="F", date="2023-janvier"):
    if members is None:
        members = polygon(ring())
    fields = {
        "ID_ZONE": "PPR_Loing-Av_F", "NIVALEA": niva,
        "NIVALEA_ST": "04", "DATECARTE": date,
        "SRCE_ANNEE": year, "SRCE_GEOM": "",
    }
    tags = "".join(f"<ms:{k}>{v}</ms:{k}>" for k, v in fields.items())
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"'
        ' xmlns:ms="http://mapserver.gis.umn.edu/mapserver"'
        ' xmlns:gml="http://www.opengis.net/gml/3.2" numberReturned="1">'
        '<wfs:boundedBy><gml:Envelope srsName="urn:ogc:def:crs:EPSG::2154">'
        '<gml:lowerCorner>673912.266249 6761573.956607</gml:lowerCorner>'
        '<gml:upperCorner>686179.627884 6785029.687534</gml:upperCorner>'
        '</gml:Envelope></wfs:boundedBy>'
        '<wfs:member><ms:N_ZONE_ALEA_PPRN_20220018_S_045>'
        '<ms:geometry><gml:MultiSurface>' + members
        + '</gml:MultiSurface></ms:geometry>' + tags
        + '</ms:N_ZONE_ALEA_PPRN_20220018_S_045></wfs:member>'
        '</wfs:FeatureCollection>'
    )
    return xml.encode("utf-8")


class LoingOneFeatureWfsTests(unittest.TestCase):
    def test_one_2023_synthetic_feature_spatially_classifies_only_one_mark(self):
        out = audit_one_gml(fixture())
        self.assertEqual(out["polygons_in_one_feature"], 1)
        self.assertEqual(out["interior_rings_in_one_feature"], 0)
        p, q = out["point_in_polygon_2016_mark_checks"]
        self.assertEqual((p["official_site_id"], p["inside_this_2023_feature"]),
                         ("CER_LO_16_S_174", 0))
        self.assertEqual((q["official_site_id"], q["inside_this_2023_feature"]),
                         ("CER_LO_16_S_175", 1))
        self.assertEqual(out["source_map_month"], "2023-janvier")

    def test_multi_surface_polygons_can_cover_both_without_complete_layer_claim(self):
        two = polygon(ring()) + polygon(
            ring("679700", "6766700", "679900", "6766900")
        )
        out = audit_one_gml(fixture(two))
        self.assertEqual(out["polygons_in_one_feature"], 2)
        self.assertEqual([x["inside_this_2023_feature"]
                          for x in out["point_in_polygon_2016_mark_checks"]], [1, 1])
        self.assertFalse(out["this_is_the_complete_ppri_layer"])

    def test_accurate_hole_excludes_point_without_declaring_dry_area(self):
        inner = ring("680180", "6766730", "680210", "6766760")
        out = audit_one_gml(fixture(polygon(ring(), inner)))
        self.assertEqual(out["interior_rings_in_one_feature"], 1)
        self.assertEqual(out["point_in_polygon_2016_mark_checks"][1]["inside_this_2023_feature"], 0)
        self.assertFalse(out["historical_2016_flood_geometry_independently_validated"])

    def test_exact_vertex_or_edge_is_uncertain_not_forcibly_inside(self):
        out = audit_one_gml(fixture(
            polygon(ring("680192.03", "6766742.32", "680300", "6766800"))
        ))
        q = out["point_in_polygon_2016_mark_checks"][1]
        self.assertEqual(q["boundary_ambiguous"], 1)
        self.assertEqual(q["inside_this_2023_feature"], 0)

    def test_synthetic_gml_content_digest_is_not_provider_attestation(self):
        src = fixture()
        out = audit_one_gml(src)
        self.assertEqual(len(out["gml_sha256_of_local_bytes"]), 64)
        self.assertEqual(out["gml_local_byte_count"], len(src))
        self.assertFalse(out["provider_original_http_byte_identity_independently_attested"])

    def test_historic_2016_admission_stays_shut_even_when_geometry_matches(self):
        out = audit_one_gml(fixture())
        for key in ("gml_schema_validated",
                    "source_event_year_present",
                    "historical_2016_flood_geometry_independently_validated",
                    "original_2016_zip_zich_acquired",
                    "2016_event_source_to_calibration_marks_lineage_known",
                    "building_depth_or_insured_loss_admitted"):
            self.assertFalse(out[key])

    def test_2016_claim_in_source_attribute_must_be_reviewed_not_autoadmitted(self):
        with self.assertRaises(GMLReviewBlocked):
            audit_one_gml(fixture(year="2016"))

    def test_wrong_hazard_code_and_map_date_must_block(self):
        for val in ("2016-juin", "2024-janvier"):
            with self.subTest(val=val), self.assertRaises(GMLReviewBlocked):
                audit_one_gml(fixture(date=val))
        with self.assertRaises(GMLReviewBlocked):
            audit_one_gml(fixture(niva="01"))

    def test_wrong_feature_layer_does_not_inherit_2023_science_claims(self):
        with self.assertRaises(GMLReviewBlocked):
            audit_one_gml(fixture().replace(
                b"N_ZONE_ALEA_PPRN_20220018_S_045",
                b"N_INOND_HORSPPRI_CLERY",
            ))

    def test_wrong_crs_must_not_use_lambert93_points(self):
        with self.assertRaises(GMLReviewBlocked):
            audit_one_gml(fixture().replace(b"EPSG::2154", b"EPSG::4326"))

    def test_missing_member_count_and_gml_geometry_block(self):
        a = fixture()
        with self.assertRaises(GMLReviewBlocked):
            audit_one_gml(a.replace(b'numberReturned="1"', b'numberReturned="2"'))
        with self.assertRaises(GMLReviewBlocked):
            audit_one_gml(a.replace(b"<gml:MultiSurface>", b"<gml:OtherGeometry>")
                             .replace(b"</gml:MultiSurface>", b"</gml:OtherGeometry>"))

    def test_truncated_geometry_and_open_ring_block(self):
        with self.assertRaises(GMLReviewBlocked):
            audit_one_gml(fixture()[:-50])
        with self.assertRaises(GMLReviewBlocked):
            audit_one_gml(fixture(polygon("680100 6766700 680300 6766700 "
                                          "680300 6766800 680100 6766800")))

    def test_malicious_dtd_entity_declarations_block(self):
        src = fixture()
        for evil in (b'<!DOCTYPE foo>', b'<!ENTITY boom "!" >'):
            with self.subTest(evil=evil), self.assertRaises(GMLReviewBlocked):
                audit_one_gml(src.replace(b"<wfs:FeatureCollection", evil + b"<wfs:FeatureCollection"))

    def test_nonfinite_and_out_of_range_projection_coordinates_block(self):
        for val in ("nan", "inf", "1000000000000000"):
            with self.subTest(val=val), self.assertRaises(GMLReviewBlocked):
                audit_one_gml(fixture(polygon(ring(west=val))))

    def test_bounded_input_and_wrong_xml_dialect_block(self):
        for blob in (b"", b"<a/>", b"x" * 8_388_609):
            with self.subTest(n=len(blob)), self.assertRaises(GMLReviewBlocked):
                audit_one_gml(blob)


if __name__ == "__main__":
    unittest.main()
