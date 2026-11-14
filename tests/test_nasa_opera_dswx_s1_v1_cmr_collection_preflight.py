# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independently invented CMR-shaped JSON only; no original NASA bytes."""
from __future__ import annotations

import json
import unittest

from research_runners.nasa_opera_dswx_s1_v1_cmr_collection_preflight import (
    CmrCollectionBlocked, FIXED_REQUEST, MAX_RESPONSE_BYTES,
    validate_collection_response,
)


def fixture():
    return {
        "hits": 1,
        "items": [{
            "meta": {"concept-id": "C2949811996-POCLOUD", "concept-type": "collection",
                     "revision-id": 2, "deleted": False},
            "umm": {"ShortName": "OPERA_L3_DSWX-S1_V1", "Version": "1.0"},
        }],
    }


def run(doc=None, **kwargs):
    params = dict(request_url=FIXED_REQUEST, status=200,
                  content_type="application/vnd.nasa.cmr.umm_results+json;version=1.18.6",
                  body=json.dumps(fixture() if doc is None else doc).encode("utf-8"))
    params.update(kwargs)
    return validate_collection_response(**params)


class CmrCollectionPreflightTests(unittest.TestCase):
    def test_exact_collection_synthetic_identity_and_hash(self):
        result = run()
        self.assertEqual(result["product_version"], "1.0")
        self.assertEqual(result["cmr_revision_id"], 2)
        self.assertEqual(len(result["original_response_sha256"]), 64)
        self.assertEqual(result["original_response_bytes"], len(json.dumps(fixture()).encode()))
        for key in ("source_asset_or_granule_acquired", "dataset_rights_or_api_terms_approved",
                    "commercial_use_or_redistribution_approved", "scientific_validity_or_cat_model_admitted",
                    "neon_storage_verified"):
            self.assertIs(result[key], False)

    def test_wrong_source_or_version_is_blocked(self):
        for k, v in (("ShortName", "OPERA_L3_DSWX-HLS_V1"),
                     ("Version", "0.2.1"), ("Version", "1.1")):
            d = fixture()
            d["items"][0]["umm"][k] = v
            with self.subTest(key=k, value=v), self.assertRaises(CmrCollectionBlocked):
                run(d)

    def test_wrong_revision_deleted_and_wrong_concept(self):
        for key, val in (("concept-id", "C123456-POCLOUD"),
                         ("concept-type", "granule"), ("deleted", True),
                         ("revision-id", 0), ("revision-id", True)):
            d = fixture()
            d["items"][0]["meta"][key] = val
            with self.subTest(key=key), self.assertRaises(CmrCollectionBlocked):
                run(d)

    def test_huge_or_empty_body_and_html_200_block(self):
        for body in (b"", b"x" * (MAX_RESPONSE_BYTES + 1),
                     b"<html>ok</html>", b"\xff"):
            with self.subTest(size=len(body)), self.assertRaises(CmrCollectionBlocked):
                run(body=body)
        with self.assertRaises(CmrCollectionBlocked):
            run(content_type="text/html")

    def test_no_arbitrary_url_or_redirect_or_http_error(self):
        for kw in ({"request_url": FIXED_REQUEST + "&page_size=9999"},
                   {"request_url": "http://127.0.0.1/"},
                   {"redirect_count": 1}, {"status": 429}, {"status": True}):
            with self.subTest(kw=kw), self.assertRaises(CmrCollectionBlocked):
                run(**kw)

    def test_search_shape_and_duplicate_json_members_block(self):
        for d in ({"hits": 0, "items": []}, {"hits": 2, "items": [fixture()["items"][0]]},
                  {"hits": 1, "items": []}, {"hits": True, "items": fixture()["items"]}):
            with self.subTest(doc=d), self.assertRaises(CmrCollectionBlocked):
                run(d)
        with self.assertRaises(CmrCollectionBlocked):
            run(body=b'{"hits":1,"hits":1,"items":[]}')
        with self.assertRaises(CmrCollectionBlocked):
            run(body=b'{"hits":NaN,"items":[]}')

    def test_umm_errors_block_nested_and_top_level(self):
        for location in ("top", "nested"):
            d = fixture()
            if location == "top":
                d["items"][0]["umm"]["_errors"] = {"Version": "bad"}
            else:
                d["items"][0]["umm"]["Platforms"] = [{"_errors": {"ShortName": "bad"}}]
            with self.subTest(location=location), self.assertRaises(CmrCollectionBlocked):
                run(d)


if __name__ == "__main__":
    unittest.main()
