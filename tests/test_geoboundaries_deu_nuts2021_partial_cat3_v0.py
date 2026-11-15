# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only CAT3 14-of-16 original geometry partition/provenance gates."""
from __future__ import annotations

import hashlib
import importlib.util
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research_runners.geoboundaries_deu_nuts2021_partial_cat3_v0 import (
    ALLOWED_EXPECTED_COUNT,CAT3_ID,CAT3_SCHEMA,WITHHELD_CODES,
    aggregate_receipt,build_cat3,decide_best,classify_pinned_originals,
    CrosswalkError,
)
from research_runners.geoboundaries_deu_adm1_nuts2021_crosswalk_v0 import (
    EXPECTED_NUTS,
)
from tests.test_geoboundaries_deu_adm1_nuts2021_crosswalk_v0 import pair
from tests.test_geoboundaries_deu_adm1_original_geojson_v0 import raw

HAS_SPATIAL=all(importlib.util.find_spec(x) is not None for x in ("shapely","pyproj"))


def score(first="DE3",best=90,second=11,source=100,ref=100):
    codes=sorted(EXPECTED_NUTS)
    if first not in codes:
        raise ValueError("bad synthetic target code")
    next_code=next(x for x in codes if x!=first)
    samples=[]
    for code in codes:
        samples.append((code,float(best) if code==first else
                        float(second) if code==next_code else 0.0,float(ref)))
    return decide_best(samples,float(source))


def rows():
    accepted=[
        {"source_shape_id":"SYN-SOURCE-"+x,"nuts1":x,
         "source_coverage":0.99,"nuts_coverage":0.98,
         "status":"polygon_supported_provisional","eligible":True}
        for x in sorted(EXPECTED_NUTS-WITHHELD_CODES)
    ]
    withheld=[
        {"source_shape_id":"SYN-SOURCE-"+x,"nuts1":x,
         "source_coverage":0.90,"nuts_coverage":0.90,
         "status":"ambiguous_runner_up_ge_10pct","eligible":False,
         "runner_up_share":0.15}
        for x in sorted(WITHHELD_CODES)
    ]
    return accepted,withheld


class PartialRegionStrictTests(unittest.TestCase):
    def test_original_berlin_like_competitor_blocks_without_lowering_threshold(self):
        outcome=score("DE3",90,11,100,100)
        self.assertFalse(outcome["eligible"])
        self.assertEqual(outcome["status"],"ambiguous_runner_up_ge_10pct")
        self.assertAlmostEqual(outcome["runner_up_share"],11/90)

    def test_original_bremen_like_competitor_blocks(self):
        outcome=score("DE5",82.5,14.5,100,91.5)
        self.assertFalse(outcome["eligible"])
        self.assertEqual(outcome["status"],"ambiguous_runner_up_ge_10pct")

    def test_high_overlap_clean_region_is_only_provisional(self):
        outcome=score("DE2",97,1,100,100)
        self.assertTrue(outcome["eligible"])
        self.assertEqual(outcome["status"],"polygon_supported_provisional")

    def test_bidirectional_overlap_gate_not_diluted(self):
        source=score("DE2",85,1,100,120)
        self.assertFalse(source["eligible"])
        self.assertEqual(source["status"],"low_bidirectional_coverage")
        source=score("DE2",70,1,100,100)
        self.assertFalse(source["eligible"])

    def test_exact_runner_up_threshold_rejects(self):
        self.assertFalse(score("DE3",90,9,100,100)["eligible"])
        self.assertTrue(score("DE3",90,8.99,100,100)["eligible"])

    def test_duplicate_candidate_codes_and_nonfinite_areas_block(self):
        with self.assertRaisesRegex(CrosswalkError,"candidate codes"):
            bad=[("DE1",1.0,1.0)]*16
            decide_best(bad,1.0)
        with self.assertRaisesRegex(CrosswalkError,"area"):
            score("DE2",best=float("nan"))
        with self.assertRaisesRegex(CrosswalkError,"area"):
            score("DE2",best=-1.0)
        with self.assertRaisesRegex(CrosswalkError,"area"):
            score("DE2",best=90,source=80)

    def test_aggregate_codes_never_expose_provider_shape_ids(self):
        accepted,withheld=rows()
        receipt=aggregate_receipt(accepted,withheld)
        self.assertEqual(receipt["polygon_supported_provisional_count"],14)
        self.assertEqual(receipt["withheld_count"],2)
        self.assertEqual(len(receipt["polygon_supported_provisional_nuts_codes"]),14)
        self.assertEqual({x["nuts1_code"] for x in receipt["withheld_diagnostic"]},
                         WITHHELD_CODES)
        self.assertFalse(receipt["insurance_model_input_admitted"])
        self.assertFalse(receipt["all_16_crosswalk_admitted"])
        self.assertNotIn("SYN-SOURCE",str(receipt))

    def test_missing_withheld_code_or_additional_rejection_fails_closed(self):
        accepted,withheld=rows()
        withheld[0]["nuts1"]="DE2"
        with self.assertRaisesRegex(CrosswalkError,"unsupported partial"):
            aggregate_receipt(accepted,withheld)
        accepted,withheld=rows()
        accepted.pop()
        with self.assertRaisesRegex(CrosswalkError,"unsupported partial"):
            aggregate_receipt(accepted,withheld)

    def test_cat3_sqlite_is_isolated_not_admitted_and_non_overwriting(self):
        accepted,withheld=rows()
        with TemporaryDirectory() as temp:
            dest=Path(temp)/"provisional.cat.sqlite"
            build_cat3(accepted,withheld,dest)
            with sqlite3.connect(dest) as conn:
                self.assertEqual(conn.execute("PRAGMA application_id").fetchone()[0],CAT3_ID)
                self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0],1)
                self.assertEqual(conn.execute("SELECT count(*) FROM provisional_region").fetchone()[0],14)
                self.assertEqual(conn.execute("SELECT count(*) FROM withheld_region").fetchone()[0],2)
                self.assertEqual(conn.execute("SELECT model_input_approved FROM source_provenance").fetchone()[0],0)
            with self.assertRaises(Exception):
                build_cat3(accepted,withheld,dest)

    def test_cat3_missing_or_duplicate_source_ids_block(self):
        accepted,withheld=rows()
        accepted[0]["source_shape_id"]=withheld[0]["source_shape_id"]
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(CrosswalkError,"14 supported"):
                build_cat3(accepted,withheld,Path(temp)/"failed.cat.sqlite")

    @unittest.skipUnless(HAS_SPATIAL,"pinned spatial dependencies absent")
    def test_source_parser_does_not_invent_real_14_of_16_for_synthetic_exact_matches(self):
        geo,nuts=pair()
        gb=raw(geo)
        nu=raw(nuts)
        with self.assertRaisesRegex(CrosswalkError,"14-supported/2-withheld"):
            classify_pinned_originals(
                gb,nu,geo_sha=hashlib.sha256(gb).hexdigest(),
                nuts_sha=hashlib.sha256(nu).hexdigest())

    @unittest.skipUnless(HAS_SPATIAL,"pinned spatial dependencies absent")
    def test_provider_original_hash_mismatch_blocks(self):
        geo,nuts=pair()
        gb=raw(geo)
        nu=raw(nuts)
        with self.assertRaisesRegex(Exception,"SHA-256"):
            classify_pinned_originals(
                gb,nu,geo_sha="0"*64,
                nuts_sha=hashlib.sha256(nu).hexdigest())


if __name__=="__main__":
    unittest.main()
