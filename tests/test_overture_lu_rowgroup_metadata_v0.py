# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-free Parquet footer and rowgroup bbox screening regression tests."""
import struct
import unittest

from research_runners.overture_lu_rowgroup_metadata_v0 import (
    EXPECTED_ROWS, EXPECTED_ROW_GROUPS_STAC, MAX_FOOTER_BYTES,
    ProbeError, Reader, inspect_group, screen, read_metadata, main,
)


def column(name, low, high):
    return {3: {1: 5, 3: [p.encode() for p in name.split(".")], 12: {
        5: struct.pack("<f", high), 6: struct.pack("<f", low)}}}


def group(x=(6.12, 6.14), y=(49.60, 49.62), size=1):
    cols = [
        column("bbox.xmin", x[0], x[1]),
        column("bbox.xmax", x[0], x[1]),
        column("bbox.ymin", y[0], y[1]),
        column("bbox.ymax", y[0], y[1]),
    ]
    cols.extend({3: {1: 6, 3: [("other" + str(i)).encode()]}}
                for i in range(41))
    return {1: cols, 3: size}


class OvertureRowGroupMetadataTests(unittest.TestCase):
    def test_intersecting_group_is_only_candidate(self):
        self.assertEqual(inspect_group(group()), "candidate")

    def test_distant_longitude_excluded(self):
        self.assertEqual(inspect_group(group(x=(3.89, 3.90))), "excluded")

    def test_distant_latitude_excluded(self):
        self.assertEqual(inspect_group(group(y=(48.707, 49.0))), "excluded")

    def test_boundary_touch_is_conservatively_not_excluded(self):
        self.assertEqual(inspect_group(group(x=(6.129, 6.129))), "candidate")

    def test_missing_statistics_cannot_exclude_group(self):
        g = group()
        del g[1][0][3][12]
        self.assertEqual(inspect_group(g), "unknown")

    def test_inconsistent_min_max_cannot_exclude_group(self):
        self.assertEqual(inspect_group(group(x=(6.14, 6.12))), "unknown")

    def test_duplicate_bbox_column_rejected(self):
        g = group()
        g[1][-1] = g[1][0]
        with self.assertRaises(ProbeError):
            inspect_group(g)

    def test_missing_bbox_column_rejected(self):
        g = group()
        g[1][0][3][3] = [b"no_bbox"]
        with self.assertRaises(ProbeError):
            inspect_group(g)

    def test_wrong_bbox_physical_type_rejected(self):
        g = group()
        g[1][0][3][1] = 6
        with self.assertRaises(ProbeError):
            inspect_group(g)

    def test_conserves_all_rowgroups_and_provider_rows(self):
        n = EXPECTED_ROWS // EXPECTED_ROW_GROUPS_STAC
        gs = [group(x=(3.89, 3.90), size=n)
              for _ in range(EXPECTED_ROW_GROUPS_STAC)]
        gs[15] = group(x=(6.12, 6.14), size=n)
        gs[-1][3] += EXPECTED_ROWS - n * EXPECTED_ROW_GROUPS_STAC
        out = screen(gs)
        self.assertEqual(out["row_group_count_by_status"]["candidate"], 1)
        self.assertEqual(out["row_group_count_by_status"]["excluded"], 255)
        self.assertEqual(sum(out["file_rows_in_groups_by_status"].values()), EXPECTED_ROWS)
        self.assertFalse(out["insurance_model_input_approved"])

    def test_reject_incomplete_list(self):
        with self.assertRaises(ProbeError):
            screen([group()])

    def test_reject_oversize_footer(self):
        with self.assertRaises(ProbeError):
            Reader(b"0" * (MAX_FOOTER_BYTES + 1))

    def test_reject_truncated_thrift_footer(self):
        with self.assertRaises(ProbeError):
            read_metadata(b"\x15\x04\x00")

    def test_binary_field_compact_parser(self):
        r = Reader(b"\x15\x04\x18\x03abc\x00")
        self.assertEqual(r.fields(), {1: 2, 2: b"abc"})

    def test_no_automatic_original_source_access(self):
        self.assertEqual(main([]), 2)


if __name__ == "__main__":
    unittest.main()
