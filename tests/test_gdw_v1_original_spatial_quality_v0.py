# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""GDW original spatial audit synthetic tests; no source shapefile/record export."""
from __future__ import annotations

import hashlib
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from research_runners.gdw_v1_original_shapefile_evidence_v0 import (
    GDW_V1_ORIGINAL_SHAPEFILE_EVIDENCE_V0 as EVIDENCE,
)
from research_runners.gdw_v1_original_spatial_source_receipt_v0 import (
    GDW_V1_ORIGINAL_SPATIAL_RECEIPT_V0 as SPATIAL_RECEIPT,
)
from research_runners import gdw_v1_original_spatial_quality_v0 as subject
from research_runners import gdw_v1_shapefile_archive_preflight_v0 as pre
from tests.test_gdw_v1_shapefile_archive_preflight_v0 import (
    COUNTS, build_zip, files,
)


def fixture(*, point=(13.05, 52.05), polygon=None, corrupt=None):
    if corrupt:
        return build_zip(**{corrupt: True})
    f = files()
    key = next(x for x in f if x.lower().endswith("gdw_barriers_v1_0.shp"))
    shp = bytearray(f[key])
    struct.pack_into("<dd", shp, 100 + 8 + 4, *point)
    f[key] = bytes(shp)
    if polygon is not None:
        name = next(x for x in f if x.lower().endswith("gdw_reservoirs_v1_0.shp"))
        shp = bytearray(f[name])
        # SHP header 100 + record header 8 + type 4 + bbox 32
        # + numparts/points 8 + 1 ring-index 4 = coordinate offset 156
        for i, (x, y) in enumerate(polygon):
            struct.pack_into("<dd", shp, 156 + i * 16, x, y)
        f[name] = bytes(shp)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for k, v in f.items():
            z.writestr(k, v)
    return out.getvalue()


HAS_SPATIAL_READER = (
    importlib.util.find_spec("shapefile") is not None
    and importlib.util.find_spec("shapely") is not None
)


@unittest.skipUnless(HAS_SPATIAL_READER, "optional pinned pyshp/Shapely source audit wheels")
class GDWOriginalSpatialAuditTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.path = Path(d.name) / "original_test_only.zip"

    def inspect(self, payload, **options):
        self.path.write_bytes(payload)
        return subject.audit(self.path,
                             expected_sha256=hashlib.sha256(payload).hexdigest(),
                             original_bytes=len(payload),
                             publisher_md5=hashlib.md5(payload, usedforsecurity=False).hexdigest(),
                             expected_counts=COUNTS, **options)

    def test_inside_polygon_and_id_pairing(self):
        r = self.inspect(fixture())
        self.assertEqual(r["barrier_points"], 1)
        self.assertEqual(r["reservoir_polygons"], 1)
        self.assertEqual(r["paired_gdw_ids"], 1)
        self.assertEqual(r["paired_barrier_within_polygon_interior"], 1)
        self.assertEqual(r["paired_barrier_outside_valid_polygon"], 0)
        self.assertTrue(r["all_assessable_id_pairs_geometrically_covered"])
        self.assertEqual(r["invalid_geometry_reason_family_counts"], {})
        self.assertTrue(r["source_original_structure_verified"])
        self.assertTrue(r["original_archive_sha256_matched_frozen"])
        self.assertFalse(r["CAT_model_source_admitted"])
        self.assertFalse(r["source_coordinates_ids_attributes_exported"])
        self.assertNotIn("13.05", str(r))

    def test_outside_polygon_diagnosed_not_approved(self):
        r = self.inspect(fixture(point=(13.4, 52.2)))
        self.assertEqual(r["paired_barrier_outside_valid_polygon"], 1)
        self.assertFalse(r["all_assessable_id_pairs_geometrically_covered"])
        self.assertFalse(r["CAT_model_source_admitted"])

    def test_boundary_included_separate_from_interior(self):
        r = self.inspect(fixture(point=(13.0, 52.05)))
        self.assertEqual(r["paired_barrier_on_polygon_boundary"], 1)
        self.assertEqual(r["paired_barrier_within_polygon_interior"], 0)

    def test_invalid_topology_is_counted_without_auto_repair(self):
        bowtie = ((13.0, 52.0), (13.1, 52.1), (13.0, 52.1),
                  (13.1, 52.0), (13.0, 52.0))
        r = self.inspect(fixture(polygon=bowtie))
        self.assertEqual(r["invalid_reservoir_polygons"] +
                         r["unparseable_or_error_reservoir_polygons"], 1)
        self.assertEqual(r["unassessable_pair_invalid_or_unparseable_polygon"], 1)
        self.assertFalse(r["all_original_geometries_topologically_valid"])
        self.assertEqual(sum(r["invalid_geometry_reason_family_counts"].values()), 1)
        self.assertNotIn("[", str(r["invalid_geometry_reason_family_counts"]))
        self.assertFalse(r["polygon_repairs_or_snapping_performed"])

    def test_bad_archive_preflight_blocks_before_geom(self):
        for case in ("open_ring", "bad_coordinate", "wrong_gdw_id",
                     "invalid_gdw_id", "bad_offset", "null_geom"):
            with self.subTest(case=case), self.assertRaises(pre.GDWArchiveError):
                self.inspect(fixture(corrupt=case))

class GDWFrozenOriginalEvidenceTests(unittest.TestCase):
    def test_reason_classifier_strips_original_geos_coordinate_details(self):
        self.assertEqual(subject._validity_reason_family("Self-intersection[13.0 52.1]"),
                         "self_intersection")
        self.assertEqual(subject._validity_reason_family("Ring Self-intersection[secret]"),
                         "ring_self_intersection")
        self.assertEqual(subject._validity_reason_family("Something with [record coordinates]"),
                         "other_invalid_geos_reason")

    def test_real_original_spatial_receipt_is_bounded_and_nonadmitted(self):
        e = SPATIAL_RECEIPT
        self.assertEqual(e["original_file_sha256"], EVIDENCE["independently_computed_from_original_sha256"])
        self.assertEqual(e["reservoir_polygons"], 35295)
        self.assertEqual(e["valid_reservoir_polygons"], 35074)
        self.assertEqual(e["invalid_reservoir_polygons"], 221)
        self.assertEqual(e["unparseable_reservoir_polygons"], 0)
        self.assertEqual(e["valid_polygon_matched_point_strict_interior"], 35074)
        self.assertEqual(e["valid_polygon_matched_point_outside"], 0)
        self.assertEqual(e["unassessable_matched_pairs_due_to_invalid_polygon"], 221)
        self.assertFalse(e["model_input_admitted"])
        self.assertFalse(e["source_geometries_repaired"])
        self.assertFalse(e["source_ids_or_coordinates_exported"])

    def test_frozen_original_receipt_no_model_promotion(self):
        self.assertEqual(EVIDENCE["original_file_bytes"], 69_745_749)
        self.assertEqual(EVIDENCE["barrier_point_records"], 41_145)
        self.assertEqual(EVIDENCE["reservoir_polygon_records"], 35_295)
        self.assertEqual(EVIDENCE["point_only_barriers"], 5_850)
        self.assertEqual(EVIDENCE["independently_computed_from_original_sha256"],
                         "2fe0b367ed3fcfb299160cd9652b16a8a19338951026ee2ac91edfebf1f3b7ae")
        for key in ("model_source_admitted", "original_archive_bytes_published",
                    "per_id_point_in_polygon_verified", "geos_polygon_topology_validated"):
            self.assertFalse(EVIDENCE[key])



if __name__ == "__main__":
    unittest.main()
