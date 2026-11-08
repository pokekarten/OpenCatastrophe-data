# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic tests for the original Zenodo v2 metadata acquirer."""

from __future__ import annotations

import csv
import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from zenodo_hail330_metadata_preflight_v0 import COLUMNS, COUNTRIES  # noqa: E402
from zenodo_hail330_metadata_acquire_v0 import (  # noqa: E402
    AcquisitionError, _check_url, write_verified_external,
)


def fake_metadata() -> bytes:
    sio = io.StringIO(newline="")
    writer = csv.writer(sio, lineterminator="\n")
    writer.writerow(COLUMNS)
    for country in COUNTRIES:
        for scenario in ("REF", "PGW"):
            writer.writerow((
                f"hail_{country}_{'ref' if scenario == 'REF' else 'PGW'}.h5",
                "model", country, scenario, "2.2", "hail", f"hail_{country}_{scenario}", "v2",
            ))
    return sio.getvalue().encode("utf-8")


class TestZenodoMetadataAcquisition(unittest.TestCase):
    def test_allowed_https_endpoint_and_rejected_redirect_hosts(self):
        _check_url("https://zenodo.org/records/17860440/files/metadata.csv?download=1")
        for url in (
            "http://zenodo.org/f", "https://evil.com/f", "https://zenodo.org.evil.com/f",
            "https://zenodo.org:444/f", "https://user:pass@zenodo.org/f", "file:///etc/passwd",
        ):
            with self.subTest(url=url), self.assertRaises(AcquisitionError):
                _check_url(url)

    def test_synthetic_original_receipt_written_external_and_exclusive(self):
        data = fake_metadata()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "metadata.csv"
            with patch("zenodo_hail330_metadata_preflight_v0.PUBLISHER_METADATA_MD5", hashlib.md5(data).hexdigest()):
                report = write_verified_external(target, data)
                self.assertEqual(report["file_count"], 56)
                self.assertEqual(target.read_bytes(), data)
                self.assertFalse(report["source_hdf5_bytes_checked"])
                with self.assertRaises(AcquisitionError):
                    write_verified_external(target, data)

    def test_wrong_source_digest_creates_no_output(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "metadata.csv"
            with self.assertRaisesRegex(AcquisitionError, "MD5 mismatch"):
                write_verified_external(target, fake_metadata())
            self.assertFalse(target.exists())

    def test_missing_pairs_creates_no_output_even_if_digest_matches(self):
        data = fake_metadata().splitlines(keepends=True)
        altered = b"".join(data[:-1])
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "metadata.csv"
            with patch("zenodo_hail330_metadata_preflight_v0.PUBLISHER_METADATA_MD5", hashlib.md5(altered).hexdigest()):
                with self.assertRaisesRegex(AcquisitionError, "56 country"):
                    write_verified_external(target, altered)
            self.assertFalse(target.exists())

    def test_refuses_path_inside_git_checkout_and_symlink(self):
        data = fake_metadata()
        with patch("zenodo_hail330_metadata_preflight_v0.PUBLISHER_METADATA_MD5", hashlib.md5(data).hexdigest()):
            with self.assertRaisesRegex(AcquisitionError, "outside Git checkout"):
                write_verified_external(Path(__file__).resolve().parents[1] / "fake-original.csv", data)
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "already").write_text("existing")
                (root / "link").symlink_to(root / "already")
                with self.assertRaises(AcquisitionError):
                    write_verified_external(root / "link", data)


if __name__ == "__main__":
    unittest.main()
