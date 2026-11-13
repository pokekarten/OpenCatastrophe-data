# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline original-response checks; NO provider HTTP requests."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import unittest

from scripts.probe_nl_cbs_83673ned_v0 import (
    BASE, CBS83673Blocked, EXPECTED_PROPERTIES, MAX_BYTES, OBJECTS,
    PRICE_FIELDS, REGIONS, TENURES, TIMEOUT,
    parse_original, probe, validate_rows, verify_contract,
)


def fixture():
    return {
        "table": {"value": [{
            "ID": 0,
            "Identifier": "83673NED", "Source": "CBS.",
            "Modified": "2026-08-20T02:00:00", "Frequency": "Perkwartaal",
            "Title": "Bouwvergunningen; kerncijfers nieuwbouwwoningen; bouwkosten, inhoud, regio",
            "Description": "zuivere nieuwe woningen vanaf 50 duizend euro, exclusief BTW",
        }]},
        "historic_rental": {"value": [{
            "ID": 0, "RegioS": "NL01  ", "Eigendom": "A028867", "Perioden": "2012VJ12",
            "GemiddeldeBouwkostenPerWoning_1": 95,
            "GemiddeldeBouwkostenPerM_2": 258,
            "GemiddeldeBouwkostenPerM_3": 748,
            "GemiddeldeInhoudWoningen_4": 370,
            "GemiddeldeOppervlakteVanWoningen_5": 127,
        }]},
        "properties": {"value": [
            {"Key": "Eigendom", "Type": "Dimension"},
            {"Key": "RegioS", "Type": "GeoDimension"},
            {"Key": "Perioden", "Type": "TimeDimension"},
            *(
                {"Key": key, "Unit": EXPECTED_PROPERTIES[key][0],
                 "Title": EXPECTED_PROPERTIES[key][1], "Type": "Topic"}
                for key in PRICE_FIELDS
            ),
        ]},
        "tenures": {"value": [
            {"Key": key, "Title": value}
            for key, value in TENURES.items()
        ]},
        "regions": {"value": [
            {"Key": key, "Title": value}
            for key, value in REGIONS.items()
        ]},
        "historic_period": {"value": [{
            "Key": "2012VJ12", "Title": "2012 januari - 2012 december",
            "Status": "Definitief",
        }]},
        "recent_rental": {"value": [{
            "ID": 54, "RegioS": "NL01  ", "Eigendom": "A028867", "Perioden": "2026VJ06",
            "GemiddeldeBouwkostenPerWoning_1": 149,
            "GemiddeldeBouwkostenPerM_2": 488,
            "GemiddeldeBouwkostenPerM_3": 1473,
            "GemiddeldeInhoudWoningen_4": 306,
            "GemiddeldeOppervlakteVanWoningen_5": 101,
        }]},
        "recent_period": {"value": [{
            "Key": "2026VJ06", "Title": "2025 juli - 2026 juni",
            "Status": "Voorlopig",
        }]},
        "recent_owner": {"value": [{
            "ID": 329, "RegioS": "NL01  ", "Eigendom": "A028868", "Perioden": "2026VJ06",
            "GemiddeldeBouwkostenPerWoning_1": 215,
            "GemiddeldeBouwkostenPerM_2": 438,
            "GemiddeldeBouwkostenPerM_3": 1297,
            "GemiddeldeInhoudWoningen_4": 490,
            "GemiddeldeOppervlakteVanWoningen_5": 165,
        }]},
    }


class Response:
    def __init__(self, url, data, *, status=200, mime="application/json", encoding="identity"):
        self.url, self.data, self.status = url, data, status
        self.headers = {"Content-Type": mime, "Content-Encoding": encoding}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, n):
        return self.data[:n]


def fake_opener(documents, *, status=200, mime="application/json",
                wrong_url=False, encoding="identity"):
    calls = []

    def opened(req, timeout):
        calls.append((req.full_url, timeout))
        named = [name for name, url in OBJECTS if url == req.full_url]
        if len(named) != 1:
            raise AssertionError("unreviewed extra provider path")
        name = named[0]
        raw = json.dumps(documents[name], sort_keys=True).encode("utf-8")
        return Response(
            req.full_url + "/redirect" if wrong_url else req.full_url, raw,
            status=status, mime=mime, encoding=encoding,
        )

    return opened, calls


class CBS83673DirectProbeTests(unittest.TestCase):
    def test_exact_contract_and_frozen_immutable_host_paths(self):
        c = verify_contract()
        self.assertEqual(c["status"], "probe_ready")
        self.assertEqual(c["source_ids"],
                         ["nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned"])
        self.assertEqual(c["probe_contract"]["mode"], "provider_specific")
        self.assertEqual(c["probe_contract"]["operation"], "nine_fixed_83673ned_odata_rows")
        self.assertEqual(c["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(c["rights_and_policy"]["commercial_automation_status"], "allowed")
        self.assertEqual(c["operational_constraints"]["retry_policy"], "none")
        self.assertEqual(MAX_BYTES, 16384)
        self.assertEqual(TIMEOUT, 30)
        self.assertEqual(len(OBJECTS), 9)
        self.assertTrue(all(url.startswith(BASE) for _, url in OBJECTS))
        self.assertTrue(all("$top=" in url for _, url in OBJECTS))
        self.assertIn("NL01%20%20", OBJECTS[-1][1])
        self.assertEqual(len(set(url for _, url in OBJECTS)), 9)

    def test_synthetic_nine_full_body_proofs_without_source_payloads(self):
        data = fixture()
        opened, calls = fake_opener(data)
        result = probe(open_request=opened, utc_clock=lambda: datetime(
            2026, 11, 13, 17, 12, tzinfo=timezone.utc,
        ))
        self.assertEqual(len(calls), 9)
        self.assertEqual([url for url, _ in calls], [u for _, u in OBJECTS])
        self.assertTrue(all(t == 30 for _, t in calls))
        self.assertTrue(result["verified_exact_direct_response_http"])
        self.assertFalse(result["trusted_github_runner_attestation"])
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["source_original_bodies_saved"])
        self.assertFalse(result["regional_data_retrieved"])
        self.assertFalse(result["insured_replacement_values_approved"])
        values = result["source_values"]
        self.assertEqual(values["national_rental_2026"]["average_eur_per_m3"], 488)
        self.assertEqual(values["national_rental_2026"]["average_eur_per_m2"], 1473)
        self.assertEqual(values["national_owner_2026"]["average_eur_per_m3"], 438)
        self.assertEqual(values["national_owner_2026"]["average_eur_per_m2"], 1297)
        self.assertEqual(values["national_rental_2012"]["average_per_dwelling_eur_thousands"], 95)
        self.assertEqual(len(result["original_response_provenance"]), 9)
        for name, url in OBJECTS:
            raw = json.dumps(data[name], sort_keys=True).encode("utf-8")
            receipt = result["original_response_provenance"][name]
            self.assertEqual(receipt["exact_source_url"], url)
            self.assertEqual(receipt["full_original_body_bytes"], len(raw))
            self.assertEqual(receipt["full_original_body_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertNotIn("value", receipt)

    def test_source_unit_columns_cannot_be_swapped(self):
        changed = fixture()
        props = changed["properties"]["value"]
        props[4]["Title"] = "Gemiddelde bouwkosten per m²"
        props[5]["Title"] = "Gemiddelde bouwkosten per m³"
        self.assertRaises(CBS83673Blocked, validate_rows, changed)
        changed = fixture()
        changed["recent_rental"]["value"][0]["GemiddeldeBouwkostenPerM_2"] = 1473
        changed["recent_rental"]["value"][0]["GemiddeldeBouwkostenPerM_3"] = 488
        self.assertRaises(CBS83673Blocked, validate_rows, changed)

    def test_original_native_geo_keys_trailing_spaces_must_match(self):
        changed = fixture()
        changed["regions"]["value"][0]["Key"] = "NL01"
        self.assertRaises(CBS83673Blocked, validate_rows, changed)
        changed = fixture()
        changed["recent_owner"]["value"][0]["RegioS"] = "NL01"
        self.assertRaises(CBS83673Blocked, validate_rows, changed)

    def test_rolling_period_preliminary_and_tenure_id_fail_closed(self):
        for field, name, row, bad in (
            ("Status", "recent_period", 0, "Definitief"),
            ("Status", "historic_period", 0, "Voorlopig"),
            ("Eigendom", "recent_owner", 0, "A028867"),
            ("ID", "recent_owner", 0, 999),
            ("GemiddeldeBouwkostenPerM_2", "recent_owner", 0, True),
        ):
            changed = fixture()
            changed[name]["value"][row][field] = bad
            with self.subTest(name=name, field=field):
                self.assertRaises(CBS83673Blocked, validate_rows, changed)

    def test_release_date_selection_threshold_and_source_identity_fail_closed(self):
        for key, value in (
            ("Modified", "2026-06-01T02:00:00"),
            ("Identifier", "85728NED"),
            ("Description", "Only large houses, no source threshold"),
        ):
            changed = fixture()
            changed["table"]["value"][0][key] = value
            with self.subTest(key=key):
                self.assertRaises(CBS83673Blocked, validate_rows, changed)

    def test_http_redirection_content_type_encoding_or_partial_block(self):
        for kw in (
            {"status": 206}, {"mime": "text/html"},
            {"encoding": "gzip"}, {"wrong_url": True},
        ):
            opened, _ = fake_opener(fixture(), **kw)
            with self.subTest(**kw):
                self.assertRaises(CBS83673Blocked, probe, open_request=opened)

    def test_unsafe_json_duplicates_nonfinite_overflow_shape_oversize(self):
        for raw in (
            b'{"value":[],"value":[]}',
            b'{"value":[NaN]}',
            b'{"value":[Infinity]}',
            b'{"value":[1e9999999]}',
            b'{"value":null}', b'{"value":[',
            b"", b"0" * (MAX_BYTES + 1),
        ):
            with self.subTest(raw=raw[:50]):
                self.assertRaises(CBS83673Blocked, parse_original, raw)

    def test_no_extra_regions_or_insurer_tiv_are_admitted(self):
        receipt = validate_rows(fixture())
        self.assertFalse(receipt["regional_data_retrieved"])
        self.assertFalse(receipt["individual_dwelling_values_retrieved"])
        self.assertFalse(receipt["insured_replacement_values_approved"])
        self.assertFalse(receipt["cat_model_input_approved"])


if __name__ == "__main__":
    unittest.main()
