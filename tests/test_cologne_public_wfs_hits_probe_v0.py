# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline-only synthetic WFS 2.0 resultType=hits tests for Cologne services."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

MODULE = Path(__file__).resolve().parents[1] / "research_runners" / "cologne_public_wfs_hits_probe_v0.py"
spec = importlib.util.spec_from_file_location("cologne_public_wfs_hits_probe_v0", MODULE)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

HITS = (
    b'<?xml version="1.0"?><wfs:FeatureCollection '
    b'xmlns:wfs="http://www.opengis.net/wfs/2.0" '
    b'timeStamp="2026-11-14T19:57:30Z" numberMatched="374" numberReturned="0"/>'
)


class CologneWfsHitsTests(unittest.TestCase):
    def test_valid_response_is_not_feature_import(self):
        result = probe.parse_hits(HITS)
        self.assertEqual(result["number_matched_reported"], 374)
        self.assertEqual(result["number_returned"], 0)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertFalse(result["original_features_acquired"])
        self.assertFalse(result["total_inventory_established"])
        self.assertFalse(result["verified_live"])
        self.assertFalse(result["model_admitted"])

    def test_invalid_root_rejected(self):
        with self.assertRaises(probe.WfsProbeError):
            probe.parse_hits(b'<FeatureCollection numberMatched="1" numberReturned="0"/>')

    def test_feature_bytes_rejected(self):
        content = HITS.replace(b'numberReturned="0"', b'numberReturned="1"')
        with self.assertRaises(probe.WfsProbeError):
            probe.parse_hits(content)

    def test_embedded_member_rejected(self):
        content = HITS.replace(b'/>', b'><wfs:member/></wfs:FeatureCollection>')
        with self.assertRaises(probe.WfsProbeError):
            probe.parse_hits(content)

    def test_missing_or_unbounded_counts_rejected(self):
        for content in (HITS.replace(b'numberMatched="374"', b'numberMatched="unknown"'),
                        HITS.replace(b'numberMatched="374"', b'numberMatched="-1"'),
                        HITS.replace(b'numberMatched="374" ', b'')):
            with self.subTest(content=content):
                with self.assertRaises(probe.WfsProbeError):
                    probe.parse_hits(content)

    def test_bad_timestamp_rejected(self):
        with self.assertRaises(probe.WfsProbeError):
            probe.parse_hits(HITS.replace(b'2026-11-14T19:57:30Z', b'no-time'))

    def test_doctype_rejected(self):
        with self.assertRaises(probe.WfsProbeError):
            probe.parse_hits(b'<!DOCTYPE x>' + HITS)

    def test_invalid_xml_and_large_payload_rejected(self):
        for raw in (b'', b'<bad>', b'x' * (probe.MAX_RESPONSE_BYTES + 1)):
            with self.subTest(length=len(raw)):
                with self.assertRaises(probe.WfsProbeError):
                    probe.parse_hits(raw)

    def test_only_known_sources_have_fixed_public_urls(self):
        self.assertEqual(set(probe.SOURCES), {"tree", "kgg"})
        for source in probe.SOURCES.values():
            self.assertTrue(source["url"].startswith("https://geoportal.stadt-koeln.de/"))
            self.assertIn("RESULTTYPE=hits&COUNT=1", source["url"])
        with self.assertRaises(probe.WfsProbeError):
            probe.probe_live("not-a-source")

    def test_mock_only_live_wrapper_receipt(self):
        class Headers:
            def get_content_type(self):
                return "application/xml"

            def get(self, _name):
                return None

        class Response:
            status = 200
            headers = Headers()

            def __init__(self, url):
                self.url = url

            def geturl(self):
                return self.url

            def read(self, n):
                assert n == probe.MAX_RESPONSE_BYTES + 1
                return HITS

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        class Opener:
            def open(self, req, timeout):
                assert timeout == 20
                return Response(req.full_url)

        with mock.patch.object(probe, "build_opener", return_value=Opener()):
            result = probe.probe_live("kgg")
        self.assertTrue(result["verified_live"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertEqual(result["source"], "kgg")


if __name__ == "__main__":
    unittest.main()
