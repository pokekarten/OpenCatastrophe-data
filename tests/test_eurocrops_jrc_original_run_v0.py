# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fabricated-byte tests for exact JRC receipt runner; NO provider fetch."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_runners import eurocrops_jrc_original_run_v0 as m


class Response:
    status = 200
    headers = {}

    def __init__(self, content, url):
        self.data = BytesIO(content)
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.data.close()

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.data.read(limit)


class OriginalJrcRunnerTests(unittest.TestCase):
    @staticmethod
    def fixture_file(folder):
        path = Path(folder) / m.JRC_FILE
        suffix = (b"toy-footer-" * 1478)[:m.FOOTER_BYTES - 8]
        suffix += (m.FOOTER_BYTES - 8).to_bytes(4, "little") + b"PAR1"
        with path.open("xb") as out:
            out.write(b"PAR1")
            out.seek(10_200_000)
            out.write(suffix)
        digest = sha256(path.read_bytes()).hexdigest()
        return path, suffix, digest

    def test_byte_receipt_needs_full_sha_and_exact_pinned_footer(self):
        with tempfile.TemporaryDirectory() as folder:
            file, tail, digest = self.fixture_file(folder)
            with patch.object(
                m, "OBSERVED_ORIGINAL_FOOTER_SHA256", sha256(tail).hexdigest()
            ):
                receipt = m.verified_original(file, digest)
                self.assertTrue(
                    receipt["independently_observed_footer_sha256_matched"])
                self.assertFalse(receipt["original_publisher_signed_full_checksum_verified"])
                self.assertEqual(receipt["first_seen_full_original_sha256"], digest)
                with self.assertRaisesRegex(m.Blocked, "full-original"):
                    m.verified_original(file, "0" * 64)

    def test_file_mismatch_and_incomplete_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            file, tail, digest = self.fixture_file(folder)
            with self.assertRaisesRegex(m.Blocked, "footer differs"):
                m.verified_original(file, digest)
            with self.assertRaises(m.Blocked):
                m.verified_original(file, "bad-hash")
            with self.assertRaises(m.Blocked):
                m.verified_original(Path(folder) / "wrong_2023.parquet", digest)
            file.write_bytes(b"PAR1toyPAR1")
            with self.assertRaisesRegex(m.Blocked, "size"):
                m.verified_original(file, sha256(file.read_bytes()).hexdigest())

    def test_exact_commit_pinned_codebook_origin_and_hash(self):
        raw = b"made-up-original-crop-taxonomy-for-offline-test"
        url = m._approved_raw_url("eurocrops.csv")
        with patch.dict(m.BOOKS, {"eurocrops.csv": m.git_blob_sha(raw)}):
            got = m.download_pinned_codebook(
                "eurocrops.csv",
                opener=lambda req, timeout: Response(raw, url)
            )
            self.assertEqual(got, raw)
            with self.assertRaisesRegex(m.Blocked, "codebook blob mismatch"):
                m.download_pinned_codebook(
                    "eurocrops.csv",
                    opener=lambda req, timeout: Response(b"changed", url)
                )
            with self.assertRaisesRegex(m.Blocked, "redirected"):
                m.download_pinned_codebook(
                    "eurocrops.csv",
                    opener=lambda req, timeout: Response(raw, "https://example.com/x")
                )
        with self.assertRaisesRegex(m.Blocked, "unapproved"):
            m._approved_raw_url("secrets.env")

    def test_bad_original_source_admission_metadata_is_blocked(self):
        with patch.object(m, "verified_original", return_value={
            "original_filename": m.JRC_FILE
        }), patch.object(m, "inspect_local", return_value={
            "source_region": "dea",
            "source_year": 2023,
            "parquet_total_rows_from_footer": m.EXPECTED_FOOTER_ROWS,
            "geo": {"primary_geometry_column": "geometry", "crs": "EPSG:3035"},
            "taxonomy_crosswalk_checked": True,
            "full_original_area_ha_scan_checked": True,
        }):
            with self.assertRaisesRegex(m.Blocked, "original provider metadata"):
                m.original_quality_report(
                    Path("toy/de4_2023.parquet"), "0" * 64,
                    Path("toy/mapping.csv"), Path("toy/hcat4.csv")
                )

    def test_report_contains_counts_only_and_not_insurer_admission(self):
        qc = {
            "source_region": "de4", "source_year": 2023,
            "source_url": "https://jeodpp.jrc.ec.europa.eu/original",
            "parquet_total_rows_from_footer": m.EXPECTED_FOOTER_ROWS,
            "parquet_row_groups": 1,
            "geo": {"primary_geometry_column": "geometry", "crs": "EPSG:3035"},
            "taxonomy_crosswalk_checked": True,
            "full_original_area_ha_scan_checked": True,
            "full_original_area_ha_scan": {
                "original_area_rows_scanned": m.EXPECTED_FOOTER_ROWS,
                "original_area_ha_zero_count": 17
            },
            "original_footer_column_quality": {},
            "sample": {"sampled": 512},
            "sampled_row_groups": 1,
            "sample_taxonomy_crosswalk": {"resolved_to_hcat4_rows": 490},
        }
        with patch.object(m, "verified_original", return_value={
            "original_filename": m.JRC_FILE
        }), patch.object(m, "inspect_local", return_value=qc):
            result = m.original_quality_report(
                Path("toy/de4_2023.parquet"), "0" * 64,
                Path("toy/mapping.csv"), Path("toy/hcat4.csv"), max_rows=512
            )
        self.assertEqual(result["complete_area_ha_attribute_quality"][
            "original_area_ha_zero_count"], 17)
        self.assertFalse(result["raw_original_source_rows_redistributed"])
        self.assertEqual(result["rights_scientific_and_insurer_model_admission"],
                         "NOT_ADMITTED")
        self.assertFalse(result["insured_value_hazard_damage_and_cat_losses_calculated"])
        self.assertNotIn("source_original_rows", result)
