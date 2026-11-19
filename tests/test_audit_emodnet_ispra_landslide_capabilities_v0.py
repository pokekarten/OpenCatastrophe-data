# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests: exact ISPRA submarine landslide WFS layer identity."""
from __future__ import annotations

import json
import unittest
from xml.sax.saxutils import escape

from scripts.audit_emodnet_ispra_landslide_capabilities_v0 import (
    CANDIDATE_NAMES, EMODnetWFSBlocked, MAX_BYTES, inspect_capabilities,
)

WFS_NS = "http://www.opengis.net/wfs/2.0"


def feature(name="ispra:landslide_pol_100k", title="Submarine Landslides Polygons (100k)",
            crs="urn:ogc:def:crs:EPSG::4326"):
    return (
        "<wfs:FeatureType><wfs:Name>" + escape(name) +
        "</wfs:Name><wfs:Title>" + escape(title) +
        "</wfs:Title><wfs:DefaultCRS>" + escape(crs) +
        "</wfs:DefaultCRS></wfs:FeatureType>"
    )


def body(*features, version="2.0.0", namespace=WFS_NS):
    return (
        '<wfs:WFS_Capabilities xmlns:wfs="' + escape(namespace) +
        '" version="' + escape(version) + '"><wfs:FeatureTypeList>' +
        "".join(features) + "</wfs:FeatureTypeList></wfs:WFS_Capabilities>"
    ).encode("utf-8")


class EMODnet100kIdentityTests(unittest.TestCase):
    def test_exact_unversioned_metadata_candidate(self):
        original = body(feature(), feature("ispra:earthquakes", "Earthquakes"))
        result = inspect_capabilities(original)
        self.assertEqual(result["candidate_in_local_capabilities"], "ispra:landslide_pol_100k")
        self.assertEqual(result["layer_count_in_local_capabilities"], 2)
        self.assertEqual(len(result["sample_input_byte_sha256"]), 64)
        self.assertFalse(result["original_provider_response_verified"])
        self.assertFalse(result["commercial_automation_approved"])
        self.assertFalse(result["cat_model_input_admitted"])
        self.assertFalse(result["asset_or_feature_bytes_acquired"])

    def test_exact_2023_metadata_candidate(self):
        result = inspect_capabilities(body(feature("ispra:landslide_pol_100k_2023")))
        self.assertEqual(result["candidate_in_local_capabilities"], "ispra:landslide_pol_100k_2023")
        self.assertEqual(len(CANDIDATE_NAMES), 2)

    def test_both_official_metadata_names_must_fail_closed(self):
        with self.assertRaises(EMODnetWFSBlocked):
            inspect_capabilities(body(feature(), feature("ispra:landslide_pol_100k_2023")))

    def test_no_reviewed_candidate_must_fail(self):
        with self.assertRaises(EMODnetWFSBlocked):
            inspect_capabilities(body(feature("ispra:earthquakes", "Earthquakes")))

    def test_duplicate_feature_name_rejected_even_outside_candidate(self):
        with self.assertRaises(EMODnetWFSBlocked):
            inspect_capabilities(body(feature(), feature("ispra:earthquakes", "Earthquakes"),
                                      feature("ispra:earthquakes", "Earthquakes")))

    def test_wrong_wfs_version_namespace_or_body(self):
        for source in (
            body(feature(), version="1.1.0"),
            body(feature(), namespace="http://www.opengis.net/wfs"),
            b"<html><body>403 blocked</body></html>",
            b"not xml",
            b"",
        ):
            with self.subTest(source=source[:40]), self.assertRaises(EMODnetWFSBlocked):
                inspect_capabilities(source)

    def test_default_crs_cannot_be_inferred(self):
        for crs in ("", "EPSG:3857", "EPSG:4269", "urn:ogc:def:crs:EPSG::2056"):
            with self.subTest(crs=crs), self.assertRaises(EMODnetWFSBlocked):
                inspect_capabilities(body(feature(crs=crs)))
        result = inspect_capabilities(body(feature(crs="EPSG:4326")))
        self.assertTrue(result["local_capabilities_identity_unambiguous"])

    def test_unreviewed_scientific_title_rejected(self):
        for title in ("Earthquakes (100k)", "Submarine Landslides", "Polygon", ""):
            with self.subTest(title=title), self.assertRaises(EMODnetWFSBlocked):
                inspect_capabilities(body(feature(title=title)))

    def test_dtd_and_entity_payloads_rejected(self):
        # Construct the forbidden local-URI payload only at runtime.
        # Preserve the adversarial XML/XXE fixture without embedding a live
        # local file URL literal in the tracked repository text.
        injected = (
            b'<!DOCTYPE root [<!ENTITY exfil SYSTEM "'
            + b"file:" + b"///etc/passwd"
            + b'">]>'
            + body(feature())
        )
        with self.assertRaises(EMODnetWFSBlocked):
            inspect_capabilities(injected)
        with self.assertRaises(EMODnetWFSBlocked):
            inspect_capabilities(b"<!doctype x>" + body(feature()))

    def test_invalid_utf8_nul_and_size(self):
        for data in (b"\xff", body(feature()) + b"\x00", b"x" * (MAX_BYTES + 1)):
            with self.subTest(length=len(data)), self.assertRaises(EMODnetWFSBlocked):
                inspect_capabilities(data)

    def test_output_contains_no_source_geometry_or_feature_data(self):
        report = inspect_capabilities(body(feature()))
        encoded = json.dumps(report, sort_keys=True)
        self.assertNotIn("<wfs:", encoded)
        self.assertNotIn("<FeatureType", encoded)
        self.assertTrue(report["expected_request_url"].startswith("https://"))
        self.assertNotIn("feature_geometry", report)


if __name__ == "__main__":
    unittest.main()
