# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only synthetic contract and response validation for CBS StatLine."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.probe_nl_cbs_85728ned_v0 import (
    BASE, COMPONENTS, MAX_BYTES, OBJECTS, CBSProbeBlocked,
    decode_json, probe, validate_rows, verify_contract,
)


def synthetic_bodies() -> dict:
    return {
        "table_info": {"value": [{
            "ID": 0, "Identifier": "85728NED", "Source": "CBS.",
            "Title": "Nieuwbouwwoningen; inputprijsindex bouwkosten 2021=100",
            "Modified": "2026-10-30T02:00:00",
        }]},
        "components": {"value": [
            {"Key": key, "Title": title}
            for key, title in COMPONENTS.items()
        ]},
        "periods": {"value": [{"Key": "2018MM01", "Title": "2018 januari", "Status": "Definitief"}]},
        "first_observation": {"value": [{
            "ID": 0, "Componenten": "T001363", "Perioden": "2018MM01",
            "InputprijsindexBouwkosten_1": 90.1,
            "OntwikkelingTOVEenJaarEerder_2": None,
        }]},
    }


class Response:
    def __init__(self, url, body, *, status=200, content_type="application/json"):
        self.url, self.body, self.status = url, body, status
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, max_bytes):
        return self.body[:max_bytes]


def fake_opener(bodies, *, wrong_url=False, status=200, content_type="application/json"):
    calls = []

    def open_request(req, timeout):
        calls.append((req.full_url, timeout))
        name = next((name for name, url in OBJECTS if url == req.full_url), None)
        if name is None:
            raise AssertionError("unreviewed request")
        url = req.full_url + "/not-authorized" if wrong_url else req.full_url
        return Response(
            url, json.dumps(bodies[name], sort_keys=True).encode("utf-8"),
            status=status, content_type=content_type,
        )

    return open_request, calls


class CBSProbeTests(unittest.TestCase):
    def test_fixed_contract_and_four_exact_endpoints(self):
        c = verify_contract()
        self.assertEqual(c["source_ids"], ["nl.cbs.new-build-input-cost-index.85728ned"])
        self.assertEqual(c["status"], "probe_ready")
        self.assertEqual(c["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(c["rights_and_policy"]["commercial_automation_status"], "allowed")
        self.assertEqual(c["probe_contract"]["mode"], "provider_specific")
        self.assertEqual(c["operational_constraints"]["retry_policy"], "none")
        self.assertEqual(len(OBJECTS), 4)
        self.assertEqual(MAX_BYTES, 16384)
        self.assertTrue(all(url.startswith(BASE) for _, url in OBJECTS))
        self.assertEqual([url.split("?")[1] for _, url in OBJECTS],
                         ["$top=1", "$top=3", "$top=1", "$top=1"])

    def test_synthetic_four_original_receipts_and_one_index(self):
        data = synthetic_bodies()
        open_request, calls = fake_opener(data)
        result = probe(open_request=open_request)
        self.assertEqual(len(calls), 4)
        self.assertEqual([url for url, _ in calls], [url for _, url in OBJECTS])
        self.assertTrue(all(timeout == 30 for _, timeout in calls))
        self.assertEqual(result["first_price_index_2021_100"], 90.1)
        self.assertEqual(result["start_period"], "2018MM01")
        self.assertEqual(result["observed_data_rows"], 1)
        self.assertEqual(result["observed_metadata_rows"], 5)
        self.assertEqual(result["individual_insured_buildings"], 0)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["original_provider_bytes_persisted"])
        for name, url in OBJECTS:
            raw = json.dumps(data[name], sort_keys=True).encode("utf-8")
            receipt = result["original_requests"][name]
            self.assertEqual(receipt["url"], url)
            self.assertEqual(receipt["original_body_bytes"], len(raw))
            self.assertEqual(receipt["original_body_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertNotIn("value", receipt)

    def test_fail_closed_on_response_status_redirect_and_media(self):
        for kwargs in ({"status": 206}, {"wrong_url": True},
                       {"content_type": "text/html"}):
            with self.subTest(kwargs=kwargs):
                opener, _ = fake_opener(synthetic_bodies(), **kwargs)
                with self.assertRaises(CBSProbeBlocked):
                    probe(open_request=opener)

    def test_missing_component_or_wrong_period_blocks(self):
        for key in ("components", "periods"):
            data = synthetic_bodies()
            data[key]["value"][0]["Key"] = "WRONG"
            with self.subTest(key=key):
                self.assertRaises(CBSProbeBlocked, validate_rows, data)

    def test_wrong_first_value_or_code_blocks(self):
        for key, wrong in (
            ("InputprijsindexBouwkosten_1", 90.2),
            ("InputprijsindexBouwkosten_1", True),
            ("InputprijsindexBouwkosten_1", "90.1"),
            ("Perioden", "2018MM02"),
            ("Componenten", "A043942"),
            ("OntwikkelingTOVEenJaarEerder_2", 0),
        ):
            data = synthetic_bodies()
            data["first_observation"]["value"][0][key] = wrong
            with self.subTest(key=key, wrong=wrong):
                self.assertRaises(CBSProbeBlocked, validate_rows, data)

    def test_original_json_duplicate_key_nan_oversize_and_shape_block(self):
        payloads = (
            b'{"value":[],"value":[]}',
            b'{"value":[NaN]}',
            b'{"value":null}',
            b'{"value":[',
            b"0" * (MAX_BYTES + 1),
            b"",
        )
        for raw in payloads:
            with self.subTest(raw=raw[:50]):
                self.assertRaises(CBSProbeBlocked, decode_json, raw)

    def test_unreviewed_contract_automation_downgrade_blocks(self):
        c = deepcopy(verify_contract())
        c["rights_and_policy"]["commercial_automation_status"] = "unknown"
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "unsafe-cbs.json"
            target.write_text(json.dumps(c), encoding="utf-8")
            with self.assertRaises((CBSProbeBlocked, ValueError)):
                verify_contract(target)


if __name__ == "__main__":
    unittest.main()
