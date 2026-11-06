# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic ZIP adversarial tests: NEVER claim real DWD archive was read."""
from __future__ import annotations
from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.dwd_kyrill_2007_berlin_original_v0 import (
    CONTRACT, FILENAME, OriginalDWDGateError,
    _gust, _utc_stamp, _header, audit_original_archive,
)


HEADER="STATIONS_ID;MESS_DATUM;QN;FX_10;EXTRA\n"
ROWS=[
    ("00433","200701162350","3","10.0"),
    ("00433","200701170000","3","10.5"),
    ("00433","200701171200","2","16.0"),
    ("00433","200701180000","2","23.5"),
    ("00433","200701181200","3","30.1"),
    ("00433","200701181210","1","34.2"),
    ("00433","200701181220","3","-999"),
    ("00433","200701190000","3","19.1"),
    ("00433","200701200000","2","15.1"),
    ("00433","200701202350","3","13.4"),
    ("00433","200701210000","3","12.3"),
]


def archive(rows=ROWS, header=HEADER, additional=None):
    stream=BytesIO()
    with ZipFile(stream,"w",ZIP_DEFLATED) as z:
        text=header+"".join(";".join(v)+";fixture\n" for v in rows)
        z.writestr("produkt_extrema_wind_00433_20000101_20091231.txt",text)
        z.writestr("readme.txt","Synthetic fixture; not a provider archive.\n")
        for key,value in (additional or {}).items():z.writestr(key,value)
    return stream.getvalue()


class TestDWDKyrill2007Original(unittest.TestCase):
    def test_known_utc_and_missing_value_semantics(self):
        self.assertEqual(_utc_stamp("200701181210"),datetime(2007,1,18,12,10))
        self.assertIsNone(_gust("-999"))
        self.assertEqual(str(_gust("34.2")),"34.2")
        self.assertEqual(_header(HEADER.encode())[:4],
                         ("STATIONS_ID","MESS_DATUM","QN","FX_10"))

    def test_synthetic_archive_4_days_and_quality_separated(self):
        data=archive()
        r=audit_original_archive(data,expected_sha256=sha256(data).hexdigest())
        self.assertEqual(r["contract"],CONTRACT)
        self.assertEqual(r["original_archive_sha256"],sha256(data).hexdigest())
        self.assertEqual(r["full_source_product_rows"],len(ROWS))
        self.assertEqual(r["dwd_station_id"],"00433")
        self.assertEqual(r["dwd_original_archive_filename"],FILENAME)
        d=r["daily_10minute_gust_aggregates"]
        self.assertEqual([x["day_utc"] for x in d],
                         ["2007-01-17","2007-01-18","2007-01-19","2007-01-20"])
        self.assertEqual(d[1]["observed_10minute_records"],4)
        self.assertEqual(d[1]["valid_gust_records"],3)
        self.assertEqual(d[1]["missing_value_records"],1)
        self.assertEqual(d[1]["max_3second_gust_within_10minutes_mps_all_quality"],"34.2")
        self.assertEqual(d[1]["max_3second_gust_within_10minutes_mps_qn2_or_qn3"],"30.1")
        self.assertEqual(d[1]["unobserved_10minute_slots"],140)
        self.assertEqual(d[1]["quality_flag_record_counts"],{"1":1,"2":1,"3":2})
        self.assertFalse(r["source_station_coordinates_at_2007_original_metadata_verified"])
        self.assertFalse(r["one_reported_storm_attribution_proven"])
        self.assertFalse(r["scientific_admission"])
        self.assertIsNone(r["annual_AEP"])
        self.assertIsNone(r["annual_OEP"])

    def test_reject_wrong_provider_sha(self):
        with self.assertRaisesRegex(OriginalDWDGateError,"SHA256"):
            audit_original_archive(archive(),expected_sha256="0"*64)

    def test_reject_wrong_station_id(self):
        rows=list(ROWS);rows[4]=("00430",*ROWS[4][1:])
        with self.assertRaisesRegex(OriginalDWDGateError,"station"):
            audit_original_archive(archive(rows))

    def test_reject_duplicate_or_unsorted_timestamp(self):
        rows=list(ROWS);rows.insert(5,ROWS[4])
        with self.assertRaisesRegex(OriginalDWDGateError,"duplicate"):
            audit_original_archive(archive(rows))
        rows=list(ROWS);rows[4],rows[5]=rows[5],rows[4]
        with self.assertRaisesRegex(OriginalDWDGateError,"nonmonotone"):
            audit_original_archive(archive(rows))

    def test_missing_window_and_not_bracketed_rejected(self):
        with self.assertRaisesRegex(OriginalDWDGateError,"bracket"):
            audit_original_archive(archive(ROWS[:4]))
        with self.assertRaisesRegex(OriginalDWDGateError,"bracket"):
            audit_original_archive(archive(ROWS[5:]))

    def test_strict_utc_grid_and_source_bounds(self):
        for ts in ("200701181201","2007011812","200701181260",
                   "199911302350","201001010000","200702300000"):
            with self.subTest(ts=ts),self.assertRaises(OriginalDWDGateError):
                _utc_stamp(ts)

    def test_bounded_pre_2000_december_prelude_excluded_not_mislabelled_utc(self):
        self.assertEqual(_utc_stamp("199912010000"),datetime(1999,12,1))
        self.assertEqual(_utc_stamp("199912312340"),datetime(1999,12,31,23,40))
        for ts in ("199911302350", "199901010000", "199812312350"):
            with self.subTest(ts=ts), self.assertRaises(OriginalDWDGateError):
                _utc_stamp(ts)
        rows=[("00433","199912010000","3","5.0"),
              ("00433","199912312340","2","6.0"),*ROWS]
        report=audit_original_archive(archive(rows))
        self.assertEqual(report["pre_2000_december_source_clock_rows_excluded"],2)
        self.assertTrue(report["pre_2000_non_utc_measurements_not_used_for_kyrill"])
        self.assertFalse(report["archive_first_clock_is_utc"])
        self.assertEqual(report["archive_first_original_clock_label"],"1999-12-01T00:00:00")
        self.assertEqual(report["daily_10minute_gust_aggregates"][1]["valid_gust_records"],3)

    def test_nonfinite_negative_and_unphysical_gust_rejected(self):
        for value in ("inf","NaN","-1","-998","200.01","invalid"):
            with self.subTest(value=value),self.assertRaises(OriginalDWDGateError):
                _gust(value)

    def test_quality_flags_explicit_not_silently_promoted(self):
        rows=list(ROWS);rows[4]=(rows[4][0],rows[4][1],"0",rows[4][3])
        with self.assertRaisesRegex(OriginalDWDGateError,"quality"):
            audit_original_archive(archive(rows))

    def test_bad_product_field_schema_rejected(self):
        with self.assertRaisesRegex(OriginalDWDGateError,"FX_10 product"):
            audit_original_archive(archive(header="STATIONS_ID;MESS_DATUM;FX_10;VAL\n"))

    def test_duplicate_product_with_same_header_rejected(self):
        extra={"another_wind.txt": HEADER+"00433;200701170000;2;1;test\n"}
        with self.assertRaisesRegex(OriginalDWDGateError,"exactly one"):
            audit_original_archive(archive(additional=extra))

    def test_reject_wrong_input_type_and_nonzip(self):
        for thing in (None,{},b"",b"not zip"*50,"PK"):
            with self.subTest(value=str(type(thing))),self.assertRaises(OriginalDWDGateError):
                audit_original_archive(thing)

    def test_no_raw_rows_or_observed_claims_leak_into_aggregate(self):
        r=audit_original_archive(archive())
        wire=json.dumps(r,sort_keys=True,allow_nan=False)
        self.assertNotIn("200701181210",wire)
        self.assertNotIn("fixture",wire)
        self.assertFalse(r["source_original_raw_gust_rows_persisted"])
        self.assertFalse(r["observed_insured_claims"])
        self.assertIsNone(r["annual_event_rate"])

    def test_original_two_source_physics_cannot_be_automatically_equated(self):
        r=audit_original_archive(archive())
        self.assertIn("NOT_SAME_OBSERVATION_OPERATOR",r["climk_gust_statistic"])
        self.assertEqual(r["climk_berlin_era5_source_max_gust_mps"],"31.090")
        self.assertFalse(r["dwd_station_identical_to_climk_synthetic_site"])
        self.assertFalse(r["historical_kyrill_label_day_utc_exact_identity_confirmed"])

if __name__=="__main__":unittest.main()
