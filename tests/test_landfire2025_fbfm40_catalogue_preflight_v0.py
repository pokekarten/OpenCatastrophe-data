# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests of LANDFIRE 2025 publication-identity conflicts."""
from __future__ import annotations

import copy
import json
import unittest

from scripts.landfire2025_fbfm40_catalogue_preflight_v0 import (
    ARCHIVE_PATH, LandfireCatalogueError, MAX_EVIDENCE_BYTES,
    screen_landfire2025_fbfm40_catalogue_claims,
)


def snapshot(label: str, *, checksum: str = "a" * 32, size: str = "620 MB") -> dict[str, str]:
    return {
        "capture_id": label,
        "captured_at_utc": "2026-11-16T20:00:00Z",
        "product_page_url": "https://landfire.gov/node/6145",
        "product": "FBFM40", "version": "LF 2025", "region": "CONUS", "theme": "Fuel",
        "archive_relative_path": ARCHIVE_PATH,
        "published_checksum_32hex": checksum, "published_size_label": size,
    }


def encoded(*snapshots: dict[str, str]) -> bytes:
    return json.dumps({"snapshots": list(snapshots)}, separators=(",", ":")).encode("utf-8")


class LANDFIRECatalogueTests(unittest.TestCase):
    def test_agreement_does_not_authenticate_original_or_grant_rights(self):
        a, b = snapshot("web_capture"), snapshot("mirror_capture")
        b["product_page_url"] = "https://www.landfire.gov/node/6145"
        output = screen_landfire2025_fbfm40_catalogue_claims(encoded(a, b))
        self.assertEqual(output["catalogue_claim_status"], "agreeing_claims_not_original_verified")
        self.assertEqual(output["distinct_publisher_32hex_claims"], 1)
        for f in ("provider_checksum_algorithm_confirmed", "original_archive_sha256_verified",
                  "independent_provider_page_byte_provenance_verified", "commercial_rights_and_automation_verified",
                  "raster_crs_resolution_and_categories_verified", "insurer_cat_model_input_approved"):
            self.assertFalse(output[f])

    def test_checksum_and_size_conflicts_fail_closed_independently(self):
        samples = [
            (snapshot("capture_one"), snapshot("capture_two", checksum="b" * 32)),
            (snapshot("capture_one"), snapshot("capture_two", size="1.14 GB")),
            (snapshot("capture_one"), snapshot("capture_two", checksum="b" * 32, size="3.29 GB"),
             snapshot("capture_three", checksum="c" * 32, size="1.14 GB")),
        ]
        for row in samples:
            with self.subTest(sample=row):
                report = screen_landfire2025_fbfm40_catalogue_claims(encoded(*row))
                self.assertEqual(report["catalogue_claim_status"], "conflicting_blocked")
                self.assertFalse(report["original_archive_sha256_verified"])
                self.assertFalse(report["insurer_cat_model_input_approved"])

    def test_rejects_wrong_version_region_season_and_untrusted_shapes(self):
        mutations = [
            lambda x: x.update(product="EVT"),
            lambda x: x.update(version="LF 2024"),
            lambda x: x.update(region="AK"),
            lambda x: x.update(theme="Vegetation"),
            lambda x: x.update(archive_relative_path=ARCHIVE_PATH.replace("FBFM40", "EVT")),
            lambda x: x.update(archive_relative_path="/data-downloads/CONUS_LF2025/LF2025_SpringSeasonalFBFM40_CONUS.zip"),
            lambda x: x.update(product_page_url="https://attacker.invalid/node/6145"),
            lambda x: x.update(product_page_url="https://landfire.gov/node/6145?download=1"),
            lambda x: x.update(published_checksum_32hex="not a digest"),
            lambda x: x.update(published_checksum_32hex="A" * 32),
            lambda x: x.update(published_checksum_32hex="a" * 64),
            lambda x: x.update(published_size_label="0 MB"),
            lambda x: x.update(published_size_label="1 GB (compressed)"),
            lambda x: x.update(published_size_label="640 MiB"),
            lambda x: x.update(captured_at_utc="2026-11-16"),
            lambda x: x.update(captured_at_utc="2026-02-30T20:00:00Z"),
            lambda x: x.update(captured_at_utc="2026-11-16T20:00:00+01:00"),
            lambda x: x.update(capture_id="../unsafe"),
            lambda x: x.update(extra_field="unexpected"),
            lambda x: x.update(version=None),
        ]
        for i, mutate in enumerate(mutations):
            first = snapshot("capture_one")
            mutate(first)
            with self.subTest(index=i):
                with self.assertRaises(LandfireCatalogueError):
                    screen_landfire2025_fbfm40_catalogue_claims(encoded(first, snapshot("capture_two")))

    def test_refuses_duplicate_captures_json_keys_malformed_and_size_abuse(self):
        payloads = [
            b"", b"not JSON", b'{"snapshots":[],"snapshots":[]}',
            b'{"snapshots": NaN}', b"\x80" * 5,
            b"x" * (MAX_EVIDENCE_BYTES + 1),
            encoded(), encoded(snapshot("capture_one")),
            encoded(*[snapshot(f"capture_{i}") for i in range(9)]),
            encoded(snapshot("capture_one"), snapshot("capture_one")),
            json.dumps({"snapshots": [snapshot("capture_one"), 5]}).encode(),
            json.dumps({"snapshots": [snapshot("capture_one"), {"capture_id": "bad"}]}).encode(),
        ]
        for i, payload in enumerate(payloads):
            with self.subTest(index=i):
                with self.assertRaises(LandfireCatalogueError):
                    screen_landfire2025_fbfm40_catalogue_claims(payload)


if __name__ == "__main__":
    unittest.main()
