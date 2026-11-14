# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic GRWL DBF value and SHP XY-sequence tests; no original features."""
import io
import struct
import unittest
import zipfile

from research_runners.grwl_original_aggregate_semantic_diff_v0 import (
    OriginalZipError, _normalized, aggregate_pair, main,
    read_dbf_semantics, read_shp_xy_sequences,
)


def dbf_bytes(rows, fields=(("width_mean", "N", 12), ("lakeflag", "N", 3),
                             ("region", "C", 3))):
    record_len = 1 + sum(length for _, _, length in fields)
    header_len = 32 + 32 * len(fields) + 1
    out = bytearray(header_len + record_len * len(rows))
    out[0] = 3
    struct.pack_into("<I", out, 4, len(rows))
    struct.pack_into("<HH", out, 8, header_len, record_len)
    for j, (name, kind, width) in enumerate(fields):
        base = 32 + 32 * j
        n = name.encode("ascii")
        out[base:base+len(n)] = n
        out[base+11] = ord(kind)
        out[base+16] = width
    out[header_len-1] = 0x0d
    for i, row in enumerate(rows):
        raw = b" " + b"".join(
            (str(value).encode("ascii").rjust(width) if kind in ("N", "F")
             else str(value).encode("ascii").ljust(width))
            for (_, kind, width), value in zip(fields, row))
        assert len(raw) == record_len
        out[header_len+i*record_len:header_len+(i+1)*record_len] = raw
    return bytes(out)


def make_shp(points_by_record):
    records = []
    for i, (start, finish) in enumerate(points_by_record):
        a, b = start, finish
        bounds = min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])
        body = (struct.pack("<i4dII", 3, *bounds, 1, 2) +
                struct.pack("<I", 0) +
                struct.pack("<4d", *a, *b))
        records.append(struct.pack(">II", i+1, len(body)//2) + body)
    full_len = 100 + sum(map(len,records))
    header = bytearray(100)
    struct.pack_into(">i",header,0,9994)
    struct.pack_into(">i",header,24,full_len//2)
    struct.pack_into("<i",header,28,1000)
    struct.pack_into("<i",header,32,3)
    struct.pack_into("<4d",header,36,-10.,-10.,10.,10.)
    return bytes(header)+b"".join(records)


A=((0.,0.),(1.,0.))
B=((1.,0.),(2.,0.))
C=((1.,0.),(2.,0.5))


def artifact(rows=(("100.00",0,"DE"),("200.0",0,"FR")), points=(A,B), fields=None):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("GRWL_summaryStats.dbf", dbf_bytes(rows,fields) if fields else dbf_bytes(rows))
        z.writestr("GRWL_summaryStats.shp", make_shp(points))
        z.writestr("GRWL_summaryStats.shx", b"SHX-file")
        z.writestr("GRWL_summaryStats.prj", b'GEOGCS["GCS_WGS_1984"]')
    return b.getvalue()


def parse(src):
    with zipfile.ZipFile(io.BytesIO(src)) as z:
        return read_dbf_semantics(z),read_shp_xy_sequences(z)


def compare(a,b):
    x,y=parse(a),parse(b)
    return aggregate_pair(x[0],y[0],x[1],y[1])


class AggregateSemanticTests(unittest.TestCase):
    def test_identical_synthetic_attributes_and_xy(self):
        r=compare(artifact(),artifact())
        self.assertTrue(r["semantic_row_multiset_equal"])
        self.assertTrue(r["shp_xy_sequence_multiset_equal"])
        self.assertEqual(r["minimum_unmatched_xy_sequences_each_release"],0)
        self.assertEqual(r["record_count_2018"],2)
        self.assertFalse(r["per_river_change_attribution_verified"])
        self.assertFalse(r["model_input_admitted"])

    def test_row_and_geometry_reordering_detected_not_mislabeled(self):
        swapped=artifact(rows=(("200.0",0,"FR"),("100.00",0,"DE")),points=(B,A))
        r=compare(artifact(),swapped)
        self.assertTrue(r["semantic_row_multiset_equal"])
        self.assertFalse(r["semantic_rows_equal_by_ordinal"])
        self.assertTrue(r["shp_xy_sequence_multiset_equal"])
        self.assertFalse(r["shp_xy_sequences_equal_by_ordinal"])
        self.assertEqual(r["minimum_unmatched_semantic_rows_each_release"],0)

    def test_real_numeric_width_distribution_shift_detectable(self):
        r=compare(artifact(),artifact(rows=(("101",0,"DE"),("200.0",0,"FR"))))
        widths=next(x for x in r["dbf_fields"] if x["field"]=="WIDTH_MEAN")
        self.assertFalse(widths["value_multiset_equal"])
        self.assertEqual(widths["minimum_unmatched_values_each_release"],1)
        self.assertFalse(r["per_river_change_attribution_verified"])

    def test_number_formatting_does_not_fake_width_change(self):
        r=compare(artifact(),artifact(rows=(("0100.000",0,"DE"),("0200.00",0,"FR"))))
        self.assertTrue(r["semantic_row_multiset_equal"])

    def test_other_column_change_keeps_width_distribution_equal(self):
        r=compare(artifact(),artifact(rows=(("100",0,"GB"),("200",0,"FR"))))
        self.assertTrue(next(x for x in r["dbf_fields"] if x["field"]=="WIDTH_MEAN")["value_multiset_equal"])
        self.assertFalse(r["semantic_row_multiset_equal"])

    def test_xy_change_distinguished_from_attribute_change(self):
        r=compare(artifact(),artifact(points=(A,C)))
        self.assertFalse(r["shp_xy_sequence_multiset_equal"])
        self.assertEqual(r["minimum_unmatched_xy_sequences_each_release"],1)
        self.assertTrue(r["semantic_row_multiset_equal"])

    def test_reverse_direction_may_change_byte_sequence_not_topology_claim(self):
        r=compare(artifact(),artifact(points=((A[1],A[0]),B)))
        self.assertFalse(r["shp_xy_sequence_multiset_equal"])
        self.assertFalse(r["per_river_change_attribution_verified"])

    def test_missing_width_field_rejected(self):
        bad=artifact(rows=((0,"DE"),(0,"FR")),fields=(("lakeflag","N",3),("region","C",3)))
        with self.assertRaises(OriginalZipError):parse(bad)

    def test_duplicate_dbf_field_name_rejected(self):
        bad=artifact(rows=(("1","2"),("3","4")),
                     fields=(("width_mean","N",12),("width_mean","N",12)))
        with self.assertRaises(OriginalZipError):parse(bad)

    def test_invalid_numeric_value_rejected(self):
        with self.assertRaises(OriginalZipError):parse(artifact(rows=(("NaN",0,"DE"),("200",0,"FR"))))

    def test_invalid_numeric_constant_rejected(self):
        with self.assertRaises(OriginalZipError):_normalized(b"inf","N")

    def test_invalid_shp_coordinate_domain_rejected(self):
        with self.assertRaises(OriginalZipError):parse(artifact(points=(A,((200.,0.),(201.,0.)))))

    def test_invalid_dbf_deleted_record_rejected(self):
        b=artifact()
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            files={i.filename:z.read(i) for i in z.infolist()}
        dbf=bytearray(files["GRWL_summaryStats.dbf"])
        hdr=struct.unpack_from("<H",dbf,8)[0]
        dbf[hdr]=ord("*")
        files["GRWL_summaryStats.dbf"]=bytes(dbf)
        out=io.BytesIO()
        with zipfile.ZipFile(out,"w") as z:
            for k,v in files.items():z.writestr(k,v)
        with self.assertRaises(OriginalZipError):parse(out.getvalue())

    def test_field_schema_change_prevents_value_comparison(self):
        src=artifact()
        other=artifact(rows=(("100",0,"DE"),("200",0,"FR")),
                       fields=(("width_mean","N",12),("lakeflag","N",3),("region","C",4)))
        r=compare(src,other)
        self.assertFalse(r["dbf_field_schema_equal"])
        self.assertEqual(r["dbf_fields"],[])
        self.assertIsNone(r["minimum_unmatched_semantic_rows_each_release"])


    def test_unique_objectid_candidate_and_no_scientific_identity_admission(self):
        cols=(("objectid","N",10),("width_mean","N",12),("lakeflag","N",3),("region","C",3))
        src=artifact(rows=((1,"100",0,"DE"),(2,"200",0,"FR")),fields=cols)
        out=compare(src,src)["objectid_keyed_candidate"]
        self.assertEqual(out["status"],"unique_matching_objectid_candidate_only")
        self.assertEqual(out["matched_export_objectid_values"],2)
        self.assertEqual(out["field_values_different_at_matching_objectid"]["WIDTH_MEAN"],0)
        self.assertEqual(out["xy_sequences_different_at_matching_objectid"],0)
        self.assertFalse(out["objectid_is_approved_stable_river_identifier"])
        self.assertFalse(out["per_river_change_attribution_verified"])
        self.assertFalse(out["any_raw_objectids_or_feature_values_emitted"])

    def test_reordered_objectid_and_corresponding_xy_stay_equal(self):
        cols=(("objectid","N",10),("width_mean","N",12),("lakeflag","N",3),("region","C",3))
        a=artifact(rows=((1,"100",0,"DE"),(2,"200",0,"FR")),fields=cols,points=(A,B))
        b=artifact(rows=((2,"200",0,"FR"),(1,"100",0,"DE")),fields=cols,points=(B,A))
        result=compare(a,b)["objectid_keyed_candidate"]
        self.assertFalse(result["export_objectid_order_equal"])
        self.assertEqual(result["field_values_different_at_matching_objectid"]["WIDTH_MEAN"],0)
        self.assertEqual(result["xy_sequences_different_at_matching_objectid"],0)

    def test_same_width_histogram_but_different_objectid_assignment(self):
        cols=(("objectid","N",10),("width_mean","N",12),("lakeflag","N",3),("region","C",3))
        a=artifact(rows=((1,"100",0,"DE"),(2,"200",0,"FR")),fields=cols)
        b=artifact(rows=((1,"200",0,"DE"),(2,"100",0,"FR")),fields=cols)
        result=compare(a,b)
        hist=next(f for f in result["dbf_fields"] if f["field"]=="WIDTH_MEAN")
        self.assertTrue(hist["value_multiset_equal"])
        self.assertEqual(result["objectid_keyed_candidate"]["field_values_different_at_matching_objectid"]["WIDTH_MEAN"],2)

    def test_keyed_xy_change_and_width_change_counted_separately(self):
        cols=(("objectid","N",10),("width_mean","N",12),("lakeflag","N",3),("region","C",3))
        a=artifact(rows=((1,"100",0,"DE"),(2,"200",0,"FR")),fields=cols)
        b=artifact(rows=((1,"101",0,"DE"),(2,"200",0,"FR")),fields=cols,points=(A,C))
        result=compare(a,b)["objectid_keyed_candidate"]
        self.assertEqual(result["field_values_different_at_matching_objectid"]["WIDTH_MEAN"],1)
        self.assertEqual(result["xy_sequences_different_at_matching_objectid"],1)

    def test_duplicate_objectid_blocks_candidate(self):
        cols=(("objectid","N",10),("width_mean","N",12),("lakeflag","N",3),("region","C",3))
        a=artifact(rows=((1,"100",0,"DE"),(1,"200",0,"FR")),fields=cols)
        result=compare(a,a)["objectid_keyed_candidate"]
        self.assertEqual(result["status"],"blocked_not_uniquely_matchable")

    def test_different_objectid_sets_block_candidate(self):
        cols=(("objectid","N",10),("width_mean","N",12),("lakeflag","N",3),("region","C",3))
        a=artifact(rows=((1,"100",0,"DE"),(2,"200",0,"FR")),fields=cols)
        b=artifact(rows=((1,"100",0,"DE"),(3,"200",0,"FR")),fields=cols)
        self.assertEqual(compare(a,b)["objectid_keyed_candidate"]["status"],"blocked_not_uniquely_matchable")

    def test_objectid_requires_numeric_column(self):
        cols=(("objectid","C",10),("width_mean","N",12),("lakeflag","N",3),("region","C",3))
        a=artifact(rows=((1,"100",0,"DE"),(2,"200",0,"FR")),fields=cols)
        self.assertEqual(compare(a,a)["objectid_keyed_candidate"]["status"],"blocked_not_uniquely_matchable")

    def test_only_shape_length_changed_at_unique_export_objectid(self):
        cols=(("objectid","N",10),("width_mean","N",12),("lakeflag","N",3),("shape_leng","F",19))
        a=artifact(rows=((1,"100",0,"3.123"),(2,"200",0,"4.321")),fields=cols)
        b=artifact(rows=((1,"100",0,"3.124"),(2,"200",0,"4.322")),fields=cols)
        keyed=compare(a,b)["objectid_keyed_candidate"]
        self.assertTrue(keyed["all_non_length_fields_equal_at_matching_objectid"])
        self.assertEqual(keyed["field_values_different_at_matching_objectid"]["SHAPE_LENG"],2)
        self.assertEqual(keyed["field_values_different_at_matching_objectid"]["WIDTH_MEAN"],0)

    def test_numeric_objectid_formatting_canonicalized(self):
        cols=(("objectid","N",10),("width_mean","N",12),("lakeflag","N",3),("region","C",3))
        a=artifact(rows=(("1","100",0,"DE"),("2","200",0,"FR")),fields=cols)
        b=artifact(rows=(("01.0","100",0,"DE"),("02.00","200",0,"FR")),fields=cols)
        keyed=compare(a,b)["objectid_keyed_candidate"]
        self.assertEqual(keyed["status"],"unique_matching_objectid_candidate_only")
        self.assertEqual(keyed["field_values_different_at_matching_objectid"]["OBJECTID"],0)

    def test_no_network_default(self):
        self.assertEqual(main([]),2)


if __name__=="__main__":
    unittest.main()
