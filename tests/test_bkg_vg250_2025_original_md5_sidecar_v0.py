# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only BKG 2025 provider sidecar and source-drift regression tests."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from research_runners.bkg_vg250_2025_original_md5_sidecar_v0 import (
    ARCHIVE_NAME,
    ARCHIVE_URL,
    BkgVg250SidecarBlocked,
    MAX_SIDECAR_BYTES,
    OFFICIAL_PUBLISHED_MD5,
    SIDE_CAR_URL,
    inspect_local_file,
    inspect_original_sidecar,
    main,
)


def synthetic_sidecar(md5: str = OFFICIAL_PUBLISHED_MD5,
                      name: str = ARCHIVE_NAME,
                      *, newline: bytes = b"\n", spaces: bytes = b"  ") -> bytes:
    return md5.encode("ascii") + spaces + name.encode("ascii") + newline


class BkgOriginalSidecarSyntheticTests(unittest.TestCase):
    def test_published_metadata_identity_as_synthetic_only(self):
        raw = synthetic_sidecar()
        r = inspect_original_sidecar(raw)
        self.assertEqual(r["original_provider_sidecar_bytes"], len(raw))
        self.assertEqual(r["original_provider_sidecar_sha256"],
                         hashlib.sha256(raw).hexdigest())
        self.assertEqual(r["publisher_zip_md5_claim_from_original_sidecar"],
                         OFFICIAL_PUBLISHED_MD5)
        self.assertEqual(r["expected_zip_basename"], ARCHIVE_NAME)
        self.assertEqual(r["original_provider_sidecar_url"], SIDE_CAR_URL)
        self.assertEqual(r["archive_url_not_downloaded"], ARCHIVE_URL)
        self.assertFalse(r["full_zip_original_sha256_verified"])
        self.assertFalse(r["full_zip_original_bytes_acquired"])
        self.assertFalse(r["model_input_approved"])
        self.assertFalse(r["risk_geolocation_approved"])
        self.assertFalse(r["sidecar_bytes_or_original_zip_persisted"])

    def test_provider_text_and_binary_md5sum_variants(self):
        for raw in (synthetic_sidecar(newline=b"", spaces=b" "),
                    synthetic_sidecar(newline=b"\r\n", spaces=b" "),
                    synthetic_sidecar(newline=b"\n", spaces=b"  "),
                    OFFICIAL_PUBLISHED_MD5.encode() + b" *" + ARCHIVE_NAME.encode() + b"\n"):
            with self.subTest(raw=raw):
                self.assertEqual(inspect_original_sidecar(raw)
                                 ["publisher_zip_md5_claim_from_original_sidecar"],
                                 OFFICIAL_PUBLISHED_MD5)

    def test_altered_publisher_md5_blocks_both_old_version_and_zero_md5(self):
        for md5 in ("f" * 32, "0" * 32, "E6B4CF28D4B83557B4D6E3236713DEC0"):
            with self.subTest(md5=md5), self.assertRaises(BkgVg250SidecarBlocked):
                inspect_original_sidecar(synthetic_sidecar(md5))

    def test_wrong_vintage_format_territory_or_extra_filename_blocks(self):
        for name in (
            "vg250_01-01.utm32s.gpkg.ebenen.zip",
            "vg250-ew_12-31.utm32s.gpkg.ebenen.zip",
            "vg250_12-31.gk3.shape.ebenen.zip",
            "../vg250_12-31.utm32s.gpkg.ebenen.zip",
            ARCHIVE_NAME + ".zip",
            "VG250_12-31.utm32s.gpkg.ebenen.zip",
        ):
            with self.subTest(name=name), self.assertRaises(BkgVg250SidecarBlocked):
                inspect_original_sidecar(synthetic_sidecar(name=name))

    def test_multi_line_binary_control_and_whitespace_pollution_block(self):
        candidates = (
            synthetic_sidecar() + synthetic_sidecar(),
            synthetic_sidecar() + b"garbage",
            b"PK\x03\x04" + b"fake-archive",
            synthetic_sidecar(spaces=b"   "),
            synthetic_sidecar(newline=b"\n\n"),
            synthetic_sidecar().replace(b" ", b"\t"),
            synthetic_sidecar().replace(b"zip", b"zip\x00"),
            synthetic_sidecar().replace(b"zip", b"zip\xff"),
        )
        for raw in candidates:
            with self.subTest(length=len(raw)), self.assertRaises(BkgVg250SidecarBlocked):
                inspect_original_sidecar(raw)

    def test_byte_budget_and_untrusted_input_types(self):
        for raw in (None, b"", "", b" " * (MAX_SIDECAR_BYTES + 1)):
            with self.subTest(input_type=type(raw).__name__), self.assertRaises(
                    BkgVg250SidecarBlocked):
                inspect_original_sidecar(raw)

    def test_real_original_sha_must_not_be_implied_by_sidecar_md5(self):
        r = inspect_original_sidecar(synthetic_sidecar())
        self.assertNotIn("full_zip_sha256", r)
        self.assertFalse(r["full_zip_original_sha256_verified"])
        self.assertFalse(r["actual_zip_vintage_and_GPKG_layers_verified"])
        self.assertFalse(r["coastal_GF2_vs_GF4_land_semantics_verified_for_2025"])
        self.assertNotIn("source_coordinates", json.dumps(r))

    def test_local_regular_file_and_symlink_rejection(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            original = base / "original.md5"
            original.write_bytes(synthetic_sidecar())
            self.assertEqual(inspect_local_file(original)
                             ["expected_zip_basename"], ARCHIVE_NAME)
            original.write_bytes(b"y" * (MAX_SIDECAR_BYTES + 1))
            with self.assertRaises(BkgVg250SidecarBlocked):
                inspect_local_file(original)
            original.write_bytes(synthetic_sidecar())
            symlink = base / "redirect.md5"
            symlink.symlink_to(original)
            with self.assertRaises(BkgVg250SidecarBlocked):
                inspect_local_file(symlink)

    def test_cli_synthetic_offline_and_no_raw_stdout(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "sidecar"
            f.write_bytes(synthetic_sidecar())
            with mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(main(["--original-sidecar", str(f)]), 0)
                report = json.loads(out.getvalue())
                self.assertFalse(report["model_input_approved"])
                self.assertNotIn(OFFICIAL_PUBLISHED_MD5 + "  " + ARCHIVE_NAME,
                                 out.getvalue())

    def test_cli_unsafe_file_never_exposes_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "sidecar"
            f.write_bytes(b"private_response_token\n")
            with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
                self.assertEqual(main(["--original-sidecar", str(f)]), 2)
                self.assertNotIn("private_response_token", err.getvalue())


if __name__ == "__main__":
    unittest.main()
