# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline integrity of a source-only CEMS archive receipt, never model admission."""
from __future__ import annotations

from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/research/cems-emns028-original-archive-receipt-20261101.toml"


class CemsEmsn028MetadataReceiptTests(unittest.TestCase):
    def test_exact_original_archive_receipt_remains_research_only(self):
        d = tomllib.loads(PATH.read_text(encoding="utf-8"))
        self.assertEqual(d["source_activation"], "EMSN028")
        self.assertEqual(d["exact_published_filename"], "EMNS028_AOI_FRANCE_utm31n.gdb.zip")
        self.assertEqual(d["source_provider"], "Copernicus Emergency Management Service (European Commission)")
        self.assertEqual(d["original_archive_bytes"], 155898548)
        self.assertEqual(d["original_archive_sha256"],
                         "7ef43d0637447abae705728723c06d2f05415a21667fdee1f10e8fc25b5bf3c2")
        self.assertRegex(d["original_archive_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(d["evidence_ci_url"],
                         "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41336175575")
        self.assertEqual(d["original_archive_zip_member_count"], 173)
        self.assertEqual(d["original_archive_declared_uncompressed_bytes"], 297718220)
        self.assertEqual(d["gdb_directories_detected"], 1)
        self.assertEqual(d["zip_member_extension_counts"][".gdbtable"], 30)
        self.assertEqual(d["zip_member_extension_counts"][".gdbtablx"], 30)
        self.assertIs(d["original_download_completed_ephemerally"], True)
        self.assertIs(d["original_archive_retained"], False)
        for key in ("archive_extracted", "archive_member_payloads_decompressed",
                    "aoi04_observed_extent_geometry_verified",
                    "historical_2016_building_geometry_verified",
                    "insurer_specific_tiv_or_loss_evidence", "model_input_approved"):
            self.assertIs(d[key], False)
        self.assertEqual(d["rights_review_status"],
                         "PENDING_ACTIVATION_SPECIFIC_AND_THIRD_PARTY_RIGHTS")

    def test_toml_duplicate_fields_fail_closed(self):
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads("source_activation = \"EMSN028\"\nsource_activation = \"EMNS028\"")


if __name__ == "__main__":
    unittest.main()
