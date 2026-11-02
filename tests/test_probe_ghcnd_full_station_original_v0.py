# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only, whole-original GHCN station CSV and HTTP gate regression."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import io
import json
import unittest

from scripts.probe_ghcnd_full_station_original_v0 import (
    HEADER, MAX_BYTES, MIN_BYTES, StationFullProbeError, URL,
    inspect_full_csv, probe, verify_contract,
)


def synthetic_csv() -> bytes:
    base = date(1869, 1, 1)
    rows = [",".join(HEADER) + "\n"]
    for n in range(41000):
        day = (base + timedelta(days=n)).strftime("%Y%m%d")
        value = "-9999" if n == 2 else str((n % 231) - 100)
        q = "D" if n == 3 else ""
        m = "T" if n == 4 else ""
        rows.append(f"USW00094728,{day},TMAX,{value},{m},{q},Z,\n")
    raw = "".join(rows).encode("utf-8")
    assert MIN_BYTES < len(raw) < MAX_BYTES
    return raw


class Response:
    def __init__(self, raw, *, status=200, url=URL, media="binary/octet-stream",
                 content_length=None, encoding="identity", content_range=None):
        self.stream = io.BytesIO(raw)
        self.url = url
        self.status = status
        self.headers = {
            "Content-Type": media,
            "Content-Length": str(len(raw)) if content_length is None else content_length,
            "Content-Encoding": encoding,
            "ETag": '"0123456789abcdef0123456789abcdef"',
            "Last-Modified": "Mon, 02 Nov 2026 17:20:00 GMT",
        }
        if content_range is not None:
            self.headers["Content-Range"] = content_range

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    def geturl(self):
        return self.url

    def read(self, size):
        return self.stream.read(size)


class FullStationProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = synthetic_csv()

    def test_access_contract_frozen(self):
        p = verify_contract()
        self.assertEqual(p["status"], "probe_ready")
        self.assertEqual(p["source_ids"], ["noaa.ncei.ghcn-daily"])
        self.assertEqual(p["probe_contract"]["mode"], "provider_specific")

    def test_all_synthetic_records_and_flags(self):
        s = inspect_full_csv(self.fixture)
        self.assertEqual(s["complete_original_rows_checked"], 41000)
        self.assertEqual(s["rows_by_element"], {"TMAX": 41000})
        self.assertEqual(s["nonblank_quality_flag_rows"], 1)
        self.assertEqual(s["nonblank_measurement_flag_rows"], 1)
        self.assertEqual(s["original_missing_sentinel_rows"], 1)
        self.assertTrue(s["all_original_rows_validated"])
        self.assertFalse(s["scientific_quality_admitted"])

    def test_original_full_body_sha_and_zero_ingestion(self):
        call = []
        def opened(req, timeout):
            call.append((req.full_url, req.get_method(), timeout, req.get_header("Range")))
            return Response(self.fixture)
        out = probe(open_request=opened, now=lambda: datetime(2026, 11, 2, 18, 0, tzinfo=timezone.utc))
        self.assertEqual(call, [(URL, "GET", 60, None)])
        self.assertEqual(out["original_body_bytes"], len(self.fixture))
        self.assertEqual(len(out["original_body_sha256"]), 64)
        self.assertEqual(out["complete_original_rows_checked"], 41000)
        self.assertFalse(out["original_observations_persisted"])
        self.assertFalse(out["model_input_admitted"])
        self.assertFalse(out["neon_artifact_inserted"])
        self.assertNotIn("DATA_VALUE", json.dumps(out))

    def test_wrong_station_rejected(self):
        raw = self.fixture.replace(b"USW00094728,", b"USW00094729,", 1)
        with self.assertRaises(StationFullProbeError):
            inspect_full_csv(raw)

    def test_duplicate_date_element_rejected(self):
        rows = self.fixture.splitlines(keepends=True)
        rows[10] = rows[9]
        with self.assertRaises(StationFullProbeError):
            inspect_full_csv(b"".join(rows))

    def test_bad_value_and_flags_rejected(self):
        first = b"USW00094728,18690101,TMAX,-100,,,Z,\n"
        self.assertIn(first, self.fixture)
        for mutant in (
            b"USW00094728,18690101,TMAX,NaN,,,Z,\n",
            b"USW00094728,18690101,TMAX,-100,,?,Z,\n",
            b"USW00094728,18691301,TMAX,-100,,,Z,\n",
            b"USW00094728,18690101,TMAX,-100,,,Z,2789\n",
            b"USW00094728,18690101,TMAX,-100,,,Z\n",
        ):
            with self.subTest(mutant=mutant[:45]), self.assertRaises(StationFullProbeError):
                inspect_full_csv(self.fixture.replace(first, mutant, 1))

    def test_not_full_or_truncated_rejected(self):
        for raw in (b"tiny\n", self.fixture[:-1], self.fixture + b"\x00"):
            with self.subTest(length=len(raw)), self.assertRaises(StationFullProbeError):
                inspect_full_csv(raw)

    def test_http_gates_fail_closed(self):
        cases = [
            {"status": 206},
            {"url": "https://unreviewed.example.test/station"},
            {"media": "text/html"},
            {"encoding": "gzip"},
            {"content_range": "bytes 0-65535/16003495"},
            {"content_length": "oops"},
            {"content_length": str(MAX_BYTES + 1)},
            {"content_length": "1"},
            {"content_length": str(len(self.fixture) + 1)},
        ]
        for kw in cases:
            with self.subTest(case=kw), self.assertRaises(StationFullProbeError):
                probe(open_request=lambda req, timeout: Response(self.fixture, **kw))

    def test_naive_receipt_rejected(self):
        with self.assertRaises(StationFullProbeError):
            probe(
                open_request=lambda req, timeout: Response(self.fixture),
                now=lambda: datetime(2026, 11, 2, 18, 0),
            )


if __name__ == "__main__":
    unittest.main()
