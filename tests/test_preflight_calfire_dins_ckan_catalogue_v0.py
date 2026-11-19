# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only contract tests for the documented California CKAN package."""

from __future__ import annotations

import json
import unittest

from scripts.preflight_calfire_dins_ckan_catalogue_v0 import (
    CkanMetadataError,
    DATASET_UUID,
    FROZEN_RESOURCES,
    MAX_BYTES,
    METADATA_MODIFIED,
    PACKAGE_SLUG,
    inspect_ckan_metadata,
)


def sample() -> dict:
    return {
        "success": True,
        "result": {
            "id": DATASET_UUID,
            "name": PACKAGE_SLUG,
            "license_id": "cc-by",
            "metadata_modified": METADATA_MODIFIED,
            "accessLevel": "public",
            "isopen": True,
            "resources": [
                {"id": rid, "format": fmt, "url": "https://example.org/do-not-fetch"}
                for rid, fmt in FROZEN_RESOURCES.items()
            ],
        },
    }


def eval_sample(value: dict) -> dict:
    return inspect_ckan_metadata(json.dumps(value, sort_keys=True).encode())


class DinsCkanCatalogueTests(unittest.TestCase):
    def test_valid_synthetic_package_only_reports_catalogue(self):
        x = sample()
        x["result"]["contact_email"] = "synthetic-private@invalid.example"
        out = eval_sample(x)
        self.assertEqual(out["resource_count"], 11)
        self.assertEqual(out["dataset_catalogue_license_label"], "cc-by")
        self.assertFalse(out["matches_recorded_original_provider_response_sha256"])
        self.assertFalse(out["input_bytes_provenance_authenticated_by_this_checker"])
        self.assertEqual(out["provider_asset_downloads_performed"], 0)
        self.assertEqual(out["provider_feature_rows_read"], 0)
        self.assertFalse(out["model_data_admitted"])
        self.assertNotIn("contact_email", json.dumps(out))
        self.assertNotIn("example.org", json.dumps(out))

    def test_reject_wrong_dataset_uuid(self):
        x = sample()
        x["result"]["id"] = "wrong"
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_wrong_dataset_name(self):
        x = sample()
        x["result"]["name"] = "wrong"
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_license_drift(self):
        x = sample()
        x["result"]["license_id"] = "other"
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_modified_metadata_vintage(self):
        x = sample()
        x["result"]["metadata_modified"] = "2026-11-01T00:00:00"
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_non_public_dataset(self):
        x = sample()
        x["result"]["accessLevel"] = "restricted"
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_false_open_label(self):
        x = sample()
        x["result"]["isopen"] = 1
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_changed_resource_uuid(self):
        x = sample()
        x["result"]["resources"][0]["id"] = "synthetic-different-resource"
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_changed_resource_format(self):
        x = sample()
        x["result"]["resources"][0]["format"] = "HTML-ALTERED"
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_duplicate_resource_id(self):
        x = sample()
        x["result"]["resources"][1]["id"] = x["result"]["resources"][0]["id"]
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_extra_resources(self):
        x = sample()
        x["result"]["resources"].append({"id": "new-resource", "format": "GEOJSON"})
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_provider_error(self):
        x = sample()
        x["success"] = False
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_fake_true_success(self):
        x = sample()
        x["success"] = 1
        with self.assertRaises(CkanMetadataError):
            eval_sample(x)

    def test_reject_duplicate_json_keys(self):
        with self.assertRaises(CkanMetadataError):
            inspect_ckan_metadata(b'{"success":true,"success":true}')

    def test_reject_nonfinite(self):
        with self.assertRaises(CkanMetadataError):
            inspect_ckan_metadata(b'{"success":NaN}')

    def test_reject_oversize(self):
        with self.assertRaises(CkanMetadataError):
            inspect_ckan_metadata(b"x" * (MAX_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
