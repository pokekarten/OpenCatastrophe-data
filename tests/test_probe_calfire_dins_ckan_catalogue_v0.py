# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only negative tests; no CAL FIRE API access on pull requests."""
from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import hashlib
from http.client import IncompleteRead
import json
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch

from scripts import probe_calfire_dins_ckan_catalogue_v0 as p
from scripts.preflight_calfire_dins_ckan_catalogue_v0 import (
    DATASET_UUID, FROZEN_RESOURCES, METADATA_MODIFIED, PACKAGE_SLUG,
)


def fixture() -> bytes:
    return json.dumps({
        "success": True,
        "result": {
            "id": DATASET_UUID, "name": PACKAGE_SLUG, "license_id": "cc-by",
            "metadata_modified": p.CURRENT_METADATA_MODIFIED, "accessLevel": "public",
            "isopen": True,
            "resources": [{"id": k, "format": v, "url": "https://invalid.test/do-not-follow"}
                          for k, v in FROZEN_RESOURCES.items()],
            "contact_email": "synthetic-should-not-appear@invalid.test",
        },
    }, sort_keys=True).encode("utf-8")


class FakeResponse:
    def __init__(self, raw=None, status=200, media="application/json; charset=utf-8", declared=None,
                 url=p.ENDPOINT, encoding=None):
        self.raw = fixture() if raw is None else raw
        self.status = status
        self.url = url
        self.headers = {"Content-Type": media}
        if declared is not None:
            self.headers["Content-Length"] = declared
        if encoding is not None:
            self.headers["Content-Encoding"] = encoding

    def geturl(self):
        return self.url

    def read(self, count):
        return self.raw[:count]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, req, timeout):
        self.requests.append((req, timeout))
        return self.response


class CalFireDinsCkanMetadataTests(TestCase):
    def test_contract_is_scoped_to_one_metadata_only_operation(self):
        p.verify_reviewed_contract()

    def test_contract_rejects_stale_response_version_before_network(self):
        original = p.validate_contract

        def stale(path):
            c = original(path)
            c["response_contract"]["format"] = c["response_contract"]["format"].replace(
                p.CURRENT_METADATA_MODIFIED, "2026-10-21T20:55:50.264159"
            )
            return c

        with patch.object(p, "validate_contract", side_effect=stale):
            with self.assertRaisesRegex(p.CkanProbeBlocked, "contract changed"):
                p.verify_reviewed_contract()

    def test_valid_synthetic_receipt_one_read_no_private_fields(self):
        opener = FakeOpener(FakeResponse())
        out = p.probe_one(opener=opener)
        self.assertEqual(len(opener.requests), 1)
        req, timeout = opener.requests[0]
        self.assertEqual(req.full_url, p.ENDPOINT)
        self.assertEqual(req.get_method(), "GET")
        self.assertEqual(timeout, 30)
        self.assertIn("OpenCatastrophe-data", req.get_header("User-agent"))
        self.assertEqual(out["source_resource_count"], 11)
        self.assertEqual(out["response_bytes"], len(fixture()))
        self.assertEqual(len(out["response_sha256"]), 64)
        self.assertFalse(out["external_bytes_persisted"])
        self.assertFalse(out["model_input_approved"])
        self.assertEqual(out["individual_damage_features_read"], 0)
        self.assertNotIn("invalid.test", json.dumps(out))
        self.assertNotIn("contact_email", json.dumps(out))

    def test_reject_wrong_http_status(self):
        with self.assertRaises(p.CkanProbeBlocked):
            p.probe_one(FakeOpener(FakeResponse(status=206)))

    def test_reject_wrong_media(self):
        with self.assertRaises(p.CkanProbeBlocked):
            p.probe_one(FakeOpener(FakeResponse(media="text/html")))

    def test_reject_declared_too_large(self):
        with self.assertRaises(p.CkanProbeBlocked):
            p.probe_one(FakeOpener(FakeResponse(declared=str(p.MAX_BYTES + 1))))

    def test_reject_declared_body_length_mismatch(self):
        for length in (len(fixture()) - 1, len(fixture()) + 1):
            with self.subTest(length=length):
                with self.assertRaises(p.CkanProbeBlocked):
                    p.probe_one(FakeOpener(FakeResponse(declared=str(length))))

    def test_exact_content_length_is_accepted(self):
        opener = FakeOpener(FakeResponse(declared=str(len(fixture())), encoding="identity"))
        self.assertEqual(p.probe_one(opener)["response_bytes"], len(fixture()))
        self.assertEqual(opener.requests[0][0].get_header("Accept-encoding"), "identity")

    def test_wrong_response_url_and_content_encoding_block(self):
        for response in (FakeResponse(url="https://invalid.test/wrong"),
                         FakeResponse(encoding="gzip"), FakeResponse(declared="١٥٥٥")):
            with self.subTest(headers=response.headers, url=response.url):
                with self.assertRaises(p.CkanProbeBlocked):
                    p.probe_one(FakeOpener(response))

    def test_incomplete_http_read_fails_closed(self):
        response = FakeResponse()
        with patch.object(response, "read", side_effect=IncompleteRead(b"{}", 4)):
            with self.assertRaises(p.CkanProbeBlocked):
                p.probe_one(FakeOpener(response))

    def test_receipt_binds_contract_snapshot(self):
        original = p.CONTRACT_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.json"
            path.write_bytes(original)

            class ChangingOpener(FakeOpener):
                def open(self, req, timeout):
                    path.write_bytes(b"{}")
                    return super().open(req, timeout)

            with patch.object(p, "CONTRACT_PATH", path):
                out = p.probe_one(ChangingOpener(FakeResponse()))
            self.assertEqual(out["contract_sha256"], hashlib.sha256(original).hexdigest())
            self.assertNotEqual(out["contract_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_reject_actual_too_large(self):
        with self.assertRaises(p.CkanProbeBlocked):
            p.probe_one(FakeOpener(FakeResponse(raw=b"x" * (p.MAX_BYTES + 5))))

    def test_reject_pinned_package_modified(self):
        x = json.loads(fixture())
        x["result"]["metadata_modified"] = "2026-11-12T00:00:00"
        with self.assertRaises(ValueError):
            p.probe_one(FakeOpener(FakeResponse(raw=json.dumps(x).encode())))

    def test_historical_october_vintage_is_not_current(self):
        x = json.loads(fixture())
        x['result']['metadata_modified'] = METADATA_MODIFIED
        with self.assertRaises(ValueError):
            p.probe_one(FakeOpener(FakeResponse(raw=json.dumps(x).encode())))

    def test_current_version_receipt_does_not_claim_historical_parity(self):
        out = p.probe_one(FakeOpener(FakeResponse()))
        self.assertEqual(out['source_package_modified'], p.CURRENT_METADATA_MODIFIED)
        self.assertFalse(out['historical_original_sha256_matches'])
        self.assertFalse(out['reviewed_20261112_response_sha256_matches'])
    def test_reject_resource_identity_drift(self):
        x = json.loads(fixture())
        x["result"]["resources"][0]["id"] = "changed"
        with self.assertRaises(ValueError):
            p.probe_one(FakeOpener(FakeResponse(raw=json.dumps(x).encode())))

    def test_denied_rights_fail_without_network(self):
        original = p.validate_contract

        def blocked(path):
            c = original(path)
            c["rights_and_policy"]["commercial_automation_status"] = "unknown"
            return c

        with patch.object(p, "validate_contract", side_effect=blocked):
            with self.assertRaisesRegex(p.CkanProbeBlocked, "contract changed"):
                p.probe_one(FakeOpener(FakeResponse()))

    def test_no_network_by_default(self):
        with redirect_stderr(StringIO()) as err, patch.object(p, "probe_one") as probe:
            code = p.main([])
        self.assertEqual(code, 2)
        probe.assert_not_called()
        self.assertIn("BLOCKED", err.getvalue())

    def test_url_cannot_be_redirected(self):
        with self.assertRaises(p.CkanProbeBlocked):
            p.NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://evil.invalid")

    def test_failed_provider_text_does_not_leak(self):
        with patch.object(p, "probe_one", side_effect=p.CkanProbeBlocked("PRIVATE_PROVIDER_CONTACT")), redirect_stderr(StringIO()) as out:
            code = p.main(["--live"])
        self.assertEqual(code, 2)
        self.assertNotIn("PRIVATE_PROVIDER_CONTACT", out.getvalue())


if __name__ == "__main__":
    import unittest
    unittest.main()
