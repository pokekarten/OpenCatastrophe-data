# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, offline, independent arithmetic tests for GPL-isolated source bridge."""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
sys.path.insert(0, str(ROOT / "tests"))
import rva_nrw_daria_climada61_source_challenger_v0 as bridge
import rva_nrw_xws_daria_invented_damage_v0 as original
from test_rva_nrw_xws_daria_invented_damage_v0 import fake_hazard, SYNTHETIC_PINS


def invented_public_model():
    # All numbers below are invented self-contained unit-test data. No
    # third-party GPL source or published curve tables enter this repository.
    prefix = '"""Dummy source: GNU General Public License. Synthetic test only."""\n'
    storm = prefix + """
class ImpfStormEurope:
    @classmethod
    def from_schwierz(cls):
        impf.intensity = np.array([0, 20, 40, 100])
        impf.paa = np.array([0, .25, .75, 1])
        impf.mdd = np.array([0, .1, .3, .5])
    @classmethod
    def from_welker(cls):
        scaling_factor = {"paa_scale": 1.2, "mdd_scale": 1.5}
"""
    calibration = prefix + """
def change_impf():
    # fake test for the actual pinned interpolation method
    return 'synthetic source, real version SHA enforced at runtime'
"""
    base = prefix + """
def calc_mdr():
    # fake test for published separate PAA/MDD interpolation semantics
    return 'synthetic source, no original code'
"""
    return {
        "storm_europe.py": storm.encode("utf-8"),
        "calibration_opt.py": calibration.encode("utf-8"),
        "base.py": base.encode("utf-8"),
    }


class SourceCLIMADAEuropeanChallengerTests(unittest.TestCase):
    def setUp(self):
        self.model = invented_public_model()
        self.model_pins = {name: bridge.git_blob_sha1(raw)
                           for name, raw in self.model.items()}

    def small(self, original_hazard: Path, *, mutate=None):
        fake_hazard(original_hazard, mutate_manifest=mutate)
        return bridge.run_challenger(
            original_hazard, self.model, expected_sites=3,
            expected_counties=3, expected_tiv_eur=600000,
            original_source_hashes=SYNTHETIC_PINS,
            expected_model_pins=self.model_pins,
        )

    def test_synthetic_method_components_and_welker_scaling_are_distinct(self):
        curves = bridge.parse_pinned_public_curves(
            self.model, expected_pins=self.model_pins
        )
        self.assertEqual(set(curves), set(bridge.MODEL_NAMES))
        original_curve = curves[bridge.MODEL_NAMES[0]]
        scaled_curve = curves[bridge.MODEL_NAMES[1]]
        self.assertEqual(original_curve["wind"], tuple(Decimal(x) for x in [0, 20, 40, 100]))
        self.assertEqual(len(scaled_curve["wind"]), 51)
        self.assertEqual(bridge._interp(original_curve["wind"], original_curve["paa"], Decimal(30)),
                         Decimal(".50"))
        self.assertEqual(bridge._interp(original_curve["wind"], original_curve["mdd"], Decimal(30)),
                         Decimal(".20"))
        self.assertEqual(bridge._interp(scaled_curve["wind"], scaled_curve["paa"], Decimal(30)),
                         Decimal(".60"))
        self.assertEqual(bridge._interp(scaled_curve["wind"], scaled_curve["mdd"], Decimal(30)),
                         Decimal(".30"))

    def test_hand_derived_three_sites_six_comparisons_and_not_calibrated(self):
        with TemporaryDirectory() as d:
            output = self.small(Path(d) / "fake.zip")
            self.assertEqual(len(output["site_rows"]), 18)
            self.assertEqual(len(output["county_rows"]), 18)
            self.assertEqual(len(output["receipt"]["scenario_comparisons"]), 6)
            values = {
                (item["method"], item["source_gust_view"]):
                item["conditional_direct_value_eur_cents"]
                for item in output["receipt"]["scenario_comparisons"]
            }
            # Fully independent toy physical wind / toy insurer-value arithmetic.
            self.assertEqual(values[("schwierz_2010_CLIMADA61", "lower95")], 3_562_500)
            self.assertEqual(values[("schwierz_2010_CLIMADA61", "mean")], 5_953_125)
            self.assertEqual(values[("schwierz_2010_CLIMADA61", "upper95")], 9_000_000)
            self.assertEqual(values[("welker_2021_CLIMADA61", "lower95")], 6_412_500)
            self.assertEqual(values[("welker_2021_CLIMADA61", "mean")], 10_715_625)
            self.assertEqual(values[("welker_2021_CLIMADA61", "upper95")], 16_200_000)
            self.assertTrue(output["receipt"]["no_annual_event_rates_OEP_AEP"])
            self.assertTrue(output["receipt"]["no_German_building_vulnerability_calibration"])
            self.assertTrue(output["receipt"]["independent_AST_interpolator_not_native_CLIMADA_execution"])

    def test_explicit_original_gpl_source_pins_and_missing_semantics_fail(self):
        with self.assertRaisesRegex(bridge.CLIMADAChallengerBlocked, "hash"):
            bridge.parse_pinned_public_curves(
                {**self.model, "storm_europe.py": self.model["storm_europe.py"] + b"bad"},
                expected_pins=self.model_pins,
            )
        with self.assertRaisesRegex(bridge.CLIMADAChallengerBlocked, "required"):
            bridge.parse_pinned_public_curves(
                {"storm_europe.py": self.model["storm_europe.py"]},
                expected_pins=self.model_pins,
            )
        damaged = {**self.model, "calibration_opt.py": b"invalid"}
        with self.assertRaisesRegex(bridge.CLIMADAChallengerBlocked, "hash"):
            bridge.parse_pinned_public_curves(damaged, expected_pins=self.model_pins)

    def test_source_hazard_insurer_promotion_is_denied(self):
        with TemporaryDirectory() as d:
            for key in (
                "actual_1990_RV_insured_geographies_or_2025_RV_coverage_known",
                "XWS_extreme_storm_selection_is_valid_annual_frequency_model",
                "German_wind_vulnerability_by_material_roof_construction_validated",
            ):
                p = Path(d) / f"{key}.zip"
                with self.subTest(key=key):
                    with self.assertRaises((ValueError, bridge.CLIMADAChallengerBlocked)):
                        self.small(p, mutate=lambda m, k=key: m.__setitem__(k, True))

    def test_source_checksum_change_and_reversed_gust_are_denied(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            p = root / "bad-src.zip"
            fake_hazard(p, mutate_sites=lambda rows:
                        rows[0].__setitem__("Daria1990MeanGustMps", "19"),
                        preserve_bad_site_hash=True)
            with self.assertRaisesRegex(ValueError, "content SHA"):
                bridge.run_challenger(
                    p, self.model, expected_sites=3, expected_counties=3,
                    expected_tiv_eur=600000,
                    original_source_hashes=SYNTHETIC_PINS,
                    expected_model_pins=self.model_pins,
                )
            q = root / "wrong-source.zip"
            fake_hazard(q, mutate_manifest=lambda m: m[
                "provider_original_four_XWS_CSV_source_receipt"][
                    "original_files"]["grid"].__setitem__("full_sha256", "0"*64))
            with self.assertRaisesRegex(ValueError, "provider CSV SHA"):
                bridge.run_challenger(
                    q, self.model, expected_sites=3, expected_counties=3,
                    expected_tiv_eur=600000,
                    original_source_hashes=SYNTHETIC_PINS,
                    expected_model_pins=self.model_pins,
                )

    def test_bounded_deterministic_artifact_and_no_GPL_source_bytes_embedded(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            result = self.small(root / "fake.zip")
            a, b = root / "a.zip", root / "b.zip"
            receipt = bridge.save_output(a, result)
            bridge.save_output(b, result)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as z:
                self.assertEqual(len(z.namelist()), 3)
                for name, expected in receipt["output_sha256"].items():
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), expected)
                manifest = json.loads(z.read(
                    "source_pinned_challenger_NOT_GUL_IL_RI_OEP_AEP.json"))
                self.assertTrue(manifest["no_insured_GUL_IL_RI_or_treaty"])
                self.assertFalse(any(
                    b"Dummy source: GNU General Public License" in z.read(name)
                    for name in z.namelist()
                ))
            with self.assertRaisesRegex(bridge.CLIMADAChallengerBlocked, "fresh"):
                bridge.save_output(a, result)
            symlink = root / "symlink.zip"
            symlink.symlink_to(root / "absent-target")
            with self.assertRaisesRegex(bridge.CLIMADAChallengerBlocked, "fresh"):
                bridge.save_output(symlink, result)

    def test_original_paa_mdd_interpolate_then_multiply_not_knot_mdr_interpolate(self):
        curves = bridge.parse_pinned_public_curves(
            self.model, expected_pins=self.model_pins
        )
        c = curves[bridge.MODEL_NAMES[0]]
        # At 30m/s true PAA=.50 and MDD=.20 => .10. Simple interpolation
        # of knot MDR at 20 (.025) and 40 (.225) would give .125 (WRONG).
        paa = bridge._interp(c["wind"], c["paa"], Decimal(30))
        mdd = bridge._interp(c["wind"], c["mdd"], Decimal(30))
        self.assertEqual(paa * mdd, Decimal(".1"))
        self.assertNotEqual(paa * mdd, Decimal(".125"))


if __name__ == "__main__":
    unittest.main()
