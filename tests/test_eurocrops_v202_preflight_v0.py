# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic EuroCrops preflight regression tests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from shapely import wkb
from shapely.geometry import Polygon
from research_runners.eurocrops_v202_preflight_v0 import (
    Blocked, asset_identity, audit_rows, geo_metadata, inspect_local,
    sampled_row_positions, read_spread_sample,
)


class FakeBatch:
    def __init__(self, rows):
        self.rows = rows
        self.num_rows = len(rows)

    def slice(self, start, size):
        return FakeBatch(self.rows[start : start + size])

    def to_pylist(self):
        return list(self.rows)


class FakeRowGroup:
    def __init__(self, n):
        self.num_rows = n


class FakeParquet:
    def __init__(self, groups):
        self.groups = groups
        self.metadata = self
        self.num_rows = sum(map(len, groups))
        self.num_row_groups = len(groups)
        self.groups_requested = []
        self.max_batch_seen = 0

    def row_group(self, i):
        return FakeRowGroup(len(self.groups[i]))

    def iter_batches(self, *, row_groups, batch_size, columns):
        assert len(row_groups) == 1
        assert batch_size <= 512
        assert columns in (["cropfield", "original_code", "area_ha", "geom"],
                           ["cropfield", "original_code", "area_ha", "geometry"])
        i = row_groups[0]
        self.groups_requested.append(i)
        for start in range(0, len(self.groups[i]), batch_size):
            batch = self.groups[i][start : start + batch_size]
            self.max_batch_seen = max(self.max_batch_seen, len(batch))
            yield FakeBatch(batch)


class EuroCropsPreflight(unittest.TestCase):
    def test_header_footer_and_region(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "de4_2023.parquet"
            path.write_bytes(b"PAR1" + b"A" * 10 + b"PAR1")
            region, year, digest = asset_identity(path)
            self.assertEqual((region, year), ("de4", 2023))
            self.assertEqual(len(digest), 64)
            with self.assertRaises(Blocked):
                asset_identity(Path(d) / "de4_stack.parquet")
            path.write_bytes(b"JUNK" + b"A" * 10 + b"PAR1")
            with self.assertRaises(Blocked):
                asset_identity(path)

    def test_metadata_is_fail_closed(self):
        # The REAL corrected DE4 2023 JRC footer uses "geometry", not
        # "geom", with WKB encoding, EPSG:3035 and six original columns.
        names = ["cropfield", "original_code", "original_name",
                 "off_area", "geometry", "area_ha"]
        geo = {"primary_column": "geometry", "columns": {
            "geometry": {"encoding": "WKB", "crs": {
                "id": {"authority": "EPSG", "code": 3035}}}}}
        good = {b"geo": json.dumps(geo).encode()}
        report = geo_metadata(good, names)
        self.assertEqual(report["crs"], "EPSG:3035")
        self.assertEqual(report["primary_geometry_column"], "geometry")
        self.assertEqual(report["geometry_encoding"], "WKB")
        with self.assertRaises(Blocked):
            geo_metadata(None, names)
        with self.assertRaises(Blocked):
            geo_metadata(good, names[:-2])
        bad_crs = {"primary_column": "geometry", "columns": {
            "geometry": {"encoding": "WKB", "crs": "EPSG:4326"}}}
        with self.assertRaises(Blocked):
            geo_metadata({b"geo": json.dumps(bad_crs).encode()}, names)
        bad_encoding = {"primary_column": "geometry", "columns": {
            "geometry": {"encoding": "WKT", "crs": "EPSG:3035"}}}
        with self.assertRaises(Blocked):
            geo_metadata({b"geo": json.dumps(bad_encoding).encode()}, names)
        # A separate original can explicitly use "geom", provided the
        # GeoParquet primary-column metadata really says so.
        alternative = {"primary_column": "geom", "columns": {
            "geom": {"encoding": "WKB", "crs": "EPSG:3035"}}}
        self.assertEqual(
            geo_metadata({b"geo": json.dumps(alternative).encode()},
                         ["cropfield", "original_code", "area_ha", "geom"])[
                             "primary_geometry_column"], "geom")

    def test_partial_or_unpinned_taxonomy_is_blocked(self):
        with self.assertRaisesRegex(Blocked, "both original codebooks"):
            inspect_local(
                Path("/nonexistent/de4_2023.parquet"), "0" * 64,
                mapping=Path("/nonexistent/eurocrops.csv"),
            )
        with self.assertRaisesRegex(Blocked, "both original codebooks"):
            inspect_local(
                Path("/nonexistent/de4_2023.parquet"), "0" * 64,
                mapping=Path("/nonexistent/eurocrops.csv"),
                mapping_git_blob_sha1="1" * 40,
                hierarchy=Path("/nonexistent/hcat4.csv"),
            )

    def test_spread_sample_is_reproducible_bounded_and_uniform(self):
        digest = "a" * 64
        positions = sampled_row_positions(1200, 120, digest)
        self.assertEqual(positions, sampled_row_positions(1200, 120, digest))
        self.assertEqual(len(positions), 120)
        self.assertEqual(len(set(positions)), 120)
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(any(p >= 800 for p in positions))
        self.assertNotEqual(positions, sampled_row_positions(1200, 120, "b" * 64))
        self.assertEqual(sampled_row_positions(4, 512, digest), [0, 1, 2, 3])
        for bad in (-1, 0, True):
            with self.assertRaises(Blocked):
                sampled_row_positions(bad, 10, digest)
        with self.assertRaises(Blocked):
            sampled_row_positions(100, 5001, digest)
        with self.assertRaises(Blocked):
            sampled_row_positions(100, 10, "invalid")

    def test_parquet_batches_cover_spread_indices_not_just_first_rows(self):
        groups = [
            [{"cropfield": x} for x in range(0, 20)],
            [{"cropfield": x} for x in range(20, 40)],
            [{"cropfield": x} for x in range(40, 60)],
        ]
        parquet = FakeParquet(groups)
        positions = sampled_row_positions(60, 30, "f" * 64)
        rows, sampled_groups = read_spread_sample(parquet, positions)
        self.assertEqual([row["cropfield"] for row in rows], positions)
        self.assertEqual(sampled_groups, 3)
        self.assertEqual(parquet.groups_requested, [0, 1, 2])
        self.assertLessEqual(parquet.max_batch_seen, 512)

    def test_footer_row_count_disagreement_blocks_even_when_samples_read(self):
        parquet = FakeParquet([
            [{"cropfield": n} for n in range(15)],
            [{"cropfield": n} for n in range(15, 30)],
        ])
        parquet.num_rows += 1
        with self.assertRaisesRegex(Blocked, "totals"):
            read_spread_sample(parquet, [0, 10, 20])

    def test_out_of_bounds_sample_offsets_fail_closed(self):
        parquet = FakeParquet([[{"cropfield": n} for n in range(8)]])
        with self.assertRaisesRegex(Blocked, "inconsistent"):
            read_spread_sample(parquet, [2, 99])
        with self.assertRaises(Blocked):
            read_spread_sample(parquet, [1, 1])

    def test_real_jrc_geometry_column_works_for_sample_and_geometry_qa(self):
        square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        parcels = [{"cropfield": n, "original_code": "429",
                    "area_ha": 1.0, "geometry": wkb.dumps(square)}
                   for n in range(16)]
        parquet = FakeParquet([parcels[:8], parcels[8:]])
        positions = sampled_row_positions(16, 8, "c" * 64)
        sampled, groups = read_spread_sample(parquet, positions, "geometry")
        self.assertEqual(groups, 2)
        self.assertEqual([row["cropfield"] for row in sampled], positions)
        self.assertEqual(audit_rows(sampled, "geometry")["invalid_or_empty_geometry"], 0)
        self.assertEqual(audit_rows(sampled, "geometry")["sampled"], 8)
        with self.assertRaises(Blocked):
            read_spread_sample(parquet, positions, "not-a-source-column")

    def test_polygon_errors(self):
        square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        rows = [
            {"cropfield": 1, "original_code": "wheat", "area_ha": 1.0, "geom": wkb.dumps(square)},
            {"cropfield": 1, "original_code": None, "area_ha": 2.0, "geom": wkb.dumps(square)},
            {"cropfield": 3, "original_code": "barley", "area_ha": float("nan"), "geom": b"bad"},
        ]
        report = audit_rows(rows)
        self.assertEqual(report["sampled"], 3)
        for key in ("duplicate_cropfield_in_sample", "missing_crop_code",
                    "invalid_area_ha", "area_disagreement_over_5pct",
                    "invalid_or_empty_geometry"):
            self.assertEqual(report[key], 1)


if __name__ == "__main__":
    unittest.main()
