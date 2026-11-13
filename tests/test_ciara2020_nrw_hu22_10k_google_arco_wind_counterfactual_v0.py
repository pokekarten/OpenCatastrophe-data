# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Public HU2022 10k site cells × actual-source wind: only hypothetical hazard."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_nrw_hu22_10k_google_arco_wind_counterfactual_v0 as m
import ciara2020_google_arco_real_96h_nrw_area_v0 as g
import ciara2020_nrw_10k_era5_area_request_v0 as a


def uniform_grid(value: float) -> list[list[float]]:
    return [[value for _ in g.LONGITUDE] for _ in g.LATITUDE]


class CiaraHU22Original2020WindCounterfactualTests(unittest.TestCase):
    def test_real_pinned_93_cell_source_count_and_fictional_tiv(self):
        cells = m.load_source_cell_aggregates()
        self.assertEqual(len(cells), 93)
        self.assertEqual(sum(x[0] for x in cells.values()), 10000)
        self.assertEqual(sum(x[1] for x in cells.values()), 4826029500)
        self.assertEqual(hashlib.sha256(m.SOURCE_CELL_CSV.read_bytes()).hexdigest(),
                         m.SOURCE_CELL_CSV_SHA256)
        self.assertEqual(m.SOURCE_COUNT_SIGNATURE_SHA256,
                         "de10099a9b79febb1a254bc765dc477a47589cb1f49ba75415bfe6b9723c2ebd")
        self.assertEqual(cells[(204, 28)], (485, 230924250))
        self.assertNotIn("SYN-NRW", str(cells))

    def test_real_source_cell_csv_mutated_value_header_or_symlink_block(self):
        with tempfile.TemporaryDirectory() as td:
            alt = Path(td) / "93.csv"
            for text in (
                m.SOURCE_CELL_CSV.read_text().replace("201,26,4,1539000",
                                                       "201,26,4,1539001"),
                m.SOURCE_CELL_CSV.read_text().replace("latitude_quarter_index",
                                                       "grid_latitude"),
                "",
            ):
                alt.write_text(text)
                with self.assertRaises(m.CiaraCounterfactualBlocked):
                    m.load_source_cell_aggregates(alt)
            alt.unlink()
            alt.symlink_to(m.SOURCE_CELL_CSV)
            with self.assertRaises(m.CiaraCounterfactualBlocked):
                m.load_source_cell_aggregates(alt)

    def test_pure_spatial_overlay_real_2022_population_conservation_and_thresholds(self):
        cells = m.load_source_cell_aggregates()
        grid = uniform_grid(31.0)
        low_key, high_key = (201, 26), (206, 28)
        grid[210 - low_key[0]][low_key[1] - 23] = 28.0
        grid[210 - high_key[0]][high_key[1] - 23] = 40.0
        result = m.summarize_exposure_by_public_source_grid(cells, grid)
        self.assertEqual(result["public_2022_building_candidate_count"], 10000)
        self.assertEqual(result["fictional_2025_like_building_tiv_eur"], 4826029500)
        self.assertEqual(result["source_occupied_original_2022_building_grid_cells"], 93)
        expected = {
            "25": (10000, 4826029500, 93),
            "30": (9996, 4826029500 - 1539000, 92),
            "35": (474, 238187250, 1),
            "40": (474, 238187250, 1),
        }
        for threshold, (count, tiv, nodes) in expected.items():
            with self.subTest(threshold=threshold):
                observed = result["peak_wind_hazard_threshold_mps"][threshold]
                self.assertEqual(observed["public_2022_building_candidate_count"], count)
                self.assertEqual(observed["fictional_2025_like_building_tiv_eur"], tiv)
                self.assertEqual(observed["distinct_occupied_0p25deg_grid_cells"], nodes)
        self.assertLess(result["candidate_weighted_2020_ciara_96h_peak_wind_mps"], 32)
        self.assertGreater(result["candidate_weighted_2020_ciara_96h_peak_wind_mps"], 31)

    def test_wrong_weather_dimensions_outliers_missing_source_cells_rejected(self):
        cells = m.load_source_cell_aggregates()
        for bad in ([], [[31.0] * 16 for _ in range(9)],
                    [[31.0] * 15 for _ in range(10)]):
            with self.subTest(shape=[len(r) for r in bad]):
                with self.assertRaises(m.CiaraCounterfactualBlocked):
                    m.summarize_exposure_by_public_source_grid(cells, bad)
        for badval in (float("nan"), float("inf"), -1, 150.01, True, "29"):
            with self.subTest(value=badval):
                grid = uniform_grid(30.0)
                grid[0][0] = badval
                with self.assertRaises(m.CiaraCounterfactualBlocked):
                    m.summarize_exposure_by_public_source_grid(cells, grid)
        removed = dict(cells)
        del removed[(204, 28)]
        with self.assertRaises(m.CiaraCounterfactualBlocked):
            m.summarize_exposure_by_public_source_grid(removed, uniform_grid(30.0))
        wrong = dict(cells)
        wrong[(204, 28)] = (486, cells[(204, 28)][1])
        with self.assertRaises(m.CiaraCounterfactualBlocked):
            m.summarize_exposure_by_public_source_grid(wrong, uniform_grid(30.0))

    def test_fake_hu22_archived_source_is_never_reidentified_as_verified(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "not-the-real-10k.zip"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("location.csv", b"LocNumber\nFAKE\n")
            with self.assertRaises(a.CiaraAreaBlocked):
                m.validate_original_zip_against_source_cells(p)

    def test_synthetic_mock_weather_join_has_no_loss_model_promotions(self):
        source = {
            "normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256":
                m.ORIGINAL_ERA5_MATRIX_SHA256,
            "actual_hourly_ERA5_original_grid_timestamps_verified": 96,
            "original_source_0p25_degree_nodes": 160,
            "previous_original_metadata_SHA256s_match": True,
            "real_RV_insurer_claims_or_policy_terms_obtained": False,
            "German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted": False,
            "public_original_source": "gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3",
            "_internal_public_10x16_event_peak_gust_mps": uniform_grid(32.0),
        }
        # A forged reported original matrix SHA PLUS an entirely synthetic
        # 32m/s 160-cell peak grid must NOT get model-source admission:
        # compare final weighted aggregate to independently accepted live receipt.
        with patch.object(g, "original_96h_grid", return_value=source) as mock:
            with self.assertRaisesRegex(m.CiaraCounterfactualBlocked, "first original live source"):
                m.run_live_counterfactual()
        mock.assert_called_once_with(include_public_grid_peaks=True)
        pure = m.summarize_exposure_by_public_source_grid(
            m.load_source_cell_aggregates(), uniform_grid(32.0)
        )
        self.assertEqual(pure["peak_wind_hazard_threshold_mps"]["30"]["public_2022_building_candidate_count"],10000)
        self.assertEqual(pure["peak_wind_hazard_threshold_mps"]["35"]["public_2022_building_candidate_count"],0)
        self.assertNotIn("SYN-NRW", json.dumps(pure))

    def test_mismatching_live_source_sha_or_claim_admission_blocks(self):
        baseline = {
            "normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256":
                m.ORIGINAL_ERA5_MATRIX_SHA256,
            "actual_hourly_ERA5_original_grid_timestamps_verified": 96,
            "original_source_0p25_degree_nodes": 160,
            "previous_original_metadata_SHA256s_match": True,
            "real_RV_insurer_claims_or_policy_terms_obtained": False,
            "German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted": False,
            "public_original_source": "gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3",
            "_internal_public_10x16_event_peak_gust_mps": uniform_grid(32.0),
        }
        edits = (
            ("normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256", "0"*64),
            ("actual_hourly_ERA5_original_grid_timestamps_verified", 95),
            ("previous_original_metadata_SHA256s_match", False),
            ("real_RV_insurer_claims_or_policy_terms_obtained", True),
            ("German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted", True),
        )
        for field, value in edits:
            with self.subTest(field=field):
                altered = deepcopy(baseline)
                altered[field] = value
                with patch.object(g, "original_96h_grid", return_value=altered):
                    with self.assertRaises(m.CiaraCounterfactualBlocked):
                        m.run_live_counterfactual()

    def test_real_public_2020_google_gust_2022_source_join_receipt_no_go(self):
        with m.ACCEPTED_SOURCE_JOIN_TOML.open("rb") as fd:
            evidence = tomllib.load(fd)
        self.assertEqual(evidence["first_successful_original_live_github_run"], 43489088388)
        self.assertEqual(evidence["source_original_2022_HU_derived_10k_archive_sha256"], a.SOURCE_ARTIFACT_SHA256)
        self.assertEqual(evidence["source_original_2022_HU_10k_93cell_csv_sha256"], m.SOURCE_CELL_CSV_SHA256)
        self.assertEqual(evidence["2020_google_arco_original_96h_160cell_decoded_sha256"], m.ORIGINAL_ERA5_MATRIX_SHA256)
        self.assertEqual(evidence["public_2022_building_candidate_count"], 10000)
        self.assertEqual(evidence["source_2022_occupied_0p25deg_grid_cells"], 93)
        self.assertEqual(evidence["fictional_building_tiv_eur"], 4826029500)
        self.assertEqual(evidence["historical_2020_google_era5_hourly_gust_frames"], 96)
        self.assertAlmostEqual(evidence["candidate_weighted_2020_ciara_96h_peak_wind_mps"], 31.673449949645995)
        self.assertAlmostEqual(evidence["fictional_tiv_weighted_2020_ciara_96h_peak_wind_mps"], 31.67299538469392)
        self.assertEqual(
            [evidence["threshold_mps"][str(v)]["public_2022_building_candidate_count"]
             for v in (25, 30, 35, 40)], [10000, 10000, 0, 0]
        )
        for key in ("public_2022_building_occupancy_as_of_2020_verified",
                    "real_RV_2020_insured_site_universe_observed",
                    "2020_insurer_coverage_or_claims_observed",
                    "German_wind_vulnerability_native_GUL_IL_RI_OEP_AEP_admitted",
                    "annual_stochastic_EP_or_capital_model_admitted"):
            self.assertFalse(evidence[key])

    def test_cli_dry_run_requires_no_public_cloud_or_source_archive(self):
        with patch.object(sys, "argv", ["joined", "--dry-run"]), \
             patch.object(g, "original_96h_grid", side_effect=AssertionError("DO NOT DOWNLOAD")):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(m.main(), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["public_building_candidates"], 10000)
        self.assertEqual(result["source_occupied_nodes"], 93)
        self.assertFalse(result["2020_public_google_live_weather_join_executed"])
        self.assertFalse(result["real_insured_claims_or_loss_model"])


if __name__ == "__main__":
    unittest.main()
