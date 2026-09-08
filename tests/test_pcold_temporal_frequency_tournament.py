from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "research-scripts" / "pcold_temporal_frequency_tournament.py"
SPEC = importlib.util.spec_from_file_location("pcold_temporal_frequency_tournament", SCRIPT)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


class PCOLDTemporalTournamentTests(unittest.TestCase):
    def test_nb2_zero_dispersion_is_poisson(self) -> None:
        y = np.array([0.0, 1.0, 3.0, 8.0])
        mu = np.array([0.2, 0.8, 2.5, 6.0])
        np.testing.assert_allclose(
            m.nb2_logpmf(y, mu, 0.0),
            m.poisson_logpmf(y, mu),
            rtol=0.0,
            atol=0.0,
        )

    def test_moving_block_bootstrap_constant_improvement(self) -> None:
        got = m.moving_block_ci(np.ones(48), m.SEED)
        self.assertEqual(got["block_length_months"], 6)
        self.assertEqual(got["reps"], 10_000)
        self.assertAlmostEqual(got["mean_improvement"], 1.0, places=15)
        self.assertAlmostEqual(got["q025"], 1.0, places=15)
        self.assertAlmostEqual(got["q975"], 1.0, places=15)

    def test_discrete_es_includes_correct_fraction_of_var_atom(self) -> None:
        pmf = np.array([0.5, 0.5])
        got = m.discrete_tail_metrics(pmf, attachment_loss=50.0)
        self.assertEqual(got["VaR99.5"], 100.0)
        self.assertAlmostEqual(got["ES99.5_quantile_integral"], 100.0, places=12)
        self.assertAlmostEqual(got["stop_loss_expectation"], 25.0, places=12)

    def test_validation_selection_requires_score_ci_and_calibration(self) -> None:
        validation = {
            "paired_nll_improvement": {
                "M1-M0": {"mean_improvement": 0.2, "q025": 0.1},
                "M2-M0": {"mean_improvement": 0.3, "q025": -0.01},
                "M3-M0": {"mean_improvement": 0.4, "q025": 0.2},
            },
            "models": {
                "M1": {"mean_nll": 1.0, "catastrophic_calibration_failure": False},
                "M2": {"mean_nll": 0.9, "catastrophic_calibration_failure": False},
                "M3": {"mean_nll": 0.8, "catastrophic_calibration_failure": True},
            },
        }
        got = m.validation_selection(validation)
        self.assertEqual(got["passed_challengers"], ["M1"])
        self.assertEqual(got["winner"], "M1")

    def test_calendar_design_is_four_column_and_train_centered(self) -> None:
        pairs = [(2014, mth) for mth in range(1, 13)] + [(2015, mth) for mth in range(1, 13)]
        keys = np.array([m.month_key(y, mo) for y, mo in pairs])
        train = np.array([y == 2014 for y, _ in pairs])
        X = m.design(keys, pairs, train)
        self.assertEqual(X.shape, (24, 4))
        self.assertAlmostEqual(float(X[train, 1].mean()), 0.0, places=15)
        np.testing.assert_allclose(X[:, 0], 1.0, rtol=0.0, atol=0.0)


if __name__ == "__main__":
    unittest.main()
