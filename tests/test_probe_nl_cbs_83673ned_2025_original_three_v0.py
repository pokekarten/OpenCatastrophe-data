# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict offline checks for three fixed CBS original-response public GETs."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.probe_nl_cbs_83673ned_2025_original_three_v0 import (
    ACCESS_ID, BASE, BYTES_MAX, CBSDirectBlocked, EXPECTED, FIELDS,
    PERIOD, REGIONS, ROWS, SOURCE_ID, TIMEOUT,
    main, parse, probe, validate, verify_contract,
)


def payloads():
    out = {}
    for name in ("rental", "owner"):
        native = []
        for code, row in zip(REGIONS, ROWS[name]):
            entry = {
                "ID": row[0], "Perioden": PERIOD, "RegioS": code,
                "Eigendom": "A028867" if name == "rental" else "A028868",
            }
            entry.update(zip(FIELDS, row[1:]))
            native.append(entry)
        out[name] = json.dumps({"value": native}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    out["period"] = json.dumps({"value": [{
        "Key": "2025VJ06", "Title": "2024 juli - 2025 juni",
        "Status": "Definitief", "Description": "",
    }]}, separators=(",", ":")).encode("utf-8")
    return out


def synth_pins(data):
    return tuple(
        (name, url, len(data[name]), hashlib.sha256(data[name]).hexdigest())
        for name, url, _, _ in EXPECTED
    )


class Response:
    def __init__(self, url, raw, status=200, mime="application/json", encoding="identity"):
        self.url, self.raw, self.status = url, raw, status
        self.headers = {"Content-Type": mime, "Content-Encoding": encoding}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, n):
        return self.raw[:n]


class CBSThreeOriginalPublicProbeTests(unittest.TestCase):
    def test_exact_product_license_version_and_scope_gate(self):
        c = verify_contract()
        self.assertEqual(c["access_id"], ACCESS_ID)
        self.assertEqual(c["source_ids"], [SOURCE_ID])
        self.assertEqual(c["status"], "probe_ready")
        self.assertEqual(c["probe_contract"]["mode"], "provider_specific")
        self.assertEqual(c["probe_contract"]["operation"], "get_three_fixed_2025v06_rows")
        self.assertEqual(c["request_contract"]["allowed_operations"], ["get_three_fixed_2025v06_rows"])
        self.assertEqual(c["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(c["rights_and_policy"]["api_terms_status"], "separate_reviewed")
        self.assertEqual(c["rights_and_policy"]["commercial_automation_status"], "allowed")
        self.assertEqual(c["operational_constraints"]["retry_policy"], "none")
        self.assertEqual(c["operational_constraints"]["max_probe_bytes"], BYTES_MAX)
        self.assertEqual(c["operational_constraints"]["timeout_seconds"], TIMEOUT)

    def test_three_exact_urls_and_original_body_sha256_are_review_pinned(self):
        self.assertEqual(len(EXPECTED), 3)
        self.assertEqual(len({row[1] for row in EXPECTED}), 3)
        self.assertTrue(all(row[1].startswith(BASE) for row in EXPECTED))
        self.assertEqual([x[0] for x in EXPECTED], ["rental", "owner", "period"])
        self.assertIn("Eigendom%20eq%20%27A028867%27&$top=5", EXPECTED[0][1])
        self.assertIn("Eigendom%20eq%20%27A028868%27&$top=5", EXPECTED[1][1])
        self.assertTrue(EXPECTED[2][1].endswith("Key%20eq%20%272025VJ06%27&$top=1"))
        self.assertEqual([x[2] for x in EXPECTED], [1457, 1459, 234])
        self.assertEqual([x[3] for x in EXPECTED], [
            "70731cf7be6e73813059c250db9f1f21ad4024f0fb7cba5075ad8af666d90a5e",
            "7c9b9e307fd7fbf4ef8d5e9e26eaf3d9b9a991dd54a6b95c01409d22663c5908",
            "626dac3ab357839e615bcf0260237651d4a3983a88a0f18f6c8e3bfc24272c4d",
        ])
        self.assertTrue(all("$top=" in x[1] for x in EXPECTED))
        self.assertTrue(all(x[2] <= BYTES_MAX for x in EXPECTED))

    def test_no_network_without_explicit_live_three_flag(self):
        with self.assertRaises(SystemExit):
            main([])
        with self.assertRaises(SystemExit):
            main(["--live"])
        with self.assertRaises(SystemExit):
            main(["--host", "https://untrusted.example"])

    def test_all_three_synthetic_original_receipts_succeed_without_body_copy(self):
        data = payloads()
        calls = []

        def opener(req, timeout):
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(timeout, TIMEOUT)
            calls.append(req.full_url)
            name = {url: name for name, url, *_ in EXPECTED}[req.full_url]
            return Response(req.full_url, data[name])

        with patch("scripts.probe_nl_cbs_83673ned_2025_original_three_v0.EXPECTED", synth_pins(data)):
            result = probe(
                open_source=opener,
                now=lambda: datetime(2026, 11, 13, 20, 0, tzinfo=timezone.utc),
            )
        self.assertEqual(calls, [x[1] for x in EXPECTED])
        self.assertEqual(result["provider_original_response_count"], 3)
        self.assertFalse(result["remote_direct_runner_trusted"])
        self.assertFalse(result["original_provider_source_bodies_saved"])
        self.assertFalse(result["scientific_cat_model_input_approved"])
        self.assertFalse(result["insured_replacement_costs_inferred"])
        self.assertEqual(result["source_id"], SOURCE_ID)
        self.assertEqual(result["retrieval_utc"], "2026-11-13T20:00:00+00:00")
        self.assertEqual(len(result["original_response_provenance"]), 3)
        for receipt in result["original_response_provenance"]:
            self.assertEqual(receipt["original_response_http_status"], 200)
            self.assertEqual(len(receipt["original_body_sha256"]), 64)
            self.assertNotIn("original_body", receipt)
            self.assertNotIn("original_JSON", receipt)
        self.assertEqual(result["original_response_provenance"][0]["typed_public_source_summary"]["regional_mean_count"], 5)
        self.assertEqual(result["original_response_provenance"][2]["typed_public_source_summary"]["period_status"], "Definitief")

    def test_real_pinned_sha_diff_from_synthetic_body_must_fail(self):
        data = payloads()
        opens = []

        def opener(req, timeout):
            opens.append(req.full_url)
            return Response(req.full_url, data["rental"])

        self.assertRaises(CBSDirectBlocked, probe, open_source=opener)
        self.assertEqual(len(opens), 1)

    def test_cbs_odd_native_eur_m3_vs_m2_mapping_and_geo_spaces(self):
        data = payloads()
        rental = parse(data["rental"])
        checked = validate("rental", rental)
        self.assertEqual(checked["source_rows"][0]["avg_permitted_eur_m3"], 474)
        self.assertEqual(checked["source_rows"][0]["avg_permitted_eur_m2"], 1417)
        self.assertEqual(checked["source_rows"][0]["native_region"], "NL01  ")
        owner = parse(data["owner"])
        self.assertEqual(validate("owner", owner)["source_rows"][0]["avg_permitted_eur_m2"], 1221)
        wrong = deepcopy(rental)
        wrong[0]["GemiddeldeBouwkostenPerM_2"] = 1417
        wrong[0]["GemiddeldeBouwkostenPerM_3"] = 474
        self.assertRaises(CBSDirectBlocked, validate, "rental", wrong)
        wrong = deepcopy(rental)
        wrong[1]["RegioS"] = "LD01"
        self.assertRaises(CBSDirectBlocked, validate, "rental", wrong)

    def test_period_must_remain_final_not_provisional(self):
        period = parse(payloads()["period"])
        self.assertEqual(validate("period", period)["period_status"], "Definitief")
        wrong = deepcopy(period)
        wrong[0]["Status"] = "Voorlopig"
        self.assertRaises(CBSDirectBlocked, validate, "period", wrong)
        wrong = deepcopy(period)
        wrong[0]["Title"] = "2025 juli - 2026 juni"
        self.assertRaises(CBSDirectBlocked, validate, "period", wrong)

    def test_redirect_mime_compression_wrong_response_status_and_oversize(self):
        data = payloads()
        options = (
            {"status": 206},
            {"status": 302},
            {"mime": "text/html"},
            {"encoding": "gzip"},
        )
        for kw in options:
            def opener(req, timeout):
                return Response(req.full_url, data["rental"], **kw)
            with self.subTest(**kw):
                with patch("scripts.probe_nl_cbs_83673ned_2025_original_three_v0.EXPECTED", synth_pins(data)):
                    self.assertRaises(CBSDirectBlocked, probe, open_source=opener)

        def redirected(req, timeout):
            return Response(req.full_url + "/redirect", data["rental"])
        with patch("scripts.probe_nl_cbs_83673ned_2025_original_three_v0.EXPECTED", synth_pins(data)):
            self.assertRaises(CBSDirectBlocked, probe, open_source=redirected)

        def oversized(req, timeout):
            return Response(req.full_url, b"X" * (BYTES_MAX + 50))
        with patch("scripts.probe_nl_cbs_83673ned_2025_original_three_v0.EXPECTED", synth_pins(data)):
            self.assertRaises(CBSDirectBlocked, probe, open_source=oversized)

    def test_invalid_json_and_duplicate_original_keys_fail_closed(self):
        for raw in (b"", b"not-json", b'{"value":[],"value":[]}',
                    b'{"value":[NaN]}', b'{"value":[1e99999]}',
                    b'{"value":null}', b"\xff\xfe", b"x" * (BYTES_MAX + 1)):
            with self.subTest(raw=raw[:20]):
                self.assertRaises(CBSDirectBlocked, parse, raw)

    def test_rights_downgrade_or_silent_bulk_enable_is_blocked(self):
        c = verify_contract()
        for change in (
            ("rights_and_policy", "api_terms_status", "separate_unreviewed"),
            ("rights_and_policy", "commercial_automation_status", "unknown"),
            ("status", None, "documented_only"),
            ("request_contract", "allowed_operations", ["read_all_data_feed"]),
            ("operational_constraints", "max_probe_bytes", 100_000),
        ):
            changed = deepcopy(c)
            section, field, value = change
            if field is None:
                changed[section] = value
            else:
                changed[section][field] = value
            with tempfile.TemporaryDirectory() as d:
                file = Path(d) / "test.json"
                file.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(change=change):
                    self.assertRaises(Exception, verify_contract, file)


if __name__ == "__main__":
    unittest.main()
