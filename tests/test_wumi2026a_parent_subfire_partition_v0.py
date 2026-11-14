# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only comparison of WUMI2026a parent/with-subfire alternative lists."""
import io
import unittest
from zipfile import ZipFile

from research_runners import wumi2026a_parent_subfire_partition_v0 as gate
from research_runners import wumi2026a_dryad_original_asset_receipt_v0 as zip_gate

# Publisher code uses at least 26 comma-separated fields; these are fictional
# rows, never source records or any real ignition coordinates.
FIELDS = ("fireid", "dataset", "agency", "name", "year", "month", "day",
          "lat", "lon", "lat_ll", "lon_ll", "lat_ur", "lon_ur",
          "poly_area_ha", "burn_area_ha", "mtbs_name", "mtbs_id",
          "irwinid", "fod_id", "fpa_id", "object_id_wfaip",
          "object_id_fpafod", "object_id_wfigs", "object_id_calfire",
          "object_id_usgs", "object_id_iafph", "cause_human_or_natural",
          "cause_specific")


def row(fireid, *, year=2024, polygon="400", burned="300", source="mtbs"):
    attrs = {key: "N/A" for key in FIELDS}
    attrs.update(fireid=fireid, year=str(year), month="7", day="8",
                 dataset=source, poly_area_ha=polygon, burn_area_ha=burned)
    return ",".join(attrs[x] for x in FIELDS)


def listbytes(*rows, header=FIELDS):
    return (",".join(header) + "\n" + "\n".join(rows) + "\n").encode()


PARENT = "20240708_330000_1110000"
CHILD1 = "20240708_330001_1110000"
CHILD2 = "20240708_330002_1110000"
STANDALONE = "20240708_330003_1110000"


def synthetic_pair():
    return (listbytes(row(PARENT), row(STANDALONE)),
            listbytes(row(CHILD1, polygon="200", burned="150"),
                      row(CHILD2, polygon="200", burned="150"),
                      row(STANDALONE)))


class WumiPartitionTests(unittest.TestCase):
    def test_two_alternative_views_are_not_summable(self):
        a, b = synthetic_pair()
        r = gate.compare_alternative_list_views(a, b)
        self.assertEqual(r["state"], "ALTERNATIVE_VIEWS_COUNTED_NOT_ADMITTED")
        self.assertEqual(r["no_subfires"]["records"], 2)
        self.assertEqual(r["with_subfires"]["records"], 3)
        self.assertEqual(r["shared_fireids"], 1)
        self.assertEqual(r["parent_view_ids_absent_from_subfire_view"], 1)
        self.assertEqual(r["subfire_view_ids_absent_from_parent_view"], 2)
        for attr in ("two_views_can_be_summed_for_frequency", "parent_subfire_genealogy_verified",
                     "event_frequency_or_insured_loss_model_admitted",
                     "publisher_fireid_can_be_recomputed_from_modified_coordinates"):
            self.assertFalse(r[attr])
        # Original IDs, coordinates or event rows must not reach logs.
        self.assertNotIn(PARENT, str(r))
        self.assertNotIn(CHILD1, str(r))

    def test_common_ids_do_not_double_count_or_require_area_sum(self):
        a, b = synthetic_pair()
        r = gate.compare_alternative_list_views(a, b)
        self.assertEqual(r["shared_fireids_with_different_area_fields"], 0)
        self.assertFalse(r["child_polygon_area_sums_verifiably_match_parents"])

    def test_revised_coordinates_not_derived_from_fireid(self):
        a, b = synthetic_pair()
        # Date mismatch is measured, not treated as new event.
        b = b.replace(b"2024,7,8", b"2024,7,9", 1)
        r = gate.compare_alternative_list_views(a, b)
        self.assertEqual(r["with_subfires"]["fireid_date_components_disagree_count"], 1)

    def test_shared_identity_with_area_revision_requires_review(self):
        a, b = synthetic_pair()
        b = b.replace(row(STANDALONE).encode(),
                      row(STANDALONE, polygon="403").encode())
        r = gate.compare_alternative_list_views(a, b)
        self.assertEqual(r["state"], "REVIEW_SHARED_ROWS")
        self.assertEqual(r["shared_fireids_with_different_area_fields"], 1)

    def test_duplicate_id_in_one_view_blocks(self):
        a, b = synthetic_pair()
        with self.assertRaisesRegex(gate.PartitionBlocked, "duplicate"):
            gate.compare_alternative_list_views(a, listbytes(row(CHILD1), row(CHILD1)))

    def test_common_id_annual_conflict_blocks(self):
        a, b = synthetic_pair()
        b = b.replace(row(STANDALONE).encode(),
                      row(STANDALONE, year=2023).encode())
        with self.assertRaisesRegex(gate.PartitionBlocked, "different years"):
            gate.compare_alternative_list_views(a, b)

    def test_different_headers_and_bad_schema_block(self):
        a, b = synthetic_pair()
        with self.assertRaises(gate.PartitionBlocked):
            gate.compare_alternative_list_views(a, listbytes(row(CHILD1), header=("x",)))
        with self.assertRaises(gate.PartitionBlocked):
            gate.compare_alternative_list_views(a, b.replace(b"poly_area_ha", b"poly_ha"))

    def test_nonfinite_negative_area_and_bad_csv_rejected(self):
        a, b = synthetic_pair()
        for bad in ("-40", "Infinity", "not-a-number"):
            with self.subTest(bad=bad):
                modified = listbytes(row(PARENT, polygon=bad), row(STANDALONE))
                with self.assertRaises(gate.PartitionBlocked):
                    gate.compare_alternative_list_views(modified, b)
        with self.assertRaises(gate.PartitionBlocked):
            gate.compare_alternative_list_views(a, b + b"invalid,extra,row\n")

    def test_original_zip_digest_enforced_even_for_fake_valid_synthetic_members(self):
        a, b = synthetic_pair()
        stream = io.BytesIO()
        with ZipFile(stream, "w") as z:
            z.writestr(gate.NO_NAME, a)
            z.writestr(gate.WITH_NAME, b)
        with self.assertRaisesRegex(zip_gate.DryadReceiptBlocked, "byte count"):
            gate.inspect_original_pinned_partition_zip(stream.getvalue())

    def test_missing_mandatory_zip_member_cannot_be_processed(self):
        with self.assertRaises(gate.PartitionBlocked):
            gate.compare_alternative_list_views(b"not-a-list", b"not-a-list")
