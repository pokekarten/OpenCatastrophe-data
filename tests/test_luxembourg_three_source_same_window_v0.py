# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only third-pair aggregate consistency and non-admission tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from research_runners import luxembourg_three_pair_same_window_v0 as mod


def fixtures():
    ae={
        "schema_version":"lu-act-eubucco-bounded-original-roof-overlap-v0",
        "research_window":{"half_width_metres":50.0,
                           "approximate_location":"central Luxembourg city / fixed research pilot"},
        "source_receipts":{"act_gpkg_sha256":mod.ACT_SHA,
                           "eubucco_parquet_sha256":mod.EBU_SHA,
                           "act_entire_source_count":238189,"eubucco_entire_source_count":186171},
        "original_local_sample":{"act_roof_features":55,"eubucco_footprint_features":11},
        "overlap_candidate_diagnostics":{
            "matched_unique_at_iou_0_60":4,"ambiguous_split_or_merge_roofs":49,
            "low_iou_unique":1,"no_substantial_overlap_roofs":1,
            "candidate_pairs_checked":120},
        "model_input_admitted":False,"per_building_data_exported":False,
        "insured_building_exposure_imported":False,
        "eubucco_upstream_independence_proven":False,
    }
    ag={
        "profile":"lu-act2023-geobase2026-bounded-geometry-v0",
        "roi_halfwidth_metres":50,
        "roi_type":"fixed 2D EPSG:3035 research window",
        "original_sha256":{"act2023":mod.ACT_SHA,"geobase2026":mod.GEO_SHA},
        "source_counts":{"act_roof_polygons":55,"geobase_building_polygons":107},
        "iou_0_60_unique_candidates":12,"ambiguous_roof_polygons":39,
        "weak_unique_roof_polygons":4,"no_substantial_overlap_roofs":0,
        "spatial_candidate_pairs_checked":322,
        "CAT_model_input_admitted":False,
        "original_id_pairs_or_geometry_exported":False,
        "independent_ground_truth_proven":False,
        "insured_exposure_or_building_stock_change_inferred":False,
    }
    ge={
        "schema_version":"lu-geobase2026-eubucco-v0.2-original-pair-v0",
        "halfwidth_metres":50,
        "region":"fixed Luxembourg-city CRS3035 100m square when default parameters used",
        "original_receipts":{"geobase2026_gpkg_sha256":mod.GEO_SHA,
                             "eubucco_v0_2_parquet_sha256":mod.EBU_SHA},
        "original_pair_features":{"geobase2026":107,"eubucco_v0_2":11},
        "geobase2026_roof_unspecified_polygon_classification":{
            "unique_candidates_iou_gte_0_60":1,
            "ambiguous_geobase_polygons":104,
            "single_candidate_iou_lt_0_60":0,
            "without_substantial_overlap":2,
            "bbox_spatial_candidate_pairs_checked":139,
        },
        "model_input_admitted":False,"raw_geometries_or_building_ids_exported":False,
        "source_pair_independent_ground_truth":False,
        "change_or_demolition_inferred":False,
    }
    return ae,ag,ge


class SameWindowTests(unittest.TestCase):
    def test_synthetic_counts_conserve_and_do_not_create_three_way_identity(self):
        a,b,c=fixtures()
        result=mod.combine(a,b,c)
        self.assertEqual(result["unique_source_polygon_counts"],{
            "act2023_roofs":55,"geobase2026_buildings":107,
            "eubucco_v0_2_footprints":11,
        })
        self.assertFalse(result["triple_source_per_building_match_generated"])
        self.assertFalse(result["manual_precision_recall_measured"])
        self.assertFalse(result["cat_model_input_admitted"])
        self.assertNotIn("building_id",json.dumps(result))
        self.assertEqual(len(result["pairwise_aggregate_candidate_diagnostics"]),3)

    def test_incomparable_250m_window_blocks_pooled_diagnostics(self):
        a,b,c=fixtures()
        a["research_window"]["half_width_metres"]=125
        with self.assertRaisesRegex(mod.TriangulationError,"window"):
            mod.combine(a,b,c)

    def test_a_different_2026_source_sample_blocks(self):
        a,b,c=fixtures()
        c["original_pair_features"]["geobase2026"]=108
        with self.assertRaisesRegex(mod.TriangulationError,"counts differ"):
            mod.combine(a,b,c)

    def test_a_different_eubucco_original_hash_blocks(self):
        a,b,c=fixtures()
        c["original_receipts"]["eubucco_v0_2_parquet_sha256"]="0"*64
        with self.assertRaisesRegex(mod.TriangulationError,"receipt mismatch"):
            mod.combine(a,b,c)

    def test_a_report_must_not_admit_model_inputs(self):
        a,b,c=fixtures()
        b["CAT_model_input_admitted"]=True
        with self.assertRaisesRegex(mod.TriangulationError,"nonadmission"):
            mod.combine(a,b,c)

    def test_arithmetic_row_conservation_is_a_hard_gate(self):
        a,b,c=fixtures()
        b["ambiguous_roof_polygons"]=40
        with self.assertRaisesRegex(mod.TriangulationError,"conserve"):
            mod.combine(a,b,c)

    def test_no_bool_or_negative_counts_accepted(self):
        a,b,c=fixtures()
        c["geobase2026_roof_unspecified_polygon_classification"]["unique_candidates_iou_gte_0_60"]=True
        with self.assertRaisesRegex(mod.TriangulationError,"count"):
            mod.combine(a,b,c)
        a,b,c=fixtures()
        a["overlap_candidate_diagnostics"]["candidate_pairs_checked"]=-1
        with self.assertRaisesRegex(mod.TriangulationError,"count"):
            mod.combine(a,b,c)

    def test_different_declared_fixed_study_region_blocks(self):
        a,b,c=fixtures()
        c["region"]="another study region"
        with self.assertRaisesRegex(mod.TriangulationError,"geographic"):
            mod.combine(a,b,c)

    def test_duplicate_json_report_keys_and_nonfinite_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/"report.json"
            target.write_text('{"schema_version":1,"schema_version":2}')
            with self.assertRaisesRegex(mod.TriangulationError,"duplicate"):
                mod._read(target)
            target.write_text('{"result":NaN}')
            with self.assertRaisesRegex(mod.TriangulationError,"NaN"):
                mod._read(target)

    def test_symlink_and_large_file_refused_before_parse(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/"report.json"
            target.write_text("{}")
            alias=Path(t)/"alias.json"
            alias.symlink_to(target)
            with self.assertRaisesRegex(mod.TriangulationError,"small regular"):
                mod._read(alias)
            target.write_bytes(b"X"*(mod.MAX_REPORT_BYTES+1))
            with self.assertRaisesRegex(mod.TriangulationError,"small regular"):
                mod._read(target)


if __name__=="__main__":
    unittest.main()
