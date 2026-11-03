# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for exact EIOPA country-year statistics and non-admission."""
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
import json
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from scripts.eiopa_solo_annual_pce_original_csv_pilot import (
    EIOPACSVError, HEADER, MAX_BYTES, preflight, stage_verified_csv,
)
from scripts.export_cat_source_registry_sqlite import materialize_source_catalog


def fake_source(rows=None):
    if rows is None:
        rows=[
            ("GERMANY","Y2024","Premiums written","Non-Life","R0101","",
             "20260723","94"),
            ("GERMANY","Y2024","Gross - Direct Business","Non-Life","R0110","1234.5600",
             "20260723","94"),
            ("GERMANY","Y2024","Net","Non-Life","R0200","0",
             "20260723","94"),
            ("FRANCE","Y2025","Claims incurred","Non-Life","R0310","-12.34",
             "20260805","61"),
        ]
    f=StringIO(newline="")
    wr=csv.writer(f,lineterminator="\r\n")
    wr.writerow(HEADER)
    wr.writerows(rows)
    return f.getvalue().encode("utf-8")


def cat_db(root):
    land=root/"land";land.mkdir()
    (land/"sources-test.json").write_text(json.dumps({
        "schema_version":"1.0.0",
        "purpose":"Non-admission synthetic EIOPA offline test only",
        "review_date":"2026-10-31",
        "entries":[{
            "candidate_id":"test.eiopa.2026","name":"Synthetic",
            "provider":"example.org","categories":["insurance"],
            "spatial_scope":"synthetic","temporal_scope":"synthetic",
            "resolution_or_granularity":"synthetic",
            "potential_roles":["market_research"],
            "authoritative_url":"https://example.org/eiopa",
            "access_class_hint":"synthetic_only",
            "candidate_status":"evidence_checked",
            "rights_review_status":"not_reviewed",
            "scientific_review_status":"not_reviewed",
            "admission_status":"not_admitted",
            "note":"not real insurer data",
        }]
    }),encoding="utf-8")
    db=root/"cat.sqlite"
    materialize_source_catalog(db,land)
    return db


class EIOPAOriginalCSVTests(unittest.TestCase):
    def test_country_year_profile_preserves_value_semantics(self):
        profile=preflight(fake_source())
        self.assertEqual(profile["source_row_count"],4)
        self.assertEqual(profile["country_labels"],["FRANCE","GERMANY"])
        self.assertEqual(profile["reference_periods"],["Y2024","Y2025"])
        self.assertEqual(profile["value_state_counts"],{
            "numeric":3,"missing":1,"zero":1,"negative":1})
        self.assertEqual(profile["country_year_business_type_combinations"],2)
        self.assertEqual(profile["nonlife_country_year_combinations"],2)
        presence=profile["selected_nonlife_accounting_item_presence"]
        self.assertEqual(presence["direct_written_premium"],1)
        self.assertEqual(presence["net_written_premium"],1)  # numeric zero counts as present
        self.assertEqual(presence["gross_direct_claims_incurred"],1)
        self.assertEqual(presence["reinsurers_share_written"],0)
        self.assertEqual(profile["value_unit"],"NOT_VERIFIED_DO_NOT_CONVERT")
        self.assertFalse(profile["company_level_observations_created"])
        self.assertFalse(profile["model_source_admitted"])

    def test_blank_is_not_numeric_zero(self):
        src=fake_source()
        with TemporaryDirectory() as d:
            db=cat_db(Path(d))
            result=stage_verified_csv(db,src)
            self.assertEqual(result["staged_observations"],4)
            with sqlite3.connect(db) as con:
                vals=con.execute("""SELECT source_item_code,source_decimal_text,
                                  source_value_missing,unit_verified,model_admitted
                                  FROM cat_eiopa_annual_market_stage
                                  ORDER BY source_row""").fetchall()
                self.assertEqual(vals[0],("R0101",None,1,0,0))
                self.assertEqual(vals[1],("R0110","1234.5600",0,0,0))
                self.assertEqual(vals[2],("R0200","0",0,0,0))
                self.assertEqual(vals[3],("R0310","-12.34",0,0,0))

    def test_idempotent_exact_source_and_new_version_preserved(self):
        with TemporaryDirectory() as d:
            db=cat_db(Path(d))
            a=fake_source()
            self.assertEqual(stage_verified_csv(db,a)["staged_observations"],4)
            self.assertEqual(stage_verified_csv(db,a)["staged_observations"],4)
            changed=fake_source().replace(b"1234.5600",b"1234.5601")
            self.assertEqual(stage_verified_csv(db,changed)["staged_observations"],4)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM cat_eiopa_annual_market_stage").fetchone()[0],8)
                self.assertEqual(con.execute("SELECT count(DISTINCT source_sha256) FROM cat_eiopa_annual_market_stage").fetchone()[0],2)

    def test_unrelated_database_is_immutable(self):
        with TemporaryDirectory() as d:
            db=Path(d)/"pokemon.sqlite"
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE cards(name TEXT)")
                con.execute("INSERT INTO cards VALUES ('Pikachu')")
            with self.assertRaises(EIOPACSVError):
                stage_verified_csv(db,fake_source())
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT name FROM cards").fetchone()[0],"Pikachu")
                self.assertFalse(con.execute("SELECT name FROM sqlite_master WHERE name='cat_eiopa_annual_market_stage'").fetchone())

    def test_bad_header_and_extra_columns_fail(self):
        raw=fake_source()
        for bad in [raw.replace(b"Reporting country",b"Country",1),
                    raw.replace(b"R0110,1234.5600",b"R0110,1234.5600,SPURIOUS")]:
            with self.subTest(data=bad[:120]):
                with self.assertRaises(EIOPACSVError):
                    preflight(bad)

    def test_duplicate_fact_or_invalid_year_fails(self):
        rows=[
            ("GERMANY","Y2024","Gross - Direct Business","Non-Life","R0110","2.3","20260723","100"),
            ("GERMANY","Y2024","Gross - Direct Business","Non-Life","R0110","4.6","20260723","100"),
        ]
        with self.assertRaisesRegex(EIOPACSVError,"duplicate"):
            preflight(fake_source(rows))
        bad=[("GERMANY","Y2030","Gross - Direct Business","Non-Life","R0110","2.3","20260723","100")]
        with self.assertRaisesRegex(EIOPACSVError,"period"):
            preflight(fake_source(bad))

    def test_malformed_extract_date_and_submission_counts_fail(self):
        base=("GERMANY","Y2024","Gross - Direct Business","Non-Life","R0110","1")
        for extracted,submissions in [("20260230","32"),("20260723","3.5"),("20260723","-1"),("20260723","no")]:
            with self.subTest(case=(extracted,submissions)):
                with self.assertRaises(EIOPACSVError):
                    preflight(fake_source([(*base,extracted,submissions)]))

    def test_invalid_amount_and_nonfinite_and_too_large_blob_fail(self):
        b=("GERMANY","Y2024","Gross - Direct Business","Non-Life","R0110")
        for value in ["NaN","inf","1,234","-","1E9999","€123", "1_000"]:
            with self.subTest(value=value):
                with self.assertRaises(EIOPACSVError):
                    preflight(fake_source([(*b,value,"20260723","22")]))
        with self.assertRaises(EIOPACSVError):
            preflight(b"X"*(MAX_BYTES+1))


if __name__=="__main__":
    unittest.main()
