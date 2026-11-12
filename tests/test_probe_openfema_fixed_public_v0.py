# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression tests: no OpenFEMA traffic or original provider records."""
from __future__ import annotations

from io import BytesIO
import json
import unittest
from urllib.error import URLError

from scripts.probe_openfema_fixed_public_v0 import (
    MAX_BYTES, PROBES, SourceError, main, probe, validate_response,
)


def payload(source, rows, **metadata_overrides):
    path, entity, version = PROBES[source]
    meta = {"entityname": entity, "version": version, "top": 2, "skip": 0,
            "format": "json", "url": path}
    meta.update(metadata_overrides)
    return json.dumps({"metadata": meta, entity: rows},
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def nfip_row(i, **kw):
    row = {"id": f"SYNTHETIC-{i}", "state": "XY", "county": "SYNTHETIC COUNTY",
           "fipsCode": f"{i:05d}", "asOfDate": "2026-08-04T00:00:00.000Z",
           "resPenetrationRate": 1.15, "resPenetrationRateSfha": None,
           "totalResStructures": 100, "totalResStructuresSfha": 50,
           "resContractsInForce": 115, "resContractsInForceSfha": 4}
    row.update(kw)
    return row


def disaster_row(i, **kw):
    row = {"id": f"SYNTHETIC-DECL-{i}", "disasterNumber": 4700 + i,
           "state": "XY", "designatedArea": "SYNTHETIC COUNTY",
           "incidentType": "Flood", "declarationDate": "2024-03-01T00:00:00Z"}
    row.update(kw)
    return row


class Response:
    status = 200

    def __init__(self, body, content_type="application/json"):
        self.content = BytesIO(body)
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.content.close()

    def read(self, n):
        return self.content.read(n)


class MockOpener:
    def __init__(self, response):
        self.response = response
        self.url = None

    def open(self, req, timeout=None):
        self.url = req.full_url
        return self.response


NFIP, DISASTER = tuple(PROBES)


class FixedOpenFEMATests(unittest.TestCase):
    def test_nfip_accepts_over_100pct_as_source_warning(self):
        raw = payload(NFIP, [nfip_row(1), nfip_row(2, resPenetrationRate=.2)])
        out = validate_response(NFIP, raw)
        self.assertEqual(out["ratio_over_100pct_field_count"], 1)
        self.assertIsNone(out["missing_structure_denominator_fields"] if False else None)
        self.assertEqual(out["rows"], 2)
        self.assertEqual(out["missing_structure_denominator_fields"], 0)
        self.assertFalse(out["model_input_approved"])
        self.assertFalse(out["commercial_underwriting_authorized"])
        self.assertNotIn("SYNTHETIC COUNTY", json.dumps(out))
        self.assertNotIn("SYNTHETIC-1", json.dumps(out))

    def test_declarations_do_not_escape_identifiers(self):
        out = validate_response(DISASTER, payload(
            DISASTER, [disaster_row(1), disaster_row(2)]))
        self.assertEqual(out["version"], "v2")
        self.assertEqual(out["rows"], 2)
        self.assertIsNone(out["ratio_over_100pct_field_count"])
        self.assertNotIn("SYNTHETIC COUNTY", json.dumps(out))

    def test_schema_drift_and_count_violation_block(self):
        with self.assertRaisesRegex(SourceError, "wrong version"):
            validate_response(NFIP, payload(NFIP, [nfip_row(1), nfip_row(2)],
                                            version="v2"))
        with self.assertRaisesRegex(SourceError, "not exactly two"):
            validate_response(NFIP, payload(NFIP, [nfip_row(1)]))
        with self.assertRaisesRegex(SourceError, "wrong response entity"):
            validate_response(DISASTER, payload(DISASTER, [disaster_row(1), disaster_row(2)]).replace(
                b"DisasterDeclarationsSummaries", b"NonFEMADataset"))
        with self.assertRaisesRegex(SourceError, "duplicate provider record"):
            validate_response(DISASTER, payload(DISASTER, [disaster_row(1), disaster_row(1)]))

    def test_fields_missing_null_types_and_out_of_range_fail_closed(self):
        bad = [
            nfip_row(1, fipsCode="1"),
            nfip_row(1, resContractsInForce=True),
            nfip_row(1, resPenetrationRate=-1),
            nfip_row(1, resPenetrationRate="NaN"),
        ]
        for row in bad:
            with self.subTest(row=row):
                with self.assertRaises(SourceError):
                    validate_response(NFIP, payload(NFIP, [row, nfip_row(2)]))
        with self.assertRaises(SourceError):
            validate_response(DISASTER, payload(
                DISASTER, [disaster_row(1, disasterNumber=True), disaster_row(2)]))
        with self.assertRaises(SourceError):
            validate_response(NFIP, b'{"x":1,"x":2}')

    def test_max_byte_bound_and_strict_content_type(self):
        with self.assertRaisesRegex(SourceError, "response byte limit"):
            validate_response(NFIP, b"x" * (MAX_BYTES + 1))
        raw = payload(DISASTER, [disaster_row(1), disaster_row(2)])
        opener = MockOpener(Response(raw))
        res = probe(DISASTER, opener=opener)
        self.assertEqual(opener.url, "https://www.fema.gov" + PROBES[DISASTER][0])
        self.assertFalse(res["provider_data_bytes_persisted"])
        with self.assertRaisesRegex(SourceError, "unexpected response content type"):
            probe(DISASTER, opener=MockOpener(Response(raw, "text/html")))

    def test_no_implicit_live_probe(self):
        self.assertEqual(main(["--source", NFIP]), 2)
        with self.assertRaisesRegex(SourceError, "unreviewed source"):
            validate_response("untrusted.api", b'{}')


if __name__ == "__main__":
    unittest.main()
