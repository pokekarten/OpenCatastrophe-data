# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only Berlin detailed Atom child/HEAD and no-CAT-admission QA."""
import hashlib
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from research_runners import berlin_srgk_detailed_atom_child_zip_heads_v0 as m


def root():
    return b'''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
      <link href="https://gdi.berlin.de/data/ua_srgk/atom/" rel="self" type="application/atom+xml"/>
      <entry><link href="https://gdi.berlin.de/data/ua_srgk/atom/0.atom"
      rel="alternate" type="application/atom+xml"/></entry></feed>'''


def child(*, rights=True, caveat=True, urls=None):
    if urls is None:
        urls = m.ZIP_URLS
    message = ("Die verschiedenen Ereignisse werden in drei ZIP-Dateien angeboten. "
               "Der Wasserstand für ein extremes Ereignis steht nicht für alle Modellgebiete zur Verfügung."
               if caveat else "Alle Ereignisse verfügbar.")
    rights_text = ("Für die Nutzung gilt Datenlizenz Deutschland - Zero - Version 2.0. "
                   "Gebiete Moabit, Flughafensee: CC-BY-4.0-Namensnennung."
                   if rights else "Nutzungsrecht nicht dokumentiert.")
    sections = "".join(
        f'<link href="{url}" rel="section" type="image/tiff"/>'
        for url in urls)
    return f'''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
        <id>{m.CHILD_URL}</id><rights>{rights_text}</rights>
        <entry><id>{m.CHILD_URL}</id><rights>{rights_text}</rights>
          <content>{message}</content>{sections}</entry>
        </feed>'''.encode()


class FakeResponse:
    status = 200

    def __init__(self, req, data=b"", status=200, content_type=None, size=None):
        self.req = req
        self.data = data
        self.status = status
        self.headers = {
            "Content-Type": content_type or (
                "application/atom+xml" if req.get_method() == "GET" else "application/zip"),
            "Content-Length": str(size) if size is not None else str(len(data)),
        }
        if req.get_method() == "HEAD" and size is None:
            self.headers.pop("Content-Length", None)

    def geturl(self):
        return self.req.full_url

    def read(self, n):
        return self.data[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class AtomChildProofTests(unittest.TestCase):
    def test_source_exact_three_scenarios_and_no_raster_admission(self):
        d = m.inspect_child(child())
        self.assertEqual(d["scenario_count"], 3)
        self.assertEqual(set(x["exact_zip_url"] for x in d["official_scenarios"]),
                         set(m.ZIP_URLS))
        self.assertTrue(d["extreme_scenario_not_for_all_model_areas"])
        self.assertTrue(d["catalogue_mixed_rights_research_only"])
        self.assertFalse(d["specific_zip_redistribution_approved"])
        self.assertFalse(d["insurance_cat_model_input_admitted"])
        self.assertFalse(d["source_raster_crs_depth_units_nodata_verified"])

    def test_root_exact_child_link_and_sha_lock(self):
        data = root()
        with patch.object(m, "ROOT_SHA256", hashlib.sha256(data).hexdigest()):
            self.assertTrue(m.inspect_root(data)["root_child_identity_verified"])
        with self.assertRaisesRegex(m.AtomScenarioBlocked, "SHA-256"):
            m.inspect_root(data)

    def test_rights_and_extreme_caveat_required(self):
        with self.assertRaisesRegex(m.AtomScenarioBlocked, "rights"):
            m.inspect_child(child(rights=False))
        with self.assertRaisesRegex(m.AtomScenarioBlocked, "scenario availability"):
            m.inspect_child(child(caveat=False))

    def test_missing_duplicate_or_redirected_scenario_identity_rejected(self):
        for paths in (
            m.ZIP_URLS[:2],
            m.ZIP_URLS[:2] + (m.ZIP_URLS[0],),
            m.ZIP_URLS[:2] + ("https://elsewhere.invalid/third.zip",),
        ):
            with self.subTest(paths=paths), self.assertRaises(m.AtomScenarioBlocked):
                m.inspect_child(child(urls=paths))

    def test_xml_entity_oversize_or_bad_feed_rejected(self):
        for data in (
            b"",
            b"not-xml",
            b'<!DOCTYPE feed [<!ENTITY external SYSTEM "file:///etc/passwd">]><feed/>',
            b"<html/>",
            b"x" * (m.CHILD_MAX_BYTES + 1),
        ):
            with self.subTest(data=data[:10]), self.assertRaises(m.AtomScenarioBlocked):
                m.inspect_child(data)

    def test_bad_head_size_retains_uncertainty_and_never_gets_zip(self):
        calls = []
        def fake(req, timeout):
            calls.append(req.get_method())
            return FakeResponse(req, b"", size=0)
        r = m._head_zip(m.ZIP_URLS[0], fake)
        self.assertEqual(calls, ["HEAD"])
        self.assertEqual(r["head_status"], "UNVERIFIED_CONTENT_LENGTH")
        self.assertIsNone(r["length_bytes"])
        with self.assertRaisesRegex(m.AtomScenarioBlocked, "unapproved"):
            m._head_zip("https://other.invalid/a.zip", fake)

    def test_probe_two_feeds_three_heads_only(self):
        rr, cr = root(), child()
        calls = []
        def fake(req, timeout):
            calls.append((req.full_url, req.get_method()))
            if req.full_url == m.ROOT_URL:
                return FakeResponse(req, rr)
            if req.full_url == m.CHILD_URL:
                return FakeResponse(req, cr)
            return FakeResponse(req, b"", size=12345)
        with patch.object(m, "ROOT_SHA256", hashlib.sha256(rr).hexdigest()):
            out = m.probe(opener=fake,
                          clock=lambda: datetime(2026, 11, 2, tzinfo=timezone.utc))
        self.assertEqual(calls, [(m.ROOT_URL, "GET"), (m.CHILD_URL, "GET")] +
                         [(url, "HEAD") for url in m.ZIP_URLS])
        self.assertEqual(out["original_source_feed_get_requests"], 2)
        self.assertEqual(out["official_source_zip_head_requests"], 3)
        self.assertEqual(out["source_zip_get_requests"], 0)
        self.assertTrue(out["original_atom_xml_or_zip_bytes_persisted"] is False)
        self.assertEqual([x["length_bytes"] for x in out["official_scenarios"]],
                         [12345] * 3)
        self.assertFalse(out["insurance_cat_model_input_admitted"])
        self.assertNotIn("Die verschiedenen Ereignisse", json.dumps(out))

    def test_silent_root_drift_blocks_before_child_or_heads(self):
        calls = []
        def fake(req, timeout):
            calls.append(req.full_url)
            return FakeResponse(req, root())
        with self.assertRaisesRegex(m.AtomScenarioBlocked, "SHA-256"):
            m.probe(opener=fake)
        self.assertEqual(calls, [m.ROOT_URL])


if __name__ == "__main__":
    unittest.main()
