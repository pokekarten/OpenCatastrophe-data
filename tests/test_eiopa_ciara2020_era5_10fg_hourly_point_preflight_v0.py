# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic 96h 2020 storm hazard, no ERA5 original bytes, no EIOPA claims."""
from __future__ import annotations
from copy import deepcopy
import csv
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import eiopa_ciara2020_era5_10fg_hourly_point_preflight_v0 as pre


def make_synthetic_csv(path: Path, *, drop=-1, duplicate=-1, shift=0,
                       bad_column=None, bad_idx=-1, bad_field=None, bad_val=None,
                       coordinate="51.0"):
    head = list(pre.HEADERS)
    if bad_column:
        head[3] = bad_column
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=head)
        writer.writeheader()
        origin = datetime(2020, 2, 8, tzinfo=timezone.utc)
        for i in range(96):
            if i == drop:
                continue
            idx = i-1 if i == duplicate else i
            t = (origin + timedelta(hours=idx+shift)).strftime("%Y-%m-%dT%H:00:00Z")
            row = {
                "time_utc": t,
                "latitude": coordinate,
                "longitude": "7.0",
                head[3]: "31.50" if i==36 else "12.0",
                "units": "m/s",
            }
            if i == bad_idx:
                row[bad_field] = bad_val
            writer.writerow(row)


class Ciara2020ERA5OnePointSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with pre.CONTRACT.open("rb") as fd:
            cls.doc = tomllib.load(fd)

    def test_era5_official_hourly_10fg_candidate_request_without_CDS_credentials(self):
        req = pre.cds_candidate_request(self.doc)
        self.assertEqual(req["dataset"], "reanalysis-era5-single-levels-timeseries")
        self.assertEqual(req["request"]["variable"], ["10m_wind_gust_since_previous_post_processing"])
        self.assertEqual(req["request"]["date"], ["2020-02-08", "2020-02-11"])
        self.assertEqual(req["request"]["location"], {"latitude": 51.0, "longitude": 7.0})
        self.assertEqual(req["request"]["data_format"], "csv")
        self.assertIs(req["CDS_terms_acceptance_required_by_user"], True)
        self.assertIs(req["data_obtained"], False)

    def test_synthetic_96h_intake_has_exact_36h_peak_but_no_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"synthetic.csv"
            make_synthetic_csv(p)
            audit=pre.audit_normalized_csv(p,self.doc)
            self.assertEqual(audit["time_steps"],96)
            self.assertEqual(audit["point_hourly_gust_peak_ms_from_local_CSV"],"31.50")
            self.assertEqual(audit["point_hourly_gust_peak_hour_utc_from_local_CSV"],
                             "2020-02-09T12:00:00Z")
            self.assertEqual(audit["local_normalized_CSV_sha256"],hashlib.sha256(p.read_bytes()).hexdigest())
            for k in ("2020_Ciara_EIOPA_insurer_claim_values_loaded",
                      "source_CDS_dataset_license_accepted_by_user_verified",
                      "R_V_real_policy_losses_or_annual_OEP_AEP_admitted"):
                self.assertIs(audit[k],False)

    def test_missing_duplicate_and_shifted_hour_block(self):
        for args in ({"drop":20},{"duplicate":21},{"shift":1},{"shift":-1}):
            with self.subTest(args=args),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/"bad.csv"
                make_synthetic_csv(p,**args)
                with self.assertRaises(pre.CiaraERA5PreflightBlocked):
                    pre.audit_normalized_csv(p,self.doc)

    def test_no_u_v_wind_speed_hourly_mean_daily_or_wrong_units(self):
        for bad in ("10m_u_component_of_wind","10m_v_component_of_wind",
                    "10m_wind_speed","daily_maximum_10m_wind_gust"):
            with self.subTest(column=bad),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/"bad.csv"
                make_synthetic_csv(p,bad_column=bad)
                with self.assertRaises(pre.CiaraERA5PreflightBlocked):
                    pre.audit_normalized_csv(p,self.doc)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"kmh.csv"
            make_synthetic_csv(p,bad_idx=4,bad_field="units",bad_val="km/h")
            with self.assertRaises(pre.CiaraERA5PreflightBlocked):
                pre.audit_normalized_csv(p,self.doc)

    def test_malformed_nonfinite_negative_or_excessive_gust_block(self):
        for gust in ("NaN", "Infinity", "-1", "150.1", "1,000", ""):
            with self.subTest(gust=gust),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/"bad.csv"
                make_synthetic_csv(p,bad_idx=8,bad_field=pre.VAR,bad_val=gust)
                with self.assertRaises(pre.CiaraERA5PreflightBlocked):
                    pre.audit_normalized_csv(p,self.doc)

    def test_wrong_point_coordinate_and_missing_header_block(self):
        for lat in ("51.25","52.0","NaN","0"):
            with self.subTest(lat=lat),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/"bad.csv"
                make_synthetic_csv(p,coordinate=lat)
                with self.assertRaises(pre.CiaraERA5PreflightBlocked):
                    pre.audit_normalized_csv(p,self.doc)

    def test_2026_daily_shift_and_insurer_event_claims_cannot_be_admitted(self):
        for field in pre.EXPECTED_FLAGS_FALSE:
            with self.subTest(field=field):
                doc=deepcopy(self.doc)
                doc[field]=True
                with self.assertRaises(pre.CiaraERA5PreflightBlocked):
                    pre.validate_contract(doc)
        for field,value in (
            ("source_dataset","derived-era5-single-levels-daily-statistics"),
            ("source_doi","10.24381/cds.adbb2d47"),
            ("wind_variable_name","10m_u_component_of_wind"),
            ("ecmwf_parameter_id",207),
            ("event_name","DARIA_1990"),
            ("event_end_utc_inclusive","2020-02-10T23:00:00Z"),
        ):
            with self.subTest(field=field):
                doc=deepcopy(self.doc)
                doc[field]=value
                with self.assertRaises(pre.CiaraERA5PreflightBlocked):
                    pre.validate_contract(doc)

    def test_no_credential_content_or_real_loss_in_contract(self):
        src=pre.CONTRACT.read_text(encoding="utf-8").lower()
        self.assertIn("original_source_csv_acquired = false",src)
        self.assertIn("source_cds_token_present_in_repo = false",src)
        self.assertNotIn("cdsapirc",src)
        self.assertNotIn("personal-access-token",src)
        self.assertNotIn("api_key =",src)
        self.assertNotIn("actual_rv_insured_loss_cents",src)


if __name__ == "__main__":
    unittest.main()
