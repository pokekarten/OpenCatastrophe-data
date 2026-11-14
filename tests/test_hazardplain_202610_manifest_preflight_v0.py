# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic provider manifest fixtures, no vendor bytes or live network."""
from __future__ import annotations

import copy
import json
import unittest

from research_runners.hazardplain_202610_manifest_preflight_v0 import (
    EXPECTED_FILES, HazardPlainMetadataError, inspect_manifest, SameHostRedirect,
)


def sample():
    files = []
    tables = []
    for path, info in EXPECTED_FILES.items():
        files.append({"path": path, "kind": "national_csv", "table": info["table"],
                      "rows": info["rows"], "bytes": info["bytes"], "sha256": info["sha256"]})
        tables.append({"name": info["table"], "rows": info["rows"],
                       "columns": sorted(info["columns"]), "sources": sorted(info["sources"])})
    return {"manifest_version": "1.0", "kind": "bulk", "product": "Hazard Plain",
            "release": "2026-10", "as_of": "2026-09-30",
            "built_at": "2026-10-17T19:57:41+00:00", "files": files, "tables": tables}


def run(payload):
    return inspect_manifest(json.dumps(payload, sort_keys=True).encode())


class HazardPlainManifestTests(unittest.TestCase):
    def test_valid_synthetic_manifest_metadata_not_asset_admission(self):
        receipt = run(sample())
        self.assertEqual(len(receipt["selected_files"]), 3)
        self.assertEqual(receipt["release"], "2026-10")
        for key in ("provider_data_file_hashes_independently_verified",
                    "nri_noaa_source_lineage_independent", "model_input_admitted",
                    "commercial_rights_reviewed", "insurance_losses_or_aep_oep_generated"):
            self.assertFalse(receipt[key])
        self.assertFalse(any(item["source_file_bytes_inspected"] for item in receipt["selected_files"]))

    def test_publisher_manifest_pin_is_deterministic(self):
        self.assertEqual(run(sample()), run(copy.deepcopy(sample())))
        self.assertEqual(len(run(sample())["original_manifest_sha256"]), 64)

    def test_release_vintage_changed_blocked(self):
        for key, val in (("release", "2026-11"), ("as_of", "2026-10-31"),
                         ("built_at", "2026-10-18T19:57:41+00:00")):
            payload = sample(); payload[key] = val
            with self.subTest(key=key), self.assertRaises(HazardPlainMetadataError):
                run(payload)

    def test_manifest_wrong_sha_or_file_size_or_row_count_blocked(self):
        for key, val in (("sha256", "1" * 64), ("bytes", 99), ("rows", 9)):
            payload = sample(); payload["files"][0][key] = val
            with self.subTest(key=key), self.assertRaisesRegex(HazardPlainMetadataError, "identity changed"):
                run(payload)

    def test_missing_table_column_blocked(self):
        payload = sample()
        payload["tables"][0]["columns"].remove("eal_total") if "eal_total" in payload["tables"][0]["columns"] else payload["tables"][0]["columns"].pop()
        with self.assertRaisesRegex(HazardPlainMetadataError, "schema"):
            run(payload)

    def test_lineage_changed_blocked(self):
        payload = sample(); payload["tables"][0]["sources"] = ["standalone_observation"]
        with self.assertRaisesRegex(HazardPlainMetadataError, "source lineage"):
            run(payload)

    def test_duplicate_file_path_blocked(self):
        payload = sample(); payload["files"].append(copy.deepcopy(payload["files"][0]))
        with self.assertRaisesRegex(HazardPlainMetadataError, "duplicate"):
            run(payload)

    def test_traversal_and_unsafe_file_paths_blocked(self):
        for bad in ("../secrets", "/tmp/file", "national/../../file", "national//file"):
            payload = sample(); payload["files"].append({"path": bad})
            with self.subTest(bad=bad), self.assertRaisesRegex(HazardPlainMetadataError, "unsafe"):
                run(payload)

    def test_duplicate_json_keys_blocked(self):
        raw = b'{"release":"2026-10","release":"2026-10"}' + b" " * 100
        with self.assertRaisesRegex(HazardPlainMetadataError, "duplicate JSON"):
            inspect_manifest(raw)

    def test_invalid_binary_and_nonfinite_blocked(self):
        for raw in (None, b"no", b"a" * 256, b"{" + b"z" * 256):
            with self.subTest(raw=type(raw).__name__), self.assertRaises(HazardPlainMetadataError):
                inspect_manifest(raw)

    def test_source_host_redirect_blocked(self):
        import urllib.request
        req = urllib.request.Request("https://files.hazardplain.org/r/2026-10/bulk/manifest.json")
        with self.assertRaisesRegex(HazardPlainMetadataError, "outside source host"):
            SameHostRedirect().redirect_request(req, None, 302, "Found", {},
                                                "https://untrusted.example/manifest.json")

    def test_no_insured_or_external_source_fields(self):
        payload = sample(); payload["source_asset_rows"] = [{"claim": 99999}]
        # The verifier only emits a deliberately fixed metadata receipt.
        self.assertNotIn("claim", run(payload))
        self.assertNotIn("source_asset_rows", run(payload))


if __name__ == "__main__":
    unittest.main()
