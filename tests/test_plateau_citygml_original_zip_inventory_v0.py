# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only, no-network tests for local CityGML original ZIP inventory."""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from research_runners.plateau_citygml_original_zip_inventory_v0 import (
    ZipPreflightError, MAX_ZIP_BYTES, inspect_zip_file, main,
)


def synthetic_zip(
    members: list[tuple[str, bytes]] | None = None,
    compression: int = zipfile.ZIP_DEFLATED,
) -> bytes:
    if members is None:
        members = [
            ("13104_synthetic_2024_citygml/udx/bldg/53390000_bldg_6697_op.gml", b"<core:CityModel/>"),
            ("13104_synthetic_2024_citygml/udx/tran/53390000_tran_6697_op.gml", b"<core:CityModel/>"),
            ("13104_synthetic_2024_citygml/metadata/synthetic.xml", b"<metadata/>"),
        ]
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as archive:
        for name, data in members:
            archive.writestr(name, data)
    return output.getvalue()


def run_zip(payload: bytes, **kwargs) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "synthetic.zip"
        path.write_bytes(payload)
        return inspect_zip_file(path, **kwargs)


class PlateauOriginalZipInventoryTests(unittest.TestCase):
    def test_safe_inventory_and_hash_not_a_provider_admission(self):
        raw = synthetic_zip()
        outcome = run_zip(raw)
        self.assertEqual(outcome["local_zip_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(outcome["local_zip_byte_count"], len(raw))
        self.assertEqual(outcome["zip_member_count"], 3)
        self.assertEqual(outcome["citygml_file_count"], 2)
        self.assertEqual(outcome["building_citygml_file_count"], 1)
        self.assertGreater(outcome["declared_total_uncompressed_bytes"], 0)
        self.assertFalse(outcome["zip_member_contents_crc_verified"])
        for key in (
            "upstream_provider_authenticated",
            "zip_member_contents_crc_verified",
            "building_geometry_parsed",
            "municipality_and_year_in_archive_verified",
            "crs_and_vertical_datum_verified",
            "exact_dataset_licence_reviewed",
            "model_input_approved",
            "provider_network_access",
        ):
            self.assertFalse(outcome[key], key)
        self.assertNotIn("53390000", json.dumps(outcome))
        self.assertNotIn("synthetic.zip", json.dumps(outcome))
        self.assertNotIn("CityModel", json.dumps(outcome))

    def test_zip_name_cannot_falsely_assert_shinjuku_municipality_or_vintage(self):
        # This is explicitly a 2020 Hokota-like archive, not Shinjuku 2024.
        raw = synthetic_zip([
            ("08234_hokota-shi_2020_citygml/udx/bldg/synthetic.gml", b"<CityModel/>"),
        ])
        receipt = run_zip(raw)
        self.assertFalse(receipt["municipality_and_year_in_archive_verified"])
        self.assertNotIn("target_municipality_code", receipt)
        self.assertNotIn("target_release_fiscal_year", receipt)
        self.assertNotIn("13104", json.dumps(receipt))
        self.assertNotIn("08234", json.dumps(receipt))

    def test_explicit_matching_expectations_are_recorded_without_licence_claim(self):
        raw = synthetic_zip()
        outcome = run_zip(
            raw, expected_sha256=hashlib.sha256(raw).hexdigest(),
            expected_byte_count=len(raw),
        )
        self.assertTrue(outcome["expected_sha256_supplied"])
        self.assertTrue(outcome["expected_byte_count_supplied"])
        self.assertFalse(outcome["upstream_provider_authenticated"])

    def test_wrong_hash_or_byte_count_is_blocked(self):
        raw = synthetic_zip()
        with self.assertRaisesRegex(ZipPreflightError, "SHA-256"):
            run_zip(raw, expected_sha256="f" * 64)
        with self.assertRaisesRegex(ZipPreflightError, "byte count"):
            run_zip(raw, expected_byte_count=len(raw) + 1)

    def test_bad_digest_and_size_contracts_are_blocked(self):
        raw = synthetic_zip()
        for digest in ("", "g" * 64, "ABC" * 21 + "a"):
            with self.subTest(digest=digest[:6]):
                with self.assertRaises(ZipPreflightError):
                    run_zip(raw, expected_sha256=digest)
        for size in (0, -1, True, MAX_ZIP_BYTES + 1):
            with self.subTest(size=size):
                with self.assertRaises(ZipPreflightError):
                    run_zip(raw, expected_byte_count=size)

    def test_empty_and_truncated_zip_are_rejected(self):
        with self.assertRaises(ZipPreflightError):
            run_zip(b"")
        with self.assertRaises(ZipPreflightError):
            run_zip(synthetic_zip()[:25])

    def test_original_zip_without_bldg_gml_is_not_admitted(self):
        raw = synthetic_zip([("synthetic/udx/tran/sample.gml", b"<core:CityModel/>")])
        with self.assertRaisesRegex(ZipPreflightError, "no CityGML files under udx/bldg"):
            run_zip(raw)

    def test_extra_unknown_city_root_stays_unverified_not_mislabelled(self):
        raw = synthetic_zip([("13100_not_shinjuku_2020/udx/bldg/file.gml", b"<core:CityModel/>")])
        result = run_zip(raw)
        self.assertEqual(result["building_citygml_file_count"], 1)
        self.assertFalse(result["municipality_and_year_in_archive_verified"])

    def test_rejects_traversal_absolute_and_backslash_paths(self):
        for bad in ("../udx/bldg/hi.gml", "/udx/bldg/hi.gml", "C:/udx/bldg/hi.gml",
                    "root//udx/bldg/hi.gml", "root/./udx/bldg/hi.gml",
                    "root/udx/../bldg/hi.gml", "root\\udx\\bldg\\file.gml"):
            with self.subTest(bad=bad):
                with self.assertRaises(ZipPreflightError):
                    run_zip(synthetic_zip([(bad, b"abc")]))

    def test_rejects_duplicate_or_case_colliding_paths(self):
        for bad in ("root/udx/bldg/A.gml", "root/udx/bldg/a.gml"):
            raw = synthetic_zip([
                ("root/udx/bldg/a.gml", b"synthetic"), (bad, b"synthetic")])
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ZipPreflightError, "duplicate"):
                    run_zip(raw)

    def test_rejects_unix_symlink_members(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            info = zipfile.ZipInfo("root/udx/bldg/pointer.gml")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "../secret")
        with self.assertRaisesRegex(ZipPreflightError, "symbolic links"):
            run_zip(output.getvalue())

    def test_rejects_unsupported_compression(self):
        raw = synthetic_zip(compression=zipfile.ZIP_BZIP2)
        with self.assertRaisesRegex(ZipPreflightError, "unsupported compression"):
            run_zip(raw)

    def test_rejects_extreme_compression_ratio_without_decompression(self):
        raw = synthetic_zip([
            ("root/udx/bldg/zeros.gml", b"z" * (2 * 1024 * 1024)),
        ])
        with self.assertRaisesRegex(ZipPreflightError, "compression ratio"):
            run_zip(raw)

    def test_missing_local_path_rejected_without_path_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "secret-original.zip"
            err = io.StringIO()
            with redirect_stderr(err):
                result = main(["--input", str(missing)])
            self.assertEqual(result, 2)
            self.assertNotIn(str(missing), err.getvalue())
            self.assertIn("BLOCKED", err.getvalue())

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
    def test_symlink_input_rejected_without_following(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "synthetic.zip"
            link = Path(directory) / "alias.zip"
            target.write_bytes(synthetic_zip())
            link.symlink_to(target)
            with self.assertRaises(ZipPreflightError):
                inspect_zip_file(link)

    @unittest.skipUnless(hasattr(os, "mkfifo") and hasattr(os, "O_NONBLOCK"), "requires POSIX FIFO")
    def test_fifo_input_rejected_without_waiting(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "local-pipe"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(ZipPreflightError, "regular file"):
                inspect_zip_file(fifo)

    def test_cli_success_omits_filename_and_original_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-original.zip"
            raw = synthetic_zip()
            path.write_bytes(raw)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main([
                    "--input", str(path), "--expected-byte-count", str(len(raw)),
                    "--expected-sha256", hashlib.sha256(raw).hexdigest(),
                ])
            self.assertEqual(code, 0)
            self.assertEqual(err.getvalue(), "")
            result = json.loads(out.getvalue())
            self.assertEqual(result["building_citygml_file_count"], 1)
            self.assertNotIn(str(path), out.getvalue())
            self.assertNotIn("CityModel", out.getvalue())


if __name__ == "__main__":
    unittest.main()
