# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline regression tests for exact NOAA GHCN-Daily NODD metadata."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import unittest

from scripts.probe_ghcnd_nodd_version_country_v0 import (
    GHCNDProbeError, MAX_BYTES, OBJECTS, parse_countries, parse_version,
    probe, verify_frozen_contract,
)

VERSION = (
    b"The current version of GHCN Daily is 3.35-upd-2026103117 "
    b"(i.e, an update that started at 2026103117 UTC),\n"
    b"created by appending recently available data updates to the "
    b"last fully reprocessed version: 3.35-por-2026102323."
)


def countries() -> bytes:
    # 120 strictly synthetic two-letter codes. Not a map of real countries.
    return "".join(
        f"{chr(65 + i // 26)}{chr(65 + i % 26)} SyntheticArea{i}\n"
        for i in range(120)
    ).encode("utf-8")


class Response:
    def __init__(self, body: bytes, url: str, status: int = 200,
                 media: str = "application/octet-stream",
                 encoding: str = "identity"):
        self.stream = io.BytesIO(body)
        self.url = url
        self.status = status
        self.headers = {"Content-Type": media, "Content-Encoding": encoding}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    def geturl(self):
        return self.url

    def read(self, size: int):
        return self.stream.read(size)


class GHCNNODDProbeTests(unittest.TestCase):
    def test_current_canonical_contract_is_scoped(self):
        contract = verify_frozen_contract()
        self.assertEqual(contract["source_ids"], ["noaa.ncei.ghcn-daily"])
        self.assertEqual(contract["status"], "probe_ready")
        self.assertEqual(len(contract["request_contract"]["path_templates"]), 2)

    def test_version_parser(self):
        result = parse_version(VERSION)
        self.assertEqual(result["rolling_version"], "3.35-upd-2026103117")
        self.assertEqual(result["last_reprocessed_version"], "3.35-por-2026102323")

    def test_country_vocab_not_iso(self):
        result = parse_countries(countries())
        self.assertEqual(result["ghcn_native_country_count"], 120)
        self.assertFalse(result["country_codes_are_iso3166"])

    def test_two_exact_requests_metadata_only(self):
        calls = []
        data = dict(zip((label for label, _ in OBJECTS), (VERSION, countries())))
        def open_request(req, timeout):
            calls.append((req.full_url, req.get_method(), timeout))
            label = next(label for label, url in OBJECTS if url == req.full_url)
            return Response(data[label], req.full_url)
        result = probe(
            open_request=open_request,
            utc_clock=lambda: datetime(2026, 11, 2, 17, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(calls, [(url, "GET", 30) for _, url in OBJECTS])
        self.assertEqual(result["rolling_version"], "3.35-upd-2026103117")
        self.assertEqual(result["ghcn_native_country_count"], 120)
        self.assertEqual(result["retrieved_at_utc"], "2026-11-02T17:00:00+00:00")
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["weather_observations_acquired"])
        self.assertEqual(len(result["objects"]), 2)
        self.assertNotIn("SyntheticArea", json.dumps(result))

    def test_rejects_duplicate_version_markers(self):
        with self.assertRaises(GHCNDProbeError):
            parse_version(VERSION + b" and 3.35-upd-2026103117")

    def test_rejects_inconsistent_versions(self):
        with self.assertRaises(GHCNDProbeError):
            parse_version(VERSION.replace(b"3.35-por-", b"3.34-por-"))

    def test_rejects_reverse_version_timeline(self):
        with self.assertRaises(GHCNDProbeError):
            parse_version(VERSION.replace(b"2026102323", b"2026110123"))

    def test_rejects_invalid_version_timestamp(self):
        with self.assertRaises(GHCNDProbeError):
            parse_version(VERSION.replace(b"2026103117", b"2026133117"))

    def test_rejects_duplicate_country_code(self):
        with self.assertRaises(GHCNDProbeError):
            parse_countries(countries() + b"AA Another Place\n")

    def test_rejects_too_few_country_codes(self):
        with self.assertRaises(GHCNDProbeError):
            parse_countries(b"DE Germany\nFR France\n")

    def test_rejects_invalid_country_code(self):
        with self.assertRaises(GHCNDProbeError):
            parse_countries(countries().replace(b"AA SyntheticArea0", b"ABC SyntheticArea0"))

    def test_rejects_overlong_and_binary(self):
        for raw in (b"x" * (MAX_BYTES + 1), b"\xff", b"A\x00B"):
            with self.subTest(raw=raw[:5]), self.assertRaises(GHCNDProbeError):
                parse_version(raw)

    def test_rejects_redirected_object(self):
        def opened(req, timeout):
            return Response(VERSION, "https://other.example.test/")
        with self.assertRaises(GHCNDProbeError):
            probe(open_request=opened)

    def test_rejects_compressed_or_wrong_type(self):
        for opts in ({"encoding": "gzip"}, {"media": "text/html"}, {"status": 206}):
            def opened(req, timeout):
                return Response(VERSION, req.full_url, **opts)
            with self.subTest(opts=opts), self.assertRaises(GHCNDProbeError):
                probe(open_request=opened)

    def test_rejects_oversized_http_stream(self):
        def opened(req, timeout):
            return Response(b"x" * (MAX_BYTES + 1), req.full_url)
        with self.assertRaises(GHCNDProbeError):
            probe(open_request=opened)

    def test_rejects_naive_receipt_timestamp(self):
        def opened(req, timeout):
            value = VERSION if req.full_url == OBJECTS[0][1] else countries()
            return Response(value, req.full_url)
        with self.assertRaises(GHCNDProbeError):
            probe(open_request=opened, utc_clock=lambda: datetime(2026, 11, 2, 17, 0))


if __name__ == "__main__":
    unittest.main()
