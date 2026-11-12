# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Mock only: anonymous Google Research ARCO metadata must not become weather/loss."""
from __future__ import annotations
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import tomllib
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_google_arco_public_10fg_metadata_v0 as p

N_TIME = 750000
N_LAT = 721
N_LON = 1440


def meta(name):
    if name == p.VAR:
        shape, chunks = [N_TIME, N_LAT, N_LON], [1, N_LAT, N_LON]
    elif name == "time":
        shape, chunks = [N_TIME], [N_TIME]
    elif name == "latitude":
        shape, chunks = [N_LAT], [N_LAT]
    else:
        shape, chunks = [N_LON], [N_LON]
    return dict(zarr_format=2, shape=shape, chunks=chunks, dtype="<f4",
                order="C", compressor={"id": "blosc"}, filters=None)


class FakeResponse(BytesIO):
    status = 200
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.close()


class FakeOpener:
    def __init__(self, alterations=None):
        self.alterations = alterations or {}
        self.called = []
    def open(self, req, timeout):
        name = req.full_url[len(p.PREFIX):].split("/")[0]
        self.called.append((req.full_url, timeout))
        data = deepcopy(meta(name))
        data.update(self.alterations.get(name, {}))
        return FakeResponse(json.dumps(data).encode())


class PublicARCO10fgResearchTests(unittest.TestCase):
    def test_dry_run_has_only_original_publisher_urls_and_no_weather_claim(self):
        preview = p.preview()
        self.assertEqual(preview["public_source_root"], p.SOURCE_ERA5_DATA_URL)
        self.assertEqual(preview["request_metadata_urls"], [
            p.PREFIX + n + "/.zarray" for n in p.SOURCE_VARIABLES
        ])
        self.assertEqual(preview["expected_hourly_time_steps"], 96)
        self.assertFalse(preview["public_metadata_bytes_confirmed"])
        self.assertFalse(preview["source_original_2020_10fg_hourly_values_fetched"])

    def test_fake_source_metadata_sha_receipt_and_no_claims(self):
        mock = FakeOpener()
        result = p.source_metadata_receipt(opener=mock)
        self.assertEqual(len(mock.called), 4)
        self.assertTrue(all(u.startswith(p.PREFIX) and timeout == 16
                            for u, timeout in mock.called))
        self.assertTrue(result["public_original_cloud_metadata_fetched_without_cds_token"])
        self.assertFalse(result["source_original_2020_10fg_hourly_values_fetched"])
        self.assertFalse(result["annual_event_rates_insured_claims_or_GUL_IL_RI_OEP_AEP_admitted"])
        self.assertTrue(result["no_CDS_operator_terms_accepted_or_cdsapi_used"])
        self.assertIn("Copernicus", result["license"])
        for name in p.SOURCE_VARIABLES:
            record = result["public_original_zarr_v2_metadata"][name]
            self.assertEqual(len(record["original_metadata_sha256"]), 64)
            self.assertGreater(record["original_metadata_bytes"], 20)

    def test_actual_source_metadata_sha_and_shape_receipt_is_immutable(self):
        path = (ROOT / "research/observations/"
                "ciara2020_google_arco_10fg_public_original_metadata_receipt_20261112.toml")
        with path.open("rb") as f:
            receipt = tomllib.load(f)
        self.assertEqual(receipt["github_workflow_job_id"], 131491098112)
        self.assertTrue(receipt["metadata_origin_unauthenticated_public"])
        for flag in ("original_wind_data_values_read",
                     "original_2020_96h_wind_data_read",
                     "site_insurer_losses_or_real_RV_contracts_read",
                     "native_GUL_IL_RI_OEP_AEP_admitted"):
            self.assertFalse(receipt[flag])
        vars = receipt["original_variables"]
        self.assertEqual(set(vars), set(p.SOURCE_VARIABLES))
        self.assertEqual(vars[p.VAR]["shape"], [1323648, 721, 1440])
        self.assertEqual(vars[p.VAR]["chunks"], [1, 721, 1440])
        self.assertEqual(vars[p.VAR]["sha256"],
                         "1e97549514364c3270a42a3af331173226d8f23a57c2378be9db14b924580800")
        self.assertEqual(vars["time"]["sha256"],
                         "78fbb0c14db1c7084fe8572fcb75de5f26457df949b66c4b825d0ca63f27d8e8")
        for record in vars.values():
            self.assertRegex(record["sha256"], r"^[a-f0-9]{64}$")
            self.assertGreater(record["metadata_bytes"], 10)

    def test_wrong_grids_and_fake_10fg_non_3d_block(self):
        edits = [
            {"latitude": {"shape": [719]}},
            {"time": {"shape": [69000]}},
            {p.VAR: {"shape": [N_TIME, N_LAT]}},
            {p.VAR: {"shape": [N_TIME, 720, N_LON]}},
            {"longitude": {"zarr_format": 3}},
            {"time": {"chunks": [0]}},
            {p.VAR: {"dtype": 11}},
        ]
        for edit in edits:
            with self.subTest(edit=edit):
                with self.assertRaises(p.PublicARCOMetadataBlocked):
                    p.source_metadata_receipt(opener=FakeOpener(edit))

    def test_arbitrary_origin_injection_denied_before_any_io(self):
        mock = FakeOpener()
        for forged in (
            "https://evil.invalid/.zarray",
            "https://storage.googleapis.com/evil-bucket/10fg/.zarray",
            p.PREFIX + "../credentials/.zarray",
            p.PREFIX + p.VAR + "/0.0.0",
        ):
            with self.subTest(url=forged):
                with self.assertRaises(p.PublicARCOMetadataBlocked):
                    p._get_metadata(forged, opener=mock)
        self.assertFalse(mock.called)

    def test_cli_dry_run_does_not_contact_network(self):
        with TemporaryDirectory() as td:
            target = Path(td) / "receipt.json"
            with patch.object(sys, "argv", ["prog", "--dry-run", "--out-json", str(target)]):
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(p.main(), 0)
            self.assertEqual(json.loads(target.read_text())["status"],
                             "PUBLIC_GOOGLE_ARCO_METADATA_CANDIDATE_NOT_FETCHED")
            self.assertNotIn("https://evil.invalid", output.getvalue())
            with patch.object(sys, "argv", ["prog", "--dry-run", "--out-json", str(target)]):
                with self.assertRaises(SystemExit) as failure:
                    p.main()
                self.assertEqual(failure.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
