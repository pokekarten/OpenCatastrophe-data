# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline original NCEI gzip acquisition, source controls and format tests."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import gzip
import io
import json
import unittest

from scripts.probe_ghcnd_ncei_us_station_gzip_v0 import (
    MAX_COMPRESSED, NCEIStationError, NODD_SHA256, URL,
    inflate_single_member, probe, verify_contract,
)


def fixture() -> bytes:
    rows = ["ID,DATE,ELEMENT,DATA_VALUE,M_FLAG,Q_FLAG,S_FLAG,OBS_TIME\n"]
    base = date(1869, 1, 1)
    for i in range(41000):
        d = (base + timedelta(days=i)).strftime("%Y%m%d")
        rows.append(f"USW00094728,{d},TMAX,{i%150},,,Z,{'' if i%5 else '2400'}\n")
    raw = "".join(rows).encode("ascii")
    assert len(raw) > 1024 * 1024
    return raw


class Response:
    def __init__(self, body: bytes, *, url=URL, status=200,
                 mime="application/gzip", encoded="identity",
                 total=None, content_range=None):
        self.body = io.BytesIO(body)
        self.url = url
        self.status = status
        self.headers = {
            "Content-Type": mime,
            "Content-Encoding": encoded,
            "Content-Length": str(len(body)) if total is None else total,
            "ETag": '"0123456789abcdef0123456789abcdef"',
            "Last-Modified": "Mon, 02 Nov 2026 18:20:00 GMT",
        }
        if content_range is not None:
            self.headers["Content-Range"] = content_range

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.body.close()

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.body.read(limit)


class NCEIGzipSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = fixture()
        cls.gzip_raw = gzip.compress(cls.raw, mtime=0)

    def test_fixed_country_limited_source_contract(self):
        c = verify_contract()
        self.assertEqual(c["status"], "probe_ready")
        self.assertEqual(c["authentication"]["mode"], "none")
        self.assertEqual(c["source_ids"], ["noaa.ncei.ghcn-daily"])
        self.assertIn("non-U.S.", c["response_contract"]["scientific_semantics"])

    def test_single_original_gzip_inflated_exact(self):
        self.assertEqual(inflate_single_member(self.gzip_raw), self.raw)

    def test_exact_source_get_and_receipt_no_neon_or_model(self):
        seen = []
        def opener(req, timeout):
            seen.append((req.full_url, req.get_method(), timeout, req.get_header("Range")))
            return Response(self.gzip_raw)
        result = probe(
            open_request=opener,
            utc_clock=lambda: datetime(2026, 11, 2, 18, 30, tzinfo=timezone.utc)
        )
        self.assertEqual(seen, [(URL, "GET", 60, None)])
        self.assertEqual(result["complete_original_rows_checked"], 41000)
        self.assertEqual(result["inflated_original_csv_bytes"], len(self.raw))
        self.assertEqual(result["compressed_original_bytes"], len(self.gzip_raw))
        self.assertEqual(result["provider_native_2400_observation_time_rows"], 8200)
        self.assertEqual(len(result["compressed_original_sha256"]), 64)
        self.assertFalse(result["same_csv_bytes_as_pinned_nodd_20261102"])
        self.assertFalse(result["ncei_last_day_later_than_pinned_nodd"])
        self.assertEqual(result["nodd_pinned_baseline_csv_sha256"], NODD_SHA256)
        self.assertFalse(result["raw_provider_bytes_persisted"])
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["commercial_global_ghcnd_rights_inferred"])
        self.assertNotIn("DATA_VALUE", json.dumps(result))

    def test_fails_closed_on_modified_original(self):
        truncated = self.gzip_raw[:-3]
        with self.assertRaises(NCEIStationError):
            inflate_single_member(truncated)

    def test_rejects_trailing_members_or_garbage(self):
        for raw in (self.gzip_raw + self.gzip_raw,
                    self.gzip_raw + b"\n",
                    b"NOPE" + self.gzip_raw):
            with self.subTest(size=len(raw)), self.assertRaises(NCEIStationError):
                inflate_single_member(raw)

    def test_bounded_inflation_for_bomb_prevention(self):
        with self.assertRaises(NCEIStationError):
            inflate_single_member(self.gzip_raw, max_csv=2048)

    def test_bad_crc_fails(self):
        corrupt = self.gzip_raw[:-8] + bytes([self.gzip_raw[-8] ^ 255]) + self.gzip_raw[-7:]
        with self.assertRaises(NCEIStationError):
            inflate_single_member(corrupt)

    def test_bad_provider_data_fails(self):
        malformed = self.raw.replace(
            b"USW00094728,18690101,TMAX,0,,,Z,2400\n",
            b"USW00094729,18690101,TMAX,0,,,Z,2400\n", 1
        )
        with self.assertRaises(ValueError):
            probe(open_request=lambda req, timeout: Response(gzip.compress(malformed, mtime=0)))

    def test_bad_http_identity_and_limits_fail(self):
        cases = [
            {"status": 206}, {"status": 302},
            {"url": "https://other.invalid/some.csv.gz"},
            {"mime": "text/html"},
            {"encoded": "gzip"},
            {"content_range": "bytes 0-1023/1234567"},
            {"total": "NaN"},
            {"total": str(MAX_COMPRESSED + 1)},
            {"total": str(len(self.gzip_raw) + 1)},
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(NCEIStationError):
                probe(open_request=lambda req, timeout: Response(self.gzip_raw, **case))

    def test_missing_content_length_is_bounded(self):
        out = probe(open_request=lambda req, timeout: Response(self.gzip_raw, total=""))
        self.assertEqual(out["complete_original_rows_checked"], 41000)

    def test_missing_timezone_fails(self):
        with self.assertRaises(NCEIStationError):
            probe(open_request=lambda req, timeout: Response(self.gzip_raw),
                  utc_clock=lambda: datetime(2026, 11, 2, 18, 30))


if __name__ == "__main__":
    unittest.main()
