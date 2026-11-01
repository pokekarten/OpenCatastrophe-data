# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No network, no ZIPs: hostile synthetic official Atom child regression."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import unittest
from xml.etree import ElementTree as ET

from research_runners.berlin_srhk_atom_child_preflight_v0 import (
    SOURCE_URL, ROOT_URL, FILES, MAX_BYTES, TIMEOUT, ChildFeedError, inspect, probe,
)

N = "{http://www.w3.org/2005/Atom}"


def synthetic():
    root = ET.Element(N + "feed")
    ET.SubElement(root, N + "title").text = "Starkregenhinweiskarte"
    ET.SubElement(root, N + "link", href=SOURCE_URL, rel="self",
                  type="application/atom+xml")
    ET.SubElement(root, N + "rights").text = "Datenlizenz Deutschland Namensnennung"
    entry = ET.SubElement(root, N + "entry")
    ET.SubElement(entry, N + "title").text = "Raster EPSG:25833, ZIP"
    ET.SubElement(entry, N + "id").text = SOURCE_URL
    ET.SubElement(entry, N + "rights").text = "BKG Datenlizenz Deutschland Namensnennung"
    ET.SubElement(entry, N + "category",
                  term="http://www.opengis.net/def/crs/EPSG/0/25833",
                  label="EPSG/0/25833")
    for filename in FILES:
        ET.SubElement(entry, N + "link", href=ROOT_URL + filename,
                      rel="section", type="image/tiff", title="reviewed fixed source")
    return ET.tostring(root, encoding="utf-8")


class Fake(io.BytesIO):
    status = 200
    def __init__(self, body, url=SOURCE_URL, media="application/atom+xml"):
        super().__init__(body)
        self.url = url
        self.headers = {"Content-Type": media}
    def geturl(self):
        return self.url


class ChildMetadataTests(unittest.TestCase):
    def test_five_exact_original_zip_metadata_roles_not_source_bytes(self):
        out = inspect(synthetic())
        self.assertEqual(out["atom_entry_reports_raster_zip_links"], 5)
        self.assertEqual(out["water_depth_zip_count"], 2)
        self.assertEqual(out["flow_speed_zip_count"], 2)
        self.assertEqual(out["separate_vulnerability_zip_count"], 1)
        self.assertTrue(out["atom_pdf_crs_labels_conflict"])
        self.assertEqual(out["official_2025_pdf_raster_crs_label"], "EPSG:25832")
        self.assertEqual(out["original_atom_child_crs_label"], "EPSG:25833")
        self.assertFalse(out["provider_zip_bytes_requested"])
        self.assertFalse(out["true_geotiff_crs_and_units_verified"])
        self.assertFalse(out["building_hazard_overlap_admitted"])
        self.assertEqual({f["filename"] for f in out["source_zip_filenames_and_roles"]}, set(FILES))

    def test_duplicate_unknown_host_or_nonzip_href_rejected(self):
        original = synthetic()
        for old, new in (
            (b"wasserstand_extrem2022.zip", b"unknown-evil-file.zip"),
            (b"wasserstand_extrem2022.zip", b"wasserstand_aussergewoehnliches_ereignis2022.zip"),
            (b"https://gdi.berlin.de/data/ua_srhk/atom/wasserstand_extrem2022.zip",
             b"https://evil.invalid/asset.zip"),
            (b"wasserstand_extrem2022.zip", b"wasserstand_extrem2022.tif"),
            (b'rel="section"', b'rel="enclosure"'),
            (b'type="image/tiff"', b'type="application/zip"'),
        ):
            with self.subTest(old=old[:38], new=new[:38]):
                with self.assertRaises(ChildFeedError):
                    inspect(original.replace(old, new, 1))

    def test_parent_namespace_metadata_rights_and_crs_invariants(self):
        original = synthetic()
        for old, new in (
            (b"/atom/0.atom", b"/atom/not-the-parent.atom"),
            (b"Namensnennung", b"Unlicensed"),
            (b"BKG", b"Unknown"),
            (b"EPSG:25833", b"EPSG:25832"),
            (b"25833", b"12345"),
        ):
            with self.subTest(old=old, new=new), self.assertRaises(ChildFeedError):
                inspect(original.replace(old, new, 1))

    def test_bounded_xml_and_no_entities(self):
        for bad in (
            b"", b"X" * (MAX_BYTES + 1),
            b"<!DOCTYPE feed [<!ENTITY item 'unexpected'>]><feed/>",
            b"<html><body>not XML</body></html>",
            b'<?xml version="1.0"?><feed xmlns="wrong"/>',
        ):
            with self.subTest(bad=bad[:30]), self.assertRaises(ChildFeedError):
                inspect(bad)

    def test_exact_https_original_metadata_only(self):
        calls = []
        def opener(req, timeout):
            calls.append((req.full_url, req.get_method(), timeout))
            return Fake(synthetic())
        obj = probe(opener=opener,
                    clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(calls, [(SOURCE_URL, "GET", TIMEOUT)])
        self.assertEqual(len(obj["original_xml_sha256"]), 64)
        self.assertEqual(obj["original_xml_response_bytes"], len(synthetic()))
        self.assertTrue(obj["source_xml_not_persisted"])
        self.assertTrue(obj["no_sourced_file_download"])
        self.assertTrue(obj["no_new_rights_or_model_admission"])

    def test_redirect_html_and_naive_clock_fail(self):
        for obj in (Fake(synthetic(), url="https://else.invalid/link"),
                    Fake(synthetic(), media="text/html")):
            with self.assertRaises(ChildFeedError):
                probe(opener=lambda req, timeout: obj)
        class Bad(Fake):
            status = 206
        with self.assertRaises(ChildFeedError):
            probe(opener=lambda req, timeout: Bad(synthetic()))
        with self.assertRaisesRegex(ChildFeedError, "clock"):
            probe(opener=lambda req, timeout: Fake(synthetic()),
                  clock=lambda: datetime(2026, 11, 1))


if __name__ == "__main__":
    unittest.main()
