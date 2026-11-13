# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic proof of frozen CBS 85772NED original-source boundaries."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import unittest

from scripts.probe_nl_cbs_85772ned_v0 import (
    BASE, CBSOutputBlocked, MAX_BYTES, OBJECTS, TIMEOUT,
    decode_original, probe, validate_rows, verify_contract,
)


def fixture():
    return {
        "table_info": {"value": [{
            "ID": 0, "Identifier": "85772NED", "Source": "CBS.",
            "Modified": "2026-09-30T02:00:00",
            "Title": "Nieuwbouwwoningen; outputprijsindex bouwkosten 2021=100",
            "Frequency": "Perkwartaal",
        }]},
        "first_index": {"value": [{
            "ID": 0, "Perioden": "2018KW01",
            "Prijsindex_1": 87.7, "Prijsindex_3": 87.7,
            "OntwikkelingTOVEenJaarEerder_2": None,
            "OntwikkelingTOVEenJaarEerder_4": None,
        }]},
        "first_period": {"value": [{
            "Key": "2018KW01", "Title": "2018 1e kwartaal",
            "Status": "Definitief",
        }]},
        "properties": {"value": [
            {"ID": 0, "Key": "Perioden", "Type": "TimeDimension"},
            {"ID": 1, "Key": "", "Type": "TopicGroup",
             "Title": "Outputprijsindex bouwkosten incl. btw"},
            {"ID": 2, "Key": "Prijsindex_1", "Type": "Topic",
             "Unit": "2021=100", "ParentID": 1},
            {"ID": 3, "Key": "OntwikkelingTOVEenJaarEerder_2", "Type": "Topic",
             "ParentID": 1},
            {"ID": 4, "Key": "", "Type": "TopicGroup",
             "Title": "Outputprijsindex bouwkosten excl. btw"},
            {"ID": 5, "Key": "Prijsindex_3", "Type": "Topic",
             "Unit": "2021=100", "ParentID": 4},
        ]},
        "q2_2026_index": {"value": [{
            "ID": 41, "Perioden": "2026KW02",
            "Prijsindex_1": 133.4, "Prijsindex_3": 133.4,
            "OntwikkelingTOVEenJaarEerder_2": 4.4,
            "OntwikkelingTOVEenJaarEerder_4": 4.4,
        }]},
        "q2_2026_period": {"value": [{
            "Key": "2026KW02", "Title": "2026 2e kwartaal",
            "Status": "Voorlopig",
        }]},
    }


class Response:
    def __init__(self, url, body, *, status=200, mime="application/json",
                 encoded="identity"):
        self.url, self.body, self.status = url, body, status
        self.headers = {"Content-Type": mime, "Content-Encoding": encoded}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, length):
        return self.body[:length]


def fake_opener(payloads, *, status=200, wrong_url=False,
                mime="application/json", encoded="identity"):
    calls = []

    def open_request(req, timeout):
        calls.append((req.full_url, timeout))
        matching = [name for name, url in OBJECTS if url == req.full_url]
        if len(matching) != 1:
            raise AssertionError("unreviewed direct provider path")
        actual = req.full_url + "/unreviewed" if wrong_url else req.full_url
        body = json.dumps(payloads[matching[0]], sort_keys=True).encode("utf-8")
        return Response(actual, body, status=status, mime=mime, encoded=encoded)

    return open_request, calls


class CBSOutputIndexTests(unittest.TestCase):
    def test_exact_contract_frozen_six_urls_and_cc_by_rights(self):
        c = verify_contract()
        self.assertEqual(c["status"], "probe_ready")
        self.assertEqual(c["access_id"], "nl.cbs.new-build-output-cost-index.85772ned")
        self.assertEqual(c["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(c["rights_and_policy"]["api_terms_status"], "separate_reviewed")
        self.assertEqual(c["rights_and_policy"]["commercial_automation_status"], "allowed")
        self.assertEqual(c["probe_contract"]["mode"], "provider_specific")
        self.assertEqual(len(OBJECTS), 6)
        self.assertEqual(TIMEOUT, 30)
        self.assertEqual(MAX_BYTES, 16384)
        self.assertTrue(all(url.startswith(BASE) for _, url in OBJECTS))
        self.assertTrue(all("$top=" in url for _, url in OBJECTS))
        self.assertEqual([u.split("?")[1].split("&")[0] for _, u in OBJECTS][-2:],
                         ["$filter=Perioden%20eq%20%272026KW02%27",
                          "$filter=Key%20eq%20%272026KW02%27"])

    def test_six_original_receipts_without_original_payload_or_admission(self):
        payloads = fixture()
        opener, calls = fake_opener(payloads)
        out = probe(open_request=opener)
        self.assertEqual(len(calls), 6)
        self.assertEqual([u for u, _ in calls], [url for _, url in OBJECTS])
        self.assertTrue(all(t == 30 for _, t in calls))
        self.assertEqual(out["first_vat_included_and_excluded_index"], 87.7)
        self.assertEqual(out["recent_vat_included_and_excluded_index"], 133.4)
        self.assertEqual(out["recent_vat_included_and_excluded_yoy_percent"], 4.4)
        self.assertFalse(out["recent_quarter_final"])
        self.assertTrue(out["first_quarter_final"])
        self.assertFalse(out["model_input_approved"])
        self.assertFalse(out["provider_bytes_persisted"])
        self.assertFalse(out["insured_replacement_eur_computed"])
        self.assertEqual(len(out["original_response_receipts"]), 6)
        for name, url in OBJECTS:
            original = json.dumps(payloads[name], sort_keys=True).encode("utf-8")
            receipt = out["original_response_receipts"][name]
            self.assertEqual(receipt["url"], url)
            self.assertEqual(receipt["original_response_bytes"], len(original))
            self.assertEqual(
                receipt["original_response_sha256"],
                hashlib.sha256(original).hexdigest(),
            )
            self.assertNotIn("value", receipt)

    def test_provisional_quarter_cannot_silently_become_definitive(self):
        d = fixture()
        d["q2_2026_period"]["value"][0]["Status"] = "Definitief"
        self.assertRaises(CBSOutputBlocked, validate_rows, d)

    def test_wrong_first_quarter_blocks_even_when_year_over_year_is_null(self):
        d = fixture()
        d["first_index"]["value"][0]["Prijsindex_1"] = 88.0
        self.assertRaises(CBSOutputBlocked, validate_rows, d)

    def test_2025_correction_revision_or_topic_mapping_not_ignored(self):
        for key in ("table_info", "properties"):
            d = fixture()
            if key == "table_info":
                d[key]["value"][0]["Modified"] = "2025-06-30T02:00:00"
            else:
                d[key]["value"][2]["Unit"] = "EUR"
            with self.subTest(key=key):
                self.assertRaises(CBSOutputBlocked, validate_rows, d)

    def test_vat_and_year_over_year_malformed_values_rejected(self):
        for field, wrong in (
            ("Prijsindex_3", 130.0),
            ("Prijsindex_3", True),
            ("OntwikkelingTOVEenJaarEerder_2", None),
            ("OntwikkelingTOVEenJaarEerder_4", "4.4"),
            ("Perioden", "2026KW01"),
        ):
            d = fixture()
            d["q2_2026_index"]["value"][0][field] = wrong
            with self.subTest(field=field):
                self.assertRaises(CBSOutputBlocked, validate_rows, d)

    def test_bad_http_status_redirect_encoding_or_media_fails_closed(self):
        for opts in (
            {"status": 206}, {"wrong_url": True},
            {"mime": "text/plain"}, {"encoded": "gzip"},
        ):
            opener, _ = fake_opener(fixture(), **opts)
            with self.subTest(opts=opts), self.assertRaises(CBSOutputBlocked):
                probe(open_request=opener)

    def test_invalid_json_duplicates_nan_overflow_and_size(self):
        for raw in (
            b'{"value":[],"value":[]}',
            b'{"value":[NaN]}',
            b'{"value":[1e9999]}',
            b'{"value":false}',
            b'{"value":[',
            b"", b"x" * (MAX_BYTES + 1),
        ):
            with self.subTest(raw=raw[:30]):
                self.assertRaises(CBSOutputBlocked, decode_original, raw)

    def test_no_whole_source_or_input_index_substitution(self):
        c = verify_contract()
        self.assertNotIn("85728NED", [u for _, u in OBJECTS])
        self.assertNotIn("ODataFeed", [u for _, u in OBJECTS])
        self.assertEqual(c["operational_constraints"]["retry_policy"], "none")
        self.assertEqual(c["authentication"]["mode"], "none")
        self.assertEqual(c["request_contract"]["allowed_operations"],
                         ["six_fixed_original_odata_rows"])


if __name__ == "__main__":
    unittest.main()
