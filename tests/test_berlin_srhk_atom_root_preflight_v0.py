# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic Atom XML and injected HTTPS response objects."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import unittest

from research_runners.berlin_srhk_atom_root_preflight_v0 import (
    URL, MAX_BYTES, TIMEOUT, AtomSourceError, inspect, probe,
)


def feed(*, entries=2):
    e = "".join(
        '<entry><id>urn:example:metadata:</id><title>not a real file</title>'
        '<link rel="alternate" type="application/zip" href="https://example.org/asset.zip"/>'
        '</entry>' for _ in range(entries)
    )
    return (
        '<?xml version="1.0"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom"><id>urn:example:root</id>'
        f'<link rel="self" href="{URL}"/>{e}</feed>'
    ).encode()


class Response(io.BytesIO):
    status = 200
    def __init__(self, data, url=URL, media="application/atom+xml"):
        super().__init__(data)
        self.url = url
        self.headers = {"Content-Type": media}
    def geturl(self):
        return self.url


class AtomPreflightTests(unittest.TestCase):
    def test_exact_synthetic_atom_root_and_no_asset_requests(self):
        obj = inspect(feed())
        self.assertTrue(obj["root_is_atom_1_0"])
        self.assertEqual(obj["root_entries"], 2)
        self.assertEqual(obj["root_links"], 3)
        self.assertEqual(obj["direct_zip_href_count"], 2)
        self.assertFalse(obj["zip_or_geotiff_bytes_retrieved"])
        self.assertFalse(obj["depth_pixel_units_or_values_verified"])
        self.assertFalse(obj["approved_as_real_hazard_model_input"])

    def test_wrong_feed_xml_and_entity_injection_rejected(self):
        for bad in (b"", b" "*(MAX_BYTES+1), b"<html/>",
                    b'<feed xmlns="urn:wrong"/>',
                    b'<!DOCTYPE feed [<!ENTITY x "secret">]><feed>&x;</feed>'):
            with self.subTest(data=bad[:40]), self.assertRaises(AtomSourceError):
                inspect(bad)

    def test_invalid_links_and_excessive_entries_rejected(self):
        with self.assertRaises(AtomSourceError):
            inspect(feed(entries=301))
        bad = feed().replace(b'href="https://example.org/asset.zip"', b'href=""')
        with self.assertRaisesRegex(AtomSourceError, "invalid Atom link"):
            inspect(bad)

    def test_exact_request_and_read_only_receipt(self):
        def opener(req, timeout):
            self.assertEqual(req.full_url, URL)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(timeout, TIMEOUT)
            return Response(feed())
        r = probe(opener=opener, clock=lambda: datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(len(r["original_atom_xml_sha256"]), 64)
        self.assertEqual(r["original_atom_xml_size"], len(feed()))
        self.assertFalse(r["raw_original_xml_persisted"])
        self.assertTrue(r["original_licence_scope_not_changed"])
        self.assertNotIn("file_payload", r)

    def test_wrong_url_status_and_content_type_fail(self):
        for resp in (Response(feed(), url="https://evil.invalid/feed"),
                     Response(feed(), media="text/html"),
                     Response(feed(), media="application/json")):
            with self.assertRaises(AtomSourceError):
                probe(opener=lambda req, timeout: resp)
        class Fail(Response):
            status = 404
        with self.assertRaises(AtomSourceError):
            probe(opener=lambda req, timeout: Fail(feed()))

    def test_naive_time_rejected(self):
        with self.assertRaisesRegex(AtomSourceError, "UTC offset"):
            probe(opener=lambda req,timeout:Response(feed()),
                  clock=lambda:datetime(2026,11,1))


if __name__ == "__main__":
    unittest.main()
