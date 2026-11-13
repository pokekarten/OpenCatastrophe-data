# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic DWD corrected 2021 gzip/TAR/NetCDF prefix regression tests."""
from __future__ import annotations

import hashlib
import json
import tarfile
import unittest
import zlib

from research_runners import dwd_radklim_2021_corrected_prefix_header_v0 as m


def synthetic_prefix(
    *, dirname="2021/", member=m.FIRST_MEMBER,
    member_size=m.FIRST_MEMBER_BYTES, magic=m.NETCDF4_MAGIC,
):
    directory = tarfile.TarInfo(dirname)
    directory.type = tarfile.DIRTYPE
    directory.size = 0
    first = tarfile.TarInfo(member)
    first.type = tarfile.REGTYPE
    first.size = member_size
    tar_start = (directory.tobuf(format=tarfile.USTAR_FORMAT)
                 + first.tobuf(format=tarfile.USTAR_FORMAT)
                 + magic)
    assert len(tar_start) == m.REQUIRED_DECOMPRESSED_PREFIX
    comp = zlib.compressobj(level=6, wbits=16 + zlib.MAX_WBITS)
    return comp.compress(tar_start) + comp.flush(zlib.Z_SYNC_FLUSH)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class DWD2021CorrectedPrefixTests(unittest.TestCase):
    def inspect(self, raw=None, **kw):
        raw = synthetic_prefix() if raw is None else raw
        args = {"source_url": m.CORRECTED_URL, "expected_range_sha256": sha(raw)}
        args.update(kw)
        return m.inspect_corrected_2021_prefix(raw, **args)

    def test_native_file_signature_is_structural_only(self):
        result = self.inspect()
        self.assertEqual(result["first_month_member"], "2021/RW_2017.002_202107.nc")
        self.assertEqual(result["first_month_member_declared_bytes"], 91_356_907)
        self.assertTrue(result["native_netcdf4_hdf5_signature_verified"])
        self.assertFalse(result["full_archive_sha256_verified"])
        self.assertFalse(result["full_month_netcdf_verified"])
        self.assertFalse(result["all_2021_months_verified"])
        self.assertFalse(result["precipitation_values_verified"])
        self.assertFalse(result["provider_request_executed"])
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("2021/", json.dumps(result).replace(result["first_month_member"], ""))

    def test_original_bad_2021_archive_and_unreviewed_version_blocked(self):
        for url in (m.UNSAFE_ORIGINAL_URL, m.CORRECTED_URL + "?download=1",
                    m.CORRECTED_URL.replace("2021", "2020"),
                    "https://attacker.invalid/test.tar.gz"):
            with self.subTest(url=url), self.assertRaises(m.DWD2021PrefixBlocked):
                self.inspect(source_url=url)

    def test_header_integrity_checks_dir_and_month(self):
        for args in (
            {"dirname": "2020/"},
            {"member": "2021/RW_2017.002_202108.nc"},
            {"member_size": m.FIRST_MEMBER_BYTES + 1},
            {"magic": b"\x89HDF\r\n\x00\n"},
        ):
            with self.subTest(args=args), self.assertRaises(m.DWD2021PrefixBlocked):
                self.inspect(synthetic_prefix(**args))

    def test_sha_and_gzip_and_size_guards(self):
        raw = synthetic_prefix()
        for bad in ("0" * 64, "not_a_sha", "A" * 64):
            with self.subTest(sha=bad), self.assertRaises(m.DWD2021PrefixBlocked):
                self.inspect(raw, expected_range_sha256=bad)
        for bad in (b"plain", b"", b"x" * 2049, raw[:10]):
            with self.subTest(size=len(bad)), self.assertRaises(m.DWD2021PrefixBlocked):
                self.inspect(bad)

    def test_tampered_tar_checksum_is_blocked(self):
        directory = tarfile.TarInfo("2021/")
        directory.type = tarfile.DIRTYPE
        first = tarfile.TarInfo(m.FIRST_MEMBER)
        first.size = m.FIRST_MEMBER_BYTES
        body = bytearray(directory.tobuf(format=tarfile.USTAR_FORMAT)
                         + first.tobuf(format=tarfile.USTAR_FORMAT)
                         + m.NETCDF4_MAGIC)
        body[2] ^= 1  # Flips original TAR header without recalculating checksum.
        comp = zlib.compressobj(wbits=31)
        raw = comp.compress(bytes(body)) + comp.flush(zlib.Z_SYNC_FLUSH)
        with self.assertRaisesRegex(m.DWD2021PrefixBlocked, "checksum"):
            self.inspect(raw)

    def test_frozen_original_wrapper_requires_prior_original_provider_digest(self):
        # Synthetic bytes can pass structural checks with a synthetic SHA but
        # cannot impersonate the reviewed 2026-11-12 provider range receipt.
        with self.assertRaises(m.DWD2021PrefixBlocked):
            m.inspect_frozen_original_prefix(synthetic_prefix())
        with self.assertRaises(m.DWD2021PrefixBlocked):
            m.inspect_frozen_original_prefix(b"x" * 2048)
        self.assertEqual(len(m.FROZEN_PREFIX_SHA256), 64)

    def test_never_emit_original_data(self):
        data = self.inspect()
        self.assertNotIn("first_raster_pixel", data)
        self.assertNotIn("precipitation", {
            key for key in data if key == "precipitation"})
        self.assertIs(data["source_bytes_exported"], False)


if __name__ == "__main__":
    unittest.main()
