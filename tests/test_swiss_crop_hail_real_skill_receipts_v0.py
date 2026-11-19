# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline regression of 48 genuine source-run aggregate skill records.

No source files needed, no original field coordinates, no model admission.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

from research_runners.swiss_crop_hail_verification_support_v0 import contingency_metrics

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research/observations/swiss_crop_hail_original_1_2_4_8km_binary_skill_v0.jsonc"


class SwissHailRealSkillReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = RECEIPT.read_text(encoding="utf-8").splitlines()
        if len(raw) < 3 or not raw[0].startswith("# SPDX-FileCopyrightText:") or not raw[1].startswith("# SPDX-License-Identifier:"):
            raise AssertionError("research receipt must retain SPDX identity header")
        cls.data = json.loads("\n".join(raw[2:]))

    def test_exact_original_replay_sources_and_non_admission(self):
        data = self.data
        self.assertEqual(data["schema_version"], "OC_SWISS_CROP_HAIL_ORIGINAL_1_2_4_8KM_BINARY_SKILL_V0")
        self.assertEqual(data["source_replay_records"], 48)
        self.assertEqual(data["threshold_metrics_records"], 192)
        for key in ("reference_study_numeric_parity_established",
                    "cross_validated_or_heldout",
                    "annual_frequency_model",
                    "insured_loss_severity_model",
                    "gross_net_oep_aep_ready",
                    "source_bytes_committed", "source_rights_admitted"):
            self.assertIs(data[key], False, key)
        self.assertIn("/actions/runs/42250217277", data["evidence_1km_workflow"])
        self.assertIn("/actions/runs/42251687616", data["evidence_coarse_workflow"])

    def test_every_crop_grid_hazard_combination_exactly_once(self):
        rows = self.data["research_records"]
        self.assertEqual(len(rows), 48)
        original = {(r["crop"], r["grid_resolution_km"], r["hazard"]) for r in rows}
        self.assertEqual(len(original), 48)
        wanted = {(crop, km, var) for crop in self.data["crops"]
                  for km in (1, 2, 4, 8) for var in ("MESHS", "POH")}
        self.assertEqual(original, wanted)

    def test_every_original_contingency_and_reported_skill_score_recomputes(self):
        counts = 0
        for row in self.data["research_records"]:
            self.assertIn(row["selected_event_count"], (10, 11, 12))
            self.assertGreater(row["exposed_grid_centroids_per_event"], 0)
            self.assertEqual(row["evaluated_binary_grid_event_cells"],
                             row["selected_event_count"]*row["exposed_grid_centroids_per_event"])
            expected_thresholds = {20, 30, 40, 60} if row["hazard"] == "MESHS" else {40, 60, 80, 90}
            self.assertEqual({int(s) for s in row["scores"]}, expected_thresholds)
            for v in row["scores"].values():
                result=contingency_metrics(v["hits"],v["false_alarms"],v["misses"],v["correct_negatives"])
                self.assertEqual(sum(v[k] for k in ("hits","false_alarms","misses","correct_negatives")),
                                 row["evaluated_binary_grid_event_cells"])
                for k in ("pod","far","frequency_bias","critical_success_index","heidke_skill_score"):
                    self.assertTrue(v[k] == result[k] or
                                    (v[k] is not None and result[k] is not None and
                                     math.isclose(v[k],result[k],abs_tol=1e-7)), (row,k))
                counts += 1
        self.assertEqual(counts,192)

    def test_source_supported_observed_outside_geometry_not_silently_lost(self):
        rows = self.data["research_records"]
        missing = {(x["crop"],x["grid_resolution_km"],x["hazard"]):
                   x["excluded_positive_gridded_event_cells"]
                   for x in rows if x["excluded_positive_gridded_event_cells"]}
        for hazard in ("MESHS","POH"):
            self.assertEqual(missing["maize",2,hazard],247)
            self.assertEqual(missing["rapeseed",2,hazard],133)
            self.assertEqual(missing["wheat",2,hazard],170)
        self.assertEqual(len(missing),6)
        self.assertEqual(self.data["max_coarse_original_crop_center_offset_m"],0.001)

    def test_historical_field_and_grapevine_scale_trend_at_same_30mm_threshold(self):
        def score(crop,km):
            row=next(x for x in self.data["research_records"]
                     if x["crop"]==crop and x["grid_resolution_km"]==km and x["hazard"]=="MESHS")
            return row["scores"]["30"]["heidke_skill_score"]
        self.assertTrue(score("field_crops",1)<score("field_crops",2)<score("field_crops",4)<score("field_crops",8))
        self.assertTrue(score("grapevine",1)>score("grapevine",2)>score("grapevine",4)>score("grapevine",8))


if __name__ == "__main__":
    unittest.main()
