# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only test: never contact FEMA or record actual claims or policy data."""
from __future__ import annotations

from io import BytesIO
import json
import unittest

from scripts.probe_openfema_nfip_v3_metadata_v0 import (
    MAX_BYTES, PROBES, SourceBlocked, check_response, main, probe,
)

CLAIMS, POLICIES = tuple(PROBES)


def fake(source, value, **meta_override):
    path, entity, column = PROBES[source]
    meta = {"version": "v3", "entityname": entity, "top": 1, "skip": 0,
            "select": column, "format": "json", "url": path}
    meta.update(meta_override)
    return json.dumps({"metadata": meta, entity: [{column: value}]}).encode()


class Response:
    status = 200

    def __init__(self, data, ctype="application/json"):
        self._file = BytesIO(data)
        self.headers = {"Content-Type": ctype, "Content-Length": str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._file.close()

    def read(self, n):
        return self._file.read(n)


class Opener:
    def __init__(self, data):
        self.response = Response(data)
        self.url = None

    def open(self, req, timeout):
        self.url = req.full_url
        return self.response


class NFIPV3MetadataCanaryTests(unittest.TestCase):
    def test_claims_valid_no_source_values_exported(self):
        out = check_response(CLAIMS, fake(CLAIMS, 2024))
        self.assertEqual(out["row_count"], 1)
        self.assertFalse(out["value_exported"])
        self.assertFalse(out["commercial_underwriting_authorized"])
        self.assertNotIn("2024", json.dumps(out))
        self.assertFalse(out["model_input_approved"])

    def test_policies_valid_no_source_value_exported(self):
        out = check_response(POLICIES, fake(POLICIES, "2026-01-01T00:00:00Z"))
        self.assertEqual(out["source_version"], "v3")
        self.assertNotIn("2026-01-01", json.dumps(out))

    def test_top_zero_and_unreviewed_query_block(self):
        with self.assertRaisesRegex(SourceBlocked, "metadata/version"):
            check_response(CLAIMS, fake(CLAIMS, 2024, top=0))
        with self.assertRaisesRegex(SourceBlocked, "metadata/version"):
            check_response(CLAIMS, fake(CLAIMS, 2024, url="/api/open/v3/NfipClaims?$top=0"))
        with self.assertRaises(SourceBlocked):
            check_response(CLAIMS, fake(CLAIMS, 2024, select="id"))
        with self.assertRaises(SourceBlocked):
            check_response("unsafe/unreviewed-source", b"{}")

    def test_sensitivity_boundaries(self):
        data = json.loads(fake(CLAIMS, 2024))
        data["NfipClaims"][0]["homeOwnerName"] = "PRIVATE SYNTHETIC"
        with self.assertRaisesRegex(SourceBlocked, "PII leak"):
            check_response(CLAIMS, json.dumps(data).encode())
        with self.assertRaises(SourceBlocked):
            check_response(CLAIMS, fake(CLAIMS, True))
        with self.assertRaises(SourceBlocked):
            check_response(POLICIES, fake(POLICIES, "not-a-date"))
        with self.assertRaises(SourceBlocked):
            check_response(POLICIES, b'{"x":1,"x":2}')
        with self.assertRaises(SourceBlocked):
            check_response(POLICIES, b"x" * (MAX_BYTES + 1))

    def test_fixed_url_and_offline_default(self):
        self.assertEqual(main(["--source", CLAIMS]), 2)
        client = Opener(fake(POLICIES, "2025-10-15"))
        response = probe(POLICIES, opener=client)
        self.assertEqual(client.url,
                         "https://www.fema.gov" + PROBES[POLICIES][0])
        self.assertFalse(response["provider_raw_response_persisted"])


if __name__ == "__main__":
    unittest.main()
