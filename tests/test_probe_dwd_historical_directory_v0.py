# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic DWD directory source-contract and payload regression tests."""
from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.acquire_dwd_extreme_wind_receipt import FILENAME as FROZEN_ARCHIVE
from scripts.probe_dwd_historical_directory_v0 import (
    DirectoryBlocked, SOURCE, URL, inspect_index, reviewed_contract, run_probe,
)


SECOND = "10minutenwerte_extrema_wind_00011_20200101_20251231_hist.zip"
THIRD = "10minutenwerte_extrema_wind_00090_20000101_20091231_hist.zip"


def html(*files: str) -> bytes:
    links = "".join(f'<a href="{name}">{name}</a>\n' for name in files)
    return ("<!doctype html><html><body>" + links + "</body></html>").encode("ascii")


def contract():
    return {
        "access_id": SOURCE,
        "status": "probe_ready",
        "interface_type": "http_file",
        "service_root": URL.removesuffix("/historical/"),
        "authentication": {"mode": "none"},
        "probe_contract": {"requires_credentials": False, "operation": "inspect_historical_directory"},
        "request_contract": {
            "allowed_operations": ["inspect_historical_directory"],
            "path_templates": ["/historical/"],
        },
        "rights_and_policy": {"commercial_automation_status": "allowed"},
        "operational_constraints": {"max_probe_bytes": 1048576, "timeout_seconds": 60},
    }


class Response(io.BytesIO):
    status = 200

    def __init__(self, body: bytes, *, url: str = URL, headers=None, status=200):
        super().__init__(body)
        self._url = url
        self.headers = headers if headers is not None else {
            "Content-Type": "text/html",
            "Content-Length": str(len(body)),
        }
        self.status = status

    def geturl(self):
        return self._url


class Client:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def open(self, request, *, timeout):
        self.calls.append((request.full_url, request.get_method(), timeout))
        return self.response


class DwdDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "access").mkdir()
        self.write_contract()

    def write_contract(self, mutate=None):
        value = contract()
        if mutate:
            mutate(value)
        (self.root / "access" / (SOURCE + ".json")).write_text(json.dumps(value))

    def test_valid_index_retains_exact_archive_identity_and_date_span(self):
        result = inspect_index(html(FROZEN_ARCHIVE, SECOND, THIRD))
        self.assertEqual(result["historical_archive_link_count"], 3)
        self.assertEqual(result["unique_station_ids"], 3)
        self.assertEqual(result["earliest_filename_coverage_start"], "2000-01-01")
        self.assertEqual(result["latest_filename_coverage_end"], "2025-12-31")
        self.assertTrue(result["existing_station_00003_archive_found"])

    def test_checked_in_dwd_contract_matches_the_reviewed_live_route(self):
        """Ensure a real provider probe is never run using stale review fixtures."""
        repo_root = Path(__file__).resolve().parents[1]
        max_bytes, timeout, contract_digest = reviewed_contract(repo_root)
        self.assertLessEqual(max_bytes, 1_048_576)
        self.assertGreater(timeout, 0)
        self.assertEqual(len(contract_digest), 64)

    def test_previous_pinned_archive_must_be_present(self):
        with self.assertRaisesRegex(DirectoryBlocked, "previously pinned"):
            inspect_index(html(SECOND, THIRD))

    def test_reject_bad_dates_duplicates_and_unreviewed_links(self):
        bad = [
            "10minutenwerte_extrema_wind_00011_20230230_20231231_hist.zip",
            "10minutenwerte_extrema_wind_00011_20231231_20230101_hist.zip",
            "10minutenwerte_extrema_wind_00011_20200101_20251231_hist.zip?download=1",
            "10minutenwerte_extrema_wind_00011_20200101_20251231_hist.zip/../other",
            "10minutenwerte_extrema_wind_00011_20200101_20251231_hist.zip%2f",
            "10minutenwerte_extrema_wind_00011_20200101_20251231_hist.zip#x",
        ]
        for filename in bad:
            with self.subTest(filename=filename):
                result = inspect_index(html(FROZEN_ARCHIVE, filename))
                self.assertEqual(result["historical_archive_link_count"], 1)
                self.assertEqual(result["quarantined_link_count"], 1)
                self.assertTrue(result["existing_station_00003_archive_found"])
        result = inspect_index(html(FROZEN_ARCHIVE, FROZEN_ARCHIVE))
        self.assertEqual(result["historical_archive_link_count"], 1)
        self.assertEqual(result["quarantined_link_reasons"]["duplicate_archive_identity"], 1)

    def test_valid_archive_kept_while_bad_interval_quarantined(self):
        reversed_date = "10minutenwerte_extrema_wind_01234_20250101_20200101_hist.zip"
        result = inspect_index(html(FROZEN_ARCHIVE, SECOND, reversed_date, FROZEN_ARCHIVE))
        self.assertEqual(result["historical_archive_link_count"], 2)
        self.assertEqual(result["quarantined_link_reasons"]["reversed_date_interval"], 1)
        self.assertEqual(result["quarantined_link_reasons"]["duplicate_archive_identity"], 1)
        self.assertEqual(result["archive_links_examined"], 4)

    def test_random_links_do_not_become_archive_candidates(self):
        result = inspect_index(html(FROZEN_ARCHIVE, "../", "?C=N;O=D", "description.txt"))
        self.assertEqual(result["historical_archive_link_count"], 1)

    def test_strict_utf8(self):
        with self.assertRaises(DirectoryBlocked):
            inspect_index(b"\xff" + html(FROZEN_ARCHIVE))

    def test_contract_rejects_scope_rights_or_credentials_drift(self):
        mutations = [
            lambda d: d.update(status="documented_only"),
            lambda d: d.update(interface_type="rest"),
            lambda d: d.update(service_root="https://untrusted.invalid"),
            lambda d: d["authentication"].update(mode="token"),
            lambda d: d["probe_contract"].update(requires_credentials=True),
            lambda d: d["probe_contract"].update(operation="fetch_exact_historical_file"),
            lambda d: d["request_contract"].update(path_templates=["/recent/"]),
            lambda d: d["rights_and_policy"].update(commercial_automation_status="restricted"),
            lambda d: d["operational_constraints"].update(max_probe_bytes=10485760),
            lambda d: d["operational_constraints"].update(timeout_seconds=400),
        ]
        for mutate in mutations:
            with self.subTest(change=repr(mutate)):
                self.write_contract(mutate)
                with self.assertRaises(DirectoryBlocked):
                    reviewed_contract(self.root)

    def test_reject_duplicate_json_keys_in_access_contract(self):
        path = self.root / "access" / (SOURCE + ".json")
        path.write_text('{"access_id":"first","access_id":"second"}')
        with self.assertRaises(DirectoryBlocked):
            reviewed_contract(self.root)

    def test_receipt_only_no_source_archive_download(self):
        raw = html(FROZEN_ARCHIVE, SECOND)
        client = Client(Response(raw))
        receipt = run_probe(self.root, opener=client)
        self.assertEqual(client.calls, [(URL, "GET", 60)])
        self.assertEqual(receipt["historical_archive_link_count"], 2)
        self.assertEqual(receipt["directory_response_bytes"], len(raw))
        for key in ("directory_response_sha256", "probe_code_sha256", "access_contract_sha256"):
            self.assertEqual(len(receipt[key]), 64)
        self.assertEqual(receipt["original_archives_downloaded"], 0)
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["model_input_approved"])
        self.assertNotIn(raw.decode(), json.dumps(receipt))

    def test_reject_response_type_status_redirect_and_length(self):
        raw = html(FROZEN_ARCHIVE)
        replies = [
            Response(raw, status=302),
            Response(raw, url="https://untrusted.invalid/"),
            Response(raw, headers={"Content-Type": "application/zip"}),
            Response(raw, headers={"Content-Type": "text/html", "Content-Encoding": "gzip"}),
            Response(raw, headers={"Content-Type": "text/html", "Content-Length": "5000000"}),
            Response(raw, headers={"Content-Type": "text/html", "Content-Length": "123"}),
            Response(b"x" * (1048576 + 1)),
        ]
        for reply in replies:
            with self.subTest(reply=reply.headers), self.assertRaises(DirectoryBlocked):
                run_probe(self.root, opener=Client(reply))


if __name__ == "__main__":
    unittest.main()
