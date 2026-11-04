# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic tests, no real NCEI archive downloaded or stored."""
from __future__ import annotations

import csv
import hashlib
import gzip
import io
import unittest
from unittest.mock import patch

from research_runners import noaa_ncei_2024_hail_row_direct_preflight_v0 as p


def rows(*entries: dict, fieldnames=None) -> bytes:
    cols = list(fieldnames or p.SELECTED_FIELDS)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry)
    return gzip.compress(buffer.getvalue().encode("utf-8"), mtime=0)


def good(**changes) -> dict:
    record = dict.fromkeys(p.SELECTED_FIELDS, "")
    record.update({
        "EVENT_ID": "1186553", "EPISODE_ID": "190994", "YEAR": "2024",
        "STATE": "TEXAS", "EVENT_TYPE": "Hail",
        "BEGIN_DATE_TIME": "27-MAY-24 18:43:00",
        "CZ_TIMEZONE": "CST-6",
        "SOURCE": "Public", "MAGNITUDE": "3.25",
        "MAGNITUDE_TYPE": "E", "BEGIN_LAT": "32.71",
        "BEGIN_LON": "-97.1", "BEGIN_LOCATION": "DALWORTHINGTON",
    })
    record.update(changes)
    return record


def audited(source: bytes) -> dict:
    with (patch.object(p, "EXPECTED_COMPRESSED_BYTES", len(source)),
          patch.object(p, "EXPECTED_ORIGINAL_SHA256",
                       hashlib.sha256(source).hexdigest())):
        return p.audit_original_csv(source)


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, *, url=None, status=200,
                 content_length=None, encoding="identity"):
        super().__init__(body)
        self.status = status
        self._url = p.PROVIDER_URL if url is None else url
        self.headers = {"Content-Encoding": encoding}
        if content_length is not None:
            self.headers["Content-Length"] = content_length

    def geturl(self):
        return self._url


class FakeOpener:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def open(self, req, timeout=None):
        self.requests.append((req, timeout))
        return self.result


class NCEIHailOriginalCSVTests(unittest.TestCase):
    def test_target_event_present_synthetic_no_model_admission(self):
        source = rows(
            good(EVENT_ID="900001", MAGNITUDE="1.50"),
            good(), good(EVENT_ID="900003", EVENT_TYPE="Tornado")
        )
        result = audited(source)
        self.assertEqual(result["candidate_id_checked_against_original"], "1186553")
        self.assertEqual(result["provider_original_fields"]["EVENT_ID"], "1186553")
        self.assertEqual(result["provider_original_fields"]["MAGNITUDE"], "3.25")
        self.assertEqual(result["source_decoded_csv_rows_checked"], 3)
        self.assertEqual(result["source_compressed_bytes"], len(source))
        self.assertEqual(len(result["source_compressed_sha256"]), 64)
        for field in (
            "source_rights_or_cat_model_admitted",
            "annual_hail_frequency_or_losses_estimated",
            "provider_source_bytes_committed_or_published",
            "nws_preliminary_mping_2024_05_27_report_identical",
            "event_independent_storm_id_resolved",
        ):
            self.assertFalse(result[field])
        self.assertTrue(result["ncei_source_row_verified"])
        self.assertNotIn("EVENT_NARRATIVE", str(result))

    def test_wrong_id_and_duplicate_id_blocked(self):
        with self.assertRaisesRegex(p.NCEIProofBlocked, "absent"):
            audited(rows(good(EVENT_ID="9999")))
        with self.assertRaisesRegex(p.NCEIProofBlocked, "duplicate"):
            audited(rows(good(), good()))

    def test_event_type_year_state_and_month_mismatch_rejected(self):
        for key, value in (
            ("EVENT_TYPE", "Tornado"), ("YEAR", "2023"),
            ("STATE", "OKLAHOMA"), ("BEGIN_DATE_TIME", "27-APR-24 18:43:00"),
        ):
            with self.subTest(key=key):
                with self.assertRaisesRegex(p.NCEIProofBlocked, "identity"):
                    audited(rows(good(**{key: value})))

    def test_original_event_episode_and_measurement_drift_fails_closed(self):
        for field, bad in (
            ("EPISODE_ID", "900"),
            ("MAGNITUDE", "2.75"),
            ("SOURCE", "Radar"),
            ("BEGIN_LAT", "32.73"),
            ("BEGIN_LON", "-97.11"),
            ("BEGIN_LOCATION", "ARLINGTON"),
            ("CZ_TIMEZONE", "CDT-5"),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(p.NCEIProofBlocked, "identity"):
                    audited(rows(good(**{field: bad})))

    def test_gzip_failure_missing_columns_and_source_size(self):
        with self.assertRaisesRegex(p.NCEIProofBlocked, "size mismatch"):
            p.audit_original_csv(b"fake")
        source = rows(good())
        with patch.object(p, "EXPECTED_COMPRESSED_BYTES", len(source)):
            with self.assertRaisesRegex(p.NCEIProofBlocked, "SHA256"):
                p.audit_original_csv(source)
        with self.assertRaises(p.NCEIProofBlocked):
            audited(b"not a gzip")
        with self.assertRaisesRegex(p.NCEIProofBlocked, "schema"):
            audited(rows(good(), fieldnames=["EVENT_ID"]))

    def test_gzip_crc_and_uncompressed_cap_are_fail_closed(self):
        source = rows(good())
        broken = bytearray(source)
        broken[-8] ^= 2
        with self.assertRaises(p.NCEIProofBlocked):
            audited(bytes(broken))
        with patch.object(p, "MAX_EXPANDED_BYTES", 20):
            with self.assertRaisesRegex(p.NCEIProofBlocked, "byte guard"):
                audited(source)

    def test_public_https_is_fixed_no_redirect_or_unsafe_encoding(self):
        source = rows(good())
        for response in (
            FakeResponse(source, status=302),
            FakeResponse(source, url="https://evil.example/archive"),
            FakeResponse(source, encoding="gzip"),
            FakeResponse(source, content_length="NaN"),
            FakeResponse(source, content_length="999999"),
        ):
            with self.subTest(response=response):
                opener = FakeOpener(response)
                with (patch.object(p, "EXPECTED_COMPRESSED_BYTES", len(source)),
                      patch.object(p, "EXPECTED_ORIGINAL_SHA256",
                                   hashlib.sha256(source).hexdigest()),
                      self.assertRaises(p.NCEIProofBlocked)):
                    p.direct_original_probe(opener)
                self.assertEqual(opener.requests[0][0].full_url, p.PROVIDER_URL)
                self.assertEqual(opener.requests[0][1], p.HTTP_TIMEOUT_SECONDS)

    def test_https_mock_success_never_returns_archive_data(self):
        source = rows(good())
        opener = FakeOpener(
            FakeResponse(source, content_length=str(len(source)))
        )
        with (patch.object(p, "EXPECTED_COMPRESSED_BYTES", len(source)),
              patch.object(p, "EXPECTED_ORIGINAL_SHA256",
                           hashlib.sha256(source).hexdigest())):
            result = p.direct_original_probe(opener)
        self.assertTrue(result["ncei_source_row_verified"])
        self.assertEqual(result["source_compressed_bytes"], len(source))
        self.assertNotIn("raw_csv", result)
        self.assertNotIn("raw_archive", result)
        self.assertEqual(opener.requests[0][0].get_method(), "GET")

    def test_reject_expanded_csv_row_count_over_bound(self):
        src = rows(good(EVENT_ID="1"), good())
        with patch.object(p, "MAX_ROWS", 1):
            with self.assertRaisesRegex(p.NCEIProofBlocked, "row count"):
                audited(src)


if __name__ == "__main__":
    unittest.main()
