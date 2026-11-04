# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fictional parent/child relations only; never original WUMI data."""
import io
import unittest
from zipfile import ZipFile

from research_runners import wumi2026a_original_subfires_genealogy_v0 as g
from research_runners import wumi2026a_dryad_original_asset_receipt_v0 as z
from tests.test_wumi2026a_parent_subfire_partition_v0 import (
    FIELDS, PARENT, CHILD1, CHILD2, STANDALONE, listbytes, row, synthetic_pair,
)

NESTED = "20240708_330004_1110000"


def note(parent=PARENT, candidates=None, *, nested=False):
    if candidates is None:
        candidates = [CHILD1, CHILD2]
    children = [row(candidates[0], polygon="200", burned="150")]
    if nested:
        children.append(row(NESTED, polygon="101", burned="90"))
    children.extend(["", row(candidates[1], polygon="200", burned="150")])
    # Publisher writes: header \n parent row \n blank \n child[ren]
    return (",".join(FIELDS) + "\n" + row(parent) + "\n\n" +
            "\n".join(children) + "\n").encode("utf8")


class OriginalGenealogyTests(unittest.TestCase):
    def test_exact_parent_subfire_candidate_mapping_non_admission(self):
        before, after = synthetic_pair()
        r = g.audit_original_genealogy_notes(before, after, {PARENT: note()})
        self.assertEqual(r["state"], "BOUNDED_SOURCE_GENEALOGY_ONLY")
        self.assertEqual(r["source_subfires_note_count"], 1)
        self.assertEqual(r["source_candidate_child_records"], 2)
        self.assertEqual(r["source_top_level_child_groups"], 2)
        self.assertEqual(r["source_nested_sub_sub_fire_records"], 0)
        self.assertEqual(r["parent_polygon_area_sums_within_publisher_rounding_tolerance"], 1)
        self.assertEqual(r["final_added_ids_absent_from_all_source_notes"], 0)
        for key in ("two_final_views_additive", "insurance_occurrence_or_loss_proven",
                    "native_source_parent_child_physical_identity_proven",
                    "source_reuse_rights_or_CAT_admission_granted"):
            self.assertFalse(r[key])
        self.assertNotIn(PARENT, str(r))
        self.assertNotIn(CHILD1, str(r))

    def test_nested_source_candidates_not_assumed_final_events(self):
        before, after = synthetic_pair()
        r = g.audit_original_genealogy_notes(before, after, {PARENT: note(nested=True)})
        self.assertEqual(r["source_top_level_child_groups"], 2)
        self.assertEqual(r["source_nested_sub_sub_fire_records"], 1)
        self.assertEqual(r["source_candidate_child_records"], 3)
        self.assertEqual(r["with_subfires"]["records"], 3)
        self.assertTrue(r["candidate_notes_not_treated_as_final_event_count"])

    def test_untraced_added_final_event_requires_review(self):
        before, after = synthetic_pair()
        r = g.audit_original_genealogy_notes(
            before, after, {PARENT: note(candidates=[CHILD1, NESTED])}
        )
        self.assertEqual(r["state"], "REVIEW_GENEALOGY_COVERAGE_OR_AREA")
        self.assertEqual(r["final_added_ids_absent_from_all_source_notes"], 1)

    def test_parent_metadata_conflict_blocks(self):
        before, after = synthetic_pair()
        wrong = note().replace(row(PARENT).encode(), row(PARENT, polygon="401").encode())
        with self.assertRaisesRegex(g.GenealogyBlocked, "parent row conflicts"):
            g.audit_original_genealogy_notes(before, after, {PARENT: wrong})

    def test_parent_note_filename_not_in_first_view_blocks(self):
        before, after = synthetic_pair()
        with self.assertRaises(g.GenealogyBlocked):
            g.audit_original_genealogy_notes(before, after, {CHILD1: note()})

    def test_parent_reused_as_child_blocks(self):
        before, after = synthetic_pair()
        with self.assertRaises(g.GenealogyBlocked):
            g.audit_original_genealogy_notes(before, after, {PARENT: note(candidates=[PARENT, CHILD2])})

    def test_missing_separation_or_header_blocks(self):
        before, after = synthetic_pair()
        for invalid in (note().replace(b"\n\n", b"\n"), note().replace(b"fireid", b"abcde")):
            with self.subTest(length=len(invalid)), self.assertRaises(g.GenealogyBlocked):
                g.audit_original_genealogy_notes(before, after, {PARENT: invalid})

    def test_wrong_polygon_conservation_requires_review_not_loss_admission(self):
        before, after = synthetic_pair()
        after = after.replace(row(CHILD2, polygon="200", burned="150").encode(),
                              row(CHILD2, polygon="210", burned="150").encode())
        result = g.audit_original_genealogy_notes(before, after, {PARENT: note()})
        self.assertEqual(result["state"], "REVIEW_GENEALOGY_COVERAGE_OR_AREA")
        self.assertEqual(result["parent_polygon_area_sums_disagree"], 1)
        self.assertFalse(result["insurance_occurrence_or_loss_proven"])

    def test_missing_source_note_is_fail_closed(self):
        before, after = synthetic_pair()
        with self.assertRaisesRegex(g.GenealogyBlocked, "missing"):
            g.audit_original_genealogy_notes(before, after, {})

    def test_real_zip_hash_is_required_before_reading_synthetic_member_contents(self):
        before, after = synthetic_pair()
        stream = io.BytesIO()
        with ZipFile(stream, "w") as a:
            a.writestr(g.NO_NAME, before)
            a.writestr(g.WITH_NAME, after)
            a.writestr("subfires/" + PARENT + ".txt", note())
        with self.assertRaisesRegex(z.DryadReceiptBlocked, "byte count"):
            g.inspect_pinned_genealogy_zip(stream.getvalue())
