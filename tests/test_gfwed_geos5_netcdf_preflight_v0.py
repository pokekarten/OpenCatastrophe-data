# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic NASA GFWED NetCDF receipt tests; no external source bytes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch
import sys
import types

from research_runners.gfwed_geos5_netcdf_preflight_v0 import (
    GFWEDPreflightError, MAX_ORIGINAL_BYTES, SOURCE_NAME, HDF5_SIG,
    inspect_local_original, netcdf_container_type, inventory_header, write_receipt,
)


class GFWEDNetCDFPreflightTests(TestCase):
    def synthetic(self, root: Path, data: bytes = b"CDF\x02synthetic") -> Path:
        source = root / SOURCE_NAME
        source.write_bytes(data)
        return source

    def test_synthetic_container_retains_all_nonadmission_gates(self):
        with tempfile.TemporaryDirectory() as d:
            source = self.synthetic(Path(d))
            receipt = inspect_local_original(source, expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(receipt["original_byte_evidence"]["original_container_signature"], "netcdf_64bit_offset")
            self.assertTrue(receipt["original_byte_evidence"]["verified_against_operator_supplied_sha256"])
            self.assertFalse(receipt["original_byte_evidence"]["external_pin_proven_independent_of_file_by_tool"])
            for key in ("provider_rights_cleared", "commercial_use_approved", "scientific_fitness_approved", "model_source_admitted", "source_downloaded_by_this_tool", "data_synced_to_neon"):
                self.assertFalse(receipt[key])
            self.assertIsNone(receipt["netcdf_header_inventory"])

    def test_recognized_container_signatures(self):
        for signature in (b"CDF\x01xxxx", b"CDF\x02xxxx", b"CDF\x05xxxx", HDF5_SIG + b"xxxx"):
            with self.subTest(signature=signature[:4]):
                self.assertIsInstance(netcdf_container_type(signature), str)

    def test_rejects_wrong_signature(self):
        with self.assertRaisesRegex(GFWEDPreflightError, "signature"):
            netcdf_container_type(b"ZIP signature-not-valid")

    def test_rejects_sha_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            source = self.synthetic(Path(d))
            with self.assertRaisesRegex(GFWEDPreflightError, "SHA-256 differs"):
                inspect_local_original(source, expected_sha256="0" * 64)

    def test_rejects_missing_or_nonhex_pin(self):
        with tempfile.TemporaryDirectory() as d:
            source = self.synthetic(Path(d))
            with self.assertRaisesRegex(GFWEDPreflightError, "expected SHA-256"):
                inspect_local_original(source, expected_sha256="not-a-hash")

    def test_rejects_renamed_source(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "other.nc"
            p.write_bytes(b"CDF\x02abcd")
            with self.assertRaisesRegex(GFWEDPreflightError, "filename"):
                inspect_local_original(p, expected_sha256=hashlib.sha256(p.read_bytes()).hexdigest())

    def test_rejects_symlink_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            original = root / "original.nc"
            original.write_bytes(b"CDF\x02abcdef")
            alias = root / SOURCE_NAME
            alias.symlink_to(original)
            with self.assertRaisesRegex(GFWEDPreflightError, "non-symlink"):
                inspect_local_original(alias, expected_sha256=hashlib.sha256(original.read_bytes()).hexdigest())

    def test_rejects_oversized_file_before_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / SOURCE_NAME
            with p.open("wb") as h:
                h.truncate(MAX_ORIGINAL_BYTES + 1)
            with self.assertRaisesRegex(GFWEDPreflightError, "128-MiB"):
                inspect_local_original(p, expected_sha256="0" * 64)

    def test_rejects_empty_short_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.synthetic(Path(d), b"CDF\x01")
            with self.assertRaisesRegex(GFWEDPreflightError, "8-byte"):
                inspect_local_original(p, expected_sha256=hashlib.sha256(p.read_bytes()).hexdigest())

    def test_write_receipt_privately_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "receipt.json"
            write_receipt(path, {"model_source_admitted": False})
            self.assertFalse(json.loads(path.read_text())["model_source_admitted"])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(GFWEDPreflightError, "exists"):
                write_receipt(path, {})

    def test_write_receipt_rejects_symlink_target(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            actual = root / "existing.json"
            actual.write_text("keep", encoding="utf-8")
            alias = root / "linked.json"
            alias.symlink_to(actual)
            with self.assertRaises(GFWEDPreflightError):
                write_receipt(alias, {})
            self.assertEqual(actual.read_text(), "keep")

    def test_metadata_inventory_with_synthetic_dataset_object(self):
        class Dim:
            def __init__(self, count): self.count = count
            def __len__(self): return self.count
        class Var:
            def __init__(self, axes, shape, dtype, units):
                self.dimensions, self.shape, self.dtype, self._units = axes, shape, dtype, units
            def ncattrs(self): return ["units"]
            def getncattr(self, key): return self._units
            def __getitem__(self, key): raise AssertionError("scientific array values must not be loaded")
        class DS:
            dimensions = {"lat": Dim(2), "lon": Dim(3)}
            variables = {"FWI": Var(("lat", "lon"), (2, 3), "float32", "1")}
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): return False
        with patch.dict(sys.modules, {"netCDF4": types.SimpleNamespace(Dataset=DS)}):
            report = inventory_header(b"synthetic")
        self.assertEqual(report["dimensions"], {"lat": 2, "lon": 3})
        self.assertEqual(report["variables"][0]["name"], "FWI")
        self.assertFalse(report["netcdf_values_loaded"])
        self.assertFalse(report["fwi_indices_semantically_validated"])

    def test_metadata_inventory_rejects_inconsistent_shape(self):
        class Dim:
            def __len__(self): return 3
        class Var:
            dimensions = ("lat",)
            shape = (2,)
            dtype = "float32"
            def ncattrs(self): return []
        class DS:
            dimensions = {"lat": Dim()}
            variables = {"FWI": Var()}
            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): return False
        with patch.dict(sys.modules, {"netCDF4": types.SimpleNamespace(Dataset=DS)}):
            with self.assertRaisesRegex(GFWEDPreflightError, "shape"):
                inventory_header(b"synthetic")


if __name__ == "__main__":
    import unittest
    unittest.main()
