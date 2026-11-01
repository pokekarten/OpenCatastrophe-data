# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only geoBoundaries canary and negative provenance tests."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import unittest

from scripts.probe_geoboundaries_deu_adm1_v0 import (
    ASSET_NAMES,
    EXPECTED_ASSET_PREFIX,
    EXPECTED_COMMIT,
    EXPECTED_ID,
    EXPECTED_LICENSE,
    EXPECTED_LICENSE_SOURCE,
    EXPECTED_SOURCE,
    GeoBoundariesProbeError,
    MAX_RESPONSE_BYTES,
    PROBE_URL,
    inspect_metadata,
    probe,
    verify_frozen_contract,
)


def sample_metadata() -> dict:
    return {
        "boundaryID": EXPECTED_ID,
        "boundaryISO": "DEU",
        "boundaryType": "ADM1",
        "boundaryName": "Germany",
        "boundaryYearRepresented": "2021",
        "boundarySource": EXPECTED_SOURCE,
        "boundaryLicense": EXPECTED_LICENSE,
        "licenseSource": EXPECTED_LICENSE_SOURCE,
        "sourceDataUpdateDate": "Sun Feb 26 12:29:46 2023",
        "buildDate": "Dec 12, 2023",
        "admUnitCount": "16",
        **{key: EXPECTED_ASSET_PREFIX + name for key, name in ASSET_NAMES.items()},
    }


def raw_metadata() -> bytes:
    return json.dumps(sample_metadata(), sort_keys=True).encode("utf-8")


class SyntheticResponse(io.BytesIO):
    status = 200

    def __init__(self, raw: bytes, *, media: str = "application/json", url: str = PROBE_URL):
        super().__init__(raw)
        self.headers = {"Content-Type": media}
        self.url = url

    def geturl(self) -> str:
        return self.url


class GeoBoundariesMetadataProbeTests(unittest.TestCase):
    def test_current_reviewed_contract_is_frozen(self):
        c = verify_frozen_contract()
        self.assertEqual(c["status"], "probe_ready")
        self.assertEqual(c["probe_contract"]["operation"], "deu_adm1_metadata")

    def test_synthetic_metadata_is_exact_and_links_are_metadata_only(self):
        row = inspect_metadata(raw_metadata())
        self.assertEqual(row["boundary_id"], EXPECTED_ID)
        self.assertEqual(row["admin_unit_count"], 16)
        self.assertEqual(row["asset_commit"], EXPECTED_COMMIT)
        self.assertEqual(set(row["asset_links_evidence_only"]), set(ASSET_NAMES))
        self.assertFalse(row["asset_bytes_acquired"])

    def test_injected_network_produces_receipt_without_geometry(self):
        def fake_open(req, timeout):
            self.assertEqual(req.full_url, PROBE_URL)
            self.assertEqual(timeout, 30)
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(req.get_header("Accept"), "application/json")
            return SyntheticResponse(raw_metadata(), media="application/json; charset=utf-8")

        row = probe(open_request=fake_open,
                    utc_clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(row["response_bytes"], len(raw_metadata()))
        self.assertEqual(len(row["response_sha256"]), 64)
        self.assertEqual(row["boundary_id"], EXPECTED_ID)
        self.assertFalse(row["geometry_imported"])
        self.assertFalse(row["model_input_approved"])
        self.assertFalse(row["provider_metadata_persisted"])
        self.assertNotIn("geometry", row)
        self.assertNotIn("features", row)

    def test_provider_drift_each_identity_field_is_blocked(self):
        fields = {
            "boundaryID": "DEU-ADM1-CHANGED",
            "boundaryISO": "USA",
            "boundaryType": "ADM2",
            "boundaryYearRepresented": "2024",
            "admUnitCount": "17",
            "boundaryLicense": "non-commercial",
            "licenseSource": "other.domain",
            "boundarySource": "Unknown",
        }
        for field, value in fields.items():
            payload = sample_metadata()
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(GeoBoundariesProbeError):
                inspect_metadata(json.dumps(payload).encode("utf-8"))

    def test_mutated_commit_and_asset_link_escape_blocked(self):
        for field in ASSET_NAMES:
            for value in (
                "http://github.com/malicious/file.geojson",
                "https://evil.example/malicious",
                sample_metadata()[field].replace(EXPECTED_COMMIT, "other123"),
                sample_metadata()[field] + "?token=secret",
            ):
                payload = sample_metadata()
                payload[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(GeoBoundariesProbeError):
                    inspect_metadata(json.dumps(payload).encode("utf-8"))

    def test_rejects_duplicate_json_keys_nan_invalid_and_oversize(self):
        for raw in (
            b'{"boundaryID":"DEU","boundaryID":"USA"}',
            b'{"foo":NaN}',
            b'[]',
            b'',
            b'not json',
            b'\xff',
            b'x' * (MAX_RESPONSE_BYTES + 1),
        ):
            with self.subTest(raw=raw[:24]), self.assertRaises(GeoBoundariesProbeError):
                inspect_metadata(raw)

    def test_network_unsafe_response_fails_closed(self):
        cases = (
            SyntheticResponse(raw_metadata(), url="https://example.org/redirect"),
            SyntheticResponse(raw_metadata(), media="text/html"),
            SyntheticResponse(b'x' * (MAX_RESPONSE_BYTES + 1)),
        )
        for item in cases:
            with self.subTest(url=item.url, media=item.headers["Content-Type"]):
                with self.assertRaises(GeoBoundariesProbeError):
                    probe(open_request=lambda req, timeout: item)

    def test_invalid_receipt_clock_refused(self):
        with self.assertRaisesRegex(GeoBoundariesProbeError, "timezone-aware"):
            probe(open_request=lambda req, timeout: SyntheticResponse(raw_metadata()),
                  utc_clock=lambda: datetime(2026, 11, 1))


if __name__ == "__main__":
    unittest.main()
