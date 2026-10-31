# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression tests for bounded, verified GLEIF Level-2 observations."""
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from scripts.export_cat_source_registry_sqlite import materialize_source_catalog
from scripts.gleif_level1_insurer_identity_pilot import PILOT_LEIS, ingest_verified_lei_pilot
from scripts.gleif_level2_relationship_pilot import (
    PILOT, GLEIFPilotError, parse_level2, source_url, store_level2,
)


def fixture(child, suffix, expected):
    if suffix.endswith("relationship"):
        attrs = {
            "relationship": {
                "startNode": {"id": child, "type": "lei"},
                "endNode": {"id": expected, "type": "lei"},
                "type": ("IS_DIRECTLY_CONSOLIDATED_BY"
                         if suffix.startswith("direct") else "IS_ULTIMATELY_CONSOLIDATED_BY"),
                "status": "ACTIVE",
                "periods": [
                    {"startDate":"2024-01-01T00:00:00Z","type":"RELATIONSHIP_PERIOD"},
                    {"startDate":"2023-12-31T23:00:00Z","endDate":"2024-12-30T23:00:00Z",
                     "type":"ACCOUNTING_PERIOD"},
                ],
            },
            "registration": {"status":"PUBLISHED"},
        }
    else:
        attrs = {"exception": {
            "lei":child,"category":"DIRECT_ACCOUNTING_CONSOLIDATION_PARENT",
            "reason":expected,
        }}
    return json.dumps({"data":{"type":"relationship-records","attributes":attrs}},
                      separators=(",",":")).encode()


def level1(lei):
    return json.dumps({"data":{
        "type":"lei-records","id":lei,"attributes":{
            "lei":lei,
            "entity":{"legalName":{"name":"Synthetic Company"},"legalAddress":{"country":"DE"},
                      "status":"ACTIVE"},
            "registration":{"status":"ISSUED"},
        }},
        "meta":{"goldenCopy":{"publishDate":"2026-10-31T00:00:00Z"}}}).encode()


def init_db(root):
    land=root/"land";land.mkdir()
    x={"candidate_id":"test.synthetic-source", "name":"Synthetic Sources",
       "provider":"example", "categories":["insurance"],"spatial_scope":"global",
       "temporal_scope":"2026","resolution_or_granularity":"synthetic",
       "potential_roles":["testing"],"authoritative_url":"https://example.org/",
       "access_class_hint":"synthetic","candidate_status":"evidence_checked",
       "rights_review_status":"not_reviewed","scientific_review_status":"not_reviewed",
       "admission_status":"not_admitted","note":"synthetic only"}
    (land/"sources-test.json").write_text(json.dumps({
        "schema_version":"1.0.0",
        "purpose":"Non-admission synthetic data only",
        "review_date":"2026-10-31","entries":[x],
    }),encoding="utf-8")
    db=root/"cat.sqlite"
    materialize_source_catalog(db,land)
    ingest_verified_lei_pilot(db,{lei:level1(lei) for lei in PILOT_LEIS},
                              "2026-10-31T20:00:00+00:00")
    return db


class GLEIFLevel2PilotTests(unittest.TestCase):
    def test_seven_bounded_source_receipts(self):
        self.assertEqual(len(PILOT),7)
        for child,suffix,target in PILOT:
            with self.subTest(suffix=suffix,child=child):
                row=parse_level2(fixture(child,suffix,target),child,suffix,target)
                self.assertEqual(row["source_url"],source_url(child,suffix))
                self.assertFalse(row["insurance_exposure_observed"])
                self.assertFalse(row["treaty_relationship_observed"])
                self.assertFalse(row["beneficial_ownership_observed"])
        self.assertEqual(sum(s.endswith("relationship") for _,s,_ in PILOT),5)

    def test_direct_and_ultimate_are_distinct(self):
        a=[row for row in PILOT if row[0]=="529900KIN5BE45V5KB18"]
        direct=parse_level2(fixture(*a[0]),*a[0])
        ultimate=parse_level2(fixture(*a[1]),*a[1])
        self.assertNotEqual(direct["relation_kind"],ultimate["relation_kind"])
        self.assertNotEqual(direct["parent_lei"],ultimate["parent_lei"])

    def test_flat_official_exception_attributes(self):
        child,suffix,reason=PILOT[-1]
        x=json.loads(fixture(child,suffix,reason))
        x["data"]["attributes"]=x["data"]["attributes"]["exception"]
        parsed=parse_level2(json.dumps(x).encode(),child,suffix,reason)
        self.assertIsNone(parsed["parent_lei"])
        self.assertEqual(parsed["reporting_exception_reason"],reason)

    def test_exception_never_constructs_parent(self):
        child,suffix,target=PILOT[-1]
        row=parse_level2(fixture(child,suffix,target),child,suffix,target)
        self.assertIsNone(row["parent_lei"])
        self.assertEqual(row["reporting_exception_reason"],target)
        self.assertEqual(row["periods"],[])

    def test_mismatched_child_parent_and_status_fail_closed(self):
        child,suffix,target=PILOT[1]
        b=json.loads(fixture(child,suffix,target))
        b["data"]["attributes"]["relationship"]["endNode"]["id"]=PILOT[0][2]
        with self.assertRaises(GLEIFPilotError):
            parse_level2(json.dumps(b).encode(),child,suffix,target)
        b["data"]["attributes"]["relationship"]["endNode"]["id"]=target
        b["data"]["attributes"]["registration"]["status"]="LAPSED"
        with self.assertRaises(GLEIFPilotError):
            parse_level2(json.dumps(b).encode(),child,suffix,target)

    def test_unsafe_bytes_and_endpoint_fail_closed(self):
        child,suffix,target=PILOT[0]
        with self.assertRaises(GLEIFPilotError):
            source_url("0"*20,suffix)
        with self.assertRaises(GLEIFPilotError):
            parse_level2(b"broken",child,suffix,target)
        with self.assertRaises(GLEIFPilotError):
            parse_level2(b"",child,suffix,target)
        with self.assertRaises(GLEIFPilotError):
            parse_level2(fixture(child,suffix,target),child,suffix,"0"*20)

    def test_store_is_reproducible_and_does_not_make_portfolios(self):
        with TemporaryDirectory() as d:
            db=init_db(Path(d))
            blobs={(child,suffix):fixture(child,suffix,target) for child,suffix,target in PILOT}
            a=store_level2(db,blobs,"2026-10-31T20:00:00+00:00")
            self.assertEqual(a["records_verified"],7)
            self.assertEqual(a["consolidation_links"],5)
            self.assertEqual(a["reporting_exceptions"],2)
            self.assertFalse(a["insured_portfolios_created"])
            self.assertFalse(a["neon_modified"])
            b=store_level2(db,blobs,"2026-10-31T20:01:00+00:00")
            self.assertEqual(b["records_verified"],7)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM cat_gleif_level2_observation").fetchone()[0],7)
                self.assertEqual(con.execute("SELECT count(*) FROM cat_source_candidate").fetchone()[0],1)
                self.assertEqual(con.execute("SELECT count(*) FROM cat_gleif_level2_observation WHERE parent_lei IS NULL").fetchone()[0],2)

    def test_unknown_database_and_missing_receipts_are_blocked(self):
        with TemporaryDirectory() as d:
            root=Path(d);db=root/"pokemon.sqlite"
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE cards(name TEXT)");con.execute("INSERT INTO cards VALUES('Pikachu')")
            blobs={(child,suffix):fixture(child,suffix,target) for child,suffix,target in PILOT}
            with self.assertRaises(GLEIFPilotError):
                store_level2(db,blobs,"2026-10-31T20:00:00+00:00")
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT name FROM cards").fetchone()[0],"Pikachu")
            cat=init_db(root)
            with self.assertRaises(GLEIFPilotError):
                store_level2(cat,dict(list(blobs.items())[:-1]),"2026-10-31T20:00:00+00:00")


if __name__=="__main__":
    unittest.main()
