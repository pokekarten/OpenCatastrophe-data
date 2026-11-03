# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-only tests of Global Dam Watch v1 Figshare metadata preflight."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from scripts.probe_globaldamwatch_gdw_v1_metadata_v0 import (
    ARCHIVES, DOI, MAX_BYTES, URL, ProbeBlocked, inspect_metadata, probe, verify_contract,
)


def example() -> dict:
    return {
        "id": 25988293,
        "version": 1,
        "doi": DOI,
        "license": {"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"},
        "files": [
            {"id": 101, "name": ARCHIVES[0], "size": 400, "supplied_md5": "a" * 32,
             "download_url": "https://untrusted.example/restricted"},
            {"id": 102, "name": ARCHIVES[1], "size": 300, "computed_md5": "b" * 32},
        ],
        "unreviewed_field": {"secret": "never-print"},
    }


def encoded(item=None) -> bytes:
    return json.dumps(example() if item is None else item).encode("utf-8")


class Reply:
    status = 200

    def __init__(self, body=None, url=URL, media="application/json; charset=utf-8", status=200):
        self.body = encoded() if body is None else body
        self.url = url
        self.headers = {"Content-Type": media}
        self.status = status

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class GDWMetadataProbeTests(unittest.TestCase):
    def test_committed_contract_is_probe_ready_and_frozen(self):
        verify_contract()

    def test_valid_metadata_never_returns_untrusted_download_links(self):
        parsed = inspect_metadata(encoded())
        self.assertEqual(parsed["article_id"], 25988293)
        self.assertEqual(parsed["article_version"], 1)
        self.assertEqual(len(parsed["archive_metadata"]), 2)
        self.assertFalse(parsed["provider_archive_bytes_verified"])
        self.assertNotIn("untrusted.example", json.dumps(parsed))
        self.assertNotIn("never-print", json.dumps(parsed))

    def test_fixed_one_get_receipt_does_not_store_data_or_admit_model(self):
        calls = []

        def fake_open(req, timeout):
            calls.append((req.full_url, req.get_method(), req.get_header("Accept"), timeout))
            return Reply()

        row = probe(open_request=fake_open,
                    utc_clock=lambda: datetime(2026, 11, 4, tzinfo=timezone.utc))
        self.assertEqual(calls, [(URL, "GET", "application/json", 30)])
        self.assertEqual(row["response_bytes"], len(encoded()))
        self.assertEqual(len(row["response_sha256"]), 64)
        self.assertEqual(len(row["probe_code_sha256"]), 64)
        self.assertFalse(row["provider_bytes_persisted"])
        self.assertFalse(row["asset_downloaded"])
        self.assertFalse(row["database_updated"])
        self.assertFalse(row["model_input_approved"])
        self.assertNotIn("untrusted.example", json.dumps(row))

    def test_wrong_identity_version_license_doi_fails_closed(self):
        for key, newval in (
            ("id", 25988294), ("id", True), ("version", 2), ("version", True),
            ("doi", "10.6084/m9.figshare.25988293.v2"),
            ("license", {"name": "CC BY-NC 4.0"}),
            ("license", {"name": "CC BY 4.0", "url": "https://bad.invalid/license"}),
        ):
            item = example()
            item[key] = newval
            with self.subTest(key=key, value=str(newval)), self.assertRaises(ProbeBlocked):
                inspect_metadata(encoded(item))

    def test_archive_file_count_size_id_md5_name_fails_closed(self):
        for changed in (
            lambda d: d["files"].pop(),
            lambda d: d["files"].append(d["files"][0]),
            lambda d: d["files"][0].update(name="GDW_v2.zip"),
            lambda d: d["files"][0].update(size=0),
            lambda d: d["files"][0].update(id=0),
            lambda d: d["files"][1].update(computed_md5="not-md5"),
            lambda d: d["files"][1].update(name=d["files"][0]["name"]),
        ):
            item = example()
            changed(item)
            with self.subTest(item=item["files"]), self.assertRaises(ProbeBlocked):
                inspect_metadata(encoded(item))

    def test_bad_json_duplicate_nonfinite_oversize_blocked(self):
        for raw in (
            b"", b"not json", b"\xff",
            b'{"id":25988293,"id":25988293}',
            b'{"a": NaN}', b'{"a": Infinity}', b"[]",
            b"x" * (MAX_BYTES + 1),
        ):
            with self.subTest(prefix=raw[:24]), self.assertRaises(ProbeBlocked):
                inspect_metadata(raw)

    def test_redirect_html_status_and_extra_bytes_rejected(self):
        for reply in (
            Reply(url="https://attacker.invalid"),
            Reply(media="text/html"),
            Reply(status=302),
            Reply(body=b"x" * (MAX_BYTES + 1)),
        ):
            with self.subTest(reply=reply.headers, reply_url=reply.url):
                with self.assertRaises(ProbeBlocked):
                    probe(open_request=lambda req, timeout: reply)

    def test_receipt_clock_must_be_timezone_aware(self):
        with self.assertRaises(ProbeBlocked):
            probe(open_request=lambda req, timeout: Reply(),
                  utc_clock=lambda: datetime(2026, 11, 4))


if __name__ == "__main__":
    unittest.main()
