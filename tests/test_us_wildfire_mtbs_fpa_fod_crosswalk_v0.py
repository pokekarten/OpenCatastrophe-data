# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests: no join multiplication or unwarranted model admission."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest

from research_runners import us_wildfire_mtbs_fpa_fod_crosswalk_v0 as w


def csv_bytes(header, records):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return out.getvalue().encode()


def fpa(**replace):
    row = dict(fpa_record_id="1", mtbs_id="MTBS-ONE", fire_year="2021")
    row.update(replace)
    return row


def mtbs(**replace):
    row = dict(mtbs_component_id="p1", mtbs_id="MTBS-ONE", fire_year="2021", event_kind="wildfire")
    row.update(replace)
    return row


def run(fpas=None, mtbss=None, **options):
    fpa_blob = csv_bytes(w.FPA_COLUMNS, [fpa()] if fpas is None else fpas)
    mtbs_blob = csv_bytes(w.MTBS_COLUMNS, [mtbs()] if mtbss is None else mtbss)
    return w.audit_crosswalk(
        fpa_blob, hashlib.sha256(fpa_blob).hexdigest(),
        mtbs_blob, hashlib.sha256(mtbs_blob).hexdigest(),
        fpa_release=options.get("fpa_release", "FPA_FOD_20260615"),
        mtbs_release=options.get("mtbs_release", "MTBS-2026Q3-publisher-reprocessed"),
    )


class WildfireCrosswalkTests(unittest.TestCase):
    def test_unique_source_id_is_only_a_candidate_not_cat_loss(self):
        result = run()
        self.assertEqual(result["state"], "RESEARCH_ID_CANDIDATES_ONLY")
        self.assertEqual(result["fpa_row_disposition"]["unique_mtbs_id_research_candidate"], 1)
        self.assertTrue(result["fpa_rows_conserved"])
        for field in (
            "mapped_components_are_independent_observations",
            "full_national_wildfire_census_proven",
            "physical_event_identity_approved", "contractual_occurrence_approved",
            "building_damage_or_insured_losses_derived",
            "scientific_fitness_established", "source_rights_or_model_admission_granted",
        ):
            self.assertFalse(result[field])
        self.assertNotIn("MTBS-ONE", json.dumps(result))

    def test_duplicate_fpa_mtbs_reference_flags_multiplication(self):
        a = fpa()
        b = dict(a, fpa_record_id="2")
        r = run(fpas=[a, b])
        self.assertEqual(r["fpa_row_disposition"]["ambiguous_one_to_many_or_many_to_one"], 2)
        self.assertEqual(r["state"], "REVIEW_NEEDED")
        self.assertEqual(r["fpa_row_disposition"]["unique_mtbs_id_research_candidate"], 0)

    def test_two_mtbs_components_one_id_not_counted_as_two_events(self):
        a = mtbs()
        b = dict(a, mtbs_component_id="p2")
        r = run(mtbss=[a, b])
        self.assertEqual(r["mtbs_component_rows"], 2)
        self.assertEqual(r["fpa_row_disposition"]["ambiguous_one_to_many_or_many_to_one"], 1)
        self.assertEqual(r["state"], "REVIEW_NEEDED")

    def test_no_mtbs_id_is_unknown_not_no_fire(self):
        r = run(fpas=[dict(fpa(), mtbs_id="")])
        self.assertEqual(r["fpa_row_disposition"]["no_mtbs_id_recorded"], 1)
        self.assertEqual(r["fpa_row_disposition"]["unique_mtbs_id_research_candidate"], 0)
        self.assertEqual(r["state"], "NO_UNAMBIGUOUS_ID_CANDIDATE")

    def test_id_missing_from_bounded_mtbs_subset_is_not_no_wildfire(self):
        r = run(fpas=[dict(fpa(), mtbs_id="OTHER")])
        self.assertEqual(r["fpa_row_disposition"]["mtbs_id_not_in_supplied_perimeter_subset"], 1)
        self.assertEqual(r["mtbs_components_without_fpa_reference"], 1)

    def test_fire_year_disagreement_blocks_promotion(self):
        r = run(mtbss=[dict(mtbs(), fire_year="2020")])
        self.assertEqual(r["fpa_row_disposition"]["source_fire_year_disagreement"], 1)
        self.assertEqual(r["state"], "REVIEW_NEEDED")

    def test_prescribed_and_unknown_are_not_wildfire_loss_candidates(self):
        for value, expected in (("prescribed", "prescribed_fire_not_wildfire"),
                                ("unknown", "unknown_mtbs_event_kind")):
            with self.subTest(value=value):
                r = run(mtbss=[dict(mtbs(), event_kind=value)])
                self.assertEqual(r["fpa_row_disposition"][expected], 1)
                self.assertEqual(r["fpa_row_disposition"]["unique_mtbs_id_research_candidate"], 0)

    def test_duplicate_source_record_ids_rejected(self):
        with self.assertRaisesRegex(w.WildfireAuditBlocked, "duplicate FPA"):
            run(fpas=[fpa(), fpa()])

    def test_duplicate_component_keys_rejected(self):
        with self.assertRaisesRegex(w.WildfireAuditBlocked, "duplicate MTBS"):
            run(mtbss=[mtbs(), mtbs()])

    def test_unfrozen_release_or_malformed_vintage_rejected(self):
        for f, m in (("FPA_FOD_2024", "MTBS-2026Q3-publisher-reprocessed"),
                     ("FPA_FOD_20260615", "current"),
                     ("FPA_FOD_20260615", "MTBS-latest-publisher")):
            with self.subTest(f=f, m=m), self.assertRaises(w.WildfireAuditBlocked):
                run(fpa_release=f, mtbs_release=m)

    def test_hash_mismatch_wrong_header_and_invalid_projections_rejected(self):
        good = csv_bytes(w.FPA_COLUMNS, [fpa()])
        m = csv_bytes(w.MTBS_COLUMNS, [mtbs()])
        sha_m = hashlib.sha256(m).hexdigest()
        with self.assertRaisesRegex(w.WildfireAuditBlocked, "SHA-256 mismatch"):
            w.audit_crosswalk(good, "0"*64, m, sha_m,
                              fpa_release="FPA_FOD_20260615",
                              mtbs_release="MTBS-2026Q3-publisher-reprocessed")
        bad = csv_bytes(("wrong",), [{"wrong":"1"}])
        with self.assertRaisesRegex(w.WildfireAuditBlocked, "column order"):
            w.audit_crosswalk(bad, hashlib.sha256(bad).hexdigest(), m, sha_m,
                              fpa_release="FPA_FOD_20260615",
                              mtbs_release="MTBS-2026Q3-publisher-reprocessed")

    def test_no_unbounded_input_or_invalid_identifier(self):
        with self.assertRaises(w.WildfireAuditBlocked):
            w._read_projection(b"x"* (w.MAX_BYTES+1), "0"*64, w.FPA_COLUMNS, "FPA")
        with self.assertRaisesRegex(w.WildfireAuditBlocked, "invalid source identifier"):
            run(fpas=[dict(fpa(), mtbs_id="MTBS ONE")])
        with self.assertRaisesRegex(w.WildfireAuditBlocked, "source temporal scope"):
            run(fpas=[dict(fpa(), fire_year="2025")])

    def test_row_dispositions_are_conserved_and_independent_of_order(self):
        a=fpa()
        b=dict(a, fpa_record_id="2", mtbs_id="")
        c=dict(a, fpa_record_id="3", mtbs_id="missing")
        first=run(fpas=[a,b,c])
        second=run(fpas=[c,a,b])
        # The input byte receipt must change on reordering, but the aggregate
        # scientific disposition is deterministic and conserves parent rows.
        self.assertNotEqual(first["fpa_projection_sha256"], second["fpa_projection_sha256"])
        self.assertEqual(first["fpa_row_disposition"], second["fpa_row_disposition"])
        self.assertEqual(first["state"], second["state"])
        self.assertEqual(sum(first["fpa_row_disposition"].values()),3)
        self.assertEqual(first["fpa_row_disposition"]["unique_mtbs_id_research_candidate"],1)
