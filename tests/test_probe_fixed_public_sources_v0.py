# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only security/contract tests. No network calls."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit

from scripts.probe_fixed_public_sources_v0 import (
    NoRedirect, PROBES, ProbeBlocked, probe, reviewed_probe, verify_response,
)


class Reply:
    status = 200

    def __init__(self, body, content_type="application/json", declared=None):
        self.body = body
        self.headers = {"Content-Type": content_type}
        if declared is not None:
            self.headers["Content-Length"] = declared

    def read(self, limit):
        return self.body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class Client:
    def __init__(self, reply):
        self.reply = reply
        self.requests = []

    def open(self, request, *, timeout):
        self.requests.append((request.full_url, request.get_method(), timeout))
        return self.reply


def contract(source):
    url, operation = PROBES[source]
    uri = urlsplit(url)
    return {
        "access_id": source,
        "status": "probe_ready",
        "service_root": uri.scheme + "://" + uri.netloc + ("/webservices/rest-api/v2" if source == "wsv.pegelonline.rest-v2.dresden" else ""),
        "authentication": {"mode": "none"},
        "probe_contract": {"mode": "provider_specific",
                           "operation": operation, "requires_credentials": False},
        "request_contract": {"allowed_operations": [operation],
                             "path_templates": ["/stations/{station_uuid}.json"]
                             if source == "wsv.pegelonline.rest-v2.dresden" else [uri.path]},
        "rights_and_policy": {"commercial_automation_status": "allowed"},
        "operational_constraints": {"timeout_seconds": 30, "max_probe_bytes": 4194304},
    }


def gfz_day_fixture():
    """Entirely synthetic GFZ 2024-01-01 definitive Kp day, no provider bytes."""
    return {
        "datetime": [f"2024-01-01T{hour:02}:00:00Z" for hour in range(0, 24, 3)],
        "Kp": [1.0, 1.3, 1.7, 2.0, 0.0, 3.0, 9.0, 2.3],
        "status": ["def"] * 8,
        "meta": {"fixture_only": True},
    }


class FixedSourceProbesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "access").mkdir()

    def write(self, source, *, change=None):
        data = contract(source)
        if change is not None:
            change(data)
        (self.root / "access" / (source + ".json")).write_text(
            json.dumps(data), encoding="utf-8")

    def test_each_source_matches_fixed_reviewed_contract(self):
        for source in PROBES:
            with self.subTest(source=source):
                if source == "emsc.seismicportal.fdsn-event":
                    # EMSC already has an independently validated full schema
                    # contract; a sparse synthetic stub must never bypass it.
                    root = Path(__file__).resolve().parents[1]
                else:
                    self.write(source)
                    root = self.root
                url, op, limit, timeout = reviewed_probe(source, root)
                self.assertEqual((url, op), PROBES[source])
                self.assertGreater(limit, 0)
                self.assertEqual(timeout, 30)

    def test_checked_in_contracts_match_each_reviewed_live_probe(self):
        """Check the actual source contracts, not only synthetic fixture copies.

        The paired PR workflow exercises the exact reviewed anonymous endpoints;
        this regression prevents contract/allowlist drift before network access.
        """
        repo_root = Path(__file__).resolve().parents[1]
        for source in PROBES:
            with self.subTest(source=source):
                url, operation, max_bytes, timeout = reviewed_probe(source, repo_root)
                self.assertEqual((url, operation), PROBES[source])
                self.assertLessEqual(max_bytes, 4 * 1024 * 1024)
                self.assertLessEqual(timeout, 60)

    def test_reject_credentials_and_rights_changes(self):
        source = "gfz.geomagnetic-kp"
        for mutate in (
            lambda d: d["authentication"].update(mode="bearer"),
            lambda d: d["rights_and_policy"].update(commercial_automation_status="unknown"),
            lambda d: d["probe_contract"].update(requires_credentials=True),
            lambda d: d.update(status="restricted_by_terms"),
            lambda d: d["request_contract"].update(allowed_operations=["other"]),
        ):
            self.write(source, change=mutate)
            with self.subTest(mutation=repr(mutate)):
                with self.assertRaises(ProbeBlocked):
                    reviewed_probe(source, self.root)

    def test_source_cannot_change_host_path_or_limit(self):
        source = "geoboundaries.gbopen"
        for mutate in (
            lambda d: d.update(service_root="https://attacker.invalid"),
            lambda d: d["request_contract"].update(path_templates=["/other"]),
            lambda d: d["operational_constraints"].update(max_probe_bytes=2**30),
            lambda d: d["operational_constraints"].update(timeout_seconds=600),
        ):
            self.write(source, change=mutate)
            with self.subTest(mutation=repr(mutate)):
                with self.assertRaises(ProbeBlocked):
                    reviewed_probe(source, self.root)

    def test_geo_boundaries_frozen_identity_and_original_licence(self):
        source = "geoboundaries.gbopen"
        payload = {"boundaryISO": "DEU", "boundaryType": "ADM1",
                   "boundaryID": "DEU-ADM1-10402087",
                   "boundaryLicense": "DL-DE BY 2.0",
                   "licenseSource": "govdata.de"}
        result = verify_response(source, json.dumps(payload).encode())
        self.assertEqual(result["frozen_id"], "DEU-ADM1-10402087")
        payload["boundaryID"] = "DEU-ADM1-CHANGED"
        with self.assertRaises(ProbeBlocked):
            verify_response(source, json.dumps(payload).encode())

    def test_gfz_noaa_structural_only(self):
        a = verify_response("gfz.geomagnetic-kp", json.dumps(gfz_day_fixture()).encode())
        self.assertIs(a["scientific_values_verified"], False)
        self.assertEqual(a["record_count"], 8)
        self.assertTrue(a["definitive_status_verified"])
        b = verify_response("noaa.swpc.real-time-solar-wind", b'[{"satellite": "x"}]')
        self.assertIs(b["sensor_lineage_verified"], False)

    def test_gfz_definitive_kp_day_rejects_false_positive_json(self):
        source = "gfz.geomagnetic-kp"
        valid = gfz_day_fixture()
        self.assertEqual(
            verify_response(source, json.dumps(valid).encode())["record_count"], 8
        )

        def changed(field, position, value):
            bad = gfz_day_fixture()
            bad[field][position] = value
            return bad

        for bad in (
            {"Kp": [1.0]},  # previously accepted any non-empty object
            [],
            changed("Kp", 0, "1.0"),
            changed("Kp", 0, True),
            changed("Kp", 0, None),
            changed("Kp", 0, -0.1),
            changed("Kp", 0, 9.1),
            changed("Kp", 0, float("inf")),
            changed("datetime", 0, "2024-01-02T00:00:00Z"),
            changed("datetime", 1, "2024-01-01T00:00:00Z"),
            changed("status", 0, "now"),
            changed("status", 0, None),
            dict(gfz_day_fixture(), Kp=[1.0]),
            dict(gfz_day_fixture(), status=["def"] * 7),
        ):
            with self.subTest(bad=str(bad)[:65]), self.assertRaises(ProbeBlocked):
                verify_response(source, json.dumps(bad).encode("utf-8"))

    def test_gfz_probe_receipt_is_values_free_and_not_admitted(self):
        source = "gfz.geomagnetic-kp"
        self.write(source)
        body = json.dumps(gfz_day_fixture()).encode("utf-8")
        receipt = probe(source, root=self.root, opener=Client(Reply(body)))
        self.assertEqual(receipt["record_count"], 8)
        self.assertEqual(len(receipt["response_sha256"]), 64)
        self.assertTrue(receipt["fixed_window_verified"])
        self.assertFalse(receipt["model_input_approved"])
        self.assertFalse(receipt["provider_bytes_persisted"])
        self.assertNotIn("1.3", json.dumps(receipt))
        self.assertNotIn("fixture_only", json.dumps(receipt))

    def test_dresden_pegelonline_strict_metadata_only(self):
        source = "wsv.pegelonline.rest-v2.dresden"
        self.write(source)
        url, operation, _, _ = reviewed_probe(source, self.root)
        self.assertEqual((url, operation), PROBES[source])
        payload = {
            "uuid": "70272185-b2b3-4178-96b8-43bea330dcae",
            "number": "501060", "shortname": "DRESDEN",
            "latitude": 51.054460, "longitude": 13.738832,
            "water": {"shortname": "ELBE"},
            "timeseries": [
                {"shortname": "Q", "longname": "ABFLUSS_ROHDATEN",
                 "unit": "m³/s", "equidistance": 15},
            ],
        }
        result = verify_response(source, json.dumps(payload).encode("utf-8"))
        self.assertEqual(result["verified_shape"], "dresden_station_q_metadata")
        self.assertEqual(result["q_sampling_interval_seconds"], 900)
        self.assertFalse(result["measurement_values_retrieved"])
        payload["timeseries"][0]["currentMeasurement"] = {"value": 1.0}
        with self.assertRaisesRegex(ProbeBlocked, "contract drift"):
            verify_response(source, json.dumps(payload).encode("utf-8"))

    def test_dresden_contract_must_not_allow_arbitrary_stations(self):
        source = "wsv.pegelonline.rest-v2.dresden"
        self.write(source, change=lambda d: d["request_contract"].update(
            path_templates=["/stations/{arbitrary_station_uuid}.json"]
        ))
        with self.assertRaises(ProbeBlocked):
            reviewed_probe(source, self.root)

    def test_emsc_real_contract_and_one_event_only(self):
        source = "emsc.seismicportal.fdsn-event"
        repo_root = Path(__file__).resolve().parents[1]
        url, operation, max_bytes, timeout = reviewed_probe(source, repo_root)
        self.assertEqual((url, operation), PROBES[source])
        self.assertEqual((max_bytes, timeout), (1_048_576, 30))
        event = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature", "id": "synthetic-not-real",
                "geometry": {"type": "Point", "coordinates": [12.5, 45.0, 11.0]},
                "properties": {"source_id": "synthetic-source", "mag": 5.2},
            }],
        }
        payload = json.dumps(event).encode("utf-8")
        verified = verify_response(source, payload)
        self.assertEqual(verified["verified_shape"], "one_earthquake_event_geojson")
        self.assertEqual(verified["event_count"], 1)
        self.assertFalse(verified["scientific_event_parameters_verified"])
        client = Client(Reply(payload))
        receipt = probe(source, root=repo_root, opener=client)
        self.assertEqual(receipt["response_bytes"], len(payload))
        self.assertFalse(receipt["model_input_approved"])
        self.assertFalse(receipt["provider_bytes_persisted"])
        self.assertNotIn("synthetic-source", json.dumps(receipt))
        self.assertNotIn("coordinates", json.dumps(receipt))
        event["features"].append(event["features"][0])
        with self.assertRaisesRegex(ProbeBlocked, "semantics drift"):
            verify_response(source, json.dumps(event).encode("utf-8"))

    def test_reject_nonfinite_and_duplicate_json_fields(self):
        for raw in (b'{"foo":NaN}', b'{"foo":1,"foo":2}', b'{"foo":Infinity}', b'not json'):
            with self.subTest(raw=raw), self.assertRaises(ProbeBlocked):
                verify_response("gfz.geomagnetic-kp", raw)

    def test_probe_receipt_has_no_provider_values(self):
        source = "gfz.geomagnetic-kp"
        self.write(source)
        synthetic = gfz_day_fixture()
        synthetic["secret"] = "never-emit-this"
        body = json.dumps(synthetic).encode("utf-8")
        client = Client(Reply(body))
        receipt = probe(source, root=self.root, opener=client)
        self.assertEqual(receipt["response_bytes"], len(body))
        self.assertEqual(len(receipt["response_sha256"]), 64)
        self.assertEqual(len(receipt["probe_code_sha256"]), 64)
        self.assertEqual(len(receipt["access_contract_sha256"]), 64)
        self.assertEqual(client.requests[0][1], "GET")
        self.assertEqual(client.requests[0][0], PROBES[source][0])
        self.assertNotIn("never-emit-this", json.dumps(receipt))
        self.assertFalse(receipt["provider_bytes_persisted"])
        self.assertFalse(receipt["model_input_approved"])

    def test_reject_oversized_and_wrong_media_type(self):
        source = "gfz.geomagnetic-kp"
        self.write(source)
        for reply in (Reply(b'{"ok":true}', "text/html"),
                      Reply(b'{"ok":true}', declared="4194305"),
                      Reply(b"x" * (4194304 + 1))):
            with self.subTest(content_type=reply.headers), self.assertRaises(ProbeBlocked):
                probe(source, root=self.root, opener=Client(reply))

    def test_no_redirect_or_unlisted_source(self):
        with self.assertRaises(ProbeBlocked):
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.invalid")
        with self.assertRaises(ProbeBlocked):
            reviewed_probe("attacker.invalid", self.root)


    def test_non_200_provider_status_never_counts_as_api_success(self):
        """Live-provider failures must not produce a successful receipt."""
        source = "gfz.geomagnetic-kp"
        self.write(source)
        for status in (204, 301, 404, 429, 503):
            with self.subTest(status=status):
                reply = Reply(b'{"Kp":[1.0]}')
                reply.status = status
                client = Client(reply)
                with self.assertRaisesRegex(ProbeBlocked, "provider status not 200"):
                    probe(source, root=self.root, opener=client)
                self.assertEqual(len(client.requests), 1)


if __name__ == "__main__":
    unittest.main()
