# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic negative/positive source-metadata contracts."""
import json
import unittest

from research_runners.meteofrance_north_hourly_catalogue_v0 import (
    DEPARTMENTS, BASE, PERIOD, Blocked, audit_catalogue
)


def fake(department: str) -> dict:
    return {
        "id": ("a" * 8 + "-b" * 4 + "-c" * 4 + "-d" * 4 + "-"
               + str(int(department)).zfill(12)),
        "title": f"HOR_departement_{department}_periode_{PERIOD}",
        "url": f"{BASE}H_{department}_previous-{PERIOD}.csv.gz",
        "filesize": 10000 + int(department),
    }


def body(resources=None) -> bytes:
    return json.dumps({"resources": resources if resources is not None
                       else [fake(dep) for dep in DEPARTMENTS]}).encode()


class TestFrenchNorthCatalogue(unittest.TestCase):
    def test_exact_five_resources_metadata_only(self):
        audit = audit_catalogue(body())
        self.assertEqual([x["department"] for x in audit["sources"]], list(DEPARTMENTS))
        self.assertEqual(audit["original_asset_count"], 0)
        self.assertFalse(audit["annual_ep_authorized"])
        for x in audit["sources"]:
            self.assertFalse(x["original_sha256_verified"])
            self.assertFalse(x["commercial_model_calibration_authorized"])

    def test_duplicate_title_or_missing_department_block(self):
        a = [fake(dep) for dep in DEPARTMENTS]
        with self.assertRaisesRegex(Blocked, "expected one"):
            audit_catalogue(body(a + [a[0]]))
        with self.assertRaisesRegex(Blocked, "expected one"):
            audit_catalogue(body(a[1:]))

    def test_duplicate_uuid_blocks(self):
        a = [fake(dep) for dep in DEPARTMENTS]
        a[1]["id"] = a[0]["id"]
        with self.assertRaisesRegex(Blocked, "UUID"):
            audit_catalogue(body(a))

    def test_mismatched_department_and_year_block(self):
        a = [fake(dep) for dep in DEPARTMENTS]
        a[0]["url"] = a[0]["url"].replace("H_02_", "H_59_")
        with self.assertRaisesRegex(Blocked, "basename"):
            audit_catalogue(body(a))
        a[0] = fake(DEPARTMENTS[0])
        a[0]["url"] = a[0]["url"].replace(PERIOD, "2021-2025")
        with self.assertRaisesRegex(Blocked, "basename"):
            audit_catalogue(body(a))

    def test_remote_host_and_signed_url_block(self):
        a = [fake(dep) for dep in DEPARTMENTS]
        a[0]["url"] = "https://unapproved.example/file.csv.gz"
        with self.assertRaisesRegex(Blocked, "official source path"):
            audit_catalogue(body(a))
        a[0] = fake(DEPARTMENTS[0])
        a[0]["url"] += "?temporary-signature=secret"
        with self.assertRaises(Blocked):
            audit_catalogue(body(a))

    def test_invalid_file_byte_sizes_block(self):
        for invalid in (-1, 0, 40000000, True, None):
            a = [fake(dep) for dep in DEPARTMENTS]
            a[0]["filesize"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(Blocked):
                audit_catalogue(body(a))

    def test_json_duplicate_keys_block(self):
        with self.assertRaisesRegex(Blocked, "duplicate"):
            audit_catalogue(b'{"resources":[],"resources":[]}')

    def test_metadata_not_station_data(self):
        audit = audit_catalogue(body())
        encoded = json.dumps(audit)
        self.assertNotIn("NUM_POSTE", encoded)
        self.assertNotIn("FXI3S", encoded)
        self.assertNotIn("station_count", encoded)


if __name__ == "__main__":
    unittest.main()
