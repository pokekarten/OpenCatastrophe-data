# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, source-free dry-run; mock CDS acquisition and real synthetic NetCDF."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_cds_original_source_one_shot_v0 as source

HAVE_NC = importlib.util.find_spec("netCDF4") is not None
if HAVE_NC:
    from netCDF4 import Dataset


def fake_netcdf(path: Path):
    with Dataset(path, "w", format="NETCDF4") as ds:
        ds.createDimension("time", 2)
        ds.createDimension("latitude", 1)
        ds.createDimension("longitude", 1)
        gust = ds.createVariable("i10fg", "f4", ("time", "latitude", "longitude"))
        gust.units = "m/s"
        gust[:] = [[[10.0]], [[12.0]]]
    return path


class ManualCDSNoSecretTests(unittest.TestCase):
    def test_public_preview_is_fixed_and_explicit_not_downloaded(self):
        preview = source.source_only_preview()
        self.assertEqual(preview["dataset"], "reanalysis-era5-single-levels-timeseries")
        self.assertEqual(preview["request"], {
            "variable": ["10m_wind_gust_since_previous_post_processing"],
            "date": ["2020-02-08", "2020-02-11"],
            "area": [52.5, 5.75, 50.25, 9.5],
            "data_format": "netcdf",
        })
        self.assertEqual(preview["max_rectangle_nodes"], 160)
        self.assertEqual(preview["occupied_2020_ERA5_grid_nodes_expected"], 93)
        self.assertEqual(len(preview["canonical_request_sha256"]), 64)
        self.assertFalse(preview["CDS_request_executed"])
        self.assertFalse(preview["original_CDS_downloaded_or_retained"])
        self.assertFalse(preview["terms_accepted_on_CDS_website_independently_verified"])
        self.assertFalse(preview["German_wind_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted"])

    def test_live_fails_closed_for_missing_consent_or_key_before_factory(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "file.nc"
            invocations = []
            def forbidden_factory(**kwargs):
                invocations.append(kwargs)
                raise AssertionError("network factory must not run")
            for terms, form, key in (
                ("", "", ""),
                (source.TERMS_SENTINEL, "", "opaque_fake_user_secret"),
                ("fake", source.FORM_SENTINEL, "opaque_fake_user_secret"),
                (source.TERMS_SENTINEL, source.FORM_SENTINEL, ""),
                (source.TERMS_SENTINEL, source.FORM_SENTINEL, "abc\nFake: token"),
            ):
                with self.subTest(terms=terms, form=form):
                    with self.assertRaises(source.CDSOriginalBlocked):
                        source.acquire(destination=target, terms=terms, api_form=form,
                                       api_key=key, client_factory=forbidden_factory)
            self.assertEqual(invocations, [])

    def test_cli_dry_run_never_sends_secrets_or_network_and_can_write_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = Path(td) / "public.json"
            with patch.object(sys, "argv", ["cds", "--dry-run", "--receipt-json", str(receipt)]):
                out = io.StringIO()
                with redirect_stdout(out):
                    self.assertEqual(source.main(), 0)
            metadata = json.loads(receipt.read_text())
            self.assertEqual(metadata["status"], "MANUAL_CDS_DATASET_TERMS_AND_API_REQUEST_FORM_REQUIRED")
            self.assertNotIn("CDSAPI_KEY", out.getvalue())
            self.assertNotIn("token", out.getvalue().lower())
            self.assertFalse(metadata["original_CDS_downloaded_or_retained"])
            with patch.object(sys, "argv", ["cds", "--dry-run", "--receipt-json", str(receipt)]):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
                    source.main()
            self.assertEqual(ctx.exception.code, 2)

    def test_forged_raw_file_and_symlink_fail_without_request(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "download.nc"
            raw.write_bytes(b"unsupported format" * 100)
            with self.assertRaisesRegex(source.CDSOriginalBlocked, "unrecognized"):
                source.inspect_original_response(raw)
            link = Path(td) / "link.nc"
            link.symlink_to(raw)
            with self.assertRaisesRegex(source.CDSOriginalBlocked, "non-regular"):
                source.inspect_original_response(link)


@unittest.skipUnless(HAVE_NC, "specialist optional netCDF4 dependency required")
class ManualCDSOriginalByteChecks(unittest.TestCase):
    def test_real_synthetic_netcdf_file_sha_and_metadata_not_loss(self):
        with tempfile.TemporaryDirectory() as td:
            raw = fake_netcdf(Path(td) / "from_mock.nc")
            data = source.inspect_original_response(raw)
            self.assertEqual(data["original_response_sha256"],
                             hashlib.sha256(raw.read_bytes()).hexdigest())
            self.assertEqual(data["original_response_format"], "NETCDF")
            self.assertEqual(data["dimension_lengths"], {"time": 2, "latitude": 1, "longitude": 1})
            self.assertEqual(data["variables"]["i10fg"]["units"], "m/s")
            self.assertTrue(data["actual_CDS_time_grid_and_gust_not_yet_normalized_or_admitted"])

    def test_real_synthetic_zip_source_package_crc_and_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            original = fake_netcdf(folder / "sample.nc")
            bundle = folder / "response.zip"
            with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(original, "source.nc")
            d = source.inspect_original_response(bundle)
            self.assertEqual(d["original_response_format"], "ZIP_WITH_ONE_NC")
            self.assertEqual(d["original_netcdf_member_sha256"],
                             hashlib.sha256(original.read_bytes()).hexdigest())
            for name in ("../escape.nc", "folder/data.nc"):
                with self.subTest(name=name):
                    bad = folder / "bad.zip"
                    with zipfile.ZipFile(bad, "w") as z:
                        z.write(original, name)
                    with self.assertRaises(source.CDSOriginalBlocked):
                        source.inspect_original_response(bad)

    def test_mock_live_auth_original_shas_and_no_insurer_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "source.nc"
            key = "opaque_mock_secret_NEVER_DISPLAY"
            calls = []
            class Client:
                def __init__(self, **kwargs):
                    calls.append(kwargs)
                def retrieve(self, dataset, request, target):
                    self.dataset, self.request = dataset, request
                    fake_netcdf(Path(target))
            metadata = source.acquire(
                destination=raw, terms=source.TERMS_SENTINEL,
                api_form=source.FORM_SENTINEL, api_key=key,
                client_factory=Client
            )
            self.assertTrue(raw.is_file())
            self.assertEqual(calls[0]["key"], key)
            self.assertFalse(metadata["original_provider_published_independent_sha256_matched"])
            self.assertFalse(metadata["observed_insured_2020_Ciara_losses_loaded"])
            self.assertFalse(metadata["German_wind_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted"])
            self.assertEqual(metadata["original_response_sha256"],
                             hashlib.sha256(raw.read_bytes()).hexdigest())
            self.assertNotIn(key, str(metadata))

    def test_failed_mock_live_never_keeps_original_response(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "bad.nc"
            class BrokenClient:
                def __init__(self, **kwargs):
                    pass
                def retrieve(self, dataset, request, target):
                    Path(target).write_bytes(b"REJECT INVALID HEADER" * 100)
            with self.assertRaises(source.CDSOriginalBlocked):
                source.acquire(destination=raw, terms=source.TERMS_SENTINEL,
                               api_form=source.FORM_SENTINEL,
                               api_key="opaque_mock_secret",
                               client_factory=BrokenClient)
            self.assertFalse(raw.exists())


if __name__ == "__main__":
    unittest.main()
