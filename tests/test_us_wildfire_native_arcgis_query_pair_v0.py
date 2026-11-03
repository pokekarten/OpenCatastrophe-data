# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for native ArcGIS 2024 source response join audit."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

from research_runners import us_wildfire_native_arcgis_query_pair_v0 as g


def reply(kind, rows, *, limited=True):
    fields = [{"name": name, "type": dtype} for name, dtype in g.COLUMNS[kind].items()]
    return {"fields": fields, "features": [{"attributes": r} for r in rows], "exceededTransferLimit": limited}


def fpa(id=1, key="Fire.2024.ID"):
    return {"fod_id": id, "mtbs_id": key, "fire_year": 2024}


def mtbs(key="Fire.2024.ID", kind="Wildfire", perim=None, map_id=1):
    return {"fire_id": key, "year": 2024, "fire_type": kind, "perim_id": perim, "map_id": map_id}


def encode(data):
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return raw, hashlib.sha256(raw).hexdigest()


def audit(fr=None, mr=None, **kwargs):
    fb, fh = encode(reply("fpa", [fpa()] if fr is None else fr))
    mb, mh = encode(reply("mtbs", [mtbs()] if mr is None else mr))
    return g.audit_original_queries(
        fb, fh, mb, mh,
        selection=kwargs.get("selection", "mtbs_id_present_2024"),
        fpa_release=kwargs.get("fpa_release", "FPA_FOD_20260615"),
        mtbs_vintage=kwargs.get("mtbs_vintage", "MTBS-2026Q3-bounded-research-label"),
    )


class NativeArcgisQueryPairTests(unittest.TestCase):
    def test_unique_key_not_event_identity_or_loss(self):
        r = audit()
        self.assertEqual(r["state"], "BOUNDED_RESEARCH_SAMPLE_ONLY")
        self.assertEqual(r["fpa_disposition"]["unique_id_wildfire_research_candidate"], 1)
        self.assertTrue(r["fpa_rows_conserved"])
        self.assertEqual(r["mtbs_perim_id_populated"], 0)
        for k in (
            "source_response_origin_authenticated", "original_archive_asset_hash_verified",
            "source_selection_representative_or_national_coverage_established",
            "perim_id_or_map_id_promoted_to_polygon_key", "physical_event_equivalence_proven",
            "financial_or_insured_loss_inferred", "source_rights_or_model_admission_granted",
        ):
            self.assertFalse(r[k])
        self.assertNotIn("Fire.2024.ID", json.dumps(r))

    def test_mtbs_id_missing_is_not_absence_of_fire(self):
        r = audit(fr=[fpa(key=None)], selection="unfiltered_2024")
        self.assertEqual(r["fpa_disposition"]["fpa_mtbs_id_missing"], 1)
        self.assertEqual(r["fpa_disposition"]["unique_id_wildfire_research_candidate"], 0)

    def test_filter_claim_with_null_mtbs_id_fails(self):
        with self.assertRaisesRegex(g.QueryAuditBlocked, "filtered"):
            audit(fr=[fpa(key=None)], selection="mtbs_id_present_2024")

    def test_absent_from_bounded_mtbs_subset_not_no_fire(self):
        r = audit(fr=[fpa(key="Other")])
        self.assertEqual(r["fpa_disposition"]["not_in_supplied_mtbs_query_slice"], 1)

    def test_repeated_fpa_reference_flags_ambiguity(self):
        r = audit(fr=[fpa(1), fpa(2)])
        self.assertEqual(r["fpa_disposition"]["ambiguous_multiplicity_needs_review"], 2)
        self.assertEqual(r["state"], "REVIEW_NEEDED")

    def test_mtbs_repeated_fire_id_blocks_double_event(self):
        r = audit(mr=[mtbs(map_id=1), mtbs(map_id=2)])
        self.assertEqual(r["mtbs_distinct_fire_ids_in_slice"], 1)
        self.assertEqual(r["mtbs_feature_count"], 2)
        self.assertEqual(r["fpa_disposition"]["ambiguous_multiplicity_needs_review"], 1)

    def test_prescribed_and_unrecognized_are_not_wildfires(self):
        for value, disposition in (
            ("Prescribed Fire", "prescribed_fire_not_wildfire"),
            ("Unexpected case", "unknown_fire_type"),
            (None, "unknown_fire_type"),
        ):
            with self.subTest(value=value):
                r = audit(mr=[mtbs(kind=value)])
                self.assertEqual(r["fpa_disposition"][disposition], 1)
                self.assertEqual(r["fpa_disposition"]["unique_id_wildfire_research_candidate"], 0)

    def test_null_perim_and_map_dont_block_or_become_identity(self):
        r = audit(mr=[mtbs(perim=None, map_id=None)])
        self.assertEqual(r["mtbs_perim_id_populated"], 0)
        self.assertEqual(r["mtbs_map_id_populated"], 0)
        self.assertEqual(r["fpa_disposition"]["unique_id_wildfire_research_candidate"], 1)

    def test_fpa_id_unique_and_strict_integer(self):
        for rows in ([fpa(), fpa()], [fpa(id=True)], [fpa(id="1")]):
            with self.subTest(rows=rows), self.assertRaises(g.QueryAuditBlocked):
                audit(fr=rows)

    def test_wrong_year_wrong_types_and_unpinned_vintage_block(self):
        for f, m, kw in (
            ([{**fpa(), "fire_year": 2023}], [mtbs()], {}),
            ([fpa()], [{**mtbs(), "year": 2023}], {}),
            ([fpa()], [mtbs()], {"mtbs_vintage":"current"}),
            ([fpa()], [mtbs()], {"fpa_release":"FPA_FOD_2020"}),
        ):
            with self.subTest(test=(f,m,kw)), self.assertRaises(g.QueryAuditBlocked):
                audit(fr=f, mr=m, **kw)

    def test_changed_field_schema_or_unexpected_geometry_rejected(self):
        for change in ("name", "type", "geometry"):
            fb = reply("fpa", [fpa()])
            mb = reply("mtbs", [mtbs()])
            if change == "name":
                fb["fields"][0]["name"] = "not_fod_id"
            if change == "type":
                fb["fields"][0]["type"] = "esriFieldTypeString"
            if change == "geometry":
                fb["features"][0]["geometry"] = {"x": -123, "y": 43}
            fbytes, fh = encode(fb)
            mbytes, mh = encode(mb)
            with self.subTest(change=change), self.assertRaises(g.QueryAuditBlocked):
                g.audit_original_queries(
                    fbytes, fh, mbytes, mh, selection="mtbs_id_present_2024",
                    fpa_release="FPA_FOD_20260615",
                    mtbs_vintage="MTBS-2026Q3-bounded-research-label",
                )

    def test_duplicate_json_or_sha_mismatch_blocks(self):
        for raw, sha in (
            (b'{"features":[],"features":[]}', hashlib.sha256(b'{"features":[],"features":[]}').hexdigest()),
            (b'{"a":NaN}', hashlib.sha256(b'{"a":NaN}').hexdigest()),
            (b'{}', "0"*64),
        ):
            with self.subTest(raw=raw), self.assertRaises(g.QueryAuditBlocked):
                g._result_rows(raw, sha, "fpa")

    def test_conserves_mixed_research_sample(self):
        r = audit(fr=[fpa(1), fpa(2,"Other"), fpa(3, None)],
                  selection="unfiltered_2024")
        self.assertEqual(r["fpa_feature_count"], 3)
        self.assertEqual(sum(r["fpa_disposition"].values()), 3)
        self.assertEqual(r["fpa_disposition"]["unique_id_wildfire_research_candidate"], 1)
        self.assertEqual(r["fpa_disposition"]["not_in_supplied_mtbs_query_slice"], 1)
        self.assertEqual(r["fpa_disposition"]["fpa_mtbs_id_missing"], 1)
