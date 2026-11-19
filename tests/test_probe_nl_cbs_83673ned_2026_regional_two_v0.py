# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression of 2x5 actual CBS regional 2026 OData proof.

CI never acquires original CBS data except the reviewed separate PR-only
live job after these offline checks. Faked provider data cannot be admitted.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib import request

from scripts.probe_nl_cbs_83673ned_2026_regional_two_v0 import (
    ACCESS_ID, CBS2026RegionalBlocked, CONTRACT, FIELDS, MAX_BYTES, NATIVE,
    OPERATION, ORIGINAL, PERIOD, REGIONS, SOURCE_ID, TIMEOUT, _direct_get,
    main, parse_original, prove, validate_native, verify_contract,
)


def fake_public_sources():
    rows = {}
    for tenure in ("rental", "owner"):
        native_tenure = {"rental": "A028867", "owner": "A028868"}[tenure]
        out = []
        for region, rec in zip(REGIONS, NATIVE[tenure]):
            row = {
                "ID": rec[0],
                "RegioS": region,
                "Perioden": PERIOD,
                "Eigendom": native_tenure,
            }
            row.update(zip(FIELDS, rec[1:]))
            out.append(row)
        rows[tenure] = json.dumps(
            {"value": out}, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    return rows


def fake_pins(payloads):
    return tuple(
        (name, url, len(payloads[name]), hashlib.sha256(payloads[name]).hexdigest())
        for name, url, _, _ in ORIGINAL
    )


class Response:
    def __init__(self, url, raw, *, status=200, media="application/json", content_encoding="identity"):
        self.url, self.raw, self.status = url, raw, status
        self.headers = {"Content-Type": media, "Content-Encoding": content_encoding}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, n):
        return self.raw[:n]


class CBSRegionalDirectOriginalTests(unittest.TestCase):
    def test_contract_exact_two_request_rights_no_secrets(self):
        c = verify_contract()
        self.assertEqual(c["access_id"], ACCESS_ID)
        self.assertEqual(c["source_ids"], [SOURCE_ID])
        self.assertEqual(c["status"], "probe_ready")
        self.assertEqual(c["interface_type"], "rest")
        self.assertEqual(c["probe_contract"]["operation"], OPERATION)
        self.assertEqual(c["request_contract"]["allowed_operations"], [OPERATION])
        self.assertEqual(
            c["request_contract"]["path_templates"],
            ["/ODataApi/OData/83673NED/TypedDataSet"],
        )
        self.assertEqual(c["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(c["rights_and_policy"]["api_terms_status"], "separate_reviewed")
        self.assertEqual(c["rights_and_policy"]["commercial_automation_status"], "allowed")
        self.assertEqual(c["operational_constraints"]["max_probe_bytes"], MAX_BYTES)
        self.assertEqual(c["operational_constraints"]["timeout_seconds"], TIMEOUT)
        self.assertEqual(c["operational_constraints"]["retry_policy"], "none")
        self.assertEqual(c["authentication"]["mode"], "none")
        self.assertFalse(c["authentication"]["secret_in_repository"])

    def test_only_two_exact_urls_sha_bytes_reviewed(self):
        self.assertEqual([p[0] for p in ORIGINAL], ["rental", "owner"])
        self.assertEqual([p[2] for p in ORIGINAL], [1457, 1459])
        self.assertEqual([p[3] for p in ORIGINAL], [
            "2b224f3f6546f7c5f5905a6b226a3471c986eaf2d7cd16b7001f720ff26e9fe0",
            "67a2647fc84a812569caf0d128d1b7f7cd8a3d8e2f427fc2ebe28ab68ed39ed3",
        ])
        self.assertEqual(len({p[1] for p in ORIGINAL}), 2)
        self.assertTrue(all(p[1].startswith("https://opendata.cbs.nl/ODataApi/OData/83673NED/TypedDataSet?") for p in ORIGINAL))
        self.assertIn("Eigendom%20eq%20%27A028867%27&$top=5", ORIGINAL[0][1])
        self.assertIn("Eigendom%20eq%20%27A028868%27&$top=5", ORIGINAL[1][1])
        self.assertTrue(all("2026VJ06" in x[1] and "$top=5" in x[1] for x in ORIGINAL))

    def test_urllib_direct_open_is_get_with_keyword_timeout_not_post_data(self):
        call = []
        marker = object()

        class FakeOpener:
            def open(self, req, *args, **kwargs):
                call.append((req, args, kwargs))
                return marker

        req = request.Request(ORIGINAL[0][1], method="GET")
        with patch(
            "scripts.probe_nl_cbs_83673ned_2026_regional_two_v0.request.build_opener",
            return_value=FakeOpener(),
        ):
            result = _direct_get(req, TIMEOUT)
        self.assertIs(result, marker)
        self.assertEqual(len(call), 1)
        self.assertEqual(call[0][0].get_method(), "GET")
        self.assertEqual(call[0][1], ())
        self.assertEqual(call[0][2], {"timeout": TIMEOUT})

    def test_original_synthetic_five_by_two_passes_without_saving_originals(self):
        fake = fake_public_sources()
        calls = []
        def fake_open(req, timeout):
            self.assertEqual(timeout, TIMEOUT)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(req.get_header("Accept"), "application/json")
            self.assertEqual(req.get_header("Accept-encoding"), "identity")
            calls.append(req.full_url)
            key = {url: name for name, url, _, _ in ORIGINAL}[req.full_url]
            return Response(req.full_url, fake[key])
        with patch("scripts.probe_nl_cbs_83673ned_2026_regional_two_v0.ORIGINAL", fake_pins(fake)):
            p = prove(
                open_request=fake_open,
                clock=lambda: datetime(2026, 11, 14, 9, 20, tzinfo=timezone.utc),
            )
        self.assertEqual(calls, [x[1] for x in ORIGINAL])
        self.assertEqual(p["original_usable_public_response_count"], 2)
        self.assertEqual(p["official_period"], "2026VJ06")
        self.assertEqual(p["period_status_from_independent_nine_originals"], "Voorlopig")
        self.assertEqual(p["retrieved_at_utc"], "2026-11-14T09:20:00+00:00")
        self.assertFalse(p["response_original_json_persisted"])
        self.assertFalse(p["trusted_runner_self_attested"])
        self.assertFalse(p["scientific_cat_model_input_approved"])
        self.assertFalse(p["insurance_rebuilding_tiv_approved"])
        self.assertEqual(len(p["direct_original_response_provenance"]), 2)
        for item in p["direct_original_response_provenance"]:
            self.assertEqual(item["direct_original_http_status"], 200)
            self.assertEqual(len(item["public_native_aggregates"]), 5)
            self.assertNotIn("raw_original_json", item)
            self.assertEqual(len(item["original_complete_body_sha256"]), 64)

    def test_real_original_sha_pin_does_not_match_synthetic_bytes(self):
        calls = []
        fake = fake_public_sources()
        def fake_open(req, timeout):
            calls.append(req.full_url)
            return Response(req.full_url, fake["rental"])
        self.assertRaises(CBS2026RegionalBlocked, prove, open_request=fake_open)
        self.assertEqual(len(calls), 1)

    def test_native_m3_m2_unit_trap_and_region_spacings(self):
        fake = fake_public_sources()
        rental = parse_original(fake["rental"])
        owner = parse_original(fake["owner"])
        a = validate_native("rental", rental)
        b = validate_native("owner", owner)
        self.assertEqual(a[0]["published_eur_per_m3"], 488)
        self.assertEqual(a[0]["published_eur_per_m2"], 1473)
        self.assertEqual(b[0]["published_eur_per_m3"], 438)
        self.assertEqual(b[0]["published_eur_per_m2"], 1297)
        self.assertEqual(a[0]["original_region_code"], "NL01  ")
        self.assertEqual(b[-1]["original_region_code"], "LD04  ")
        inverted = deepcopy(rental)
        inverted[0][FIELDS[1]], inverted[0][FIELDS[2]] = inverted[0][FIELDS[2]], inverted[0][FIELDS[1]]
        self.assertRaises(CBS2026RegionalBlocked, validate_native, "rental", inverted)
        wrong_region = deepcopy(rental)
        wrong_region[1]["RegioS"] = "LD01"
        self.assertRaises(CBS2026RegionalBlocked, validate_native, "rental", wrong_region)
        wrong_status = deepcopy(owner)
        wrong_status[0]["Perioden"] = "2025VJ06"
        self.assertRaises(CBS2026RegionalBlocked, validate_native, "owner", wrong_status)
        duplicate = deepcopy(owner)
        duplicate[3]["RegioS"] = duplicate[2]["RegioS"]
        self.assertRaises(CBS2026RegionalBlocked, validate_native, "owner", duplicate)

    def test_response_http_content_and_original_full_bytes_fail_closed(self):
        fake = fake_public_sources()
        tests = (
            {"status": 206}, {"status": 302}, {"media": "text/html"},
            {"content_encoding": "gzip"},
        )
        for changes in tests:
            def opened(req, timeout):
                return Response(req.full_url, fake["rental"], **changes)
            with self.subTest(changes=changes), patch(
                "scripts.probe_nl_cbs_83673ned_2026_regional_two_v0.ORIGINAL",
                fake_pins(fake),
            ):
                self.assertRaises(CBS2026RegionalBlocked, prove, open_request=opened)
        def redirected(req, timeout):
            return Response(req.full_url+"/redirect", fake["rental"])
        with patch("scripts.probe_nl_cbs_83673ned_2026_regional_two_v0.ORIGINAL", fake_pins(fake)):
            self.assertRaises(CBS2026RegionalBlocked, prove, open_request=redirected)
        def too_big(req, timeout):
            return Response(req.full_url, b"A" * (MAX_BYTES + 100))
        with patch("scripts.probe_nl_cbs_83673ned_2026_regional_two_v0.ORIGINAL", fake_pins(fake)):
            self.assertRaises(CBS2026RegionalBlocked, prove, open_request=too_big)

    def test_untrusted_json_duplicate_key_nonfinite_wrong_shape(self):
        for raw in (
            b"", b"not-json", b'{"value":[],"value":[]}',
            b'{"value":[NaN]}', b'{"value":[1e9999]}',
            b'{"value":[false]}', b'{"value":null}', b"\xff", b"A"*(MAX_BYTES + 1),
        ):
            with self.subTest(body=raw[:20]):
                self.assertRaises(CBS2026RegionalBlocked, parse_original, raw)

    def test_no_provider_access_without_explicit_nonabbreviated_cli_option(self):
        with self.assertRaises(SystemExit):
            main([])
        with self.assertRaises(SystemExit):
            main(["--live"])
        with self.assertRaises(SystemExit):
            main(["--host", "untrusted.example"])

    def test_rights_downgrade_or_unlimited_approval_stops_runner(self):
        orig = verify_contract()
        changes = [
            ("rights_and_policy", "api_terms_status", "separate_unreviewed"),
            ("rights_and_policy", "commercial_automation_status", "unknown"),
            ("status", None, "documented_only"),
            ("probe_contract", "operation", "generic_unbounded_odata"),
            ("request_contract", "allowed_operations", ["all_table_rows"]),
            ("operational_constraints", "max_probe_bytes", 900000),
        ]
        for group, prop, val in changes:
            changed = deepcopy(orig)
            if prop is None:
                changed[group] = val
            else:
                changed[group][prop] = val
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "contract.json"
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(change=(group, prop, val)):
                    self.assertRaises(Exception, verify_contract, path)


if __name__ == "__main__":
    unittest.main()
