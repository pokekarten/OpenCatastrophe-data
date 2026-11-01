# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic XML/HTTP only: height service is not a source of model admissions."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import unittest

from research_runners.berlin_umweltatlas_gebaeudehoehen_wfs_metadata_v0 import (
    URL, CATALOGUE, MAX_BYTES, SOURCE_ID, TIMEOUT,
    HeightWfsError, inspect, probe,
)


def capabilities(name="ua_gebaeudehoehen:gebaeudehoehen_2022", version="2.0.0"):
    return (
        f'<?xml version="1.0" encoding="utf-8"?>'
        f'<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0" version="{version}">'
        f'<wfs:FeatureTypeList><wfs:FeatureType><wfs:Name>{name}</wfs:Name>'
        f'<wfs:DefaultCRS>urn:ogc:def:crs:EPSG::25833</wfs:DefaultCRS>'
        f'</wfs:FeatureType></wfs:FeatureTypeList></wfs:WFS_Capabilities>'
    ).encode()


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, url=URL, media="application/xml; charset=utf-8"):
        super().__init__(data)
        self.url = url
        self.headers = {"Content-Type": media}

    def geturl(self):
        return self.url


class BerlinHeightWfsMetadataTests(unittest.TestCase):
    def test_metadata_only_height_service_and_correct_crs(self):
        obj = inspect(capabilities())
        self.assertEqual(obj["height_feature_type_count"], 1)
        self.assertEqual(obj["height_feature_types"][0]["advertised_crs"],
                         ["urn:ogc:def:crs:EPSG::25833"])
        self.assertFalse(obj["building_heights_retrieved"])
        self.assertFalse(obj["measured_heights_proven"])
        self.assertFalse(obj["model_input_admitted"])

    def test_current_alkis_or_unrelated_wfs_not_misclassified(self):
        for name in ("alkis_gebaeude:gebaeude", "other:roads", "roads:hoehe"):
            with self.subTest(layer=name), self.assertRaises(HeightWfsError):
                inspect(capabilities(name=name))

    def test_wrong_protocol_xxe_empty_and_oversized_blocked(self):
        for raw in (
            capabilities(version="9.9.9"), capabilities(version="1.1.0"),
            b'<!DOCTYPE x [<!ENTITY e "X">]><WFS_Capabilities>&e;</WFS_Capabilities>',
            b'<ExceptionReport/>', b"", b" " * (MAX_BYTES + 1),
        ):
            with self.subTest(raw=raw[:35]), self.assertRaises(HeightWfsError):
                inspect(raw)

    def test_duplicate_height_layer_rejected(self):
        original = capabilities()
        duplicate = original.replace(
            b"</wfs:FeatureTypeList>",
            b'<wfs:FeatureType><wfs:Name>ua_gebaeudehoehen:gebaeudehoehen_2022'
            b'</wfs:Name></wfs:FeatureType></wfs:FeatureTypeList>',
        )
        with self.assertRaises(HeightWfsError):
            inspect(duplicate)

    def test_exact_url_and_no_provider_attributes_or_geometry(self):
        def fake(req, timeout):
            self.assertEqual(req.full_url, URL)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(timeout, TIMEOUT)
            return Response(capabilities())
        result = probe(opener=fake, clock=lambda:datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(result["candidate_id"], SOURCE_ID)
        self.assertEqual(result["catalogue_url"], CATALOGUE)
        self.assertEqual(result["response_bytes"], len(capabilities()))
        self.assertEqual(len(result["response_sha256"]), 64)
        self.assertTrue(result["height_may_be_imputed_as_three_metres"])
        self.assertFalse(result["source_independent_from_current_alkis"])
        self.assertTrue(result["no_individual_buildings_or_roof_attributes_requested"])
        self.assertFalse(result["new_model_permission_granted"])
        self.assertFalse(result["source_raw_xml_persisted"])
        self.assertNotIn("individual_height_m", result)
        self.assertNotIn("building_address", result)

    def test_changed_request_url_media_type_and_http_status_blocked(self):
        for resp in (
            Response(capabilities(), url="https://example.com/fake"),
            Response(capabilities(), media="text/html"),
            Response(capabilities(), media="application/json"),
        ):
            with self.subTest(url=resp.url,media=resp.headers["Content-Type"]):
                with self.assertRaises(HeightWfsError):
                    probe(opener=lambda _req,_timeout:resp)

    def test_naive_clock_rejected(self):
        with self.assertRaisesRegex(HeightWfsError, "timezone-aware"):
            probe(
                opener=lambda _req,_timeout:Response(capabilities()),
                clock=lambda:datetime(2026,11,1),
            )


if __name__ == "__main__":
    unittest.main()
