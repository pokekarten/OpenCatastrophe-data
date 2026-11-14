# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ArcGIS grouped statistics. No source events or original bytes."""
import hashlib
import json
import unittest
from research_runners import us_wildfire_2024_state_size_linkage_v0 as g

FIELDS = [
    {"name": "state", "type": "esriFieldTypeString"},
    {"name": "fire_size_class", "type": "esriFieldTypeString"},
    {"name": "n", "type": "esriFieldTypeBigInteger"},
]


def fixture():
    a = {
        ("CA", "A"): 100, ("CA", "B"): 200, ("CA", "C"): 80,
        ("CA", "D"): 40, ("CA", "E"): 30, ("CA", "F"): 20, ("CA", "G"): 10,
        ("OR", "A"): 50, ("OR", "B"): 20, ("OR", "C"): 10,
        ("OR", "D"): 2, ("OR", "E"): 3, ("OR", "F"): 12, ("OR", "G"): 8,
    }
    y = {
        ("CA", "A"): 1, ("CA", "D"): 1, ("CA", "F"): 10, ("CA", "G"): 7,
        ("OR", "F"): 10, ("OR", "G"): 8,
    }
    n = {key: count-y.get(key, 0) for key, count in a.items()}
    return a, y, n


def original(cells):
    return {
        "fields": [dict(field) for field in FIELDS],
        "features": [
            {"attributes": {"state": state, "fire_size_class": cls, "n": count}}
            for (state, cls), count in cells.items() if count
        ],
    }


def enc(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return raw, hashlib.sha256(raw).hexdigest()


def expected(a, y, n):
    return {
        label: {
            cls: sum(v for (s, c), v in cells.items() if c == cls)
            for cls in g.CLASSES
        }
        for label, cells in (("all", a), ("linked", y), ("unlinked", n))
    }


def audit(a=None, y=None, n=None, *, state_count=2, version="FPA_FOD_20260615"):
    orig = fixture()
    vals = [orig[i] if val is None else val for i, val in enumerate((a, y, n))]
    payload = [enc(original(v)) for v in vals]
    return g.audit_state_size(
        payload[0][0], payload[0][1], payload[1][0], payload[1][1],
        payload[2][0], payload[2][1],
        fpa_release=version, expected_marginals=expected(*orig),
        expected_states=state_count,
    )


class JointStateSizeTests(unittest.TestCase):
    def test_genuine_joint_counts_and_stable_denominators(self):
        report = audit()
        self.assertEqual(report["number_state_territory_codes"], 2)
        self.assertEqual(report["original_nonempty_cell_count"]["all"], 14)
        self.assertEqual(report["record_totals"], dict(all=585, linked=37, unlinked=548))
        ca, ore = report["state_rows"]
        self.assertEqual((ca["state_code"],ca["large_fg_fpa_total"],ca["large_fg_mtbs_id_present"]),("CA",30,17))
        self.assertEqual((ore["state_code"],ore["large_fg_fpa_total"],ore["large_fg_mtbs_id_present"]),("OR",20,18))
        self.assertEqual(ca["large_fg_pct_if_n_ge_10"], "56.67")
        self.assertEqual(ore["large_fg_pct_if_n_ge_10"], "90.00")
        self.assertEqual(report["linked_class_A_count_requires_identity_review"], 1)
        for field in ("source_rights_and_CAT_admission_granted",
                      "MTBS_ID_equivalent_to_verified_MTBS_FIRE_ID_join",
                      "original_archived_fpa_asset_sha256_verified"):
            self.assertFalse(report[field])

    def test_cross_state_compensation_cannot_hide_missing_link(self):
        a,y,n = fixture()
        n[("CA","A")] -= 1
        n[("OR","A")] += 1
        with self.assertRaisesRegex(g.GroupedStateBlocked,"three-way conservation"):
            audit(n=n)

    def test_cross_class_compensation_cannot_hide_missing_link(self):
        a,y,n = fixture()
        n[("CA","B")] += 1
        n[("CA","D")] -= 1
        with self.assertRaisesRegex(g.GroupedStateBlocked,"three-way conservation"):
            audit(n=n)

    def test_new_link_without_denominator_is_blocked(self):
        a,y,n = fixture()
        y[("ZZ","A")] = 1
        with self.assertRaisesRegex(g.GroupedStateBlocked,"outside"):
            audit(y=y)

    def test_duplicate_state_size_and_duplicate_metadata_column(self):
        doc = original(fixture()[0])
        doc["features"].append({"attributes":{"state":"CA","fire_size_class":"A","n":1}})
        raw, sha = enc(doc)
        with self.assertRaisesRegex(g.GroupedStateBlocked,"duplicate state"):
            g._parse(raw,sha,"all")
        doc = original(fixture()[0])
        doc["fields"][1] = {"name":"STATE","type":"esriFieldTypeString"}
        raw,sha=enc(doc)
        with self.assertRaises(g.GroupedStateBlocked):
            g._parse(raw,sha,"all")

    def test_invalid_source_size_code_and_numeric_field(self):
        for key, val in (("state","California"),("fire_size_class","H"),("n",True),("n",-1),("n","20")):
            doc=original(fixture()[0])
            doc["features"][0]["attributes"][key]=val
            raw,sha=enc(doc)
            with self.subTest(key=key,value=val),self.assertRaises(g.GroupedStateBlocked):
                g._parse(raw,sha,"all")

    def test_geom_transfer_limit_and_bad_sha_fail_closed(self):
        doc=original(fixture()[0])
        raw,sha=enc(doc)
        with self.assertRaisesRegex(g.GroupedStateBlocked,"SHA256 mismatch"):
            g._parse(raw,"0"*64,"all")
        doc["features"][0]["geometry"]={"x":-120,"y":43}
        raw,sha=enc(doc)
        with self.assertRaisesRegex(g.GroupedStateBlocked,"geometry"):
            g._parse(raw,sha,"all")
        doc=original(fixture()[0])
        doc["exceededTransferLimit"]=True
        raw,sha=enc(doc)
        with self.assertRaisesRegex(g.GroupedStateBlocked,"transfer"):
            g._parse(raw,sha,"all")

    def test_bad_json_key_duplication_and_nan_rejected(self):
        for raw in (b'{"x":1,"x":2}',b'{"a":NaN}'):
            with self.assertRaises(g.GroupedStateBlocked):
                g._parse(raw,hashlib.sha256(raw).hexdigest(),"all")

    def test_drifted_seventh_edition_or_different_state_count_blocks(self):
        with self.assertRaisesRegex(g.GroupedStateBlocked,"edition"):
            audit(version="current")
        with self.assertRaisesRegex(g.GroupedStateBlocked,"unexpected original state"):
            audit(state_count=53)

    def test_valid_2024_count_change_requires_a_new_source_review(self):
        a,y,n=fixture()
        a[("CA","A")]+=1
        n[("CA","A")]+=1
        with self.assertRaisesRegex(g.GroupedStateBlocked,"marginals drifted"):
            audit(a=a,n=n)

    def test_small_large_fire_denominator_suppressed(self):
        a,y,n=fixture()
        a[("OR","F")]=2
        a[("OR","G")]=1
        y[("OR","F")]=1
        y[("OR","G")]=1
        n={k:v-y.get(k,0) for k,v in a.items()}
        pairs=[enc(original(v)) for v in (a,y,n)]
        report=g.audit_state_size(
            pairs[0][0],pairs[0][1],pairs[1][0],pairs[1][1],pairs[2][0],pairs[2][1],
            fpa_release="FPA_FOD_20260615",expected_marginals=expected(a,y,n),
            expected_states=2
        )
        self.assertEqual(report["state_rows"][1]["large_fg_fpa_total"],3)
        self.assertIsNone(report["state_rows"][1]["large_fg_pct_if_n_ge_10"])
