# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests; provider URLs are data, not executed endpoints."""

from __future__ import annotations

import json
import unittest

from scripts.preflight_ea_flood_ckan_v0 import (
    EACatalogueError, MAX_BYTES, PACKAGES, OBSERVED_ORIGINAL_METADATA_RECEIPTS,
    expected_url, inspect_metadata,
)


def synthetic(dataset: str) -> dict:
    item = PACKAGES[dataset]
    return {
        "success": True,
        "result": {
            "id": item["id"], "name": item["slug"],
            "private": False, "isopen": False, "license_id": None,
            "metadata_modified": item["modified"],
            "num_resources": len(item["resources"]),
            "extras": [{"key": "licence", "value": '["Open Government Licence"]'}],
            "resources": [
                {"id": rid, "name": name, "format": fmt, "url": expected_url(item, name, role)}
                for rid, name, fmt, role in item["resources"]
            ],
        },
    }


def check(doc: dict, dataset: str = "river_present") -> dict:
    return inspect_metadata(json.dumps(doc, sort_keys=True).encode(), dataset)


class EAOfflineCkanTests(unittest.TestCase):
    def test_five_catalogues_and_no_network_or_rights_promotion(self):
        for ds, n in (
            ("river_present", 8), ("river_climate", 8), ("surface_present", 4),
            ("river_3p3_present", 9), ("river_3p3_climate", 9),
        ):
            with self.subTest(ds=ds):
                s = synthetic(ds)
                s["result"]["contact_email"] = "private@example.invalid"
                result = check(s, ds)
                self.assertEqual(result["resource_count"], n)
                self.assertEqual(result["input_bytes"], len(json.dumps(s, sort_keys=True).encode()))
                self.assertEqual(result["provider_requests_performed"], 0)
                self.assertEqual(result["resource_links_followed"], 0)
                self.assertFalse(result["input_authenticity_verified"])
                self.assertFalse(result["matches_observed_original_metadata_receipt"])
                self.assertFalse(result["commercial_reuse_approved"])
                self.assertFalse(result["model_data_admitted"])
                self.assertNotIn("private@example.invalid", json.dumps(result))
                self.assertNotIn("environment.data.gov.uk", json.dumps(result))

    def test_receipts_are_pinned_and_synthetic_bytes_do_not_match(self):
        self.assertEqual(set(OBSERVED_ORIGINAL_METADATA_RECEIPTS), set(PACKAGES))
        self.assertEqual(
            sum(size for size, _digest in OBSERVED_ORIGINAL_METADATA_RECEIPTS.values()),
            66670,
        )
        for dataset, (size, digest) in OBSERVED_ORIGINAL_METADATA_RECEIPTS.items():
            with self.subTest(dataset=dataset):
                self.assertGreater(size, 0)
                self.assertEqual(len(digest), 64)
                self.assertTrue(all(ch in "0123456789abcdef" for ch in digest))
                report = check(synthetic(dataset), dataset)
                self.assertFalse(report["matches_observed_original_metadata_receipt"])
                self.assertEqual(report["observed_original_metadata_receipt_date"], "2026-11-10")

    def test_3p3_present_and_climate_have_separate_source_ids(self):
        present = synthetic("river_3p3_present")
        climate = synthetic("river_3p3_climate")
        self.assertNotEqual(present["result"]["id"], climate["result"]["id"])
        self.assertEqual(present["result"]["num_resources"], 9)
        self.assertEqual(climate["result"]["num_resources"], 9)
        with self.assertRaises(EACatalogueError):
            check(present, "river_3p3_climate")
        with self.assertRaises(EACatalogueError):
            check(climate, "river_3p3_present")

    def test_3p3_source_url_tamper_fails_closed(self):
        record = synthetic("river_3p3_present")
        record["result"]["resources"][-1]["url"] = (
            "https://untrusted.example.invalid/ogc/features/v1"
        )
        with self.assertRaises(EACatalogueError):
            check(record, "river_3p3_present")

    def test_wrong_selector(self):
        with self.assertRaises(EACatalogueError):
            check(synthetic("river_present"), "anything")

    def test_swapped_datasets(self):
        with self.assertRaises(EACatalogueError):
            check(synthetic("river_climate"), "river_present")

    def test_version_drift(self):
        data = synthetic("river_present")
        data["result"]["metadata_modified"] = "2027-01-01T00:00:00"
        with self.assertRaises(EACatalogueError):
            check(data)

    def test_reject_nonpublic(self):
        data = synthetic("river_present")
        data["result"]["private"] = True
        with self.assertRaises(EACatalogueError):
            check(data)

    def test_reject_false_success(self):
        data = synthetic("river_present")
        data["success"] = 1
        with self.assertRaises(EACatalogueError):
            check(data)

    def test_license_change(self):
        data = synthetic("river_present")
        data["result"]["extras"][0]["value"] = '["Other"]'
        with self.assertRaises(EACatalogueError):
            check(data)

    def test_resource_swap(self):
        data = synthetic("river_present")
        data["result"]["resources"][0]["id"] = "wrong"
        with self.assertRaises(EACatalogueError):
            check(data)

    def test_resource_missing(self):
        data = synthetic("river_present")
        data["result"]["resources"].pop()
        with self.assertRaises(EACatalogueError):
            check(data)

    def test_duplicate_resource(self):
        data = synthetic("river_present")
        data["result"]["resources"][1] = data["result"]["resources"][0].copy()
        with self.assertRaises(EACatalogueError):
            check(data)

    def test_link_to_untrusted_domain(self):
        data = synthetic("river_present")
        data["result"]["resources"][0]["url"] = "https://evil.invalid/payload"
        with self.assertRaises(EACatalogueError):
            check(data)

    def test_mutated_resource_path(self):
        data = synthetic("surface_present")
        data["result"]["resources"][-1]["url"] += "?foo=bar"
        with self.assertRaises(EACatalogueError):
            check(data, "surface_present")

    def test_reject_json_duplicate_keys(self):
        with self.assertRaises(EACatalogueError):
            inspect_metadata(b'{"success":true,"success":true}', "river_present")

    def test_reject_non_finite(self):
        with self.assertRaises(EACatalogueError):
            inspect_metadata(b'{"success":NaN}', "river_present")

    def test_reject_overflowed_float_even_in_ignored_metadata(self):
        # Python's default json.loads accepts 1e999 as inf, which must
        # never pass as valid publisher metadata just because it is unused.
        raw = json.dumps(synthetic("river_present"), sort_keys=True).encode()
        self.assertTrue(raw.endswith(b"}"))
        injected = raw[:-1] + b',"untrusted_numeric":1e999}'
        with self.assertRaisesRegex(EACatalogueError, "overflowed JSON float"):
            inspect_metadata(injected, "river_present")

    def test_reject_oversized_response(self):
        with self.assertRaises(EACatalogueError):
            inspect_metadata(b"x" * (MAX_BYTES + 1), "river_present")

    def test_reject_malformed_type(self):
        with self.assertRaises(EACatalogueError):
            inspect_metadata("not bytes", "river_present")


if __name__ == "__main__":
    unittest.main()
