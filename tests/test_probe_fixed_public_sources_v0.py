# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only security/contract tests. No network calls."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit

from scripts.probe_fixed_public_sources_v0 import (
    NoRedirect, PROBES, ProbeBlocked, probe, reviewed_probe, verify_response,
)


class Reply:
    status = 200

    def __init__(self, body, content_type="application/json", declared=None):
        self.body = body
        self.headers = {"Content-Type": content_type}
        if declared is not None:
            self.headers["Content-Length"] = declared

    def read(self, limit):
        return self.body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class Client:
    def __init__(self, reply):
        self.reply = reply
        self.requests = []

    def open(self, request, *, timeout):
        self.requests.append((request.full_url, request.get_method(), timeout))
        return self.reply


def contract(source):
    url, operation = PROBES[source]
    uri = urlsplit(url)
    return {
        "access_id": source,
        "status": "probe_ready",
        "service_root": uri.scheme + "://" + uri.netloc,
        "authentication": {"mode": "none"},
        "probe_contract": {"mode": "provider_specific",
                           "operation": operation, "requires_credentials": False},
        "request_contract": {"allowed_operations": [operation],
                             "path_templates": [uri.path]},
        "rights_and_policy": {"commercial_automation_status": "allowed"},
        "operational_constraints": {"timeout_seconds": 30, "max_probe_bytes": 4194304},
    }


class FixedSourceProbesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "access").mkdir()

    def write(self, source, *, change=None):
        data = contract(source)
        if change is not None:
            change(data)
        (self.root / "access" / (source + ".json")).write_text(
            json.dumps(data), encoding="utf-8")

    def test_each_source_matches_fixed_reviewed_contract(self):
        for source in PROBES:
            with self.subTest(source=source):
                self.write(source)
                url, op, limit, timeout = reviewed_probe(source, self.root)
                self.assertEqual((url, op), PROBES[source])
                self.assertGreater(limit, 0)
                self.assertEqual(timeout, 30)

    def test_reject_credentials_and_rights_changes(self):
        source = "gfz.geomagnetic-kp"
        for mutate in (
            lambda d: d["authentication"].update(mode="bearer"),
            lambda d: d["rights_and_policy"].update(commercial_automation_status="unknown"),
            lambda d: d["probe_contract"].update(requires_credentials=True),
            lambda d: d.update(status="restricted_by_terms"),
            lambda d: d["request_contract"].update(allowed_operations=["other"]),
        ):
            self.write(source, change=mutate)
            with self.subTest(mutation=repr(mutate)):
                with self.assertRaises(ProbeBlocked):
                    reviewed_probe(source, self.root)

    def test_source_cannot_change_host_path_or_limit(self):
        source = "geoboundaries.gbopen"
        for mutate in (
            lambda d: d.update(service_root="https://attacker.invalid"),
            lambda d: d["request_contract"].update(path_templates=["/other"]),
            lambda d: d["operational_constraints"].update(max_probe_bytes=2**30),
            lambda d: d["operational_constraints"].update(timeout_seconds=600),
        ):
            self.write(source, change=mutate)
            with self.subTest(mutation=repr(mutate)):
                with self.assertRaises(ProbeBlocked):
                    reviewed_probe(source, self.root)

    def test_geo_boundaries_frozen_identity_and_original_licence(self):
        source = "geoboundaries.gbopen"
        payload = {"boundaryISO": "DEU", "boundaryType": "ADM1",
                   "boundaryID": "DEU-ADM1-10402087",
                   "boundaryLicense": "DL-DE BY 2.0",
                   "licenseSource": "govdata.de"}
        result = verify_response(source, json.dumps(payload).encode())
        self.assertEqual(result["frozen_id"], "DEU-ADM1-10402087")
        payload["boundaryID"] = "DEU-ADM1-CHANGED"
        with self.assertRaises(ProbeBlocked):
            verify_response(source, json.dumps(payload).encode())

    def test_gfz_noaa_structural_only(self):
        a = verify_response("gfz.geomagnetic-kp", b'{"Kp":[1.0]}')
        self.assertIs(a["scientific_values_verified"], False)
        b = verify_response("noaa.swpc.real-time-solar-wind", b'[{"satellite": "x"}]')
        self.assertIs(b["sensor_lineage_verified"], False)

    def test_reject_nonfinite_and_duplicate_json_fields(self):
        for raw in (b'{"foo":NaN}', b'{"foo":1,"foo":2}', b'{"foo":Infinity}', b'not json'):
            with self.subTest(raw=raw), self.assertRaises(ProbeBlocked):
                verify_response("gfz.geomagnetic-kp", raw)

    def test_probe_receipt_has_no_provider_values(self):
        source = "gfz.geomagnetic-kp"
        self.write(source)
        body = b'{"Kp":[1.0],"secret":"never-emit-this"}'
        client = Client(Reply(body))
        receipt = probe(source, root=self.root, opener=client)
        self.assertEqual(receipt["response_bytes"], len(body))
        self.assertEqual(len(receipt["response_sha256"]), 64)
        self.assertEqual(client.requests[0][1], "GET")
        self.assertEqual(client.requests[0][0], PROBES[source][0])
        self.assertNotIn("never-emit-this", json.dumps(receipt))
        self.assertFalse(receipt["provider_bytes_persisted"])
        self.assertFalse(receipt["model_input_approved"])

    def test_reject_oversized_and_wrong_media_type(self):
        source = "gfz.geomagnetic-kp"
        self.write(source)
        for reply in (Reply(b'{"ok":true}', "text/html"),
                      Reply(b'{"ok":true}', declared="4194305"),
                      Reply(b"x" * (4194304 + 1))):
            with self.subTest(content_type=reply.headers), self.assertRaises(ProbeBlocked):
                probe(source, root=self.root, opener=Client(reply))

    def test_no_redirect_or_unlisted_source(self):
        with self.assertRaises(ProbeBlocked):
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.invalid")
        with self.assertRaises(ProbeBlocked):
            reviewed_probe("attacker.invalid", self.root)


if __name__ == "__main__":
    unittest.main()
