# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only checks for exact STORM v4 DOI metadata preflight."""
from __future__ import annotations

import hashlib
import json
import unittest

from research_runners.storm_v4_datacite_preflight_v0 import Blocked, inspect_metadata


def _example() -> dict:
    return {
        "data": {
            "type": "dois",
            "id": "10.4121/12706085.v4",
            "attributes": {
                "doi": "10.4121/12706085.v4",
                "types": {"resourceTypeGeneral": "Dataset"},
                "titles": [{"title": "STORM IBTrACS present climate synthetic tropical cyclone tracks"}],
                "publisher": "4TU.ResearchData",
                "version": "4",
                "rightsList": [{"rightsIdentifier": "CC0-1.0"}],
            },
        }
    }


def _raw(value: dict) -> bytes:
    return json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _inspect(value: dict) -> dict:
    raw = _raw(value)
    return inspect_metadata(raw, hashlib.sha256(raw).hexdigest())


class MetadataPreflight(unittest.TestCase):
    def test_valid_metadata_is_still_non_admitted(self):
        receipt = _inspect(_example())
        self.assertTrue(receipt["data_cite_dataset_identity_verified"])
        self.assertTrue(receipt["datacite_cc0_claim_observed"])
        self.assertFalse(receipt["original_track_files_acquired"])
        self.assertFalse(receipt["model_input_authorized"])
        self.assertFalse(receipt["service_automation_authorized"])

    def test_absent_license_does_not_imply_cc0(self):
        payload = _example()
        payload["data"]["attributes"].pop("rightsList")
        self.assertFalse(_inspect(payload)["datacite_cc0_claim_observed"])

    def test_other_doi_is_rejected_at_both_levels(self):
        for field in ("id", "attributes"):
            payload = _example()
            if field == "id":
                payload["data"]["id"] = "10.4121/12706085.v3"
            else:
                payload["data"]["attributes"]["doi"] = "10.4121/12706085.v3"
            with self.subTest(field=field), self.assertRaises(Blocked):
                _inspect(payload)

    def test_other_version_and_resource_type_rejected(self):
        for field, value in (("version", "3"), ("types", {"resourceTypeGeneral": "Software"})):
            payload = _example()
            payload["data"]["attributes"][field] = value
            with self.subTest(field=field), self.assertRaises(Blocked):
                _inspect(payload)

    def test_license_conflict_rejected(self):
        payload = _example()
        payload["data"]["attributes"]["rightsList"] = [{"rightsIdentifier": "CC-BY-4.0"}]
        with self.assertRaises(Blocked):
            _inspect(payload)

    def test_missing_title_and_publisher_rejected(self):
        for field, value in (("titles", []), ("publisher", "")):
            payload = _example()
            payload["data"]["attributes"][field] = value
            with self.subTest(field=field), self.assertRaises(Blocked):
                _inspect(payload)

    def test_sha_mismatch_rejected(self):
        with self.assertRaisesRegex(Blocked, "SHA-256 mismatch"):
            inspect_metadata(_raw(_example()), "0" * 64)

    def test_non_hex_sha_rejected(self):
        with self.assertRaises(Blocked):
            inspect_metadata(_raw(_example()), "A" * 64)

    def test_over_limit_rejected(self):
        with self.assertRaises(Blocked):
            inspect_metadata(b" " * 262145, "0" * 64)

    def test_duplicate_json_key_rejected(self):
        raw = b'{"data":{},"data":{}}'
        with self.assertRaisesRegex(Blocked, "duplicate JSON key"):
            inspect_metadata(raw, hashlib.sha256(raw).hexdigest())

    def test_nonfinite_json_rejected(self):
        raw = b'{"data":1e400}'
        with self.assertRaises(Blocked):
            inspect_metadata(raw, hashlib.sha256(raw).hexdigest())

    def test_utf8_decode_rejected(self):
        raw = b'{"data":"\xff"}'
        with self.assertRaises(Blocked):
            inspect_metadata(raw, hashlib.sha256(raw).hexdigest())

    def test_reject_partial_metadata_shape(self):
        payload = _example()
        payload["data"]["attributes"]["types"] = {}
        with self.assertRaises(Blocked):
            _inspect(payload)


if __name__ == "__main__":
    unittest.main()
