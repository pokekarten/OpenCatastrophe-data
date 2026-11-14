# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline strict original-source CatRaRE W3/T5 rights/route SHA gate tests."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.validate_source_access import validate_path
from scripts.structured_public_views import render_structured_markdown
from scripts import probe_dwd_catrare_w3_range_v0 as runner
from tests.test_probe_dwd_catrare_w3_range_v0 import synthetic_prefix

ROOT = Path(__file__).resolve().parents[1]


class FakeRangeResponse:
    def __init__(self, raw: bytes, variant: str):
        self.status = 206
        self.url = runner.BASE + runner.ALLOWED[variant]["filename"]
        self.headers = {
            "Content-Type": "application/octet-stream",
            "Content-Encoding": "identity",
            "Content-Range": f"bytes 0-4095/{runner.ALLOWED[variant]['total_bytes']}",
            "Content-Length": str(len(raw)),
        }
        self.raw = raw

    def geturl(self):
        return self.url

    def read(self, count: int):
        return self.raw[:count]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, response: FakeRangeResponse):
        self.response = response
        self.requests = []

    def open(self, req, timeout):
        self.requests.append((req.full_url, req.get_method(), timeout, req.get_header("Range")))
        return self.response


class CatRaRESourceAccessGatesTests(unittest.TestCase):
    def test_two_exact_separate_contracts_and_generated_views(self):
        self.assertEqual(set(runner.ALLOWED), {"W3", "T5"})
        self.assertNotEqual(runner.KNOWN_PREFIX_SHA256["W3"], runner.KNOWN_PREFIX_SHA256["T5"])
        for variant in runner.ALLOWED:
            with self.subTest(variant=variant):
                cfg = runner.ALLOWED[variant]
                path = runner.verify_reviewed_contract(variant)
                self.assertEqual(path, ROOT / "access" / (cfg["source"] + ".json"))
                c = validate_path(path)
                self.assertEqual(c["source_ids"], [cfg["source"]])
                self.assertEqual(c["service_root"], runner.BASE.rstrip("/"))
                self.assertEqual(c["request_contract"]["path_templates"], ["/" + cfg["filename"]])
                self.assertEqual(c["operational_constraints"]["max_sample_bytes"], 4096)
                self.assertEqual(c["rights_and_policy"]["commercial_automation_status"], "allowed")
                self.assertEqual(c["rights_and_policy"]["api_terms_status"], "same_as_dataset")
                self.assertEqual(c["probe_contract"]["mode"], "provider_specific")
                self.assertEqual(c["probe_contract"]["operation"], "read_fixed_csv_prefix")
                self.assertIn(runner.KNOWN_PREFIX_SHA256[variant], c["operational_constraints"]["mutability_notes"])
                self.assertEqual(path.with_suffix(".md").read_text(encoding="utf-8"),
                                 render_structured_markdown(path, c, kind="access"))

    def test_rights_revocation_blocks_before_any_source_request(self):
        for variant in runner.ALLOWED:
            cfg = runner.ALLOWED[variant]
            real = validate_path(ROOT / "access" / (cfg["source"] + ".json"))
            for changed in ("commercial_automation_status", "api_terms_status", "path_templates", "max_probe_bytes"):
                fake = deepcopy(real)
                if changed == "commercial_automation_status":
                    fake["rights_and_policy"][changed] = "unknown"
                elif changed == "api_terms_status":
                    fake["rights_and_policy"][changed] = "unknown"
                elif changed == "path_templates":
                    fake["request_contract"][changed] = ["/another_release.csv"]
                else:
                    fake["operational_constraints"][changed] = 8192
                with (self.subTest(variant=variant, changed=changed),
                      patch.object(runner, "validate_path", return_value=fake),
                      patch.object(runner, "build_opener") as opener):
                    with self.assertRaises(runner.DWDRangeBlocked):
                        runner.probe(variant)
                    opener.assert_not_called()

    def test_explicit_live_only_not_default(self):
        with patch.object(runner, "probe") as probe:
            with self.assertRaises(SystemExit) as context:
                runner.main([])
            self.assertEqual(context.exception.code, 2)
            probe.assert_not_called()

    def test_wrong_or_missing_original_sha_is_blocked(self):
        for variant in runner.ALLOWED:
            with self.subTest(variant=variant):
                with self.assertRaises(runner.DWDRangeBlocked):
                    runner.verify_original_prefix_digest({"response_sha256": "0" * 64},
                                                         variant=variant)
                with self.assertRaises(runner.DWDRangeBlocked):
                    runner.verify_original_prefix_digest({}, variant=variant)
                runner.verify_original_prefix_digest(
                    {"response_sha256": runner.KNOWN_PREFIX_SHA256[variant]},
                    variant=variant,
                )

    def test_synthetic_correct_csv_cannot_impersonate_original_source(self):
        for variant in runner.ALLOWED:
            response = FakeRangeResponse(synthetic_prefix(variant), variant)
            fake_opener = FakeOpener(response)
            with self.subTest(variant=variant), patch.object(runner, "build_opener",
                                                            return_value=fake_opener):
                with self.assertRaisesRegex(runner.DWDRangeBlocked, "SHA-256 drift"):
                    runner.probe(variant)
            self.assertEqual(len(fake_opener.requests), 1)
            self.assertEqual(fake_opener.requests[0][0], runner.BASE + runner.ALLOWED[variant]["filename"])
            self.assertEqual(fake_opener.requests[0][3], runner.RANGE_HEADER)

    def test_non_identity_provider_bytes_are_rejected(self):
        for variant in runner.ALLOWED:
            response = FakeRangeResponse(synthetic_prefix(variant), variant)
            response.headers["Content-Encoding"] = "gzip"
            with self.subTest(variant=variant), patch.object(
                    runner, "build_opener", return_value=FakeOpener(response)):
                with self.assertRaisesRegex(runner.DWDRangeBlocked, "compressed"):
                    runner.probe(variant)

    def test_wrong_content_length_rejected(self):
        for variant in runner.ALLOWED:
            response = FakeRangeResponse(synthetic_prefix(variant), variant)
            response.headers["Content-Length"] = "1234"
            with self.subTest(variant=variant), patch.object(
                    runner, "build_opener", return_value=FakeOpener(response)):
                with self.assertRaisesRegex(runner.DWDRangeBlocked, "Content-Length"):
                    runner.probe(variant)


if __name__ == "__main__":
    unittest.main()
