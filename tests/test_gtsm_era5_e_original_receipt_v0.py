# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-only regression tests; no external provider bytes."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request

from scripts import gtsm_era5_e_original_receipt_v0 as mod

from scripts.gtsm_era5_e_original_receipt_v0 import (
    GtsmReceiptError, HDF5_MAGIC, _file_receipt, verify_original,
)


class GtsmReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.nc"

    def fixture(self, prefix: bytes = HDF5_MAGIC):
        data = prefix + b"independently invented bytes only" * 7
        self.path.write_bytes(data)
        return data

    def verify_fixture(self, data: bytes):
        return _file_receipt(self.path, expected_size=len(data),
                             expected_md5=hashlib.md5(data, usedforsecurity=False).hexdigest())

    def test_positive_hdf5_synthetic(self):
        data = self.fixture()
        result = self.verify_fixture(data)
        self.assertEqual(result["container_signature"], "netcdf4_hdf5")
        self.assertEqual(result["sha256_observed_not_publisher_pinned"], hashlib.sha256(data).hexdigest())

    def test_positive_classic_synthetic(self):
        data = self.fixture(b"CDF\x02")
        self.assertEqual(self.verify_fixture(data)["container_signature"], "netcdf_classic")

    def test_wrong_publisher_digest_rejected(self):
        data = self.fixture()
        with self.assertRaises(GtsmReceiptError):
            _file_receipt(self.path, expected_size=len(data), expected_md5="0" * 32)

    def test_wrong_length_rejected(self):
        data = self.fixture()
        with self.assertRaises(GtsmReceiptError):
            _file_receipt(self.path, expected_size=len(data) + 1,
                          expected_md5=hashlib.md5(data, usedforsecurity=False).hexdigest())

    def test_malformed_netcdf_signature_rejected_even_if_md5_matches(self):
        data = self.fixture(b"NOTNC123")
        with self.assertRaises(GtsmReceiptError):
            self.verify_fixture(data)

    def test_symlink_rejected(self):
        data = self.fixture()
        link = self.path.with_name("link.nc")
        link.symlink_to(self.path)
        with self.assertRaises(GtsmReceiptError):
            _file_receipt(link, expected_size=len(data),
                          expected_md5=hashlib.md5(data, usedforsecurity=False).hexdigest())

    def test_public_entry_point_never_accepts_synthetic_pin_override(self):
        self.fixture()
        with self.assertRaises(GtsmReceiptError):
            verify_original(self.path)


    def test_fixed_publisher_target(self):
        self.assertEqual(mod.SOURCE_BYTES, 9_652_424)
        self.assertEqual(mod.SOURCE_MD5, "0f2b7071c6ec3585768be6cf427e6eab")
        self.assertEqual(mod.PINNED_SHA256, "e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767")
        self.assertEqual(mod.SOURCE_DOWNLOAD_URL, (
            "https://zenodo.org/records/14671593/files/"
            "ds_GTSM-ERA5-E_1950-2024_stats.nc?download=1"
        ))

    def test_non_publisher_redirect_rejected(self):
        handler = mod._ZenodoOnlyRedirect()
        for url in ("https://example.org/fake.nc", "http://zenodo.org/fake.nc"):
            with self.subTest(url=url):
                with self.assertRaises(GtsmReceiptError):
                    handler.redirect_request(Request(mod.SOURCE_DOWNLOAD_URL), None, 302,
                                             "Found", {}, url)

    def test_fetch_denies_unexpected_final_host(self):
        class FakeResponse:
            status = 200
            headers = {"Content-Length": str(mod.SOURCE_BYTES)}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def geturl(self): return "https://example.org/changed"
            def read(self, n): raise AssertionError("unexpected source read")
        class Opener:
            def open(self, *args, **kwargs): return FakeResponse()
        with patch.object(mod, "build_opener", return_value=Opener()):
            with self.assertRaises(GtsmReceiptError):
                mod.fetch_verified_original()

    def test_fetch_denies_incorrect_header_before_read(self):
        class FakeResponse:
            status = 200
            headers = {"Content-Length": "3"}
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def geturl(self): return mod.SOURCE_DOWNLOAD_URL
            def read(self, n): raise AssertionError("unexpected source read")
        class Opener:
            def open(self, *args, **kwargs): return FakeResponse()
        with patch.object(mod, "build_opener", return_value=Opener()):
            with self.assertRaises(GtsmReceiptError):
                mod.fetch_verified_original()


    def test_wrong_sha256_rejected_even_with_matching_mock_publisher_md5(self):
        data = self.fixture()
        valid_structure = self.verify_fixture(data)
        with patch.object(mod, "_file_receipt", return_value=valid_structure):
            with self.assertRaisesRegex(GtsmReceiptError, "SHA-256"):
                verify_original(self.path)

    def test_scientific_header_cannot_precede_exact_original_sha(self):
        self.fixture()
        with patch.object(mod, "inspect_scientific_header") as reader:
            with self.assertRaises(GtsmReceiptError):
                verify_original(self.path, inspect_header=True)
            reader.assert_not_called()


    def native_header_example(self):
        dims = dict(mod.EXPECTED_NATIVE_DIMS)
        fields = [
            {"name": name, "dimensions": list(axes),
             "shape": [dims[axis] for axis in axes], "units": units, "dtype": dtype}
            for name, (axes, units, dtype) in mod.EXPECTED_NATIVE_FIELDS.items()
        ]
        return dims, fields

    def test_original_observed_header_contract_synthetic(self):
        dims, fields = self.native_header_example()
        mod.validate_native_header(dims, fields)

    def test_native_header_rejects_missing_station(self):
        dims, fields = self.native_header_example()
        dims["stations"] -= 1
        with self.assertRaises(GtsmReceiptError):
            mod.validate_native_header(dims, fields)

    def test_native_header_rejects_metre_to_centimetre_drift(self):
        dims, fields = self.native_header_example()
        next(x for x in fields if x["name"] == "wl_extreme_bestfit")["units"] = "cm"
        with self.assertRaisesRegex(GtsmReceiptError, "units"):
            mod.validate_native_header(dims, fields)

    def test_native_header_rejects_native_coordinate_type_drift(self):
        dims, fields = self.native_header_example()
        next(x for x in fields if x["name"] == "lon")["dtype"] = "float64"
        with self.assertRaises(GtsmReceiptError):
            mod.validate_native_header(dims, fields)


    def test_native_coordinate_packing_synthetic(self):
        mod.validate_coordinate_packing({
            "lon": dict(mod.EXPECTED_COORD_PACKING["lon"]),
            "lat": dict(mod.EXPECTED_COORD_PACKING["lat"]),
        })

    def test_scaled_coordinates_must_not_drop_scale_or_fill_marker(self):
        for field, bad_value in (("scale_factor", None), ("scale_factor", "1.0"),
                                 ("_FillValue", "0"), ("add_offset", "1.0")):
            with self.subTest(field=field, bad_value=bad_value):
                packing = {name: dict(value) for name, value in mod.EXPECTED_COORD_PACKING.items()}
                packing["lon"][field] = bad_value
                with self.assertRaises(GtsmReceiptError):
                    mod.validate_coordinate_packing(packing)


    def test_coordinate_audit_requires_validated_header(self):
        self.fixture()
        with patch.object(mod, "_file_receipt") as receipt:
            with self.assertRaises(GtsmReceiptError):
                verify_original(self.path, audit_coordinates=True)
            receipt.assert_not_called()

    def test_coordinate_audit_requires_exact_source_sha(self):
        self.fixture()
        with patch.object(mod, "audit_original_coordinates") as location_reader:
            with self.assertRaises(GtsmReceiptError):
                verify_original(self.path, inspect_header=True, audit_coordinates=True)
            location_reader.assert_not_called()


    def test_statistical_axis_read_requires_validated_header(self):
        self.fixture()
        with patch.object(mod, "_file_receipt") as receipt:
            with self.assertRaises(GtsmReceiptError):
                verify_original(self.path, inspect_labels=True)
            receipt.assert_not_called()

    def test_statistical_axis_read_requires_exact_sha256(self):
        self.fixture()
        with patch.object(mod, "inspect_original_level_labels") as label_reader:
            with self.assertRaises(GtsmReceiptError):
                verify_original(self.path, inspect_header=True, inspect_labels=True)
            label_reader.assert_not_called()


    def test_return_level_audit_requires_native_header_and_year_axes(self):
        self.fixture()
        with patch.object(mod, "_file_receipt") as byte_reader:
            with self.assertRaises(GtsmReceiptError):
                verify_original(self.path, audit_return_levels=True)
            with self.assertRaises(GtsmReceiptError):
                verify_original(self.path, inspect_header=True, audit_return_levels=True)
            byte_reader.assert_not_called()

    def test_return_level_audit_rejects_wrong_original_sha_before_matrix_read(self):
        self.fixture()
        with patch.object(mod, "audit_original_return_levels") as reader:
            with self.assertRaises(GtsmReceiptError):
                verify_original(self.path, inspect_header=True, inspect_labels=True,
                                audit_return_levels=True)
            reader.assert_not_called()


    def test_source_native_release_header_metadata_is_strictly_allowlisted(self):
        result = mod.select_original_release_attributes({
            "license": "Creative Commons Attribution 4.0 International",
            "history": "This is version 2 of the dataset",
            "provider_data": "not published",
        })
        self.assertEqual(
            result["license"], "Creative Commons Attribution 4.0 International"
        )
        self.assertNotIn("provider_data", result)
        self.assertIsNone(result["time_coverage_start"])

    def test_native_release_header_rejects_nonstring_and_unsafe_values(self):
        for malformed in (42, "\n", "a" * 257, "x\ty", "é"):
            with self.subTest(value=str(malformed)[:25]):
                with self.assertRaises(GtsmReceiptError):
                    mod.select_original_release_attributes({"license": malformed})

    def test_no_original_file_rejected(self):
        with self.assertRaises(GtsmReceiptError):
            _file_receipt(self.path, expected_size=10, expected_md5="0" * 32)


if __name__ == "__main__":
    unittest.main()
