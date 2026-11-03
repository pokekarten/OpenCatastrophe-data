# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic GHCN-Daily fixed-station byte-range parser tests."""
from __future__ import annotations

from datetime import datetime, timezone, date, timedelta
import io
import json
import unittest

from scripts.probe_ghcnd_station_prefix_v0 import (
    GHCNDStationProbeError, BYTE_LIMIT, URL, inspect_station_prefix, probe,
    verify_contract,
)


def sample(*, alter=None, tail: bool = True) -> bytes:
    # All observations synthetic; no downloaded source bytes in repository.
    origin = date(1980, 1, 1)
    lines: list[str] = []
    for n in range(2500):
        d = (origin + timedelta(days=n)).strftime("%Y%m%d")
        row = ["USW00094728", d, "PRCP", str(n % 211), "", "", "Z", ""]
        if n == 4 and alter is not None:
            alter(row)
        lines.append(",".join(row) + "\n")
    raw = "".join(lines).encode("utf-8")
    assert len(raw) > BYTE_LIMIT
    return raw[:BYTE_LIMIT] if tail else raw[:BYTE_LIMIT - 1] + b"\n"


class Response:
    def __init__(self, raw, *, url=URL, status=206,
                 range_header="bytes 0-65535/130000",
                 media="application/octet-stream", encoding="identity"):
        self.raw = io.BytesIO(raw)
        self.url = url
        self.status = status
        self.headers = {
            "Content-Type": media,
            "Content-Range": range_header,
            "Content-Encoding": encoding,
        }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.raw.close()

    def geturl(self):
        return self.url

    def read(self, amount):
        return self.raw.read(amount)


class GHCNDOriginalStationTests(unittest.TestCase):
    def test_reviewed_contract_requires_one_fixed_station_and_range(self):
        c = verify_contract()
        self.assertEqual(c["status"], "probe_ready")
        self.assertEqual(c["probe_contract"]["mode"], "provider_specific")
        self.assertEqual(c["source_ids"], ["noaa.ncei.ghcn-daily"])

    def test_synthetic_csv_sample_parses_without_exposing_raw_values(self):
        s = inspect_station_prefix(sample())
        self.assertGreater(s["complete_original_rows_checked"], 1000)
        self.assertEqual(s["element_types_seen"], ["PRCP"])
        self.assertEqual(s["station_id"], "USW00094728")
        self.assertEqual(s["nonblank_quality_flags"], 0)
        self.assertFalse(s["scientific_quality_admitted"])
        self.assertNotIn("data_value", json.dumps(s))
        self.assertFalse(s["full_station_history_complete"])

    def test_receipt_exact_206_no_persistence(self):
        raw = sample()
        calls = []
        def opener(req, timeout):
            calls.append((req.full_url, req.get_method(), req.get_header("Range"), timeout))
            return Response(raw)
        receipt = probe(
            open_request=opener,
            utc_clock=lambda: datetime(2026, 11, 2, 17, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(calls, [(URL, "GET", "bytes=0-65535", 30)])
        self.assertEqual(receipt["sample_bytes"], BYTE_LIMIT)
        self.assertEqual(receipt["original_file_total_bytes_observed"], 130000)
        self.assertEqual(len(receipt["sample_sha256"]), 64)
        self.assertFalse(receipt["raw_observations_persisted"])
        self.assertFalse(receipt["model_input_admitted"])

    def test_accepts_exact_provider_observed_binary_octet_stream(self):
        # NOAA S3 returns the original CSV object as binary/octet-stream.
        receipt = probe(
            open_request=lambda req, timeout: Response(
                sample(), media="binary/octet-stream"
            )
        )
        self.assertEqual(receipt["media_type"], "binary/octet-stream")
        self.assertGreater(receipt["complete_original_rows_checked"], 1000)

    def test_rejects_other_station(self):
        with self.assertRaises(GHCNDStationProbeError):
            inspect_station_prefix(sample(alter=lambda row: row.__setitem__(0, "USW00094729")))

    def test_rejects_duplicate_element_day(self):
        with self.assertRaises(GHCNDStationProbeError):
            inspect_station_prefix(sample(alter=lambda row: row.__setitem__(1, "19800104")))

    def test_rejects_malformed_date_and_numeric(self):
        for column, value in [(1, "19801333"), (3, "NaN"), (3, "1.0")]:
            with self.subTest(column=column, value=value), self.assertRaises(GHCNDStationProbeError):
                inspect_station_prefix(sample(alter=lambda row: row.__setitem__(column, value)))

    def test_rejects_bad_quality_or_source_flag(self):
        for column, value in [(4, "QQ"), (5, "#"), (6, "BAD"), (7, "2569")]:
            with self.subTest(column=column, value=value), self.assertRaises(GHCNDStationProbeError):
                inspect_station_prefix(sample(alter=lambda row: row.__setitem__(column, value)))

    def test_rejects_missing_or_extra_csv_field(self):
        def missing(row): row.pop()
        def extra(row): row.append("X")
        for mutation in [missing, extra]:
            with self.subTest(mutation=mutation.__name__), self.assertRaises(GHCNDStationProbeError):
                inspect_station_prefix(sample(alter=mutation))

    def test_requires_exact_65536_bytes(self):
        for value in [b"", b"test\n", sample()[:-1], sample() + b"x"]:
            with self.subTest(length=len(value)), self.assertRaises(GHCNDStationProbeError):
                inspect_station_prefix(value)

    def test_rejects_wrong_http_status_range_redirect_and_media(self):
        for opts in [
            {"status": 200},
            {"status": 416},
            {"range_header": "bytes 0-65534/130000"},
            {"range_header": "bytes 0-65535/*"},
            {"range_header": "bytes 0-65535/65536"},
            {"url": "https://another.example.org/data"},
            {"media": "text/html"},
            {"encoding": "gzip"},
        ]:
            def opener(req, timeout):
                return Response(sample(), **opts)
            with self.subTest(opts=opts), self.assertRaises(GHCNDStationProbeError):
                probe(open_request=opener)

    def test_bad_receipt_clock_fails(self):
        with self.assertRaises(GHCNDStationProbeError):
            probe(
                open_request=lambda req, timeout: Response(sample()),
                utc_clock=lambda: datetime(2026, 11, 2, 17, 0),
            )


if __name__ == "__main__":
    unittest.main()
