# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only controls for true size-conditioned MTBS-ID missingness."""
import hashlib
import json
import unittest

from research_runners import us_wildfire_2024_size_linkage_stats_v0 as gate


def grouped(counts, *, kind="esriFieldTypeBigInteger"):
    return {
        "fields": [
            {"name": "fire_size_class", "type": "esriFieldTypeString"},
            {"name": "n", "type": kind},
        ],
        "features": [
            {"attributes": {"fire_size_class": cls, "n": value}}
            for cls, value in counts.items() if value
        ],
    }


def encode(doc):
    raw = json.dumps(doc, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return raw, hashlib.sha256(raw).hexdigest()


def example():
    all_counts = dict(A=100, B=200, C=300, D=40, E=30, F=20, G=10)
    linked = dict(A=1, D=2, E=5, F=10, G=8)
    unlinked = {k: v-linked.get(k, 0) for k, v in all_counts.items()}
    return all_counts, linked, unlinked


def audited(a=None, y=None, n=None, *, arg=None):
    originals = example()
    docs = (
        grouped(originals[0]) if a is None else a,
        grouped(originals[1]) if y is None else y,
        grouped(originals[2]) if n is None else n,
    )
    pairs = [encode(x) for x in docs]
    return gate.audit_size_linkage(
        pairs[0][0], pairs[0][1],
        pairs[1][0], pairs[1][1],
        pairs[2][0], pairs[2][1],
        fpa_release="FPA_FOD_20260615" if arg is None else arg,
    )


class SizeLinkageStatsTests(unittest.TestCase):
    def test_complete_disjoint_partition_and_denominator(self):
        r = audited()
        self.assertEqual(r["fpa_reported_records"], 700)
        self.assertEqual(r["mtbs_id_present_records"], 26)
        self.assertEqual(r["mtbs_id_absent_records"], 674)
        self.assertEqual(r["mtbs_id_present_pct_all"], "3.7143")
        self.assertEqual(r["classes_F_G_records"], 30)
        self.assertEqual(r["classes_F_G_mtbs_id_present"], 18)
        self.assertEqual(r["classes_F_G_mtbs_id_present_pct"], "60.0000")
        self.assertEqual(r["classes_A_C_mtbs_id_present"], 1)
        self.assertTrue(r["fpa_cohort_conserved_by_class_and_total"])
        self.assertTrue(r["small_class_A_linkage_requires_identity_review"])

    def test_conservative_status_flags_and_no_input_event_ids(self):
        r = audited()
        self.assertEqual(r["state"], "RESEARCH_COUNTS_CONSERVED_NOT_MODEL_ADMITTED")
        for name in (
            "query_selection_origin_independently_authenticated",
            "full_MTBS_fire_id_match_proven",
            "source_coverage_or_fire_frequency_established",
            "independent_MTBS_obs_proven",
            "original_archived_asset_hash_verified",
            "rights_and_scientific_CAT_admission_granted",
            "insurance_loss_or_portfolio_inferred",
        ):
            self.assertFalse(r[name])

    def test_class_ratios_preserve_division_bases(self):
        r = audited()
        b = {row["class"]: row for row in r["class_groups"]}
        self.assertEqual(b["A"]["id_present_pct_of_class"], "1.0000")
        self.assertEqual(b["B"]["id_present_pct_of_class"], "0.0000")
        self.assertEqual(b["E"]["id_present_pct_of_class"], "16.6667")
        self.assertEqual(b["G"]["id_present_pct_of_class"], "80.0000")

    def test_three_way_missing_counts_cannot_disappear(self):
        a, yes, no = example()
        no["A"] -= 1
        with self.assertRaisesRegex(gate.SizeLinkageBlocked, "three-way conservation"):
            audited(n=grouped(no))

    def test_compensating_cross_class_errors_not_hidden_by_total(self):
        a, yes, no = example()
        no["A"] -= 1
        no["B"] += 1
        with self.assertRaisesRegex(gate.SizeLinkageBlocked, "three-way conservation"):
            audited(n=grouped(no))

    def test_unexpected_size_group_blocked(self):
        a, _, _ = example()
        a["H"] = a.pop("G")
        with self.assertRaisesRegex(gate.SizeLinkageBlocked, "unknown"):
            audited(a=grouped(a))

    def test_missing_denominator_class_rejected(self):
        a, _, _ = example()
        del a["B"]
        with self.assertRaisesRegex(gate.SizeLinkageBlocked, "complete 2024"):
            audited(a=grouped(a))

    def test_size_class_duplicate_rejected(self):
        a, _, _ = example()
        obj = grouped(a)
        obj["features"].append({"attributes": {"fire_size_class":"A","n":1}})
        with self.assertRaises(gate.SizeLinkageBlocked):
            audited(a=obj)

    def test_negative_nonnumeric_and_boolean_values_rejected(self):
        a, _, _ = example()
        for count in (-1, "100", True, 0):
            obj = grouped(a)
            obj["features"][0]["attributes"]["n"] = count
            if count == 0:
                with self.assertRaises(gate.SizeLinkageBlocked):
                    audited(a=obj)
            else:
                with self.assertRaises(gate.SizeLinkageBlocked):
                    audited(a=obj)

    def test_arcgis_group_query_transfer_limit_must_be_false(self):
        a, _, _ = example()
        obj = grouped(a)
        obj["exceededTransferLimit"] = True
        with self.assertRaisesRegex(gate.SizeLinkageBlocked, "transfer limit"):
            audited(a=obj)

    def test_wrong_group_type_or_missing_fields_rejected(self):
        a, _, _ = example()
        for obj in (
            grouped(a, kind="esriFieldTypeDouble"),
            {"features": grouped(a)["features"]},
            {**grouped(a), "fields": []},
        ):
            with self.assertRaises(gate.SizeLinkageBlocked):
                audited(a=obj)

    def test_malformed_hash_duplicate_json_nonfinite_rejected(self):
        blob, hashval = encode(grouped(example()[0]))
        with self.assertRaisesRegex(gate.SizeLinkageBlocked, "SHA-256 mismatch"):
            gate._parse_grouped(blob, "0"*64, "all")
        for raw in (b'{"a":1,"a":2}', b'{"n":NaN}'):
            with self.assertRaises(gate.SizeLinkageBlocked):
                gate._parse_grouped(raw, hashlib.sha256(raw).hexdigest(), "all")

    def test_duplicate_field_casefold_and_attributes_blocked(self):
        a, _, _ = example()
        obj = grouped(a)
        obj["fields"][1]["name"] = "FIRE_SIZE_CLASS"
        with self.assertRaises(gate.SizeLinkageBlocked):
            audited(a=obj)
        obj = grouped(a)
        obj["features"][0]["geometry"] = {"x":0,"y":0}
        with self.assertRaises(gate.SizeLinkageBlocked):
            audited(a=obj)

    def test_invalid_release_and_unbounded_count_rejected(self):
        with self.assertRaisesRegex(gate.SizeLinkageBlocked, "seventh-edition"):
            audited(arg="FPA_FOD_2020")
        a, _, _ = example()
        a["A"] = 5_000_001
        with self.assertRaises(gate.SizeLinkageBlocked):
            audited(a=grouped(a))
