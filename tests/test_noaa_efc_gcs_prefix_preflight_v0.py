# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only NOAA EFC GCS prefix preflight and fail-closed rights tests."""

import copy
import json
import unittest
from pathlib import Path

from research_runners.noaa_efc_gcs_prefix_preflight_v0 import (
    EfcGcsPreflightError, MAX_BYTES, PREFIX, inspect_original_metadata,
)
from scripts.validate_source_access import SourceAccessError, validate_contract

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access/noaa.ncei.event-footprint-catalog.gcs-prefix.2026.json"


def example() -> dict:
    return {
        "kind": "storage#objects",
        "items": [{
            "kind": "storage#object",
            "name": PREFIX + "example-small.json",
            "bucket": "noaa-ncei-ipg",
            "generation": "123",
            "size": "128",
            "contentType": "application/geo+json",
        }],
        "nextPageToken": "synthetic-token",
    }


def raw(payload: dict) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


class EfcGcsPrefixTests(unittest.TestCase):
    def test_exact_contract_is_nonexecuting_despite_cloud_path(self):
        doc = json.loads(CONTRACT.read_text(encoding="utf-8"))
        validate_contract(doc)
        self.assertEqual(doc["source_ids"], ["noaa.ncei.event-footprint-catalog.2026"])
        self.assertEqual(doc["service_root"], "https://storage.googleapis.com")
        self.assertEqual(doc["request_contract"]["path_templates"], [
            "/storage/v1/b/noaa-ncei-ipg/o",
        ])
        self.assertEqual(doc["status"], "documented_only")
        self.assertEqual(doc["probe_contract"]["mode"], "none")
        self.assertIsNone(doc["probe_contract"]["operation"])
        self.assertEqual(doc["rights_and_policy"]["api_terms_status"], "separate_unreviewed")
        self.assertEqual(doc["rights_and_policy"]["commercial_automation_status"], "unknown")
        self.assertEqual(doc["implementation_decision"], "document_only")

    def test_rights_not_laundered_into_active_probe(self):
        changed = json.loads(CONTRACT.read_text(encoding="utf-8"))
        changed["status"] = "probe_ready"
        changed["probe_contract"].update(
            mode="catalogue_query", operation="efc_gcs_prefix_metadata_list",
            expected_evidence=["one bounded metadata response"],
        )
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)
        changed = json.loads(CONTRACT.read_text(encoding="utf-8"))
        changed["rights_and_policy"]["commercial_automation_status"] = "allowed"
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)

    def test_single_synthetic_catalogue_page_no_download_or_pagination(self):
        result = inspect_original_metadata(raw(example()))
        self.assertEqual(result["object_count"], 1)
        self.assertEqual(result["prefix_count"], 0)
        self.assertTrue(result["more_pages_indicated_but_not_followed"])
        self.assertEqual(result["objects_metadata_only"][0]["generation"], "123")
        self.assertEqual(len(result["original_response_sha256"]), 64)
        self.assertFalse(result["original_event_geojson_acquired"])
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["source_byte_persistence_authorized"])

    def test_safe_subprefix_only(self):
        doc = {"kind": "storage#objects", "prefixes": [
            PREFIX + "hail/", PREFIX + "tornado/"
        ]}
        result = inspect_original_metadata(raw(doc))
        self.assertEqual(result["object_count"], 0)
        self.assertEqual(result["prefix_count"], 2)

    def test_reject_foreign_bucket_paths_and_traversal(self):
        for attribute, value in [
            ("bucket", "foreign-public-bucket"),
            ("name", "other-data/file.geojson"),
            ("name", PREFIX + "../secret.json"),
            ("name", PREFIX + "%2e%2e/file.geojson"),
            ("name", "https://invalid.example/data"),
            ("name", PREFIX + "folder//bad.geojson"),
            ("name", PREFIX),
        ]:
            doc = example()
            doc["items"][0][attribute] = value
            with self.subTest(attribute=attribute, value=value):
                with self.assertRaises(EfcGcsPreflightError):
                    inspect_original_metadata(raw(doc))

    def test_reject_unsafe_object_metadata(self):
        for key, value in [
            ("generation", "bad"), ("generation", "0"),
            ("size", -1), ("size", "1e3"),
            ("kind", "storage#bucket"), ("contentType", "HTML"),
        ]:
            doc = example()
            doc["items"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(EfcGcsPreflightError):
                inspect_original_metadata(raw(doc))

    def test_reject_duplicate_json_nonfinite_html_and_oversize(self):
        for blob in (
            b'{"kind":"storage#objects","kind":"storage#objects"}',
            b'{"kind":"storage#objects","items":[NaN]}',
            b'{"kind":"storage#objects","items":[1e999]}',
            b'<html>not data</html>',
            b'',
            b'x' * (MAX_BYTES + 1),
        ):
            with self.subTest(blob=blob[:25]), self.assertRaises(EfcGcsPreflightError):
                inspect_original_metadata(blob)

    def test_reject_oversized_or_unsorted_response(self):
        doc = {"kind": "storage#objects", "items": [
            {**example()["items"][0], "name": PREFIX + f"obj-{i:02d}.geojson"}
            for i in range(11)
        ]}
        with self.assertRaises(EfcGcsPreflightError):
            inspect_original_metadata(raw(doc))
        doc["items"] = doc["items"][:2][::-1]
        with self.assertRaises(EfcGcsPreflightError):
            inspect_original_metadata(raw(doc))

    def test_reject_ambiguous_pagination_and_duplicate_names(self):
        doc = copy.deepcopy(example())
        doc["nextPageToken"] = "x" * 2049
        with self.assertRaises(EfcGcsPreflightError):
            inspect_original_metadata(raw(doc))
        doc = copy.deepcopy(example())
        doc["items"].append(dict(doc["items"][0]))
        with self.assertRaises(EfcGcsPreflightError):
            inspect_original_metadata(raw(doc))


if __name__ == "__main__":
    unittest.main()
